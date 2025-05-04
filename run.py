from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from forms import SearchForm, SellerForm, SignupForm, RegistrationForm
from config import Config
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
import uuid
from functools import wraps

# Initialize Flask app
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Load configuration
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
supabase = Config.init_supabase()

# Ensure upload folder exists (for backup purposes)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user' not in session:
            # Store the requested URL for redirecting after login
            session['next_url'] = request.url
            if request.is_xhr:
                # For AJAX requests
                return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('unauthorized'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')

# Initialize Supabase storage bucket
def initialize_supabase_storage():
    try:
        # Check if bucket exists
        existing_buckets = supabase.storage.list_buckets()
        bucket_name = app.config['SUPABASE_STORAGE_BUCKET']
        
        if not any(bucket['name'] == bucket_name for bucket in existing_buckets):
            # Create the bucket if it doesn't exist
            supabase.storage.create_bucket(
                bucket_name,
                {
                    'public': True,
                    'allowed_mime_types': ['image/*'],
                    'file_size_limit': 5  # MB
                }
            )
            print(f"Created storage bucket: {bucket_name}")
            
            # Set bucket policies
            policy = {
                'action': 'select',
                'effect': 'allow',
                'role': 'authenticated',
                'bucket': bucket_name
            }
            supabase.storage.set_bucket_policy(bucket_name, policy)
            
        return True
    except Exception as e:
        print(f"Error initializing storage: {str(e)}")
        return False

# Call this when the app starts
if supabase:
    initialize_supabase_storage()

# Helper function for file validation
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# Helper function to get car data with image URLs
def get_car_with_image_url(car):
    if car.get('image_path'):
        car['image_url'] = f"{app.config['SUPABASE_URL']}/storage/v1/object/public/{car['image_path']}"
    elif car.get('image_data'):
        car['image_url'] = f"data:image/jpeg;base64,{car['image_data']}"
    return car

# Routes
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('homepage'))
    return redirect(url_for('login'))

@app.route('/homepage')
@login_required
def homepage():
    # Get cars with homepage promotion
    try:
        homepage_cars_response = supabase.table('car_listings').select('*').eq('promotion', 'homepage').execute()
        homepage_cars = [get_car_with_image_url(car) for car in homepage_cars_response.data]
        return render_template('homepage.html', promoted_cars=homepage_cars)
    except Exception as e:
        flash(f'Error loading featured cars: {str(e)}', 'danger')
        return render_template('homepage.html', promoted_cars=[])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('homepage'))
        
    registration_form = RegistrationForm()
    signup_form = SignupForm()
    
    if registration_form.validate_on_submit():
        session['user_type'] = registration_form.user_type.data
        return redirect(url_for('signup'))
        
    return render_template('signup.html', form=signup_form, reg_form=registration_form)

