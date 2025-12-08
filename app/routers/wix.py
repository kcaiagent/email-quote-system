"""
Wix integration endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Security
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.services.quote_service import quote_service
from app.services.email_service import email_service
from app.middleware.auth import verify_api_key
from app.config import settings

router = APIRouter()


@router.post("/webhook/email", response_model=dict)
async def wix_email_webhook(
    webhook_data: schemas.WixEmailWebhook,
    background_tasks: BackgroundTasks,
    request: Request,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for Wix to send incoming emails
    
    Wix can call this endpoint when a new email is received.
    Requires API key authentication via X-API-Key header.
    """
    # Process email in background
    background_tasks.add_task(
        quote_service.process_wix_email,
        webhook_data,
        db
    )
    
    return {
        "status": "received",
        "message": "Email is being processed"
    }


@router.post("/quote", response_model=schemas.WixQuoteResponse)
async def create_quote_from_wix(
    quote_request: schemas.WixQuoteRequest,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Endpoint for Wix to directly request a quote
    
    This allows Wix frontend to create quotes directly.
    Requires API key authentication via X-API-Key header.
    """
    try:
        quote_result = quote_service.create_quote_from_wix_request(
            db=db,
            request=quote_request
        )
        
        return quote_result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quote/{quote_number}", response_model=schemas.WixQuoteResponse)
async def get_quote_for_wix(
    quote_number: str,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get quote information formatted for Wix
    
    Requires API key authentication via X-API-Key header.
    """
    quote_result = quote_service.get_quote_for_wix(
        db=db,
        quote_number=quote_number
    )
    
    if not quote_result:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return quote_result


