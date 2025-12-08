"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# Business Schemas
class BusinessCreate(BaseModel):
    name: str
    email: EmailStr
    imap_host: Optional[str] = "imap.gmail.com"
    imap_port: Optional[int] = 993
    poll_interval_minutes: Optional[int] = 10


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    poll_interval_minutes: Optional[int] = None
    active: Optional[bool] = None


class BusinessResponse(BaseModel):
    id: int
    name: str
    email: str
    imap_host: str
    imap_port: int
    poll_interval_minutes: int
    oauth_email: Optional[str]  # Which Google account is connected
    oauth_connected_at: Optional[datetime]  # When OAuth was connected
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# OAuth Schemas
class OAuthStatusResponse(BaseModel):
    """OAuth connection status for a business"""
    business_id: int
    is_connected: bool
    oauth_email: Optional[str] = None
    oauth_connected_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None


class OAuthConnectResponse(BaseModel):
    """Response with OAuth authorization URL"""
    authorization_url: str
    business_id: int


# Email Schemas
class EmailInboxCreate(BaseModel):
    business_id: int
    message_id: str
    from_email: EmailStr
    from_name: Optional[str] = None
    to_email: Optional[str] = None  # To: address to identify business
    subject: str
    body: str


class EmailInboxResponse(BaseModel):
    id: int
    business_id: int
    message_id: str
    from_email: str
    from_name: Optional[str]
    to_email: Optional[str]
    subject: str
    body: str
    processed: bool
    received_at: datetime
    
    class Config:
        from_attributes = True


# Customer Schemas
class CustomerCreate(BaseModel):
    business_id: int  # Required: link customer to business
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None


class CustomerResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    company: Optional[str]
    is_new_customer: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Product Schemas
class ProductCreate(BaseModel):
    business_id: int  # Required: link product to business
    name: str
    description: Optional[str] = None
    price_per_sq_in: float = 0.05  # Legacy field
    pricing_formula: Optional[str] = None  # New formula field
    min_size_sq_in: float = 100
    max_size_sq_in: float = 10000


class ProductResponse(BaseModel):
    id: int
    business_id: int
    name: str
    description: Optional[str]
    price_per_sq_in: float
    pricing_formula: Optional[str]
    min_size_sq_in: float
    max_size_sq_in: float
    active: bool
    
    class Config:
        from_attributes = True


# Quote Schemas
class QuoteCreate(BaseModel):
    customer_id: int
    product_id: int
    business_id: Optional[int] = None  # Optional: will use product's business_id if not provided
    length_inches: float = Field(gt=0)
    width_inches: float = Field(gt=0)
    notes: Optional[str] = None


class QuoteResponse(BaseModel):
    id: int
    business_id: int
    quote_number: str
    customer_id: int
    product_id: int
    length_inches: float
    width_inches: float
    area_sq_inches: float
    unit_price: float
    total_price: float
    status: str
    pdf_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Wix Integration Schemas
class WixEmailWebhook(BaseModel):
    """Webhook payload from Wix for incoming emails"""
    business_id: Optional[int] = None  # Optional: identifies which business
    email: EmailStr
    name: Optional[str] = None
    subject: str
    body: str
    to_email: Optional[str] = None  # To: address to identify business
    received_at: Optional[datetime] = None


class WixQuoteRequest(BaseModel):
    """Request from Wix to generate a quote"""
    business_id: Optional[int] = None  # Optional: if not provided, uses first active business
    customer_email: EmailStr
    product_name: str
    length_inches: float
    width_inches: float
    notes: Optional[str] = None


class WixQuoteResponse(BaseModel):
    """Response to Wix with quote information"""
    quote_number: str
    customer_name: Optional[str]
    product_name: str
    dimensions: str
    area_sq_inches: float
    total_price: float
    pdf_url: Optional[str] = None
    status: str
    message: str


