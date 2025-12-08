"""
Database models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Business(Base):
    """Business/tenant information"""
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    # IMAP configuration
    imap_host = Column(String, default="imap.gmail.com")
    imap_port = Column(Integer, default=993)
    imap_folder = Column(String, default="INBOX")
    poll_interval_minutes = Column(Integer, default=10)  # Polling interval in minutes
    # OAuth configuration
    oauth_refresh_token_encrypted = Column(Text, nullable=True)  # Encrypted refresh token (long-lived)
    oauth_access_token_encrypted = Column(Text, nullable=True)  # Encrypted access token (temporary)
    oauth_token_expires_at = Column(DateTime(timezone=True), nullable=True)  # When access token expires
    oauth_connected_at = Column(DateTime(timezone=True), nullable=True)  # When OAuth was connected
    oauth_email = Column(String, nullable=True)  # Which Google account is connected
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="business", cascade="all, delete-orphan")
    emails = relationship("EmailInbox", back_populates="business")
    quotes = relationship("Quote", back_populates="business")


class BusinessSettings(Base):
    """Business configuration settings"""
    __tablename__ = "business_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Product(Base):
    """Product catalog with pricing"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    price_per_sq_in = Column(Float, default=0.05)  # Legacy field, kept for backward compatibility
    pricing_formula = Column(Text, nullable=True)  # New formula field (e.g., "base_price + (area * rate)")
    min_size_sq_in = Column(Float, default=100)
    max_size_sq_in = Column(Float, default=10000)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    business = relationship("Business", back_populates="products")
    quotes = relationship("Quote", back_populates="product")


class Customer(Base):
    """Customer information"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    email = Column(String, index=True)  # Remove unique constraint, email can be same across businesses
    name = Column(String)
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    is_new_customer = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_quote_date = Column(DateTime(timezone=True), nullable=True)
    
    business = relationship("Business", back_populates="customers")
    quotes = relationship("Quote", back_populates="customer")
    emails = relationship("EmailInbox", back_populates="customer")


class EmailInbox(Base):
    """Raw incoming emails"""
    __tablename__ = "email_inbox"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    message_id = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    from_email = Column(String, index=True)
    from_name = Column(String)
    to_email = Column(String, index=True)  # To: address to identify which business
    subject = Column(String)
    body = Column(Text)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    # Thread tracking fields
    in_reply_to = Column(String, nullable=True, index=True)  # Message-ID this email is replying to
    references = Column(Text, nullable=True)  # References header (list of message IDs in thread)
    thread_id = Column(String, nullable=True, index=True)  # Thread identifier (extracted from References)
    is_reply_to_us = Column(Boolean, default=False)  # True if this is a reply to an email we sent
    
    business = relationship("Business", back_populates="emails")
    customer = relationship("Customer", back_populates="emails")


class Quote(Base):
    """Generated quotes"""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    quote_number = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    length_inches = Column(Float)
    width_inches = Column(Float)
    area_sq_inches = Column(Float)
    unit_price = Column(Float)
    total_price = Column(Float)
    status = Column(String, default="pending")  # pending, sent, accepted, rejected
    pdf_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    business = relationship("Business", back_populates="quotes")
    customer = relationship("Customer", back_populates="quotes")
    product = relationship("Product", back_populates="quotes")
    email_response = relationship("EmailResponse", back_populates="quote", uselist=False)


class EmailResponse(Base):
    """Outgoing emails (quote responses)"""
    __tablename__ = "email_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), unique=True)
    to_email = Column(String, index=True)
    subject = Column(String)
    body = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="sent")  # sent, failed
    # Thread tracking fields
    message_id = Column(String, nullable=True, unique=True, index=True)  # Message-ID of sent email
    in_reply_to = Column(String, nullable=True, index=True)  # Message-ID we're replying to
    thread_id = Column(String, nullable=True, index=True)  # Thread identifier
    related_email_id = Column(Integer, ForeignKey("email_inbox.id"), nullable=True)  # Link to incoming email that triggered this
    
    quote = relationship("Quote", back_populates="email_response")


