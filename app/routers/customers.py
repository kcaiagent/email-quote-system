"""
Customer endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.CustomerResponse)
async def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """Create or get existing customer"""
    # Check if customer exists
    db_customer = db.query(models.Customer).filter(
        models.Customer.email == customer.email
    ).first()
    
    if db_customer:
        # Update if needed
        if customer.name and not db_customer.name:
            db_customer.name = customer.name
        if customer.company and not db_customer.company:
            db_customer.company = customer.company
        db_customer.is_new_customer = False
        db.commit()
        db.refresh(db_customer)
        return db_customer
    
    # Create new customer
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


@router.get("/", response_model=List[schemas.CustomerResponse])
async def get_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all customers"""
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=schemas.CustomerResponse)
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer by ID"""
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/email/{email}", response_model=schemas.CustomerResponse)
async def get_customer_by_email(email: str, db: Session = Depends(get_db)):
    """Get customer by email"""
    customer = db.query(models.Customer).filter(
        models.Customer.email == email
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer









