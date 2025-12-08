"""
Quote service - handles quote creation and processing
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app import models, schemas
from app.services.ai_service import ai_service
from app.services.pricing_service import pricing_service
from app.services.pdf_service import pdf_service
from app.services.email_service import email_service
from app.services.pricing_formula_service import pricing_formula_service
import random
import string
import logging

logger = logging.getLogger(__name__)


class QuoteService:
    """Service for managing quotes"""
    
    @staticmethod
    def identify_business_from_email(to_email: str, db: Session) -> models.Business:
        """Identify which business an email belongs to based on To: address"""
        if not to_email:
            # Default to first active business or create one
            business = db.query(models.Business).filter(models.Business.active == True).first()
            if business:
                return business
            raise Exception("No active business found and no To: address provided")
        
        # Normalize email (remove angle brackets, lowercase)
        to_email = to_email.strip().lower()
        if to_email.startswith('<') and to_email.endswith('>'):
            to_email = to_email[1:-1]
        
        # Try to find business by exact email match
        business = db.query(models.Business).filter(
            models.Business.email.ilike(to_email)
        ).first()
        
        if business:
            return business
        
        # Try to find by IMAP email
        business = db.query(models.Business).filter(
            models.Business.imap_email.ilike(to_email)
        ).first()
        
        if business:
            return business
        
        # Try partial match (e.g., "info@" matches "info@domain.com")
        email_local = to_email.split('@')[0] if '@' in to_email else to_email
        business = db.query(models.Business).filter(
            models.Business.email.ilike(f"{email_local}@%")
        ).first()
        
        if business:
            return business
        
        # Default to first active business
        business = db.query(models.Business).filter(models.Business.active == True).first()
        if business:
            return business
        
        raise Exception(f"Could not identify business for email: {to_email}")
    
    @staticmethod
    def generate_quote_number() -> str:
        """Generate unique quote number"""
        prefix = "Q"
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}-{date_str}-{random_str}"
    
    @staticmethod
    def create_quote(
        db: Session,
        business_id: int,
        customer_id: int,
        product_id: int,
        length_inches: float,
        width_inches: float,
        notes: str = None
    ) -> models.Quote:
        """Create a new quote"""
        # Get product to access business_id
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise Exception(f"Product {product_id} not found")
        
        # Use product's business_id if not provided
        if not business_id:
            business_id = product.business_id
        
        # Calculate pricing
        pricing = pricing_service.calculate_price(
            db, product_id, length_inches, width_inches
        )
        
        # Generate quote number
        quote_number = QuoteService.generate_quote_number()
        
        # Create quote
        db_quote = models.Quote(
            business_id=business_id,
            quote_number=quote_number,
            customer_id=customer_id,
            product_id=product_id,
            length_inches=length_inches,
            width_inches=width_inches,
            area_sq_inches=pricing["area_sq_inches"],
            unit_price=pricing["unit_price"],
            total_price=pricing["total_price"],
            notes=notes,
            status="pending"
        )
        
        db.add(db_quote)
        db.flush()
        
        # Generate PDF
        customer = db.query(models.Customer).filter(
            models.Customer.id == customer_id
        ).first()
        
        pdf_path = pdf_service.generate_quote_pdf(
            quote_number=quote_number,
            customer_name=customer.name or customer.email,
            customer_email=customer.email,
            product_name=product.name if product else "Custom Product",
            length_inches=length_inches,
            width_inches=width_inches,
            area_sq_inches=pricing["area_sq_inches"],
            unit_price=pricing["unit_price"],
            total_price=pricing["total_price"],
            notes=notes
        )
        
        db_quote.pdf_path = pdf_path
        db.commit()
        db.refresh(db_quote)
        
        return db_quote
    
    @staticmethod
    def process_email_and_generate_quote(email_id: int, db: Session):
        """Process email and generate quote if possible"""
        email = db.query(models.EmailInbox).filter(
            models.EmailInbox.id == email_id
        ).first()
        
        if not email or email.processed:
            return
        
        # Get business from email (should already be set by IMAP service)
        business_id = email.business_id
        if not business_id:
            # Try to identify business from To: address
            business = QuoteService.identify_business_from_email(email.to_email, db)
            business_id = business.id
            email.business_id = business_id
        
        # Check for duplicate replies in same thread
        if email.thread_id or email.in_reply_to:
            # Check if we already replied to this thread
            from app.models import EmailResponse
            thread_identifier = email.thread_id or email.in_reply_to
            
            existing_reply = db.query(EmailResponse).filter(
                (EmailResponse.thread_id == thread_identifier) |
                (EmailResponse.in_reply_to == email.in_reply_to)
            ).first()
            
            if existing_reply:
                # We already replied to this thread - use AI to check if this is a duplicate
                intent = ai_service.detect_email_intent(
                    email.body, 
                    email.subject, 
                    is_reply_to_us=email.is_reply_to_us
                )
                
                if intent["intent"] == "duplicate" and intent["confidence"] > 0.7:
                    # This appears to be a duplicate request
                    logger.info(f"Detected duplicate request in thread {thread_identifier}, sending acknowledgment")
                    business = db.query(models.Business).filter(models.Business.id == business_id).first()
                    
                    if business:
                        customer = db.query(models.Customer).filter(
                            models.Customer.email == email.from_email,
                            models.Customer.business_id == business_id
                        ).first()
                        
                        if customer:
                            # Send friendly acknowledgment
                            acknowledgment = f"""Hi {customer.name or customer.email.split('@')[0]},

