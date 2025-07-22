from simple_salesforce import Salesforce
from app.core.security import decrypt_token
from config import Config
import requests
import json
import logging
from datetime import datetime, timedelta

# Set up logger
logger = logging.getLogger(__name__)

def get_salesforce_api_client(connection, api_version=None):
    """Create a Salesforce API client using the stored connection."""
    decrypted_refresh_token = decrypt_token(connection.encrypted_refresh_token)
    
    if not decrypted_refresh_token:
        raise ValueError("Unable to decrypt refresh token")
    
    try:
        # Step 1: Use the correct token URL based on sandbox/production
        if connection.is_sandbox:
            token_url = "https://test.salesforce.com/services/oauth2/token"
        else:
            token_url = "https://login.salesforce.com/services/oauth2/token"
            
        # Determine API version to use
        if not api_version:
            api_version = connection.get_effective_api_version()
            
        logger.info(f"Refreshing token for {'sandbox' if connection.is_sandbox else 'production'} org")
        logger.info(f"Using token URL: {token_url}")
        logger.info(f"Using API version: {api_version}")
        logger.info(f"Instance URL: {connection.instance_url}")
        logger.info(f"Client ID: {Config.SALESFORCE_CLIENT_ID}")
        
        refresh_data = {
            'grant_type': 'refresh_token',
            'client_id': Config.SALESFORCE_CLIENT_ID,
            'client_secret': Config.SALESFORCE_CLIENT_SECRET,
            'refresh_token': decrypted_refresh_token
        }
        
        logger.info(f"Sending token refresh request to: {token_url}")
        response = requests.post(token_url, data=refresh_data)
        
        logger.info(f"Token refresh response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Token refresh failed. Response text: {response.text}")
            logger.error(f"Response headers: {dict(response.headers)}")
            
        response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)
        
        new_token_data = response.json()
        new_access_token = new_token_data.get('access_token')

        if not new_access_token:
            logger.error(f"No access token in response: {new_token_data}")
            raise ValueError("Failed to obtain a new access token from refresh token")

        logger.info("Successfully obtained new access token")
        
        # Step 2: Instantiate the Salesforce client with the specific API version
        sf = Salesforce(
            instance_url=connection.instance_url,
            session_id=new_access_token,
            consumer_key=Config.SALESFORCE_CLIENT_ID,
            consumer_secret=Config.SALESFORCE_CLIENT_SECRET,
            version=api_version  # Specify the API version
        )
        return sf
    except Exception as e:
        logger.error(f"Failed to create Salesforce client: {str(e)}")
        raise ValueError(f"Failed to create Salesforce client: {str(e)}")

def exchange_code_for_tokens(authorization_code, redirect_uri, code_verifier, token_url="https://login.salesforce.com/services/oauth2/token"):
    """Exchange authorization code for access and refresh tokens."""
    
    data = {
        'grant_type': 'authorization_code',
        'client_id': Config.SALESFORCE_CLIENT_ID,
        'client_secret': Config.SALESFORCE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'code': authorization_code,
        'code_verifier': code_verifier
    }
    
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to exchange code for tokens: {response.text}")
    
    return response.json()

