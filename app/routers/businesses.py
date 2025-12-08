"""
Business management endpoints
"""
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Security
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models, schemas
# Password utilities removed - OAuth only now
from app.config import settings
from app.services.document_parser_service import document_parser_service
from app.services.pricing_formula_service import pricing_formula_service
from app.services.scheduler_service import poll_business_emails
from app.middleware.auth import verify_api_key

router = APIRouter()


@router.post("/", response_model=schemas.BusinessResponse)
async def create_business(
    business: schemas.BusinessCreate,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_db)
):
    """Create a new business (requires API key)"""
    # Check if business with same email already exists
    existing = db.query(models.Business).filter(
        models.Business.email == business.email
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Business with this email already exists")
    
    db_business = models.Business(
        name=business.name,
        email=business.email,
        imap_host=business.imap_host,
        imap_port=business.imap_port,
        poll_interval_minutes=business.poll_interval_minutes,
        active=True
    )
    
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    
    return db_business


@router.get("/", response_model=List[schemas.BusinessResponse])
async def get_businesses(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all businesses"""
    query = db.query(models.Business)
    
    if active_only:
        query = query.filter(models.Business.active == True)
    
    businesses = query.offset(skip).limit(limit).all()
    return businesses


@router.get("/{business_id}", response_model=schemas.BusinessResponse)
async def get_business(
    business_id: int,
    db: Session = Depends(get_db)
):
    """Get business by ID"""
    business = db.query(models.Business).filter(
        models.Business.id == business_id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    return business


@router.put("/{business_id}", response_model=schemas.BusinessResponse)
async def update_business(
    business_id: int,
    business_update: schemas.BusinessUpdate,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_db)
):
    """Update business (requires API key)"""
    db_business = db.query(models.Business).filter(
        models.Business.id == business_id
    ).first()
    
    if not db_business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Update fields if provided
    update_data = business_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_business, key, value)
    
    db.commit()
    db.refresh(db_business)
    
    return db_business


@router.delete("/{business_id}")
async def delete_business(
    business_id: int,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_db)
):
    """Delete business (soft delete - set active=False) (requires API key)"""
    db_business = db.query(models.Business).filter(
        models.Business.id == business_id
    ).first()
    
    if not db_business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Soft delete
    db_business.active = False
    db.commit()
    
    return {"message": "Business deleted successfully"}


# Email setup endpoint removed - use OAuth endpoints instead
# POST /api/oauth/google/authorize/{business_id} to connect Gmail account


@router.get("/{business_id}/products", response_model=List[schemas.ProductResponse])
async def get_business_products(
    business_id: int,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all products for a business"""
    business = db.query(models.Business).filter(
        models.Business.id == business_id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    query = db.query(models.Product).filter(
        models.Product.business_id == business_id
    )
    
    if active_only:
        query = query.filter(models.Product.active == True)
    
    products = query.offset(skip).limit(limit).all()
    return products


@router.post("/{business_id}/pricing/upload")
async def upload_pricing_document(
    business_id: int,
    file: UploadFile = File(...),
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_db)
):
    """Upload pricing document (CSV, PDF, Excel, Word) and extract products (requires API key)"""
    business = db.query(models.Business).filter(
        models.Business.id == business_id
    ).first()
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}"
        )
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Create upload directory for business
    upload_dir = os.path.join(settings.UPLOAD_DIR, "pricing", str(business_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    try:
        # Parse document
        parse_result = document_parser_service.parse_document(file_path, file_ext)
        
        if not parse_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse document: {parse_result.get('error', 'Unknown error')}"
            )
        
        products_data = parse_result["products"]
        
        if not products_data:
            return {
                "message": "Document parsed successfully but no products found",
                "products_created": 0,
                "file_path": file_path
            }
        
        # Create/update products
        products_created = 0
        products_updated = 0
        
        for product_data in products_data:
            # Validate formula
            formula = product_data.get("pricing_formula", "")
            is_valid, error_msg = pricing_formula_service.validate_formula(formula)
            
            if not is_valid:
                # Skip invalid formulas, but log them
                continue
            
            # Check if product already exists
            existing_product = db.query(models.Product).filter(
                models.Product.name == product_data["name"],
                models.Product.business_id == business_id
            ).first()
            
            if existing_product:
                # Update existing product
                existing_product.description = product_data.get("description", existing_product.description)
                existing_product.pricing_formula = formula
                existing_product.price_per_sq_in = product_data.get("rate", existing_product.price_per_sq_in)
                existing_product.min_size_sq_in = product_data.get("min_size_sq_in", existing_product.min_size_sq_in)
                existing_product.max_size_sq_in = product_data.get("max_size_sq_in", existing_product.max_size_sq_in)
                products_updated += 1
            else:
                # Create new product
                new_product = models.Product(
                    business_id=business_id,
                    name=product_data["name"],
                    description=product_data.get("description", ""),
                    pricing_formula=formula,
                    price_per_sq_in=product_data.get("rate", 0.05),
                    min_size_sq_in=product_data.get("min_size_sq_in", 100),
                    max_size_sq_in=product_data.get("max_size_sq_in", 10000),
                    active=True
                )
                db.add(new_product)
                products_created += 1
        
        db.commit()
        
        return {
            "message": "Pricing document processed successfully",
            "products_created": products_created,
            "products_updated": products_updated,
            "total_products": len(products_data),
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.post("/{business_id}/poll-emails", response_model=dict)
async def manual_poll_emails(
    business_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger email polling for a business (for testing)
    This bypasses the 10-minute wait and polls immediately.
    """
    business = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    if not business.oauth_refresh_token_encrypted:
        raise HTTPException(
            status_code=400,
            detail="Business has no OAuth credentials configured"
        )
    
    # Trigger polling in background (non-blocking)
    poll_business_emails(business_id)
    
    return {
        "message": f"Email polling triggered for business {business_id}",
        "business_name": business.name,
        "note": "Check server logs for polling results"
    }

