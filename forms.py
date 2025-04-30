from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Optional
from flask_wtf.file import FileField, FileAllowed




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
    # The choices will be populated dynamically from the database
    brand = SelectField('Brand', validators=[Optional()])
    model = SelectField('Model', validators=[Optional()])
    
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
    
    
class SellerForm(FlaskForm):
    # Personal information
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    
    # Car information (choices will be populated dynamically)
    brand = SelectField('Brand', validators=[Optional()])
    model = SelectField('Model', validators=[Optional()])
    
    year = IntegerField('Year', validators=[Optional()])
    price = IntegerField('Price', validators=[Optional()])
    mileage = IntegerField('Mileage', validators=[Optional()])
    
    condition = SelectField('Condition', choices=[
        ('', 'Select Condition'),
        ('new', 'New'),
        ('used', 'Used')
    ], validators=[Optional()])
    
    location = StringField('Location', validators=[Optional()])
    
    # Additional fields
    description = TextAreaField('Description', validators=[Optional()])
    images = FileField('Vehicle Images', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    
    submit = SubmitField('Submit Listing')