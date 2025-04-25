from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo



class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
class RegistrationForm(FlaskForm):
    user_type = RadioField(
        'I am a:',
        choices=[('buyer', 'Buyer'), ('seller', 'Seller')],
        validators=[DataRequired(message="Please select your role")]
    )
    submit = SubmitField('Continue')