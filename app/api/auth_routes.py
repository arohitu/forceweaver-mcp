from flask import Blueprint, redirect, request, current_app, jsonify, session, url_for
from app.models import Customer, APIKey, SalesforceConnection
from app.core.security import encrypt_token, hash_api_key, generate_api_key
from app.services.salesforce_service import exchange_code_for_tokens, get_salesforce_user_info
from app import db
from config import Config
import urllib.parse
import secrets
import hashlib
import base64

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/salesforce/initiate')
def initiate_salesforce_auth():
    """Initiate the Salesforce OAuth flow with PKCE, supporting production and sandbox."""
    try:
        # Generate a state parameter for security
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state

        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(64)
        session['code_verifier'] = code_verifier
        hashed_verifier = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(hashed_verifier).decode('utf-8').replace('=', '')
        
        # Get customer email from query parameters
        customer_email = request.args.get('email')
        if not customer_email:
            return jsonify({"error": "Email parameter is required"}), 400
        
        session['customer_email'] = customer_email
        
        # Determine Salesforce environment
        environment = request.args.get('environment', 'production').lower()
        if environment == 'sandbox':
            auth_url = "https://test.salesforce.com/services/oauth2/authorize"
            token_url = "https://test.salesforce.com/services/oauth2/token"
        else:
            auth_url = "https://login.salesforce.com/services/oauth2/authorize"
            token_url = "https://login.salesforce.com/services/oauth2/token"
            
        session['token_url'] = token_url

        # Build the Salesforce authorization URL with dynamic redirect URI
        redirect_uri = Config.get_salesforce_redirect_uri()
        params = {
            'response_type': 'code',
            'client_id': Config.SALESFORCE_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': 'api refresh_token',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url_with_params = f"{auth_url}?{urllib.parse.urlencode(params)}"
        
        return redirect(auth_url_with_params)
    
    except Exception as e:
        return jsonify({"error": f"Failed to initiate OAuth: {str(e)}"}), 500

@auth_bp.route('/salesforce/callback')
def salesforce_callback():
    """Handle the Salesforce OAuth callback."""
    try:
        # 1. Verify state and get code verifier
        returned_state = request.args.get('state')
        code_verifier = session.get('code_verifier')
        token_url = session.get('token_url') # Get the token URL from the session

        if not returned_state or returned_state != session.get('oauth_state') or not code_verifier or not token_url:
            return jsonify({"error": "Invalid state, missing code verifier, or missing token URL"}), 400
        
        # 2. Get the authorization code
        code = request.args.get('code')
        if not code:
            error = request.args.get('error')
            error_description = request.args.get('error_description')
            return jsonify({
                "error": f"Authorization failed: {error}",
                "description": error_description
            }), 400
        
        # 3. Exchange the code for tokens using PKCE
        # Use dynamic redirect URI based on environment
        redirect_uri = Config.get_salesforce_redirect_uri()
        token_response = exchange_code_for_tokens(code, redirect_uri, code_verifier, token_url)
        
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        instance_url = token_response.get('instance_url')
        
        if not all([access_token, refresh_token, instance_url]):
            return jsonify({"error": "Invalid token response from Salesforce"}), 400
        
        # 4. Get user info to identify the org
        # The user info endpoint is based on the instance_url returned by Salesforce
        user_info_url = f"{instance_url}/services/oauth2/userinfo"
        user_info = get_salesforce_user_info(access_token, user_info_url)
        salesforce_org_id = user_info.get('organization_id')
        
        if not salesforce_org_id:
            return jsonify({"error": "Unable to retrieve organization ID"}), 400
        
        # 5. Determine if this is a web dashboard or API integration
        web_user_id = session.get('user_id_for_oauth')
        customer_email = session.get('customer_email')
        org_nickname = session.get('org_nickname', 'My Salesforce Org')
        
        if web_user_id:
            # Web dashboard integration
            from app.models import User
            user = User.query.get(web_user_id)
            if not user:
                return jsonify({"error": "User not found"}), 400
            
            # Create or get customer for this user
            customer = user.customer
            if not customer:
                customer = Customer(email=user.email, user_id=user.id)
                db.session.add(customer)
                db.session.flush()
        else:
            # API integration
            customer = Customer.query.filter_by(email=customer_email).first()
            if not customer:
                customer = Customer(email=customer_email)
                db.session.add(customer)
                db.session.flush()
        
        # 6. Create or update API key (only if not exists)
        api_key_value = None
        if not customer.api_key:
            api_key_value = generate_api_key()
            api_key = APIKey(
                hashed_key=hash_api_key(api_key_value),
                customer_id=customer.id,
                name=org_nickname if web_user_id else "API Integration"
            )
            db.session.add(api_key)
        
        # 7. Encrypt and save the refresh token
        encrypted_refresh_token = encrypt_token(refresh_token)
        
        # 8. Create or update Salesforce connection
        connection = SalesforceConnection.query.filter_by(
            customer_id=customer.id
        ).first()
        
        if connection:
            # Update existing connection
            connection.salesforce_org_id = salesforce_org_id
            connection.encrypted_refresh_token = encrypted_refresh_token
            connection.instance_url = instance_url
            connection.org_name = user_info.get('organization_name', org_nickname)
            connection.org_type = user_info.get('organization_type', 'Unknown')
            connection.is_sandbox = 'sandbox' in instance_url.lower()
        else:
            # Create new connection
            connection = SalesforceConnection(
                salesforce_org_id=salesforce_org_id,
                encrypted_refresh_token=encrypted_refresh_token,
                instance_url=instance_url,
                customer_id=customer.id,
                org_name=user_info.get('organization_name', org_nickname),
                org_type=user_info.get('organization_type', 'Unknown'),
                is_sandbox='sandbox' in instance_url.lower()
            )
            db.session.add(connection)
        
        db.session.commit()
        
        # 9. Clear session data
        session.pop('oauth_state', None)
        session.pop('customer_email', None)
        session.pop('code_verifier', None)
        session.pop('token_url', None)
        
        # 10. Return appropriate response
        if web_user_id:
            # Web dashboard - redirect to dashboard
            session.pop('user_id_for_oauth', None)
            session.pop('org_nickname', None)
            from flask import flash
            flash('Salesforce organization connected successfully!', 'success')
            return redirect(url_for('dashboard.salesforce'))
        else:
            # API integration - return JSON
            response_data = {
                "message": "Salesforce connection established successfully",
                "customer_id": customer.id,
                "salesforce_org_id": salesforce_org_id,
                "instance_url": instance_url
            }
            
            if api_key_value:
                response_data["api_key"] = api_key_value
                response_data["note"] = "Please save this API key securely. It will not be shown again."
            
            return jsonify(response_data), 200
    
    except Exception as e:
        db.session.rollback()
        if session.get('user_id_for_oauth'):
            # Web dashboard error
            from flask import flash
            flash('Failed to connect Salesforce organization. Please try again.', 'error')
            return redirect(url_for('dashboard.salesforce'))
        else:
            # API error
            return jsonify({"error": f"OAuth callback failed: {str(e)}"}), 500

@auth_bp.route('/customer/status')
def customer_status():
    """Check the status of a customer's connection."""
    customer_email = request.args.get('email')
    if not customer_email:
        return jsonify({"error": "Email parameter is required"}), 400
    
    customer = Customer.query.filter_by(email=customer_email).first()
    if not customer:
        return jsonify({"connected": False, "message": "Customer not found"}), 404
    
    has_api_key = customer.api_key is not None
    has_salesforce_connection = customer.salesforce_connection is not None
    
    return jsonify({
        "connected": has_api_key and has_salesforce_connection,
        "has_api_key": has_api_key,
        "has_salesforce_connection": has_salesforce_connection,
        "customer_id": customer.id
    })