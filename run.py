from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from forms import SignupForm, RegistrationForm, SearchForm, SellerForm
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
            
            # Get user profile data including user_type
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
                    return redirect(url_for('home'))
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
            # 1. Create auth user
            auth_response = supabase.auth.sign_up({
                "email": signup_form.email.data,
                "password": signup_form.password.data
            })
            
            # 2. Create profile in user_profiles table with user type
            profile_data = {
                "id": auth_response.user.id,
                "username": signup_form.username.data,
                "email": signup_form.email.data,
                "user_type": session.get('user_type', 'buyer')  # Default to buyer if not specified
            }
            
            supabase.table("user_profiles").insert(profile_data).execute()
            
            # Store user info in session
            session['user'] = {
                'id': auth_response.user.id,
                'email': signup_form.email.data,
                'username': signup_form.username.data,
                'user_type': session.get('user_type', 'buyer')
            }
            
            flash('Account created successfully!', 'success')
            
            # Redirect based on user type
            if session.get('user_type') == 'seller':
                return redirect(url_for('sellers'))
            else:
                return redirect(url_for('home'))
                
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
        
    # Always pass both forms to the template
    return render_template('signup.html', form=signup_form, reg_form=registration_form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    
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


@app.before_request
def check_user_type():
    # List of routes that sellers should be redirected from if they try to access
    buyer_only_routes = ['/search']
    
    # List of routes that buyers should be redirected from if they try to access
    seller_only_routes = ['/sellers']
    
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
            return redirect(url_for('home'))

@app.route('/sellers', methods=['GET', 'POST'])
def sellers():
    form = SellerForm()
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