@app.route('/featuredCars')
@login_required
def featuredCars():
    # Get cars with featured promotion
    try:
        featured_cars_response = supabase.table('car_listings').select('*').eq('promotion', 'featured').execute()
        featured_cars = [get_car_with_image_url(car) for car in featured_cars_response.data]
        return render_template('featured-cars.html', featured_cars=featured_cars)
    except Exception as e:
        flash(f'Error loading featured cars: {str(e)}', 'danger')
        return render_template('featured-cars.html', featured_cars=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('homepage'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validate inputs
        if not email or not password:
            flash('Please provide both email and password', 'danger')
            return render_template('login.html')
        
        try:
            # Authenticate with Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response.user:
                flash('Invalid email or password', 'danger')
                return render_template('login.html')
            
            if not auth_response.user.email_confirmed_at:
                flash('Login failed: Email not confirmed. Please check your inbox.', 'danger')
                return redirect(url_for('login'))
                
            user_id = auth_response.user.id
            profile_response = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
            
            if profile_response.data and len(profile_response.data) > 0:
                user_profile = profile_response.data[0]
                
                session['user'] = {
                    'id': user_id,
                    'email': email,
                    'username': user_profile.get('username'),
                    'user_type': user_profile.get('user_type')
                }
                
                flash('Logged in successfully!', 'success')
                
                # Check if there's a next URL to redirect to
                next_url = session.pop('next_url', None)
                if next_url:
                    return redirect(next_url)
                    
                if user_profile.get('user_type') == 'seller':
                    return redirect(url_for('sellers'))
                else:
                    return redirect(url_for('homepage'))
            else:
                flash('User profile not found.', 'danger')
                
        except Exception as e:
            error_message = str(e)
            if "Invalid login credentials" in error_message:
                flash('Invalid email or password', 'danger')
            else:
                flash(f'Login failed: {error_message}', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('homepage'))
        
    signup_form = SignupForm()
    registration_form = RegistrationForm()
    
    if signup_form.validate_on_submit():
        try:
            user_type = request.form.get('user_type', session.get('user_type', 'buyer'))
            auth_response = supabase.auth.sign_up({
                "email": signup_form.email.data,
                "password": signup_form.password.data,
                "options": {
                    "email_confirm": True,
                    "data": {
                        "username": signup_form.username.data,
                        "user_type": user_type
                    },
                    "redirect_to": f"{app.config['SITE_URL']}/confirm-email"
                }
            })
            
            profile_data = {
                "id": auth_response.user.id,
                "username": signup_form.username.data,
                "email": signup_form.email.data,
                "user_type": user_type
            }
            
            supabase.table("user_profiles").insert(profile_data).execute()
            
            flash('Account created! Please check your email to confirm.', 'success')
            return redirect(url_for('login'))
                
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
        
    return render_template('signup.html', form=signup_form, reg_form=registration_form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.before_request
def check_authentication():
    # List of routes that don't require authentication
    public_routes = ['static', 'login', 'register', 'signup', 'logout', 'home', 'unauthorized']
    
    # Check if the route requires authentication
    if request.endpoint and request.endpoint not in public_routes:
        if 'user' not in session:
            # Store the requested URL for redirecting after login
            session['next_url'] = request.url
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # For AJAX requests
                return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('unauthorized'))

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    
    try:
        # Load unique brands from database
        brands_response = supabase.table('car_listings').select('brand').execute()
        unique_brands = list(set([item['brand'] for item in brands_response.data if item.get('brand')]))
        form.brand.choices = [('', 'Select Brand')] + [(brand, brand) for brand in sorted(unique_brands)]
        
        # Initialize model choices
        form.model.choices = [('', 'Select Model')]
        
        # Load year options from database
        years_response = supabase.table('car_listings').select('year').execute()
        unique_years = list(set([item['year'] for item in years_response.data if item.get('year')]))
        form.year.choices = [('', 'Select Year')] + [(str(year), str(year)) for year in sorted(unique_years)]
        
        # Load location options from database
        locations_response = supabase.table('car_listings').select('location').execute()
        unique_locations = list(set([item['location'] for item in locations_response.data if item.get('location')]))
        form.location.choices = [('', 'Select Location')] + [(loc, loc) for loc in sorted(unique_locations)]
        
        # Load condition options
        conditions_response = supabase.table('car_listings').select('condition').execute()
        unique_conditions = list(set([item['condition'] for item in conditions_response.data if item.get('condition')]))
        if unique_conditions:
            form.condition.choices = [('', 'Select Condition')] + [(cond, cond.capitalize()) for cond in sorted(unique_conditions)]
        else:
            form.condition.choices = [('', 'Select Condition'), ('new', 'New'), ('used', 'Used')]
        
        # If a brand is selected, load models for that brand
        if form.brand.data:
            models_response = supabase.table('car_listings').select('model').eq('brand', form.brand.data).execute()
            unique_models = list(set([item['model'] for item in models_response.data if item.get('model')]))
            form.model.choices = [('', 'Select Model')] + [(model, model) for model in sorted(unique_models)]
            
    except Exception as e:
        flash(f'Error loading search filters: {str(e)}', 'danger')
        print(f"Error loading search filters: {str(e)}")
    
    # Process search request
    if request.method == 'POST' or request.args.get('show_all'):
        try:
            # Special case for "show_all" - bypass all filters
            if request.args.get('show_all'):
                results = supabase.table('car_listings').select('*').execute()
                filters_applied = False
            else:
                # Start with a basic query
                query = supabase.table('car_listings').select('*')
                
                # Initialize filters_applied as False
                filters_applied = False
                
                # Build filter conditions
                filters = {
                    'brand': form.brand.data,
                    'model': form.model.data,
                    'year': form.year.data,
                    'condition': form.condition.data,
                    'location': form.location.data
                }
                
                numeric_filters = {
                    'price': (form.min_price.data, form.max_price.data),
                    'mileage': (form.min_mileage.data, form.max_mileage.data)
                }
                
                # Apply exact match filters
                for field, value in filters.items():
                    if value:
                        query = query.eq(field, value)
                        filters_applied = True
                
                # Apply range filters
                for field, (min_val, max_val) in numeric_filters.items():
                    if min_val is not None and min_val > 0:
                        query = query.gte(field, min_val)
                        filters_applied = True
                    if max_val is not None and max_val > 0:
                        query = query.lte(field, max_val)
                        filters_applied = True
                
                # If no filters were applied (empty search), get all vehicles
                if not filters_applied:
                    results = supabase.table('car_listings').select('*').execute()
                else:
                    results = query.execute()
            
            # Process images for results
            processed_results = []
            for car in results.data:
                if car.get('image_path'):
                    car['image_url'] = f"{app.config['SUPABASE_URL']}/storage/v1/object/public/{car['image_path']}"
                elif car.get('image_data'):
                    car['image_url'] = f"data:image/jpeg;base64,{car['image_data']}"
                processed_results.append(car)
            
            # Debug log
            print(f"Found {len(processed_results)} results")
            
            # Store results and search parameters in session
            session['search_results'] = processed_results
            session['search_params'] = {
                'brand': form.brand.data,
                'model': form.model.data,
                'year': form.year.data,
                'min_price': form.min_price.data,
                'max_price': form.max_price.data,
                'min_mileage': form.min_mileage.data,
                'max_mileage': form.max_mileage.data,
                'condition': form.condition.data,
                'location': form.location.data,
                'filters_applied': filters_applied
            }
            
            return redirect(url_for('search_results'))
            
        except Exception as e:
            flash(f'Error searching for cars: {str(e)}', 'danger')
            print(f"Search error: {str(e)}")
            return redirect(url_for('search'))
    
    return render_template('search.html', form=form)

@app.route('/all-vehicles')
@login_required
def all_vehicles():
    # Get all vehicles and set them in the session
    try:
        print("Loading all vehicles...")
        results = supabase.table('car_listings').select('*').execute()
        
        # Process images for results
        processed_results = []
        for car in results.data:
            if car.get('image_path'):
                car['image_url'] = f"{app.config['SUPABASE_URL']}/storage/v1/object/public/{car['image_path']}"
            elif car.get('image_data'):
                car['image_url'] = f"data:image/jpeg;base64,{car['image_data']}"
            processed_results.append(car)
        
        print(f"All vehicles loaded: {len(processed_results)} vehicles found")
        
        # Store results and search parameters in session
        session['search_results'] = processed_results
        session['search_params'] = {
            'filters_applied': False
        }
        
        return redirect(url_for('search_results'))
    except Exception as e:
        flash(f'Error loading vehicles: {str(e)}', 'danger')
        print(f"Error in all_vehicles: {str(e)}")
        return redirect(url_for('search'))

@app.route('/search-results')
@login_required
def search_results():
    # Get search results and parameters from session
    results = session.get('search_results', [])
    search_params = session.get('search_params', {})
    
    # Log for debugging
    print(f"Retrieved {len(results)} results from session")
    
    # Check if we got any results
    if results is None or len(results) == 0:
        # If specific filters were applied but no results found
        if search_params.get('filters_applied', False):
            flash('No vehicles found matching your criteria. Try broadening your search.', 'info')
        else:
            # If no filters were applied but still no results, there might be an issue with the database
            flash('No vehicles are currently available in our system.', 'info')
    
    return render_template('searchresults.html', 
                          results=results,
                          search_params=search_params)

@app.route('/clear-search', methods=['POST'])
@login_required
def clear_search():
    # Clear any search-related session data
    session.pop('search_results', None)
    session.pop('search_params', None)
    return jsonify({'status': 'success'})



# Add these two new route handlers to your run.py file

@app.route('/get_years/')
@login_required
def get_years():
    brand = request.args.get('brand')
    model = request.args.get('model')
    
    if not brand or not model:
        return jsonify({'years': []})
    
    try:
        # Query database for years matching the selected brand and model
        years_response = supabase.table('car_listings')\
            .select('year')\
            .eq('brand', brand)\
            .eq('model', model)\
            .execute()
        
        unique_years = list(set([item['year'] for item in years_response.data if item.get('year')]))
        
        return jsonify({'years': sorted(unique_years)})
    except Exception as e:
        print(f"Error fetching years: {str(e)}")
        return jsonify({'years': []})

@app.route('/get_locations/')
@login_required
def get_locations():
    brand = request.args.get('brand')
    model = request.args.get('model')
    
    if not brand or not model:
        return jsonify({'locations': []})
    
    try:
        # Query database for locations matching the selected brand and model
        locations_response = supabase.table('car_listings')\
            .select('location')\
            .eq('brand', brand)\
            .eq('model', model)\
            .execute()
        
        unique_locations = list(set([item['location'] for item in locations_response.data if item.get('location')]))
        
        return jsonify({'locations': sorted(unique_locations)})
    except Exception as e:
        print(f"Error fetching locations: {str(e)}")
        return jsonify({'locations': []})



@app.route('/get_models/<brand>')
@login_required
def get_models(brand):
    try:
        models_response = supabase.table('car_listings').select('model').eq('brand', brand).execute()
        models = list(set([item['model'] for item in models_response.data if item.get('model')]))
        return jsonify({'models': sorted(models)})
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        return jsonify({'models': []})

@app.route('/sellers', methods=['GET', 'POST'])
@login_required
def sellers():
    form = SellerForm()
    
    if form.validate_on_submit():
        try:
            image_url = None
            image_path = None
            
            if form.images.data:
                image_file = form.images.data
                
                if not allowed_file(image_file.filename):
                    flash('Only JPG, PNG or GIF images are allowed.', 'danger')
                    return redirect(url_for('sellers'))
                
                
                filename = secure_filename(image_file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                bucket_name = app.config['SUPABASE_STORAGE_BUCKET']
                
                try:
                    file_content = image_file.read()
                    
                    # Upload to Supabase storage
                    res = supabase.storage.from_(bucket_name).upload(
                        path=unique_filename,
                        file=file_content,
                        file_options={
                            "content-type": image_file.content_type
                        }
                    )
                    
                    # Get public URL
                    image_url = f"{app.config['SUPABASE_URL']}/storage/v1/object/public/{bucket_name}/{unique_filename}"
                    image_path = f"{bucket_name}/{unique_filename}"
                    
                except Exception as upload_error:
                    print(f"Upload error: {str(upload_error)}")
                    flash('Image upload failed. Please try again.', 'danger')
                    return redirect(url_for('sellers'))
            
            # Get the promotion type from the form
            promotion_type = form.promotion.data
            
            listing_data = {
                "seller_name": form.name.data,
                "seller_email": form.email.data,
                "seller_phone": form.phone.data,
                "brand": form.brand.data,
                "model": form.model.data,
                "year": form.year.data,
                "price": form.price.data,
                "mileage": form.mileage.data,
                "condition": form.condition.data,
                "location": form.location.data,
                "description": form.description.data,
                "image_url": image_url,
                "image_path": image_path,
                "user_id": session.get('user', {}).get('id', None),
                "promotion": promotion_type  # Add promotion type to database
            }
            
            response = supabase.table('car_listings').insert(listing_data).execute()
            
            flash('Vehicle listed successfully!', 'success')
            
            # Redirect based on promotion type
            if promotion_type == 'featured':
                flash('Your car has been added to our Featured Cars collection!', 'success')
                return redirect(url_for('featuredCars'))
            elif promotion_type == 'homepage':
                flash('Your car has been added to our Homepage Spotlight!', 'success')
                return redirect(url_for('homepage'))
            else:
                return redirect(url_for('sellers'))
            
        except Exception as e:
            flash(f'Error submitting listing: {str(e)}', 'danger')
    
    return render_template('sellers.html', form=form)

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True)