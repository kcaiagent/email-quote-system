"""
OAuth service for Google authentication
"""
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
from app.config import settings
from app.utils import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes
# Use 'mail.google.com' scope for IMAP/SMTP XOAUTH2 access
# This scope allows full access to Gmail via IMAP and SMTP
SCOPES = ['https://mail.google.com/']


class OAuthService:
    """Service for managing Google OAuth authentication"""
    
    @staticmethod
    def get_oauth_flow(redirect_uri: str) -> Flow:
        """
        Create OAuth flow for authorization
        
        Args:
            redirect_uri: Callback URL after authorization
        
        Returns:
            OAuth flow object
        """
        if not settings.GOOGLE_OAUTH_CLIENT_ID or not settings.GOOGLE_OAUTH_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        return flow
    
    @staticmethod
    def get_authorization_url(business_id: int, redirect_uri: str) -> str:
        """
        Get Google OAuth authorization URL
        
        Args:
            business_id: Business ID to associate with this OAuth flow
            redirect_uri: Callback URL
        
        Returns:
            Authorization URL to redirect user to
        """
        flow = OAuthService.get_oauth_flow(redirect_uri)
        
        # Add business_id to state to retrieve it in callback
        state = json.dumps({"business_id": business_id})
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',  # Request refresh token
            include_granted_scopes='false',  # Don't include previously granted scopes (avoids scope mismatch errors)
            prompt='consent',  # Force consent screen to get refresh token
            state=state
        )
        
        return authorization_url
    
    @staticmethod
    def exchange_code_for_tokens(
        authorization_code: str,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Tuple[Dict, Optional[int], Optional[str]]:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            authorization_code: Authorization code from Google callback
            redirect_uri: Callback URL
            state: State parameter (contains business_id)
        
        Returns:
            Tuple of (token_dict, business_id, oauth_email)
            token_dict contains: access_token, refresh_token, expires_in, etc.
        """
        flow = OAuthService.get_oauth_flow(redirect_uri)
        
        # Exchange code for tokens
        flow.fetch_token(code=authorization_code)
        
        credentials = flow.credentials
        
        # Parse business_id from state
        business_id = None
        if state:
            try:
                state_data = json.loads(state)
                business_id = state_data.get("business_id")
            except Exception:
                pass
        
        # Get user info (optional - mail.google.com scope doesn't include userinfo)
        # If this fails, we'll use the business email instead
        oauth_email = None
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            oauth_email = user_info.get('email')
        except Exception as e:
            # This is expected - mail.google.com scope doesn't include userinfo
            # We'll use the business email instead, which is fine
            logger.debug(f"Could not fetch user info (expected with mail.google.com scope): {e}")
            oauth_email = None
        
        token_dict = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        return token_dict, business_id, oauth_email
    
    @staticmethod
    def refresh_access_token(refresh_token_encrypted: str) -> Optional[Dict]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token_encrypted: Encrypted refresh token
        
        Returns:
            Token dictionary with new access token, or None if refresh fails
        """
        try:
            # Decrypt refresh token
            refresh_token_data = decrypt_token(refresh_token_encrypted)
            if not refresh_token_data:
                return None
            
            token_dict = json.loads(refresh_token_data)
            
            # Create credentials object
            credentials = Credentials(
                token=None,  # Will be refreshed
                refresh_token=token_dict.get('refresh_token'),
                token_uri=token_dict.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=token_dict.get('client_id', settings.GOOGLE_OAUTH_CLIENT_ID),
                client_secret=token_dict.get('client_secret', settings.GOOGLE_OAUTH_CLIENT_SECRET),
                scopes=token_dict.get('scopes', SCOPES)
            )
            
            # Refresh the token
            credentials.refresh(Request())
            
            # Update token dict
            token_dict['access_token'] = credentials.token
            token_dict['expiry'] = credentials.expiry.isoformat() if credentials.expiry else None
            
            return token_dict
            
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return None
    
    @staticmethod
    def get_valid_access_token(
        refresh_token_encrypted: str,
        access_token_encrypted: Optional[str],
        expires_at: Optional[datetime]
    ) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary
        
        Args:
            refresh_token_encrypted: Encrypted refresh token
            access_token_encrypted: Current encrypted access token
            expires_at: When current access token expires
        
        Returns:
            Valid access token (decrypted), or None if refresh fails
        """
        # Check if current token is still valid (with 5 minute buffer)
        if access_token_encrypted and expires_at:
            if datetime.now() < expires_at - timedelta(minutes=5):
                # Token is still valid
                return decrypt_token(access_token_encrypted)
        
        # Need to refresh
        logger.info("Access token expired or missing, refreshing...")
        token_dict = OAuthService.refresh_access_token(refresh_token_encrypted)
        
        if token_dict:
            return token_dict.get('access_token')
        
        return None
    
    @staticmethod
    def revoke_token(refresh_token_encrypted: str) -> bool:
        """
        Revoke OAuth token
        
        Args:
            refresh_token_encrypted: Encrypted refresh token to revoke
        
        Returns:
            True if revocation successful
        """
        try:
            refresh_token_data = decrypt_token(refresh_token_encrypted)
            if not refresh_token_data:
                return False
            
            token_dict = json.loads(refresh_token_data)
            refresh_token = token_dict.get('refresh_token')
            
            if not refresh_token:
                return False
            
            # Revoke token via Google API
            Request().post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': refresh_token},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False


# Singleton instance
oauth_service = OAuthService()

