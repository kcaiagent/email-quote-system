"""
Email service for sending emails
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import base64
import logging
from typing import Optional
from app.config import settings
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.services.oauth_service import oauth_service

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails using OAuth"""
    
    @staticmethod
    def send_email(
        db: Session,
        business: models.Business,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        in_reply_to: str = None,
        related_email_id: int = None
    ) -> bool:
        """Send a plain text email using business OAuth credentials"""
        from email.utils import make_msgid
        
        try:
            # Get valid access token
            access_token = oauth_service.get_valid_access_token(
                refresh_token_encrypted=business.oauth_refresh_token_encrypted,
                access_token_encrypted=business.oauth_access_token_encrypted,
                expires_at=business.oauth_token_expires_at
            )
            
            if not access_token:
                logger.error(f"Failed to get access token for business {business.id}")
                return False
            
            # Use OAuth email if available
            sender_email = from_email or business.oauth_email or business.email
            
            # Generate Message-ID for tracking
            message_id = make_msgid()
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Message-ID'] = message_id
            
            # Add In-Reply-To header if replying to a thread
            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to
                msg['References'] = in_reply_to
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server with OAuth
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            # Authenticate using XOAUTH2
            auth_string = EmailService._generate_oauth2_string(sender_email, access_token)
            server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
            
            text = msg.as_string()
            server.sendmail(sender_email, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email} from business {business.id} (Message-ID: {message_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    @staticmethod
    def _generate_oauth2_string(email: str, access_token: str) -> str:
        """Generate OAuth 2.0 authentication string for SMTP XOAUTH2"""
        auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
        return base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def send_quote_email(
        to_email: str,
        subject: str,
        body: str,
        pdf_path: str,
        quote_id: int,
        business: models.Business,
        db: Session = None,
        in_reply_to: str = None,
        related_email_id: int = None
    ) -> bool:
        """Send email with PDF quote attachment using business OAuth credentials"""
        import uuid
        from email.utils import make_msgid
        
        try:
            # Get valid access token
            access_token = oauth_service.get_valid_access_token(
                refresh_token_encrypted=business.oauth_refresh_token_encrypted,
                access_token_encrypted=business.oauth_access_token_encrypted,
                expires_at=business.oauth_token_expires_at
            )
            
            if not access_token:
                logger.error(f"Failed to get access token for business {business.id}")
                return False
            
            # Use OAuth email if available
            sender_email = business.oauth_email or business.email
            
            # Generate Message-ID for tracking
            message_id = make_msgid()
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Message-ID'] = message_id
            
            # Add In-Reply-To header if replying to a thread
            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to
                msg['References'] = in_reply_to
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(pdf_path)}'
                )
                msg.attach(part)
            
            # Send email with OAuth
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            # Authenticate using XOAUTH2
            auth_string = EmailService._generate_oauth2_string(sender_email, access_token)
            server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
            
            text = msg.as_string()
            server.sendmail(sender_email, to_email, text)
            server.quit()
            
            # Record email response with thread tracking
            if db:
                # Extract thread_id from in_reply_to if available
                thread_id = in_reply_to if in_reply_to else None
                
                email_response = models.EmailResponse(
                    quote_id=quote_id,
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    status="sent",
                    message_id=message_id,
                    in_reply_to=in_reply_to,
                    thread_id=thread_id,
                    related_email_id=related_email_id
                )
                db.add(email_response)
                db.commit()
            
            logger.info(f"Quote email sent successfully to {to_email} from business {business.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send quote email: {e}")
            if db:
                email_response = models.EmailResponse(
                    quote_id=quote_id,
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    status="failed"
                )
                db.add(email_response)
                db.commit()
            return False


# Singleton instance
email_service = EmailService()


