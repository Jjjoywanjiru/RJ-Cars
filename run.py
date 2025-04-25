from flask import Flask, render_template, redirect, url_for
from forms import SignupForm, RegistrationForm


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

@app.route('/search')
def search():
    return render_template('search.html')

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


if __name__ == '__main__':
    app.run(debug=True)