"""
Background scheduler service for IMAP email polling
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Business, EmailInbox
from app.services.imap_service import imap_service
from app.services.quote_service import quote_service
from datetime import datetime

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()


def poll_business_emails(business_id: int):
    """Poll emails for a specific business"""
    db: Session = SessionLocal()
    
    try:
        business = db.query(Business).filter(Business.id == business_id).first()
        
        if not business or not business.active:
            logger.debug(f"Business {business_id} not found or inactive, skipping")
            return
        
        # Check if OAuth is configured
        if not business.oauth_refresh_token_encrypted:
            logger.debug(f"Business {business_id} has no OAuth credentials configured, skipping")
            return
        
        logger.info(f"Polling emails for business {business_id} ({business.name})")
        
        # Connect to IMAP
        mail = imap_service.connect_to_business_email(business)
        if not mail:
            logger.warning(f"Failed to connect to IMAP for business {business_id}")
            return
        
        try:
            # Only fetch emails received after OAuth connection
            # This prevents processing old emails that were in the inbox before signup
            since_date = business.oauth_connected_at
            
            if not since_date:
                logger.warning(f"Business {business_id} has no oauth_connected_at date, processing all emails")
            
            # Fetch unread emails (only those after OAuth connection)
            emails = imap_service.fetch_unread_emails(
                mail=mail,
                folder=business.imap_folder,
                business_id=business.id,
                since_date=since_date
            )
            
            if since_date:
                logger.info(f"Found {len(emails)} unread emails for business {business_id} (received after {since_date})")
            else:
                logger.info(f"Found {len(emails)} unread emails for business {business_id}")
            
            # Process each email
            for email_data in emails:
                try:
                    # Check if email already processed
                    existing = db.query(EmailInbox).filter(
                        EmailInbox.message_id == email_data["message_id"]
                    ).first()
                    
                    if existing:
                        logger.debug(f"Email {email_data['message_id']} already processed, skipping")
                        continue
                    
                    # Identify which business this email is for (check To: address)
                    to_email = email_data.get("to_email", "")
                    if to_email:
                        # Try to identify business from To: address
                        try:
                            target_business = quote_service.identify_business_from_email(to_email, db)
                            business_id_for_email = target_business.id
                        except Exception:
                            # Fallback to the business whose inbox we're polling
                            business_id_for_email = business.id
                    else:
                        business_id_for_email = business.id
                    
                    # Check if this email is a reply to one we sent
                    is_reply_to_us = False
                    in_reply_to = email_data.get("in_reply_to")
                    if in_reply_to:
                        # Check if the Message-ID we're replying to is one we sent
                        from app.models import EmailResponse
                        our_email = db.query(EmailResponse).filter(
                            EmailResponse.message_id == in_reply_to
                        ).first()
                        if our_email:
                            is_reply_to_us = True
                    
                    # Create email record
                    db_email = EmailInbox(
                        business_id=business_id_for_email,
                        message_id=email_data["message_id"],
                        from_email=email_data["from_email"],
                        from_name=email_data["from_name"],
                        to_email=email_data.get("to_email", ""),
                        subject=email_data["subject"],
                        body=email_data["body"],
                        received_at=email_data["received_at"],
                        processed=False,
                        in_reply_to=email_data.get("in_reply_to"),
                        references=email_data.get("references"),
                        thread_id=email_data.get("thread_id"),
                        is_reply_to_us=is_reply_to_us
                    )
                    
                    db.add(db_email)
                    db.flush()
                    
                    # Mark email as read in IMAP
                    try:
                        imap_service.mark_as_read(mail, email_data["raw_message_id"], business.imap_folder)
                    except Exception as e:
                        logger.warning(f"Failed to mark email as read: {e}")
                    
                    # Process email in background (async would be better, but this works)
                    logger.info(f"Processing email {db_email.id} from {email_data['from_email']}")
                    quote_service.process_email_and_generate_quote(db_email.id, db)
                    
                except Exception as e:
                    logger.error(f"Error processing email: {e}")
                    db.rollback()
                    continue
            
            db.commit()
            
        finally:
            # Close IMAP connection
            try:
                mail.logout()
            except Exception:
                pass
        
    except Exception as e:
        logger.error(f"Error polling emails for business {business_id}: {e}")
        db.rollback()
    finally:
        db.close()


def poll_all_businesses():
    """Poll emails for all active businesses"""
    db: Session = SessionLocal()
    
    try:
        businesses = db.query(Business).filter(Business.active == True).all()
        
        logger.info(f"Polling emails for {len(businesses)} businesses")
        
        for business in businesses:
            try:
                poll_business_emails(business.id)
            except Exception as e:
                logger.error(f"Error polling business {business.id}: {e}")
                continue
        
    finally:
        db.close()


def start_scheduler():
    """Start the email polling scheduler"""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return
    
    logger.info("Starting email polling scheduler")
    
    # Add job to poll all businesses every 10 minutes (default)
    # Individual businesses can have different intervals, but we'll use a global job for simplicity
    scheduler.add_job(
        func=poll_all_businesses,
        trigger=IntervalTrigger(minutes=10),  # Default: poll every 10 minutes
        id="poll_all_businesses",
        name="Poll all businesses for new emails",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Email polling scheduler started")


def stop_scheduler():
    """Stop the email polling scheduler"""
    if scheduler.running:
        logger.info("Stopping email polling scheduler")
        scheduler.shutdown()
        logger.info("Email polling scheduler stopped")


def add_business_job(business: Business):
    """Add a scheduled job for a specific business"""
    if not scheduler.running:
        return
    
    job_id = f"poll_business_{business.id}"
    
    # Remove existing job if any
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    
    # Add new job with business-specific interval
    interval_minutes = business.poll_interval_minutes or 10
    
    scheduler.add_job(
        func=poll_business_emails,
        trigger=IntervalTrigger(minutes=interval_minutes),
        args=[business.id],
        id=job_id,
        name=f"Poll emails for business {business.id}",
        replace_existing=True
    )
    
    logger.info(f"Added polling job for business {business.id} (interval: {interval_minutes} minutes)")

