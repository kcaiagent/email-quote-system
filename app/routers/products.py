"""
Product endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.ProductResponse)
async def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/", response_model=List[schemas.ProductResponse])
async def get_products(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all products"""
    query = db.query(models.Product)
    if active_only:
        query = query.filter(models.Product.active == True)
    products = query.all()
    return products


@router.get("/{product_id}", response_model=schemas.ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/name/{product_name}", response_model=schemas.ProductResponse)
async def get_product_by_name(product_name: str, db: Session = Depends(get_db)):
    """Get product by name (case-insensitive)"""
    product = db.query(models.Product).filter(
        models.Product.name.ilike(f"%{product_name}%")
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product









