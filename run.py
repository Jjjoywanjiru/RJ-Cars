from flask import Flask, render_template

# Create the Flask application
app = Flask(__name__, 
            template_folder='app/templates')  # Point to your templates folder

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/search')
def search():
    return render_template('search.html')

# Add other routes for your templates

if __name__ == '__main__':
    app.run(debug=True)