def get_salesforce_user_info(access_token, user_info_url):
    """Get user information from Salesforce using the access token and provided identity URL."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(user_info_url, headers=headers)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to get user info: {response.text}")
    
    return response.json()

def get_available_api_versions(connection):
    """
    Fetch available API versions from the Salesforce org using the /services/data endpoint.
    Returns a list of the latest 5 API versions, sorted from newest to oldest.
    """
    try:
        logger.info(f"Fetching available API versions for org: {connection.salesforce_org_id}")
        
        # Get a fresh access token for the request
        decrypted_refresh_token = decrypt_token(connection.encrypted_refresh_token)
        
        if not decrypted_refresh_token:
            raise ValueError("Unable to decrypt refresh token")
        
        # Step 1: Get a fresh access token
        if connection.is_sandbox:
            token_url = "https://test.salesforce.com/services/oauth2/token"
        else:
            token_url = "https://login.salesforce.com/services/oauth2/token"
            
        refresh_data = {
            'grant_type': 'refresh_token',
            'client_id': Config.SALESFORCE_CLIENT_ID,
            'client_secret': Config.SALESFORCE_CLIENT_SECRET,
            'refresh_token': decrypted_refresh_token
        }
        
        token_response = requests.post(token_url, data=refresh_data)
        token_response.raise_for_status()
        
        new_token_data = token_response.json()
        access_token = new_token_data.get('access_token')
        
        if not access_token:
            raise ValueError("Failed to obtain access token for API versions")
        
        # Step 2: Fetch available API versions from /services/data endpoint
        versions_url = f"{connection.instance_url}/services/data"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Fetching API versions from: {versions_url}")
        response = requests.get(versions_url, headers=headers)
        response.raise_for_status()
        
        versions_data = response.json()
        
        # Step 3: Extract and format the latest 5 versions
        all_versions = []
        for version_info in versions_data:
            if 'version' in version_info and 'label' in version_info:
                version_number = version_info['version']
                label = version_info['label']
                
                # Format as "vXX.0" for consistency with our system
                formatted_version = f"v{version_number}"
                
                all_versions.append({
                    'version': formatted_version,
                    'label': label,
                    'raw_version': version_number,
                    'url': version_info.get('url', '')
                })
        
        # Step 4: Sort by version number (newest first) and take latest 5
        def version_sort_key(v):
            try:
                return float(v['raw_version'])
            except (ValueError, TypeError):
                return 0
        
        all_versions.sort(key=version_sort_key, reverse=True)
        
        # Get the latest 5 versions
        latest_versions = all_versions[:5]
        
        logger.info(f"Found {len(all_versions)} total API versions, returning latest 5")
        for version in latest_versions:
            logger.info(f"  {version['version']} ({version['label']})")
        
        return latest_versions
        
    except Exception as e:
        logger.error(f"Failed to fetch API versions: {str(e)}")
        # Return empty list on error - the system will handle fallbacks
        return []

def update_connection_api_versions(connection, force_update=False):
    """
    Update the connection with the latest available API versions from Salesforce.
    This fetches the latest 5 versions from the /services/data endpoint.
    
    Args:
        connection: SalesforceConnection instance
        force_update: If True, bypass time-based update limits
    """
    try:
        from app import db
        
        # For dashboard display, we want fresh data every time
        # Only rate-limit automatic background updates
        if not force_update and connection.api_versions_last_updated:
            time_since_update = datetime.utcnow() - connection.api_versions_last_updated
            if time_since_update < timedelta(hours=1):  # Rate limit to once per hour for auto updates
                logger.info(f"API versions updated recently, returning cached versions")
                return connection.available_versions_list
        
        logger.info(f"Updating API versions for connection: {connection.salesforce_org_id}")
        
        # Fetch available versions (gets latest 5)
        versions_data = get_available_api_versions(connection)
        
        if versions_data:
            # Store both version info and labels for the UI
            version_info = {
                'versions': [],
                'labels': {}
            }
            
            for version_data in versions_data:
                version = version_data['version']  # e.g., "v64.0"
                label = version_data['label']      # e.g., "Summer '25"
                
                version_info['versions'].append(version)
                version_info['labels'][version] = label
            
            # Store the version information
            connection.available_api_versions = json.dumps(version_info)
            connection.api_versions_last_updated = datetime.utcnow()
            
            # Set preferred version to latest if not already set
            if not connection.preferred_api_version and version_info['versions']:
                connection.preferred_api_version = version_info['versions'][0]  # Latest version
                logger.info(f"Set preferred API version to latest: {connection.preferred_api_version}")
            
            # Save changes
            db.session.commit()
            logger.info(f"Updated connection with {len(version_info['versions'])} API versions")
            
            return version_info['versions']
        else:
            logger.warning("No API versions found, using fallback")
            return []
            
    except Exception as e:
        logger.error(f"Error updating API versions: {str(e)}")
        return connection.available_versions_list or []