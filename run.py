from flask import Flask, render_template, redirect, url_for
from forms import SignupForm

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
    form = SignupForm()
    if form.validate_on_submit():
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/search')
def search():
    return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=True)