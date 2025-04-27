from flask import Flask, render_template, redirect, url_for, request, flash
from forms import SignupForm, RegistrationForm, SearchForm, SellerForm
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='app/templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this!

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    signup_form = SignupForm()
    registration_form = RegistrationForm()
    
    if signup_form.validate_on_submit():
        return redirect(url_for('login'))
        
    return render_template('signup.html', form=signup_form, reg_form=registration_form)


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    
    # Process form submission
    if form.validate_on_submit():
        # Get all the search parameters
        search_params = {
            'brand': form.brand.data,
            'model': form.model.data,
            'year': form.year.data,
            'price': form.price.data,
            'mileage': form.mileage.data,
            'condition': form.condition.data,
            'location': form.location.data
        }
        
        # Here you would typically query your database
        # results = Car.query.filter_by(**search_params).all()
        
        # For now, we'll just pass the search parameters to the template
        return render_template('search_results.html', 
                            form=form,
                            search_params=search_params,
                            results=[])  # Replace with actual results
    
    # For GET requests or invalid form submissions
    return render_template('search.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user_type = form.user_type.data
        
        # Process based on user type
        if user_type == 'buyer':
            flash('Proceeding with buyer registration', 'success')
            return redirect(url_for('buyer_registration'))  # Replace with your actual endpoint
        else:
            flash('Proceeding with seller registration', 'success')
            return redirect(url_for('seller_registration'))  # Replace with your actual endpoint
    
    return render_template('register.html', form=form)

@app.route('/featured-cars')
def featuredCars():
    return render_template('featured-cars.html')

import os
from werkzeug.utils import secure_filename

# Define where uploaded files will be stored
UPLOAD_FOLDER = 'app/static/uploads'
# Make sure this directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/sellers', methods=['GET', 'POST'])
def sellers():
    form = SellerForm()
    if form.validate_on_submit():
        # Process the form data
        name = form.name.data
        email = form.email.data
        phone = form.phone.data
        brand = form.brand.data
        model = form.model.data
        year = form.year.data
        price = form.price.data
        mileage = form.mileage.data
        condition = form.condition.data
        location = form.location.data
        description = form.description.data
        
        # Handle the file upload
        if form.images.data:
            # Get the uploaded file
            image_file = form.images.data
            # Generate a secure filename
            filename = secure_filename(image_file.filename)
            # Create a unique filename to avoid overwriting
            unique_filename = f"{name}_{brand}_{model}_{filename}"
            # Save the file
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            image_file.save(file_path)
            
            # Store the file path in your database or wherever you're storing listings
            image_path = f"uploads/{unique_filename}"
        else:
            image_path = None
        
        # Save all this information to your database
        # This is just a placeholder - replace with your actual database code
        # Example: db.session.add(new_listing)
        # db.session.commit()
        
        flash('Your vehicle listing has been submitted successfully!', 'success')
        return redirect(url_for('sellers'))
    
    return render_template('sellers.html', form=form)

if __name__ == '__main__':
    print("Starting Flask application...")
    app.run(debug=True)