"""
OAuth endpoints for Google authentication
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json
import logging

from app.database import get_db
from app.models import Business
from app import schemas
from app.services.oauth_service import oauth_service
from app.utils import encrypt_token, decrypt_token
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/authorize/{business_id}", response_model=schemas.OAuthConnectResponse)
async def authorize_business(
    business_id: int,
    redirect_uri: Optional[str] = Query(None, description="Override redirect URI (optional)"),
    db: Session = Depends(get_db)
):
    """
    Initiate OAuth flow for a business
    
    Returns authorization URL that the user should be redirected to.
    After authorization, Google will redirect to the callback endpoint.
    """
    # Verify business exists
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Use provided redirect_uri or default from settings
    callback_uri = redirect_uri or settings.GOOGLE_OAUTH_REDIRECT_URI
    
    try:
        authorization_url = oauth_service.get_authorization_url(
            business_id=business_id,
            redirect_uri=callback_uri
        )
        
        return {
            "authorization_url": authorization_url,
            "business_id": business_id
        }
    
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter with business_id"),
    redirect_uri: Optional[str] = Query(None, description="Redirect URI used in authorization"),
    db: Session = Depends(get_db)
):
    """
    OAuth callback endpoint
    
    Google redirects here after user authorization.
    Exchanges authorization code for tokens and saves them to the business.
    """
    logger.info(f"OAuth callback received. Code present: {bool(code)}, State: {state}")
    
    if not code:
        logger.error("OAuth callback missing authorization code")
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    # Use provided redirect_uri or default from settings
    callback_uri = redirect_uri or settings.GOOGLE_OAUTH_REDIRECT_URI
    logger.info(f"Using redirect URI: {callback_uri}")
    
    try:
        # Exchange code for tokens
        logger.info("Exchanging authorization code for tokens...")
        token_dict, business_id, oauth_email = oauth_service.exchange_code_for_tokens(
            authorization_code=code,
            redirect_uri=callback_uri,
            state=state
        )
        
        logger.info(f"Token exchange successful. Business ID: {business_id}, Email: {oauth_email}")
        
        if not business_id:
            logger.error("Could not identify business from OAuth state")
            raise HTTPException(status_code=400, detail="Could not identify business from OAuth state")
        
        # Get business
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Encrypt and store tokens
        # Store full token dict encrypted (for refresh)
        token_dict_json = json.dumps(token_dict)
        encrypted_token_dict = encrypt_token(token_dict_json)
        
        # Calculate expiry time
        expires_at = None
        if token_dict.get('expiry'):
            try:
                expires_at = datetime.fromisoformat(token_dict['expiry'].replace('Z', '+00:00'))
            except Exception:
                pass
        
        # Update business with OAuth tokens
        business.oauth_refresh_token_encrypted = encrypted_token_dict
        business.oauth_access_token_encrypted = encrypt_token(token_dict.get('access_token', ''))
        business.oauth_token_expires_at = expires_at
        business.oauth_connected_at = datetime.now()
        business.oauth_email = oauth_email
        
        db.commit()
        db.refresh(business)
        
        logger.info(f"OAuth tokens saved successfully for business {business_id}")
        
        # Redirect to success page (Wix or frontend)
        # In production, this should redirect to Wix dashboard
        success_url = f"{settings.FRONTEND_URL}/oauth/success?business_id={business_id}"
        logger.info(f"Redirecting to: {success_url}")
        
        return RedirectResponse(url=success_url)
    
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        error_url = f"{settings.FRONTEND_URL}/oauth/error?error={str(e)}"
        return RedirectResponse(url=error_url)


@router.get("/status/{business_id}", response_model=schemas.OAuthStatusResponse)
async def get_oauth_status(
    business_id: int,
    db: Session = Depends(get_db)
):
    """
    Get OAuth connection status for a business
    """
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    is_connected = bool(
        business.oauth_refresh_token_encrypted and
        business.oauth_connected_at
    )
    
    return {
        "business_id": business.id,
        "is_connected": is_connected,
        "oauth_email": business.oauth_email,
        "oauth_connected_at": business.oauth_connected_at,
        "token_expires_at": business.oauth_token_expires_at
    }


@router.post("/disconnect/{business_id}")
async def disconnect_oauth(
    business_id: int,
    db: Session = Depends(get_db)
):
    """
    Disconnect OAuth for a business (revoke tokens)
    """
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    if not business.oauth_refresh_token_encrypted:
        raise HTTPException(status_code=400, detail="No OAuth connection to disconnect")
    
    # Revoke token with Google
    try:
        oauth_service.revoke_token(business.oauth_refresh_token_encrypted)
    except Exception as e:
        # Continue with cleanup even if revocation fails
        pass
    
    # Clear OAuth data
    business.oauth_refresh_token_encrypted = None
    business.oauth_access_token_encrypted = None
    business.oauth_token_expires_at = None
    business.oauth_connected_at = None
    business.oauth_email = None
    
    db.commit()
    
    return {"message": "OAuth disconnected successfully", "business_id": business_id}

