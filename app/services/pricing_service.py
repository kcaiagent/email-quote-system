"""
Pricing calculation service
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Product
from app.config import settings
from app.services.pricing_formula_service import pricing_formula_service


class PricingService:
    """Service for calculating quote prices"""
    
    @staticmethod
    def calculate_price(
        db: Session,
        product_id: int,
        length_inches: float,
        width_inches: float
    ) -> dict:
        """
        Calculate price based on product and dimensions
        
        Returns:
            {
                "area_sq_inches": float,
                "unit_price": float,
                "total_price": float,
                "min_price": float
            }
        """
        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        
        # Calculate area
        area_sq_inches = length_inches * width_inches
        
        # Calculate total price using formula or legacy method
        if product and product.pricing_formula:
            # Use formula engine
            base_price = product.price_per_sq_in if product.price_per_sq_in > 0 else 0
            rate = product.price_per_sq_in if product.price_per_sq_in > 0 else settings.BASE_PRICE_PER_SQ_IN
            
            total_price = pricing_formula_service.execute_formula(
                formula=product.pricing_formula,
                area=area_sq_inches,
                base_price=base_price,
                rate=rate,
                length=length_inches,
                width=width_inches
            )
            
            # Calculate unit price (average)
            unit_price = total_price / area_sq_inches if area_sq_inches > 0 else 0
        else:
            # Legacy calculation
            if not product:
                unit_price = settings.BASE_PRICE_PER_SQ_IN
            else:
                unit_price = product.price_per_sq_in or settings.BASE_PRICE_PER_SQ_IN
            
            total_price = area_sq_inches * unit_price
        
        # Apply minimum order amount
        min_price = settings.MIN_ORDER_AMOUNT
        if total_price < min_price:
            total_price = min_price
        
        return {
            "area_sq_inches": round(area_sq_inches, 2),
            "unit_price": round(unit_price, 4),
            "total_price": round(total_price, 2),
            "min_price": min_price
        }
    
    @staticmethod
    def validate_dimensions(
        db: Session,
        product_id: int,
        length_inches: float,
        width_inches: float
    ) -> tuple:
        """
        Validate dimensions against product constraints
        
        Returns:
            (is_valid, error_message)
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            return True, None  # No product-specific constraints
        
        area = length_inches * width_inches
        
        if area < product.min_size_sq_in:
            return False, f"Minimum size is {product.min_size_sq_in} square inches"
        
        if area > product.max_size_sq_in:
            return False, f"Maximum size is {product.max_size_sq_in} square inches"
        
        return True, None


# Singleton instance
pricing_service = PricingService()

