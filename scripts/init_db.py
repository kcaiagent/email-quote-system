"""
Initialize database with sample data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, engine, Base
from app.models import Product, Customer, BusinessSettings, Business

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Create or get default business
    default_business = db.query(Business).filter(
        Business.email == "info@kyotocustomsurfaces.com"
    ).first()
    
    if not default_business:
        default_business = Business(
            name="Kyoto Custom Surfaces",
            email="info@kyotocustomsurfaces.com",
            imap_host="imap.gmail.com",
            imap_port=993,
            poll_interval_minutes=10,
            active=True
        )
        db.add(default_business)
        db.flush()
        print("Created default business: Kyoto Custom Surfaces")
    else:
        print(f"Using existing business: {default_business.name}")
    
    # Create sample products (linked to default business)
    products = [
        Product(
            business_id=default_business.id,
            name="Custom Felt Rug",
            description="Custom sized felt rug",
            price_per_sq_in=0.0588,  # ~$101.40 for 48x36
            min_size_sq_in=100,
            max_size_sq_in=10000,
            active=True
        ),
        Product(
            business_id=default_business.id,
            name="Acrylic Tabletop",
            description="Custom acrylic tabletop",
            price_per_sq_in=0.15,
            min_size_sq_in=200,
            max_size_sq_in=5000,
            active=True
        ),
        Product(
            business_id=default_business.id,
            name="Custom Product",
            description="Generic custom product",
            price_per_sq_in=0.05,
            min_size_sq_in=100,
            max_size_sq_in=10000,
            active=True
        )
    ]
    
    created_count = 0
    for product in products:
        existing = db.query(Product).filter(
            Product.name == product.name,
            Product.business_id == default_business.id
        ).first()
        if not existing:
            db.add(product)
            created_count += 1
    
    # Create business settings
    settings = [
        BusinessSettings(key="business_name", value="Kyoto Custom Surfaces"),
        BusinessSettings(key="business_email", value="info@kyotocustomsurfaces.com"),
        BusinessSettings(key="quote_validity_days", value="30"),
    ]
    
    settings_count = 0
    for setting in settings:
        existing = db.query(BusinessSettings).filter(
            BusinessSettings.key == setting.key
        ).first()
        if not existing:
            db.add(setting)
            settings_count += 1
    
    db.commit()
    print("Database initialized with sample data!")
    print(f"Created {created_count} products")
    print(f"Created {settings_count} business settings")
    
except Exception as e:
    print(f"Error initializing database: {e}")
    db.rollback()
finally:
    db.close()


