"""
Upstox OAuth Authentication Helper
"""

import webbrowser
import logging
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
import json
import requests
from config import UPSTOX_API_KEY, UPSTOX_API_SECRET, UPSTOX_REDIRECT_URL

logger = logging.getLogger(__name__)


class UpstoxAuth:
    """Handle Upstox OAuth authentication"""
    
    AUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
    TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"
    
    def __init__(self, api_key: str, api_secret: str, redirect_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_url = redirect_url
        self.access_token = None
    
    def get_auth_url(self) -> str:
        """Generate authorization URL"""
        params = {
            "client_id": self.api_key,
            "redirect_uri": self.redirect_url,
            "response_type": "code"
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    def open_browser_for_auth(self):
        """Open browser for user authorization"""
        auth_url = self.get_auth_url()
        logger.info(f"Opening browser for authentication: {auth_url}")
        webbrowser.open(auth_url)
    
    def get_access_token(self, auth_code: str) -> str:
        """
        Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from callback
        
        Returns:
            Access token string
        """
        try:
            payload = {
                "code": auth_code,
                "client_id": self.api_key,
                "client_secret": self.api_secret,
                "redirect_uri": self.redirect_url,
                "grant_type": "authorization_code"
            }
            
            response = requests.post(self.TOKEN_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                logger.info("Access token obtained successfully")
                return self.access_token
            else:
                logger.error(f"Error getting access token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception in get_access_token: {str(e)}")
            return None


def get_upstox_access_token(api_key: str = None, api_secret: str = None, 
                           redirect_url: str = None) -> str:
    """
    Get Upstox access token through OAuth flow
    
    Returns:
        Access token string
    """
    api_key = api_key or UPSTOX_API_KEY
    api_secret = api_secret or UPSTOX_API_SECRET
    redirect_url = redirect_url or UPSTOX_REDIRECT_URL
    
    auth = UpstoxAuth(api_key, api_secret, redirect_url)
    
    # Open browser for authentication
    auth.open_browser_for_auth()
    
    # Get authorization code from user
    print("\nAfter logging in and authorizing, copy the authorization code from the URL")
    auth_code = input("Enter the authorization code: ").strip()
    
    # Exchange code for access token
    access_token = auth.get_access_token(auth_code)
    
    if access_token:
        # Save token to file for later use
        with open("access_token.txt", "w") as f:
            f.write(access_token)
        logger.info("Access token saved to access_token.txt")
        return access_token
    else:
        logger.error("Failed to get access token")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    token = get_upstox_access_token()
    if token:
        print(f"Access Token: {token}")
