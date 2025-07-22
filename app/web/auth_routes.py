"""
Authentication routes for the ForceWeaver MCP Server
"""
import os
import uuid
import urllib.parse
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.salesforce_org import SalesforceOrg
from app import db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validation
        if not all([name, email, password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
        
        if password != password_confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please sign in instead.', 'error')
            return render_template('auth/register.html')
        
        try:
            # Create user
            user = User.create_user(email=email, name=name, password=password)
            login_user(user)
            flash(f'Welcome to ForceWeaver, {user.name}!', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
            current_app.logger.error(f'Registration error: {e}')
    
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        current_app.logger.info(f"Login attempt for email: {email}")
        
        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        current_app.logger.info(f"User found: {bool(user)}")
        
        if user and user.check_password(password):
            current_app.logger.info(f"Password check passed for user: {user.email}")
            if user.is_active:
                current_app.logger.info("User is active, attempting login_user")
                current_app.logger.info(f"Before login_user - session: {dict(session)}")
                login_user(user)
                current_app.logger.info(f"After login_user - session: {dict(session)}")
                current_app.logger.info(f"login_user completed, current_user authenticated: {current_user.is_authenticated if current_user else 'No current_user'}")
                
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('dashboard.index')
                current_app.logger.info(f"Redirecting to: {next_page}")
                return redirect(next_page)
            else:
                current_app.logger.warning(f"User {user.email} is not active")
                flash('Your account has been deactivated. Please contact support.', 'error')
        else:
            current_app.logger.warning(f"Authentication failed for email: {email}")
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html')

# Salesforce OAuth Routes

@bp.route('/salesforce/authorize')
@login_required
def salesforce_authorize():
    """Initiate Salesforce OAuth flow"""
    org_identifier = request.args.get('org_identifier')
    is_sandbox = request.args.get('is_sandbox', 'false').lower() == 'true'
    
    if not org_identifier:
        flash('Org identifier is required.', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    # Store org info in session for callback
    session['oauth_org_identifier'] = org_identifier
    session['oauth_is_sandbox'] = is_sandbox
    session['oauth_state'] = str(uuid.uuid4())
    
    # Salesforce OAuth endpoints
    if is_sandbox:
        auth_url = "https://test.salesforce.com/services/oauth2/authorize"
    else:
        auth_url = "https://login.salesforce.com/services/oauth2/authorize"
    
    # OAuth parameters
    params = {
        'response_type': 'code',
        'client_id': os.environ.get('SALESFORCE_CLIENT_ID'),
        'redirect_uri': os.environ.get('SALESFORCE_REDIRECT_URI'),
        'scope': 'api refresh_token',
        'state': session['oauth_state']
    }
    
    oauth_url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    return redirect(oauth_url)

@bp.route('/salesforce/callback')
@login_required
def salesforce_callback():
    """Handle Salesforce OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    # Check for OAuth errors
    if error:
        flash(f'Salesforce authorization failed: {error}', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    # Validate state parameter
    if not state or state != session.get('oauth_state'):
        flash('Invalid OAuth state. Please try again.', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    if not code:
        flash('No authorization code received from Salesforce.', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    try:
        # Get org info from session
        org_identifier = session.get('oauth_org_identifier')
        is_sandbox = session.get('oauth_is_sandbox', False)
        
        if not org_identifier:
            flash('Session expired. Please try again.', 'error')
            return redirect(url_for('dashboard.orgs'))
        
        # Exchange code for tokens
        token_url = "https://test.salesforce.com/services/oauth2/token" if is_sandbox else "https://login.salesforce.com/services/oauth2/token"
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': os.environ.get('SALESFORCE_CLIENT_ID'),
            'client_secret': os.environ.get('SALESFORCE_CLIENT_SECRET'),
            'redirect_uri': os.environ.get('SALESFORCE_REDIRECT_URI'),
            'code': code
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code != 200:
            flash('Failed to exchange authorization code for tokens.', 'error')
            current_app.logger.error(f'Token exchange failed: {response.text}')
            return redirect(url_for('dashboard.orgs'))
        
        token_response = response.json()
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        instance_url = token_response.get('instance_url')
        
        if not all([access_token, refresh_token, instance_url]):
            flash('Incomplete token response from Salesforce.', 'error')
            return redirect(url_for('dashboard.orgs'))
        
        # Get user info from Salesforce
        user_info_response = requests.get(
            f"{instance_url}/services/oauth2/userinfo",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        org_name = None
        org_id = None
        if user_info_response.status_code == 200:
            user_info = user_info_response.json()
            org_name = user_info.get('organization_name')
            org_id = user_info.get('organization_id')
        
        # Create or update Salesforce org
        try:
            salesforce_org = SalesforceOrg.create_for_oauth(
                user_id=current_user.id,
                org_identifier=org_identifier,
                is_sandbox=is_sandbox
            )
        except ValueError as e:
            # Org identifier already exists, update it
            salesforce_org = SalesforceOrg.get_by_identifier_and_user(org_identifier, current_user.id)
            if not salesforce_org:
                flash(str(e), 'error')
                return redirect(url_for('dashboard.orgs'))
        
        # Set OAuth tokens and org info
        salesforce_org.set_oauth_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            instance_url=instance_url,
            org_id=org_id,
            org_name=org_name
        )
        
        # Clear session data
        session.pop('oauth_org_identifier', None)
        session.pop('oauth_is_sandbox', None)
        session.pop('oauth_state', None)
        
        flash(f'Successfully connected to Salesforce org "{org_identifier}"!', 'success')
        return redirect(url_for('dashboard.orgs'))
        
    except Exception as e:
        flash('An error occurred during Salesforce authentication.', 'error')
        current_app.logger.error(f'OAuth callback error: {e}')
        return redirect(url_for('dashboard.orgs')) 