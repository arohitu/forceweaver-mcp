from simple_salesforce import Salesforce
from app.core.security import decrypt_token
from config import Config
import requests
import json
import logging

# Set up logger
logger = logging.getLogger(__name__)

def get_salesforce_api_client(connection):
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
            
        logger.info(f"Refreshing token for {'sandbox' if connection.is_sandbox else 'production'} org")
        logger.info(f"Using token URL: {token_url}")
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
        
        # Step 2: Instantiate the Salesforce client with the new, valid session ID
        sf = Salesforce(
            instance_url=connection.instance_url,
            session_id=new_access_token,
            consumer_key=Config.SALESFORCE_CLIENT_ID,
            consumer_secret=Config.SALESFORCE_CLIENT_SECRET
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