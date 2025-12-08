"""
IMAP email polling service
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Optional, Dict
from datetime import datetime, timezone
import logging
import base64
from app.models import Business
from app.services.oauth_service import oauth_service
from app.utils import decrypt_token

logger = logging.getLogger(__name__)


class IMAPService:
    """Service for connecting to IMAP servers and fetching emails"""
    
    @staticmethod
    def connect_to_business_email(business: Business) -> Optional[imaplib.IMAP4_SSL]:
        """
        Connect to business email via IMAP using OAuth XOAUTH2
        
        Returns:
            IMAP4_SSL connection or None if connection fails
        """
        try:
            # Check if OAuth is configured
            if not business.oauth_refresh_token_encrypted:
                logger.warning(f"Business {business.id} ({business.name}) has no OAuth configured")
                return None
            
            # Get valid access token (will refresh if needed)
            access_token = oauth_service.get_valid_access_token(
                refresh_token_encrypted=business.oauth_refresh_token_encrypted,
                access_token_encrypted=business.oauth_access_token_encrypted,
                expires_at=business.oauth_token_expires_at
            )
            
            if not access_token:
                logger.error(f"Failed to get valid access token for business {business.id}")
                return None
            
            # Use OAuth email if available, otherwise use business email
            email_address = business.oauth_email or business.email
            logger.info(f"Attempting IMAP XOAUTH2 authentication for email: {email_address}")
            
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(business.imap_host, business.imap_port)
            
            # Check if XOAUTH2 is supported
            typ, data = mail.capability()
            if b'AUTH=XOAUTH2' not in data[0]:
                logger.error("Server does not support XOAUTH2 authentication")
                mail.logout()
                return None
            
            # Authenticate using XOAUTH2
            # XOAUTH2 format: "user=" {User} "^Aauth=Bearer " {Access Token} "^A^A"
            # For imaplib.authenticate(), the handler should return the RAW string (not base64-encoded)
            # imaplib will handle the base64 encoding internally
            auth_string_raw = f"user={email_address}\x01auth=Bearer {access_token}\x01\x01"
            logger.debug(f"Generated XOAUTH2 raw auth string (length: {len(auth_string_raw)})")
            
            # The authenticate method expects a callable that returns the raw auth string
            # imaplib will base64-encode it internally
            def oauth2_handler(response):
                # response is the server's challenge (usually empty for XOAUTH2)
                # Return the raw authentication string (imaplib will encode it)
                logger.debug(f"OAuth handler called with response: {response}")
                return auth_string_raw
            
            # Use XOAUTH2 authentication
            logger.info("Calling mail.authenticate('XOAUTH2', ...)")
            mail.authenticate('XOAUTH2', oauth2_handler)
            
            logger.info(f"Connected to IMAP server for business {business.id} ({business.name}) via OAuth")
            return mail
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP for business {business.id} ({business.name}): {e}")
            return None
    
    @staticmethod
    def _generate_oauth2_string(email: str, access_token: str) -> str:
        """
        Generate OAuth 2.0 authentication string for IMAP XOAUTH2 (as string for SMTP)
        
        Format: base64("user=" {email} "^Aauth=Bearer " {access_token} "^A^A")
        where ^A is ASCII character 1 (\x01)
        """
        auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
        return base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def _generate_oauth2_string_bytes(email: str, access_token: str) -> bytes:
        """
        Generate OAuth 2.0 authentication string for IMAP XOAUTH2 (as bytes for IMAP authenticate)
        
        Format: base64("user=" {email} "^Aauth=Bearer " {access_token} "^A^A")
        where ^A is ASCII character 1 (\x01)
        """
        auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
        return base64.b64encode(auth_string.encode('utf-8'))
    
    @staticmethod
    def fetch_unread_emails(
        mail: imaplib.IMAP4_SSL,
        folder: str = "INBOX",
        business_id: int = None,
        since_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch unread emails from IMAP folder
        
        Args:
            mail: IMAP connection
            folder: Folder to search in
            business_id: Business ID (for logging)
            since_date: Only fetch emails received after this date (filters out old emails)
        
        Returns:
            List of email dictionaries with:
            - message_id
            - from_email
            - from_name
            - to_email
            - subject
            - body
            - received_at
        """
        emails = []
        
        try:
            # Select folder
            status, messages = mail.select(folder)
            if status != "OK":
                logger.error(f"Failed to select folder {folder}")
                return emails
            
            # Build search criteria
            # IMAP date format: DD-MMM-YYYY (e.g., "07-Dec-2024")
            search_criteria = ["UNSEEN"]
            
            if since_date:
                # Format date for IMAP: DD-MMM-YYYY
                date_str = since_date.strftime("%d-%b-%Y")
                search_criteria.append(f"SINCE {date_str}")
                logger.info(f"Filtering emails to only those received after {date_str} (OAuth connection date)")
            
            # Search for unread emails (with optional date filter)
            search_query = " ".join(search_criteria)
            status, message_numbers = mail.search(None, search_query)
            if status != "OK":
                logger.error(f"Failed to search for unread emails: {search_query}")
                return emails
            
            message_ids = message_numbers[0].split()
            
            for msg_id in message_ids:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    # Parse email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Extract headers
                    subject = IMAPService._decode_header(email_message["Subject"])
                    from_header = email_message["From"]
                    to_header = email_message["To"]
                    
                    # Parse from address
                    from_email, from_name = IMAPService._parse_address(from_header)
                    
                    # Get message ID
                    message_id = email_message.get("Message-ID", "").strip("<>")
                    if not message_id:
                        # Generate a fallback message ID
                        message_id = f"imap_{business_id}_{msg_id.decode()}_{datetime.now(timezone.utc).timestamp()}"
                    
                    # Extract thread tracking information
                    in_reply_to = email_message.get("In-Reply-To", "").strip("<>")
                    references = email_message.get("References", "")
                    
                    # Extract thread ID from References or In-Reply-To
                    # Thread ID is typically the first message ID in the References header
                    thread_id = None
                    if references:
                        # References can contain multiple message IDs separated by whitespace
                        ref_ids = [ref.strip().strip("<>") for ref in references.split()]
                        if ref_ids:
                            thread_id = ref_ids[0]  # First message ID in thread
                    elif in_reply_to:
                        thread_id = in_reply_to
                    
                    # Get date
                    date_str = email_message.get("Date")
                    received_at = IMAPService._parse_date(date_str) if date_str else datetime.now(timezone.utc)
                    
                    # Extract body
                    body = IMAPService._extract_body(email_message)
                    
                    # Additional safety check: filter by received_at if since_date is provided
                    # (IMAP SINCE filter might not be 100% reliable, so double-check)
                    if since_date:
                        try:
                            # Ensure both dates are timezone-aware for comparison
                            # Make copies to avoid modifying originals
                            compare_received = received_at
                            compare_since = since_date
                            
                            if compare_received.tzinfo is None:
                                compare_received = compare_received.replace(tzinfo=timezone.utc)
                            if compare_since.tzinfo is None:
                                compare_since = compare_since.replace(tzinfo=timezone.utc)
                            
                            if compare_received < compare_since:
                                logger.debug(f"Skipping email {message_id} - received at {compare_received} is before OAuth connection date {compare_since}")
                                continue
                        except Exception as date_error:
                            logger.warning(f"Error comparing dates for email {message_id}: {date_error}. Processing email anyway.")
                    
                    emails.append({
                        "message_id": message_id,
                        "from_email": from_email,
                        "from_name": from_name,
                        "to_email": to_header or "",
                        "subject": subject or "(No Subject)",
                        "body": body,
                        "received_at": received_at,
                        "raw_message_id": msg_id.decode(),
                        "in_reply_to": in_reply_to or None,
                        "references": references or None,
                        "thread_id": thread_id
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing email {msg_id}: {e}", exc_info=True)
                    continue
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return emails
    
    @staticmethod
    def mark_as_read(mail: imaplib.IMAP4_SSL, message_id: str, folder: str = "INBOX"):
        """Mark email as read"""
        try:
            mail.select(folder)
            # Note: message_id here is the IMAP message number, not the email Message-ID
            mail.store(message_id.encode(), '+FLAGS', '\\Seen')
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
    
    @staticmethod
    def _decode_header(header: Optional[str]) -> str:
        """Decode email header"""
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode()
                else:
                    decoded_string += part
            return decoded_string
        except Exception:
            return str(header) if header else ""
    
    @staticmethod
    def _parse_address(address_header: Optional[str]) -> tuple:
        """Parse email address from header"""
        if not address_header:
            return "", ""
        
        try:
            name, email_addr = email.utils.parseaddr(address_header)
            return email_addr or "", name or ""
        except Exception:
            return address_header or "", ""
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse email date - ensures timezone-aware datetime"""
        try:
            parsed = email.utils.parsedate_to_datetime(date_str)
            # Ensure timezone-aware (if naive, assume UTC)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            # Return timezone-aware datetime.now()
            return datetime.now(timezone.utc)
    
    @staticmethod
    def _extract_body(email_message: email.message.Message) -> str:
        """Extract body text from email message"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get text content
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body += payload.decode(charset, errors="ignore")
                    except Exception as e:
                        logger.warning(f"Error decoding email part: {e}")
        else:
            # Not multipart
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="ignore")
            except Exception as e:
                logger.warning(f"Error decoding email: {e}")
        
        return body.strip()


# Singleton instance
imap_service = IMAPService()