Thank you for your email. We've already sent you a quote for this request. Please check your previous emails for the quote details.

If you need any modifications or have questions, please let us know!

Best regards,
Kyoto Custom Surfaces"""
                            
                            email_service.send_email(
                                db=db,
                                business=business,
                                to_email=customer.email,
                                subject=f"Re: {email.subject}",
                                body=acknowledgment,
                                in_reply_to=email.message_id,
                                related_email_id=email.id
                            )
                    
                    # Mark as processed but don't create new quote
                    email.processed = True
                    email.processed_at = datetime.now()
                    db.commit()
                    return
        
        # Detect email intent (new request, follow-up, etc.)
        intent = ai_service.detect_email_intent(
            email.body,
            email.subject,
            is_reply_to_us=email.is_reply_to_us
        )
        
        logger.info(f"Email intent detected: {intent['intent']} (confidence: {intent['confidence']})")
        
        # Extract information using AI
        extracted_info = ai_service.extract_quote_info(email.body, email.subject)
        
        # Find or create customer (business-specific)
        customer = db.query(models.Customer).filter(
            models.Customer.email == email.from_email,
            models.Customer.business_id == business_id
        ).first()
        
        if not customer:
            customer = models.Customer(
                business_id=business_id,
                email=email.from_email,
                name=email.from_name,
                is_new_customer=True
            )
            db.add(customer)
            db.flush()
        else:
            customer.is_new_customer = False
        
        # Check if we have complete information
        if extracted_info["has_complete_info"]:
            # Find product (business-specific)
            product = db.query(models.Product).filter(
                models.Product.name.ilike(f"%{extracted_info['product_name']}%"),
                models.Product.business_id == business_id,
                models.Product.active == True
            ).first()
            
            if not product:
                # Use default product or create one
                product = db.query(models.Product).filter(
                    models.Product.name == "Custom Product",
                    models.Product.business_id == business_id
                ).first()
                
                if not product:
                    product = models.Product(
                        business_id=business_id,
                        name=extracted_info['product_name'] or "Custom Product",
                        price_per_sq_in=0.05
                    )
                    db.add(product)
                    db.flush()
            
            # Create quote
            quote = QuoteService.create_quote(
                db=db,
                business_id=business_id,
                customer_id=customer.id,
                product_id=product.id,
                length_inches=extracted_info['length_inches'],
                width_inches=extracted_info['width_inches']
            )
            
            # Generate response message
            quote_data = {
                "customer_name": customer.name or customer.email.split("@")[0],
                "product_name": product.name,
                "length_inches": extracted_info['length_inches'],
                "width_inches": extracted_info['width_inches'],
                "area_sq_inches": quote.area_sq_inches,
                "total_price": quote.total_price
            }
            
            response_message = ai_service.generate_response_message(
                quote_data,
                []
            )
            
            # Get business for email sending
            business = db.query(models.Business).filter(models.Business.id == business_id).first()
            
            # Send email with quote
            if business:
                email_service.send_quote_email(
                    to_email=customer.email,
                    subject=f"Re: {email.subject} - Your Quote",
                    body=response_message,
                    pdf_path=quote.pdf_path,
                    quote_id=quote.id,
                    business=business,
                    db=db,
                    in_reply_to=email.message_id,  # Reply to the incoming email
                    related_email_id=email.id
                )
            
            # Mark email as processed
            email.processed = True
            email.processed_at = datetime.now()
            customer.last_quote_date = datetime.now()
            
        else:
            # Request missing information
            response_message = ai_service.generate_response_message(
                {"customer_name": customer.name or customer.email.split("@")[0]},
                extracted_info['missing_fields']
            )
            
            # Get business for email sending
            business = db.query(models.Business).filter(models.Business.id == business_id).first()
            
            if business:
                email_service.send_email(
                    db=db,
                    business=business,
                    to_email=customer.email,
                    subject=f"Re: {email.subject} - More Information Needed",
                    body=response_message,
                    in_reply_to=email.message_id,  # Reply to the incoming email
                    related_email_id=email.id
                )
            
            email.processed = True
            email.processed_at = datetime.now()
        
        db.commit()
    
    @staticmethod
    def process_wix_email(webhook_data: schemas.WixEmailWebhook, db: Session):
        """Process email from Wix webhook"""
        # Identify business
        if webhook_data.business_id:
            business = db.query(models.Business).filter(
                models.Business.id == webhook_data.business_id,
                models.Business.active == True
            ).first()
            if not business:
                raise Exception(f"Business {webhook_data.business_id} not found or inactive")
            business_id = business.id
        else:
            # Try to identify from To: address
            business = QuoteService.identify_business_from_email(webhook_data.to_email or "", db)
            business_id = business.id
        
        # Create email record
        db_email = models.EmailInbox(
            business_id=business_id,
            message_id=f"wix_{datetime.now().timestamp()}",
            from_email=webhook_data.email,
            from_name=webhook_data.name,
            to_email=webhook_data.to_email,
            subject=webhook_data.subject,
            body=webhook_data.body,
            received_at=webhook_data.received_at or datetime.now()
        )
        db.add(db_email)
        db.flush()
        
        # Process email
        QuoteService.process_email_and_generate_quote(db_email.id, db)
    
    @staticmethod
    def create_quote_from_wix_request(
        db: Session,
        request: schemas.WixQuoteRequest
    ) -> schemas.WixQuoteResponse:
        """Create quote from Wix request"""
        # Get business
        if request.business_id:
            business = db.query(models.Business).filter(
                models.Business.id == request.business_id,
                models.Business.active == True
            ).first()
            if not business:
                raise Exception(f"Business {request.business_id} not found or inactive")
            business_id = business.id
        else:
            # Use first active business
            business = db.query(models.Business).filter(models.Business.active == True).first()
            if not business:
                raise Exception("No active business found. Please create a business first.")
            business_id = business.id
        
        # Find or create customer (business-specific)
        customer = db.query(models.Customer).filter(
            models.Customer.email == request.customer_email,
            models.Customer.business_id == business_id
        ).first()
        
        if not customer:
            customer = models.Customer(
                business_id=business_id,
                email=request.customer_email,
                is_new_customer=True
            )
            db.add(customer)
            db.flush()
        
        # Find product (business-specific)
        product = db.query(models.Product).filter(
            models.Product.name.ilike(f"%{request.product_name}%"),
            models.Product.business_id == business_id,
            models.Product.active == True
        ).first()
        
        if not product:
            # Create default product
            product = models.Product(
                business_id=business_id,
                name=request.product_name,
                price_per_sq_in=0.05
            )
            db.add(product)
            db.flush()
        
        # Create quote
        quote = QuoteService.create_quote(
            db=db,
            business_id=business_id,
            customer_id=customer.id,
            product_id=product.id,
            length_inches=request.length_inches,
            width_inches=request.width_inches,
            notes=request.notes
        )
        
        return schemas.WixQuoteResponse(
            quote_number=quote.quote_number,
            customer_name=customer.name,
            product_name=product.name,
            dimensions=f"{quote.length_inches}\" × {quote.width_inches}\"",
            area_sq_inches=quote.area_sq_inches,
            total_price=quote.total_price,
            pdf_url=f"/api/quotes/{quote.id}/pdf" if quote.pdf_path else None,
            status=quote.status,
            message="Quote generated successfully"
        )
    
    @staticmethod
    def get_quote_for_wix(db: Session, quote_number: str) -> schemas.WixQuoteResponse:
        """Get quote formatted for Wix"""
        quote = db.query(models.Quote).filter(
            models.Quote.quote_number == quote_number
        ).first()
        
        if not quote:
            return None
        
        customer = db.query(models.Customer).filter(
            models.Customer.id == quote.customer_id
        ).first()
        product = db.query(models.Product).filter(
            models.Product.id == quote.product_id
        ).first()
        
        return schemas.WixQuoteResponse(
            quote_number=quote.quote_number,
            customer_name=customer.name if customer else None,
            product_name=product.name if product else "Unknown",
            dimensions=f"{quote.length_inches}\" × {quote.width_inches}\"",
            area_sq_inches=quote.area_sq_inches,
            total_price=quote.total_price,
            pdf_url=f"/api/quotes/{quote.id}/pdf" if quote.pdf_path else None,
            status=quote.status,
            message="Quote retrieved successfully"
        )
    
    @staticmethod
    def validate_dimensions(
        db: Session,
        product_id: int,
        length_inches: float,
        width_inches: float
    ) -> tuple:
        """Validate dimensions"""
        return pricing_service.validate_dimensions(
            db, product_id, length_inches, width_inches
        )


# Singleton instance
quote_service = QuoteService()

