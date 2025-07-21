"""
Web Authentication Routes for ForceWeaver Dashboard
Handles user registration, login, logout, and Google OAuth
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models import User, Customer
from app.web.forms import LoginForm, RegistrationForm
import requests
import secrets
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

web_auth_bp = Blueprint('web_auth', __name__)

@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        
        if user and user.check_password(form.password.data):
            # Update last login
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard.index')
            
            flash('Welcome back!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@web_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing_user:
            flash('An account with this email already exists', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            email=form.email.data.lower().strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip()
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('web_auth.login'))
    
    return render_template('auth/register.html', form=form)

@web_auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('web_auth.login'))

@web_auth_bp.route('/google')
def google_login():
    """Initiate Google OAuth login"""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    # Google OAuth parameters
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={current_app.config.get('GOOGLE_CLIENT_ID')}&"
        f"redirect_uri={url_for('web_auth.google_callback', _external=True)}&"
        f"scope=openid email profile&"
        f"response_type=code&"
        f"state={state}"
    )
    
    return redirect(google_auth_url)

@web_auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # Verify state parameter
        returned_state = request.args.get('state')
        if not returned_state or returned_state != session.get('oauth_state'):
            flash('Invalid state parameter', 'error')
            return redirect(url_for('web_auth.login'))
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            error = request.args.get('error')
            flash(f'Google authentication failed: {error}', 'error')
            return redirect(url_for('web_auth.login'))
        
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
            'client_secret': current_app.config.get('GOOGLE_CLIENT_SECRET'),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('web_auth.google_callback', _external=True)
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'id_token' not in token_json:
            flash('Failed to get user information from Google', 'error')
            return redirect(url_for('web_auth.login'))
        
        # Verify and decode ID token
        id_info = id_token.verify_oauth2_token(
            token_json['id_token'],
            google_requests.Request(),
            current_app.config.get('GOOGLE_CLIENT_ID')
        )
        
        # Extract user information
        google_id = id_info.get('sub')
        email = id_info.get('email')
        first_name = id_info.get('given_name', '')
        last_name = id_info.get('family_name', '')
        
        # Find or create user
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            # Check if user exists with same email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link Google account to existing user
                user.google_id = google_id
            else:
                # Create new user
                user = User(
                    email=email,
                    google_id=google_id,
                    first_name=first_name,
                    last_name=last_name,
                    is_verified=True  # Google accounts are pre-verified
                )
                db.session.add(user)
        
        # Update last login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log in user
        login_user(user)
        
        # Clear session state
        session.pop('oauth_state', None)
        
        flash(f'Welcome, {user.first_name or user.email}!', 'success')
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {e}")
        flash('Google authentication failed. Please try again.', 'error')
        return redirect(url_for('web_auth.login'))

@web_auth_bp.route('/forgot-password')
def forgot_password():
    """Forgot password page (placeholder)"""
    flash('Password reset functionality will be available soon. Please contact support.', 'info')
    return redirect(url_for('web_auth.login')) 