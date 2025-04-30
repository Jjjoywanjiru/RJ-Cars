from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from forms import SearchForm, SellerForm, SignupForm, RegistrationForm
from config import Config
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
import uuid

# Initialize Flask app
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Load configuration
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
supabase = Config.init_supabase()

# Ensure upload folder exists (for backup purposes)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/homepage')
def homepage():
    return render_template('homepage.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    registration_form = RegistrationForm()
    signup_form = SignupForm()
    
    if registration_form.validate_on_submit():
        session['user_type'] = registration_form.user_type.data
        return redirect(url_for('signup'))
        
    return render_template('signup.html', form=signup_form, reg_form=registration_form)

@app.route('/featuredCars')
def featuredCars():
    return render_template('featured-cars.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
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
                
                if user_profile.get('user_type') == 'seller':
                    return redirect(url_for('sellers'))
                else:
                    return redirect(url_for('homepage'))
            else:
                flash('User profile not found.', 'danger')
                
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
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
    return redirect(url_for('home'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    form.condition.choices = [('', 'Select Condition'), ('new', 'New'), ('used', 'Used')]
    
    try:
        brands_response = supabase.table('car_listings').select('brand').execute()
        unique_brands = list(set([item['brand'] for item in brands_response.data if item.get('brand')]))
        form.brand.choices = [('', 'Select Brand')] + [(brand, brand) for brand in sorted(unique_brands)]
        
        form.model.choices = [('', 'Select Model')]
        
        if request.method == 'POST' and request.form.get('brand'):
            brand = request.form.get('brand')
            models_response = supabase.table('car_listings').select('model').eq('brand', brand).execute()
            unique_models = list(set([item['model'] for item in models_response.data if item.get('model')]))
            form.model.choices = [('', 'Select Model')] + [(model, model) for model in sorted(unique_models)]
            
            if request.form.get('model'):
                submitted_model = request.form.get('model')
                if submitted_model not in [choice[0] for choice in form.model.choices]:
                    form.model.choices.append((submitted_model, submitted_model))
        
        conditions_response = supabase.table('car_listings').select('condition').execute()
        unique_conditions = list(set([item['condition'] for item in conditions_response.data if item.get('condition')]))
        if unique_conditions:
            form.condition.choices = [('', 'Select Condition')] + [(cond, cond.capitalize()) for cond in sorted(unique_conditions)]
        
    except Exception as e:
        flash(f'Error loading search filters: {str(e)}', 'danger')
        print(f"Error loading search filters: {str(e)}")
    
    if form.validate_on_submit():
        try:
            query = supabase.table('car_listings').select('*')
            
            if form.brand.data:
                query = query.eq('brand', form.brand.data)
            if form.model.data:
                query = query.eq('model', form.model.data)
            if form.year.data:
                query = query.eq('year', form.year.data)
            if form.price.data:
                query = query.lte('price', form.price.data)
            if form.mileage.data:
                query = query.lte('mileage', form.mileage.data)
            if form.condition.data:
                query = query.eq('condition', form.condition.data)
            if form.location.data:
                query = query.ilike('location', f'%{form.location.data}%')
            
            results = query.execute()
            
            for car in results.data:
                if car.get('image_path'):
                    car['image_url'] = f"{app.config['SUPABASE_URL']}/storage/v1/object/public/{car['image_path']}"
                elif car.get('image_data'):
                    car['image_url'] = f"data:image/jpeg;base64,{car['image_data']}"
            
            session['search_results'] = results.data
            session['search_params'] = {
                'brand': form.brand.data,
                'model': form.model.data,
                'year': form.year.data,
                'price': form.price.data,
                'mileage': form.mileage.data,
                'condition': form.condition.data,
                'location': form.location.data
            }
            
            return redirect(url_for('search_results'))
            
        except Exception as e:
            flash(f'Error searching for cars: {str(e)}', 'danger')
            return redirect(url_for('search'))
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", 'danger')
    
    return render_template('search.html', form=form)

@app.route('/search-results')
def search_results():
    results = session.get('search_results', [])
    search_params = session.get('search_params', {})
    
    session.pop('search_results', None)
    session.pop('search_params', None)
    
    return render_template('searchresults.html', 
                         results=results,
                         search_params=search_params)

@app.route('/get_models/<brand>')
def get_models(brand):
    try:
        models_response = supabase.table('car_listings').select('model').eq('brand', brand).execute()
        models = list(set([item['model'] for item in models_response.data if item.get('model')]))
        return jsonify({'models': sorted(models)})
    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        return jsonify({'models': []})

@app.route('/sellers', methods=['GET', 'POST'])
def sellers():
    brands, models = get_car_options_from_db()
    
    form = SellerForm()
    form.brand.choices = brands
    form.model.choices = models
    
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
                "user_id": session.get('user', {}).get('id', None)
            }
            
            response = supabase.table('car_listings').insert(listing_data).execute()
            
            flash('Vehicle listed successfully!', 'success')
            return redirect(url_for('sellers'))
            
        except Exception as e:
            flash(f'Error submitting listing: {str(e)}', 'danger')
    
    return render_template('sellers.html', form=form)

def get_car_options_from_db():
    try:
        brands_response = supabase.table('car_listings').select('brand').execute()
        brands = [('', 'Select Brand')]
        
        if brands_response.data:
            unique_brands = set(item['brand'] for item in brands_response.data if item.get('brand'))
            brands.extend([(brand, brand) for brand in sorted(unique_brands)])
        
        models_response = supabase.table('car_listings').select('model').execute()
        models = [('', 'Select Model')]
        
        if models_response.data:
            unique_models = set(item['model'] for item in models_response.data if item.get('model'))
            models.extend([(model, model) for model in sorted(unique_models)])
            
        return brands, models
    except Exception as e:
        print(f"Error fetching car options: {str(e)}")
        return [('', 'Select Brand'), ('Toyota', 'Toyota'), ('Honda', 'Honda')], \
               [('', 'Select Model'), ('Corolla', 'Corolla'), ('Civic', 'Civic')]

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True)