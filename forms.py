from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Optional
from flask_wtf.file import FileField, FileAllowed


class SignupForm(FlaskForm):
    username = StringField('Full Name', validators=[DataRequired()])
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
    brand = SelectField('Brand', choices=[], validators=[Optional()])
    model = SelectField('Model', choices=[], validators=[Optional()])
    year = SelectField('Year', choices=[], validators=[Optional()])
    min_price = IntegerField('Min Price', validators=[Optional()])
    max_price = IntegerField('Max Price', validators=[Optional()])
    min_mileage = IntegerField('Min Mileage', validators=[Optional()])
    max_mileage = IntegerField('Max Mileage', validators=[Optional()])
    # Initialize with default conditions
    condition = SelectField('Condition', choices=[
        ('', 'Select Condition'),
        ('new', 'New'),
        ('used', 'Used')
    ], validators=[Optional()])
    location = SelectField('Location', choices=[], validators=[Optional()])
    submit = SubmitField('Search')
    
    

class SellerForm(FlaskForm):
    # Personal information
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    
    # Car information - changed to StringField to allow any input
    brand = StringField('Brand', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    
    year = IntegerField('Year', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    mileage = IntegerField('Mileage', validators=[DataRequired()])
    
    condition = SelectField('Condition', choices=[
        ('', 'Select Condition'),
        ('new', 'New'),
        ('used', 'Used')
    ], validators=[DataRequired()])
    
    location = StringField('Location', validators=[DataRequired()])
    
    # Additional fields
    description = TextAreaField('Description', validators=[Optional()])
    images = FileField('Vehicle Images', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    
    # Add promotion field
    promotion = RadioField(
        'Promotional Placement',
        choices=[
            ('none', 'Standard Listing'),
            ('featured', 'Featured Cars Collection'),
            ('homepage', 'Homepage Spotlight')
        ],
        default='none'
    )
    
    submit = SubmitField('Submit Listing')