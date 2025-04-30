from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from forms import SearchForm, SellerForm, SignupForm, RegistrationForm
from config import Config
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename


# Initialize Flask app
app = Flask(__name__, template_folder='app/templates')

# Load configuration
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
supabase = Config.init_supabase()

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Rest of your routes remain the same...
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
        # Store the user_type in session
        session['user_type'] = registration_form.user_type.data
        return redirect(url_for('signup'))
        
    return render_template('signup.html', form=signup_form, reg_form=registration_form)


@app.route('/featuredCars')
def featuredCars():
    return render_template('featured-cars.html')  # Added 'return' keyword

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Authenticate with Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Check if email is confirmed in Supabase auth
            if not auth_response.user.email_confirmed_at:
                flash('Login failed: Email not confirmed. Please check your inbox and confirm your email.', 'danger')
                return redirect(url_for('login'))
                
            # Get user profile data
            user_id = auth_response.user.id
            profile_response = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
            
            if profile_response.data and len(profile_response.data) > 0:
                user_profile = profile_response.data[0]
                
                # Store user in session
                session['user'] = {
                    'id': user_id,
                    'email': email,
                    'username': user_profile.get('username'),
                    'user_type': user_profile.get('user_type')
                }
                
                flash('Logged in successfully!', 'success')
                
                # Redirect based on user type
                if user_profile.get('user_type') == 'seller':
                    return redirect(url_for('sellers'))
                else:
                    return redirect(url_for('homepage'))
            else:
                flash('User profile not found.', 'danger')
                
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'danger')
    
    return render_template('login.html')
