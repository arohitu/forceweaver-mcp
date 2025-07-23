"""
Authentication routes using simple session-based authentication
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from app import db, login_user, logout_user
from app.models.user import User
from app.models.salesforce_org import SalesforceOrg
import requests
import urllib.parse

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login route"""
    current_app.logger.info(f"=== LOGIN REQUEST === Method: {request.method}")
    current_app.logger.info(f"Session before: {dict(session)}")
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        current_app.logger.info(f"Login attempt for: {email}")
        
        # Basic validation
        if not email or not password:
            current_app.logger.warning("Missing email or password")
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        # Find user
        try:
            user = User.query.filter_by(email=email).first()
            current_app.logger.info(f"User found: {bool(user)}")
            
            if user:
                current_app.logger.info(f"User active: {user.is_active}")
                current_app.logger.info(f"Testing password...")
                
                # Verify password
                if user.check_password(password):
                    current_app.logger.info("Password verified successfully!")
                    
                    if user.is_active:
                        # Login successful
                        login_user(user)
                        current_app.logger.info(f"Session after login: {dict(session)}")
                        
                        # Get next page from form or URL parameter
                        next_page = request.form.get('next') or request.args.get('next')
                        current_app.logger.info(f"Next page from request: {next_page}")
                        
                        # Validate and construct redirect URL
                        if not next_page or not next_page.startswith('/'):
                            next_page = url_for('dashboard.index')
                        
                        current_app.logger.info(f"Login successful, redirecting to: {next_page}")
                        
                        # Force session to be saved before redirect
                        session.permanent = True
                        
                        return redirect(next_page)
                    else:
                        current_app.logger.warning("User account is inactive")
                        flash('Your account is inactive. Please contact support.', 'error')
                else:
                    current_app.logger.warning("Password verification failed")
                    flash('Invalid email or password', 'error')
            else:
                current_app.logger.warning("User not found")
                flash('Invalid email or password', 'error')
                
        except Exception as e:
            current_app.logger.error(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
    
    current_app.logger.info("Rendering login template")
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    """Simple logout route"""
    current_app.logger.info("User logging out")
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        
        current_app.logger.info(f"Registration attempt for: {email}")
        
        # Validation
        if not email or not name or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email address already registered', 'error')
            return render_template('auth/register.html')
        
        try:
            # Create new user
            user = User(email=email, name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            current_app.logger.info(f"New user registered: {email}")
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')

# Salesforce OAuth routes (keeping existing functionality)
@bp.route('/salesforce/authorize')
def salesforce_authorize():
    """Initiate Salesforce OAuth flow"""
    org_identifier = request.args.get('org_identifier')
    is_sandbox = request.args.get('is_sandbox', 'false').lower() == 'true'
    
    current_app.logger.info(f"Salesforce OAuth request: org={org_identifier}, sandbox={is_sandbox}")
    
    # Store org info in session for callback
    session['oauth_org_identifier'] = org_identifier
    session['oauth_is_sandbox'] = is_sandbox
    
    # Salesforce OAuth URLs
    if is_sandbox:
        auth_url = 'https://test.salesforce.com/services/oauth2/authorize'
    else:
        auth_url = 'https://login.salesforce.com/services/oauth2/authorize'
    
    client_id = current_app.config.get('SALESFORCE_CLIENT_ID')
    redirect_uri = current_app.config.get('SALESFORCE_REDIRECT_URI')
    
    # Build authorization URL
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'full refresh_token'
    }
    
    oauth_url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    current_app.logger.info(f"Redirecting to Salesforce OAuth: {oauth_url}")
    
    return redirect(oauth_url)

@bp.route('/salesforce/callback')
def salesforce_callback():
    """Handle Salesforce OAuth callback"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    current_app.logger.info(f"Salesforce callback: code={bool(code)}, error={error}")
    
    if error:
        flash(f'Salesforce authentication failed: {error}', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    if not code:
        flash('No authorization code received from Salesforce', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    try:
        # Get org info from session
        org_identifier = session.get('oauth_org_identifier')
        is_sandbox = session.get('oauth_is_sandbox', False)
        
        current_app.logger.info(f"Processing OAuth for org: {org_identifier}")
        
        # Exchange code for tokens
        if is_sandbox:
            token_url = 'https://test.salesforce.com/services/oauth2/token'
        else:
            token_url = 'https://login.salesforce.com/services/oauth2/token'
        
        client_id = current_app.config.get('SALESFORCE_CLIENT_ID')
        client_secret = current_app.config.get('SALESFORCE_CLIENT_SECRET')
        redirect_uri = current_app.config.get('SALESFORCE_REDIRECT_URI')
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': code
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            token_info = response.json()
            access_token = token_info.get('access_token')
            refresh_token = token_info.get('refresh_token')
            instance_url = token_info.get('instance_url')
            
            # Get user info
            user_id = session.get('user_id')
            if not user_id:
                flash('Session expired. Please log in again.', 'error')
                return redirect(url_for('auth.login'))
            
            # Create or update Salesforce org
            org = SalesforceOrg.create_for_oauth(
                user_id=user_id,
                org_identifier=org_identifier,
                is_sandbox=is_sandbox
            )
            
            org.set_oauth_tokens(access_token, refresh_token, instance_url)
            db.session.add(org)
            db.session.commit()
            
            current_app.logger.info(f"OAuth successful for org: {org_identifier}")
            flash('Salesforce organization connected successfully!', 'success')
        else:
            current_app.logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            flash('Failed to complete Salesforce authentication', 'error')
            
    except Exception as e:
        current_app.logger.error(f"Salesforce OAuth error: {e}")
        flash('An error occurred during Salesforce authentication', 'error')
    
    # Clean up session
    session.pop('oauth_org_identifier', None)
    session.pop('oauth_is_sandbox', None)
    
    return redirect(url_for('dashboard.orgs')) 