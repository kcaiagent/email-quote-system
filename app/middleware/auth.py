"""
API key authentication middleware
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional
from app.config import settings

# API Key can be provided in header or query parameter
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def verify_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Security(api_key_query)
) -> str:
    """
    Verify API key from header or query parameter
    
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    # Check if API key is configured
    if not settings.API_KEY:
        # If no API key is set, allow access (development mode)
        # In production, this should be required
        return "development_mode"
    
    # Try header first, then query parameter
    api_key = api_key_header or api_key_query
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing. Provide it in X-API-Key header or api_key query parameter."
        )
    
    # In production, you might want to support multiple API keys
    # For now, we'll check against a single key
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return api_key


async def verify_webhook_signature(
    request_body: bytes,
    signature: Optional[str] = None,
    api_key: Optional[str] = None
) -> bool:
    """
    Verify webhook signature for Wix webhooks
    
    Args:
        request_body: Raw request body bytes
        signature: Signature from X-Webhook-Signature header (optional)
        api_key: API key from X-API-Key header or query parameter (optional)
    
    Returns:
        True if signature is valid, False otherwise
    
    Note:
        For now, we'll use API key authentication for webhooks.
        In the future, you can implement HMAC signature verification
        if Wix provides signature headers.
    """
    # If signature verification is enabled, check signature
    if settings.WEBHOOK_SECRET and signature:
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
    
    # Fallback to API key authentication
    if api_key:
        return api_key == settings.API_KEY
    
    # If no authentication method configured, reject in production
    if not settings.DEBUG:
        return False
    
    # Allow in development mode
    return True



