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
    Fetch available API versions from the Salesforce org.
    Returns a list of available API versions, sorted from newest to oldest.
    """
    try:
        logger.info(f"Fetching available API versions for org: {connection.salesforce_org_id}")
        
        # Create a minimal client to fetch versions
        sf_client = get_salesforce_api_client(connection)
        
        # Get the versions endpoint URL
        versions_url = f"{connection.instance_url}/services/data/"
        
        # Use the client's session to make the request
        headers = {
            'Authorization': f'Bearer {sf_client.session_id}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(versions_url, headers=headers)
        response.raise_for_status()
        
        versions_data = response.json()
        
        # Extract version numbers and sort them (newest first)
        versions = []
        for version_info in versions_data:
            if 'version' in version_info:
                version_number = version_info['version']
                # Format as "vXX.0" for consistency
                formatted_version = f"v{version_number}"
                versions.append({
                    'version': formatted_version,
                    'label': f"Version {version_number}",
                    'url': version_info.get('url', '')
                })
        
        # Sort by version number (newest first)
        def version_sort_key(v):
            # Extract numeric part from "v59.0" -> 59.0
            try:
                return float(v['version'][1:])
            except (ValueError, IndexError):
                return 0
        
        versions.sort(key=version_sort_key, reverse=True)
        
        logger.info(f"Found {len(versions)} API versions for org")
        return versions
        
    except Exception as e:
        logger.error(f"Failed to fetch API versions: {str(e)}")
        return []

def update_connection_api_versions(connection):
    """
    Update the connection with the latest available API versions from Salesforce.
    This should be called periodically or when the user requests an update.
    """
    try:
        from app import db
        
        # Check if we need to update (don't fetch too frequently)
        if connection.api_versions_last_updated:
            time_since_update = datetime.utcnow() - connection.api_versions_last_updated
            if time_since_update < timedelta(hours=24):  # Update at most once per day
                logger.info(f"API versions were updated recently, skipping fetch")
                return connection.available_versions_list
        
        logger.info(f"Updating API versions for connection: {connection.salesforce_org_id}")
        
        # Fetch available versions
        versions = get_available_api_versions(connection)
        
        if versions:
            # Store the versions in the connection
            version_list = [v['version'] for v in versions]
            connection.available_versions_list = version_list
            
            # Set preferred version to latest if not already set
            if not connection.preferred_api_version and version_list:
                connection.preferred_api_version = version_list[0]
                logger.info(f"Set preferred API version to latest: {connection.preferred_api_version}")
            
            # Save changes
            db.session.commit()
            logger.info(f"Updated connection with {len(version_list)} API versions")
            
            return version_list
        else:
            logger.warning("No API versions found, using fallback")
            return []
            
    except Exception as e:
        logger.error(f"Error updating API versions: {str(e)}")
        return []