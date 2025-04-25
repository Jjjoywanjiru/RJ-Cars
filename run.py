from flask import Flask, render_template, redirect, url_for, request, flash
from forms import SignupForm, RegistrationForm, SearchForm

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


if __name__ == '__main__':
    app.run(debug=True)