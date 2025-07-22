"""
Web Forms for ForceWeaver Dashboard
Login, registration, and other web forms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    """User login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """User registration form"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data.lower().strip()).first()
        if user:
            raise ValidationError('This email is already registered. Please use a different email.')

class ConnectSalesforceForm(FlaskForm):
    """Form to connect Salesforce org"""
    org_nickname = StringField('Organization Nickname', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Nickname must be between 2 and 100 characters')
    ])
    environment = SelectField('Environment', choices=[
        ('production', 'Production'),
        ('sandbox', 'Sandbox/Developer')
    ], validators=[DataRequired()])
    submit = SubmitField('Connect Salesforce Org')

class APIKeyForm(FlaskForm):
    """Form to manage API keys"""
    key_name = StringField('API Key Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    submit = SubmitField('Create API Key')

class APIVersionForm(FlaskForm):
    """Form to select preferred Salesforce API version"""
    api_version = SelectField('Preferred API Version', validators=[DataRequired()])
    submit = SubmitField('Save API Version')
    
    def __init__(self, connection=None, *args, **kwargs):
        super(APIVersionForm, self).__init__(*args, **kwargs)
        if connection:
            # Get versions with labels from the connection
            versions_with_labels = connection.get_versions_with_labels()
            self.api_version.choices = versions_with_labels
        else:
            self.api_version.choices = []

class RunHealthCheckForm(FlaskForm):
    """Form to run health check"""
    submit = SubmitField('Run Health Check') 