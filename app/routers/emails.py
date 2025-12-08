"""
Email processing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services.email_service import email_service
from app.services.ai_service import ai_service
from app.services.quote_service import quote_service

router = APIRouter()


@router.post("/process", response_model=schemas.EmailInboxResponse)
async def process_email(
    email_data: schemas.EmailInboxCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process incoming email and generate quote if possible"""
    # Check if email already processed
    existing = db.query(models.EmailInbox).filter(
        models.EmailInbox.message_id == email_data.message_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already processed")
    
    # Identify business from To: address
    business = quote_service.identify_business_from_email(email_data.to_email or "", db)
    
    # Create email record
    email_dict = email_data.dict()
    email_dict["business_id"] = business.id
    db_email = models.EmailInbox(**email_dict)
    db.add(db_email)
    db.flush()
    
    # Process in background
    background_tasks.add_task(
        quote_service.process_email_and_generate_quote,
        db_email.id,
        db
    )
    
    return db_email


@router.get("/", response_model=List[schemas.EmailInboxResponse])
async def get_emails(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all emails"""
    emails = db.query(models.EmailInbox).offset(skip).limit(limit).all()
    return emails


@router.get("/{email_id}", response_model=schemas.EmailInboxResponse)
async def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get email by ID"""
    email = db.query(models.EmailInbox).filter(models.EmailInbox.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


