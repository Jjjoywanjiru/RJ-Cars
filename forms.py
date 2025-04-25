from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Optional




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
    
class SearchForm(FlaskForm):
    brand = SelectField('Brand', choices=[
        ('', 'Select Brand'),
        ('Toyota', 'Toyota'),
        ('Honda', 'Honda'),
        ('Ford', 'Ford')
    ], validators=[Optional()])
    
    model = SelectField('Model', choices=[
        ('', 'Select Model'),
        ('Corolla', 'Corolla'),
        ('Civic', 'Civic'),
        ('Mustang', 'Mustang')
    ], validators=[Optional()])
    
    year = IntegerField('Year', validators=[Optional()])
    price = IntegerField('Price', validators=[Optional()])
    mileage = IntegerField('Mileage', validators=[Optional()])
    
    condition = SelectField('Condition', choices=[
        ('', 'Select Condition'),
        ('new', 'New'),
        ('used', 'Used')
    ], validators=[Optional()])
    
    location = StringField('Location', validators=[Optional()])
    
    submit = SubmitField('Search')