# Add this middleware to check user type and redirect if needed

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_form = SignupForm()
    registration_form = RegistrationForm()  # Create registration form instance
    
    if signup_form.validate_on_submit():
        try:
            
            user_type = request.form.get('user_type', session.get('user_type', 'buyer'))
            # 1. Create auth user with email confirmation enabled
            auth_response = supabase.auth.sign_up({
                "email": signup_form.email.data,
                "password": signup_form.password.data,
                "options": {
                    "email_confirm": True,  # Enable email confirmation
                    "data": {
                        "username": signup_form.username.data,
                        "user_type": user_type
                    },
                    # Define redirect URL for email confirmation
                    "redirect_to": f"{app.config['SITE_URL']}/confirm-email"
                }
            })
            
            # 2. Create profile in user_profiles table with user type
            profile_data = {
                "id": auth_response.user.id,
                "username": signup_form.username.data,
                "email": signup_form.email.data,
                "user_type": user_type # Default to buyer if not specified
                # Removed the email_confirmed field
            }
            
            supabase.table("user_profiles").insert(profile_data).execute()
            
            flash('Account created successfully! Please check your email to confirm your account before logging in.', 'success')
            return redirect(url_for('login'))
                
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
        
    # Always pass both forms to the template
    return render_template('signup.html', form=signup_form, reg_form=registration_form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# Helper function to get brands and models from database
def get_car_options_from_db():
    try:
        # Fetch all unique brands from the cars table
        brands_response = supabase.table('cars_listings').select('brand').execute()
        brands = [('', 'Select Brand')]  # Default empty option
        
        if brands_response.data:
            # Extract unique brands and add to list
            unique_brands = set(item['brand'] for item in brands_response.data if item.get('brand'))
            brands.extend([(brand, brand) for brand in sorted(unique_brands)])
        
        # Fetch all unique models from the cars table
        models_response = supabase.table('cars_listings').select('model').execute()
        models = [('', 'Select Model')]  # Default empty option
        
        if models_response.data:
            # Extract unique models and add to list
            unique_models = set(item['model'] for item in models_response.data if item.get('model'))
            models.extend([(model, model) for model in sorted(unique_models)])
            
        return brands, models
    except Exception as e:
        print(f"Error fetching car options: {str(e)}")
        # Return default options in case of error
        return [('', 'Select Brand'), ('Toyota', 'Toyota'), ('Honda', 'Honda'), ('Ford', 'Ford')], \
               [('', 'Select Model'), ('Corolla', 'Corolla'), ('Civic', 'Civic'), ('Mustang', 'Mustang')]

@app.route('/search', methods=['GET', 'POST'])
def search():
    # Get brand and model options from database
    brands, models = get_car_options_from_db()
    
    # Create form with dynamic choices
    form = SearchForm()
    form.brand.choices = brands
    form.model.choices = models
    
    if form.validate_on_submit():
        # Build query for Supabase
        query = supabase.table('cars').select('*')
        
        if form.brand.data:
            query = query.eq('brand', form.brand.data)
        if form.model.data:
            query = query.eq('model', form.model.data)
        if form.year.data:
            query = query.eq('year', form.year.data)
        if form.price.data:
            query = query.lte('price', form.price.data)  # Less than or equal to
        if form.mileage.data:
            query = query.lte('mileage', form.mileage.data)
        if form.condition.data:
            query = query.eq('condition', form.condition.data)
        if form.location.data:
            query = query.ilike('location', f'%{form.location.data}%')
        
        try:
            results = query.execute()
            return render_template('search_results.html', 
                                form=form,
                                search_params=form.data,
                                results=results.data)
        except Exception as e:
            flash('Error searching for cars.', 'danger')
            return render_template('search_results.html', 
                                form=form,
                                search_params=form.data,
                                results=[])
    
    return render_template('search.html', form=form)

# Ajax endpoint to get models for a selected brand
@app.route('/get_models/<brand>', methods=['GET'])
def get_models(brand):
    try:
        if not brand or brand == 'Select Brand':
            # If no brand selected, return all models
            models_response = supabase.table('cars_listings').select('model').execute()
        else:
            # Filter models by brand
            models_response = supabase.table('cars_listings').select('model').eq('brand', brand).execute()
        
        models = [('', 'Select Model')]  # Default empty option
        if models_response.data:
            # Extract unique models and add to list
            unique_models = set(item['model'] for item in models_response.data if item.get('model'))
            models.extend([(model, model) for model in sorted(unique_models)])
            
        return jsonify(models)
    except Exception as e:
        return jsonify([('', f'Error: {str(e)}')])


@app.before_request
def check_user_type():
    # List of routes that sellers should be redirected from if they try to access
    buyer_only_routes = []
    
    # List of routes that buyers should be redirected from if they try to access
    seller_only_routes = []
    
    # Get current user type from session
    user_type = session.get('user', {}).get('user_type')
    
    # If user is logged in and has a type
    if user_type:
        # If seller tries to access buyer-only route
        if user_type == 'seller' and request.path in buyer_only_routes:
            flash('That page is for buyers only.', 'warning')
            return redirect(url_for('sellers'))
            
        # If buyer tries to access seller-only route
        elif user_type == 'buyer' and request.path in seller_only_routes:
            flash('That page is for sellers only.', 'warning')
            return redirect(url_for('homepage'))


@app.route('/confirm-email', methods=['GET'])
def confirm_email():
    # Get the token from the query parameters
    token = request.args.get('token')
    
    if not token:
        flash('Invalid confirmation link.', 'danger')
        return redirect(url_for('login'))
    
    try:
        # Use the token to verify the user's email
        result = supabase.auth.verify_email_otp({
            "token": token,
            "type": "signup"
        })
        
        if result and result.user:
            # Email confirmed successfully
            flash('Your email has been confirmed successfully! You can now log in.', 'success')
        else:
            flash('Email verification failed.', 'danger')
            
    except Exception as e:
        flash(f'Email confirmation error: {str(e)}', 'danger')
    
    return redirect(url_for('login'))

@app.route('/sellers', methods=['GET', 'POST'])
def sellers():
    # Get brand and model options from database for the seller form
    brands, models = get_car_options_from_db()
    
    form = SellerForm()
    form.brand.choices = brands
    form.model.choices = models
    
    if form.validate_on_submit():
        # Handle the file upload
        image_path = None
        if form.images.data:
            image_file = form.images.data
            filename = secure_filename(image_file.filename)
            unique_filename = f"{form.name.data}_{form.brand.data}_{form.model.data}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            image_file.save(file_path)
            image_path = f"uploads/{unique_filename}"
        
        try:
            # Insert car listing into Supabase
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
                "image_path": image_path,
                "user_id": session.get('user', {}).get('id', None)  # Link to user if logged in
            }
            
            response = supabase.table('car_listings').insert(listing_data).execute()
            
            flash('Your vehicle listing has been submitted successfully!', 'success')
            return redirect(url_for('sellers'))
        except Exception as e:
            flash(f'Error submitting listing: {str(e)}', 'danger')
    
    return render_template('sellers.html', form=form)

@app.route('/test-db')
def test_db():
    try:
        # Check if Supabase is initialized
        if not supabase:
            return "Supabase client not initialized!", 500
            
        # Try to check tables
        tables = ["user_profiles", "cars", "car_listings"]
        results = {}
        
        for table in tables:
            try:
                query = supabase.table(table).select("*").limit(1).execute()
                results[table] = f"Table exists, found {len(query.data)} records"
            except Exception as e:
                results[table] = f"Error: {str(e)}"
                
        # Also add environment variables check
        env_vars = {
            "SUPABASE_URL": Config.SUPABASE_URL,
            "SUPABASE_KEY": "Present" if Config.SUPABASE_KEY else "Missing",
            "DB_PASSWORD": "Present" if os.environ.get("DB_PASSWORD") else "Missing"
        }
        
        return {
            "database_tables": results,
            "environment": env_vars
        }
        
    except Exception as e:
        return f"Database test failed: {str(e)}", 500

    
@app.route('/check-env')
def check_env():
    return {
        'SUPABASE_URL': os.environ.get("SUPABASE_URL"),
        'SUPABASE_KEY_exists': bool(os.environ.get("SUPABASE_KEY"))
    }

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True)