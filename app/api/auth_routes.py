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
        from flask import current_app
        
        current_app.logger.info("=== SALESFORCE OAUTH INITIATION STARTED ===")
        current_app.logger.info(f"Request args: {dict(request.args)}")
        current_app.logger.info(f"Request headers: Host={request.headers.get('Host')}, User-Agent={request.headers.get('User-Agent')}")
        current_app.logger.info(f"Session before: {dict(session)}")
        
        # Check if there's already an active OAuth flow to prevent conflicts
        existing_state = session.get('oauth_state')
        if existing_state:
            current_app.logger.info(f"Found existing OAuth state, clearing old session data: {existing_state}")
            # Clear any existing OAuth session data to start fresh
            for key in ['oauth_state', 'code_verifier', 'token_url', 'customer_email', 'user_id_for_oauth', 'org_nickname', 'environment']:
                session.pop(key, None)
        
        # Generate a fresh state parameter for security
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        current_app.logger.info(f"Generated new OAuth state: {state}")

        # Generate PKCE code verifier and challenge
        code_verifier = secrets.token_urlsafe(64)
        session['code_verifier'] = code_verifier
        hashed_verifier = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(hashed_verifier).decode('utf-8').replace('=', '')
        current_app.logger.info(f"Generated PKCE code_verifier length: {len(code_verifier)}")
        current_app.logger.info(f"Generated PKCE code_challenge: {code_challenge[:20]}...")
        
        # Get customer email from query parameters
        customer_email = request.args.get('email')
        if not customer_email:
            current_app.logger.error("Missing required email parameter in OAuth initiation")
            return jsonify({"error": "Email parameter is required"}), 400
        
        session['customer_email'] = customer_email
        current_app.logger.info(f"Customer email stored in session: {customer_email}")
        
        # Determine Salesforce environment
        environment = request.args.get('environment', 'production').lower()
        current_app.logger.info(f"Salesforce environment requested: {environment}")
        
        if environment == 'sandbox':
            auth_url = "https://test.salesforce.com/services/oauth2/authorize"
            token_url = "https://test.salesforce.com/services/oauth2/token"
        else:
            auth_url = "https://login.salesforce.com/services/oauth2/authorize"
            token_url = "https://login.salesforce.com/services/oauth2/token"
            
        session['token_url'] = token_url
        current_app.logger.info(f"Auth URL: {auth_url}")
        current_app.logger.info(f"Token URL: {token_url}")

        # Build the Salesforce authorization URL with dynamic redirect URI
        redirect_uri = Config.get_salesforce_redirect_uri()
        current_app.logger.info(f"Configured redirect URI: {redirect_uri}")
        
        params = {
            'response_type': 'code',
            'client_id': Config.SALESFORCE_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': 'api refresh_token',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        current_app.logger.info(f"OAuth parameters: {dict(params)}")
        auth_url_with_params = f"{auth_url}?{urllib.parse.urlencode(params)}"
        current_app.logger.info(f"Final OAuth URL: {auth_url_with_params}")
        current_app.logger.info(f"Session after initiation: {dict(session)}")
        current_app.logger.info("=== REDIRECTING TO SALESFORCE ===")
        
        return redirect(auth_url_with_params)
    
    except Exception as e:
        return jsonify({"error": f"Failed to initiate OAuth: {str(e)}"}), 500

@auth_bp.route('/salesforce/callback')
def salesforce_callback():
    """Handle the Salesforce OAuth callback."""
    try:
        from flask import current_app
        
        # 1. Verify state and get code verifier
        returned_state = request.args.get('state')
        code_verifier = session.get('code_verifier')
        token_url = session.get('token_url') # Get the token URL from the session
        stored_state = session.get('oauth_state')
        
        if returned_state != stored_state:
            current_app.logger.error("OAuth state verification failed")
            return jsonify({"error": "Invalid state parameter"}), 400
        
        if not returned_state or returned_state != stored_state or not code_verifier or not token_url:
            error_msg = f"OAuth validation failed - State match: {returned_state == stored_state}, Code verifier: {code_verifier is not None}, Token URL: {token_url is not None}"
            current_app.logger.error(error_msg)
            current_app.logger.error(f"Expected state: {stored_state}")
            current_app.logger.error(f"Received state: {returned_state}")
            
            # If it's a state mismatch (common with multiple OAuth attempts), provide helpful error
            if returned_state and stored_state and returned_state != stored_state:
                return jsonify({"error": "OAuth state mismatch - please try connecting again (avoid multiple clicks)"}), 400
            else:
                return jsonify({"error": "Invalid state, missing code verifier, or missing token URL"}), 400
        
        # 2. Get the authorization code
        code = request.args.get('code')
        current_app.logger.info(f"Authorization code received: {code is not None}")
        if code:
            current_app.logger.info(f"Authorization code length: {len(code)}")
        
        if not code:
            error = request.args.get('error')
            error_description = request.args.get('error_description')
            current_app.logger.error(f"Authorization failed - Error: {error}, Description: {error_description}")
            return jsonify({
                "error": f"Authorization failed: {error}",
                "description": error_description
            }), 400
        
        # 3. Exchange the code for tokens using PKCE
        # Use dynamic redirect URI based on environment
        redirect_uri = Config.get_salesforce_redirect_uri()
        current_app.logger.info(f"Exchanging code for tokens - Redirect URI: {redirect_uri}")
        current_app.logger.info(f"Token exchange URL: {token_url}")
        
        try:
            token_response = exchange_code_for_tokens(code, redirect_uri, code_verifier, token_url)
            current_app.logger.info(f"Token exchange successful - Response keys: {list(token_response.keys())}")
        except Exception as e:
            current_app.logger.error(f"Token exchange failed: {str(e)}")
            raise
        
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        instance_url = token_response.get('instance_url')
        identity_url = token_response.get('id')  # Salesforce provides the identity URL
        
        current_app.logger.info(f"Token validation - Access token: {access_token is not None}, Refresh token: {refresh_token is not None}, Instance URL: {instance_url}")
        current_app.logger.info(f"Identity URL from Salesforce: {identity_url}")
        
        # Check required fields (identity_url only needed for production)
        required_fields = [access_token, refresh_token, instance_url]
        if 'sandbox' not in instance_url.lower():
            required_fields.append(identity_url)
            
        if not all(required_fields):
            current_app.logger.error("Invalid token response - missing required tokens, instance URL, or identity URL")
            return jsonify({"error": "Invalid token response from Salesforce"}), 400
        
        # 4. Get organization information - handle sandbox vs production differently
        is_sandbox = 'sandbox' in instance_url.lower()
        current_app.logger.info(f"Salesforce environment detected - Sandbox: {is_sandbox}")
        
        if is_sandbox:
            # For sandbox environments, extract org info from instance URL and other sources
            # Sandbox URLs are like: https://domain--orgname.sandbox.my.salesforce.com
            import re
            org_match = re.search(r'https://([^.]+)\.sandbox\.my\.salesforce\.com', instance_url)
            if org_match:
                org_identifier = org_match.group(1)
                # Use the org identifier as a pseudo organization ID for sandbox
                salesforce_org_id = f"sandbox_{org_identifier}"
                org_name = session.get('org_nickname', org_identifier.split('--')[-1] if '--' in org_identifier else org_identifier)
                org_type = 'Sandbox'
                current_app.logger.info(f"Sandbox org extracted - ID: {salesforce_org_id}, Name: {org_name}, Type: {org_type}")
            else:
                current_app.logger.error(f"Could not extract org info from sandbox URL: {instance_url}")
                return jsonify({"error": "Unable to extract organization information from sandbox"}), 400
        else:
            # For production environments, use the identity URL to get user info
            current_app.logger.info(f"Getting user info from Salesforce identity URL: {identity_url}")
            try:
                user_info = get_salesforce_user_info(access_token, identity_url)
                current_app.logger.info(f"User info retrieved - Keys: {list(user_info.keys())}")
                current_app.logger.info(f"Organization details: Name={user_info.get('organization_name')}, ID={user_info.get('organization_id')}, Type={user_info.get('organization_type')}")
                
                salesforce_org_id = user_info.get('organization_id')
                org_name = user_info.get('organization_name', session.get('org_nickname', 'My Salesforce Org'))
                org_type = user_info.get('organization_type', 'Production')
                
                if not salesforce_org_id:
                    current_app.logger.error("Unable to retrieve organization ID from Salesforce user info")
                    return jsonify({"error": "Unable to retrieve organization ID"}), 400
            except Exception as e:
                current_app.logger.error(f"Failed to retrieve user info: {str(e)}")
                raise
        
        # 5. Determine if this is a web dashboard or API integration
        web_user_id = session.get('user_id_for_oauth')
        customer_email = session.get('customer_email')
        org_nickname = session.get('org_nickname', 'My Salesforce Org')
        
        current_app.logger.info(f"Integration type determination - Web user ID: {web_user_id}, Customer email: {customer_email}, Org nickname: {org_nickname}")
        current_app.logger.info(f"Full session contents: {dict(session)}")
        
        if web_user_id:
            # Web dashboard integration
            current_app.logger.info(f"Processing web dashboard integration for user ID: {web_user_id}")
            from app.models import User
            user = User.query.get(web_user_id)
            if not user:
                current_app.logger.error(f"User {web_user_id} not found in database")
                return jsonify({"error": "User not found"}), 400
            
            current_app.logger.info(f"User found: {user.email} (ID: {user.id})")
            # Create or get customer for this user
            customer = user.customer
            if not customer:
                current_app.logger.info(f"Creating new customer for user {user.email}")
                customer = Customer(email=user.email, user_id=user.id)
                db.session.add(customer)
                db.session.flush()
                current_app.logger.info(f"New customer created with ID: {customer.id}")
            else:
                current_app.logger.info(f"Existing customer found: {customer.id}")
        else:
            # API integration
            current_app.logger.info(f"Processing API integration for email: {customer_email}")
            customer = Customer.query.filter_by(email=customer_email).first()
            if not customer:
                current_app.logger.info(f"Creating new customer for API integration: {customer_email}")
                customer = Customer(email=customer_email)
                db.session.add(customer)
                db.session.flush()
                current_app.logger.info(f"New API customer created with ID: {customer.id}")
            else:
                current_app.logger.info(f"Existing API customer found: {customer.id}")
        
        # 6. Create or update API key (only if not exists)
        api_key_value = None
        existing_api_key = customer.api_key
        current_app.logger.info(f"API key check - Existing API key: {existing_api_key is not None}")
        
        if not existing_api_key:
            current_app.logger.info("Generating new API key for customer")
            api_key_value = generate_api_key()
            current_app.logger.info("API key generated successfully")
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
            connection.org_name = org_name
            connection.org_type = org_type
            connection.is_sandbox = is_sandbox
        else:
            # Create new connection
            connection = SalesforceConnection(
                salesforce_org_id=salesforce_org_id,
                encrypted_refresh_token=encrypted_refresh_token,
                instance_url=instance_url,
                customer_id=customer.id,
                org_name=org_name,
                org_type=org_type,
                is_sandbox=is_sandbox
            )
            db.session.add(connection)
        
        db.session.commit()
        
        # 9. Clear session data
        session.pop('oauth_state', None)
        session.pop('customer_email', None)
        session.pop('code_verifier', None)
        session.pop('token_url', None)
        
        # 10. Return appropriate response
        current_app.logger.info(f"=== CALLBACK COMPLETION - web_user_id: {web_user_id} ===")
        if web_user_id:
            # Web dashboard - redirect to external dashboard URL
            current_app.logger.info("Processing web dashboard redirect...")
            session.pop('user_id_for_oauth', None)
            session.pop('org_nickname', None)
            from flask import flash
            flash('Salesforce organization connected successfully!', 'success')
            # Redirect to the external dashboard URL instead of relative URL
            redirect_url = Config.get_dashboard_url('/dashboard/salesforce')
            current_app.logger.info(f"Redirecting to external URL: {redirect_url}")
            return redirect(redirect_url)
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
        current_app.logger.error(f"=== SALESFORCE CALLBACK ERROR ===")
        current_app.logger.error(f"Exception: {str(e)}")
        current_app.logger.exception("Full callback error details:")
        db.session.rollback()
        if session.get('user_id_for_oauth'):
            # Web dashboard error
            current_app.logger.error("Handling as web dashboard error...")
            from flask import flash
            flash('Failed to connect Salesforce organization. Please try again.', 'error')
            # Redirect to external dashboard URL for error case too
            error_redirect = Config.get_dashboard_url('/dashboard/salesforce')
            current_app.logger.error(f"Error redirect URL: {error_redirect}")
            return redirect(error_redirect)
        else:
            # API error
            current_app.logger.error("Handling as API error...")
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