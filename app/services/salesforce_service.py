from simple_salesforce import Salesforce
from app.core.security import decrypt_token
from config import Config
import requests
import json

def get_salesforce_api_client(connection):
    """Create a Salesforce API client using the stored connection."""
    decrypted_refresh_token = decrypt_token(connection.encrypted_refresh_token)
    
    if not decrypted_refresh_token:
        raise ValueError("Unable to decrypt refresh token")
    
    try:
        # Corrected Instantiation: Do not pass instance_url or session_id here.
        # The refresh_token method will populate them automatically.
        sf = Salesforce(
            consumer_key=Config.SALESFORCE_CLIENT_ID,
            consumer_secret=Config.SALESFORCE_CLIENT_SECRET
        )
        sf.refresh_token(decrypted_refresh_token, instance_url=connection.instance_url)
        return sf
    except Exception as e:
        raise ValueError(f"Failed to create Salesforce client: {str(e)}")

def exchange_code_for_tokens(authorization_code, redirect_uri, code_verifier):
    """Exchange authorization code for access and refresh tokens."""
    token_url = "https://login.salesforce.com/services/oauth2/token"
    
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

def get_salesforce_user_info(access_token, instance_url):
    """Get user information from Salesforce using the access token."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Get user ID from the access token response
    user_info_url = f"{instance_url}/services/oauth2/userinfo"
    
    response = requests.get(user_info_url, headers=headers)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to get user info: {response.text}")
    
    return response.json()