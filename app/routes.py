from flask import Blueprint, render_template

# Create a Blueprint for organizing routes
bp = Blueprint('main', __name__)

@bp.route('/login')
def login():
    return render_template('login.html')  # This renders the login.html template