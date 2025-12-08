"""
Quote endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services.quote_service import quote_service

router = APIRouter()


@router.post("/", response_model=schemas.QuoteResponse)
async def create_quote(quote: schemas.QuoteCreate, db: Session = Depends(get_db)):
    """Create a new quote"""
    # Validate dimensions
    is_valid, error_msg = quote_service.validate_dimensions(
        db, quote.product_id, quote.length_inches, quote.width_inches
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Create quote
    db_quote = quote_service.create_quote(
        db=db,
        business_id=quote.business_id,
        customer_id=quote.customer_id,
        product_id=quote.product_id,
        length_inches=quote.length_inches,
        width_inches=quote.width_inches,
        notes=quote.notes
    )
    
    return db_quote


@router.get("/", response_model=List[schemas.QuoteResponse])
async def get_quotes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all quotes"""
    quotes = db.query(models.Quote).offset(skip).limit(limit).all()
    return quotes


@router.get("/{quote_id}", response_model=schemas.QuoteResponse)
async def get_quote(quote_id: int, db: Session = Depends(get_db)):
    """Get quote by ID"""
    quote = db.query(models.Quote).filter(models.Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.get("/number/{quote_number}", response_model=schemas.QuoteResponse)
async def get_quote_by_number(quote_number: str, db: Session = Depends(get_db)):
    """Get quote by quote number"""
    quote = db.query(models.Quote).filter(
        models.Quote.quote_number == quote_number
    ).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


