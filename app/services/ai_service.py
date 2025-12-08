"""
AI service for extracting information from customer emails
"""
import json
import re
from typing import Dict, Optional, Tuple
from app.config import settings
import openai


class AIService:
    """Service for AI-powered email extraction"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
    
    def extract_quote_info(self, email_body: str, email_subject: str) -> Dict:
        """
        Extract product and dimension information from customer email using AI
        
        Returns:
            {
                "product_name": str or None,
                "length_inches": float or None,
                "width_inches": float or None,
                "has_complete_info": bool,
                "missing_fields": list,
                "confidence": float
            }
        """
        if not settings.OPENAI_API_KEY:
            # Fallback to regex extraction if AI is not configured
            return self._regex_extraction(email_body, email_subject)
        
        try:
            prompt = f"""Extract product quote information from this customer email.

Email Subject: {email_subject}
Email Body: {email_body}

Please extract:
1. Product name/type (e.g., "custom felt rug", "acrylic tabletop", "felt rug", etc.)
2. Length in inches (look for dimensions like "48 inches", "48\"", "48 x 36", etc.)
3. Width in inches

Return a JSON object with:
{{
    "product_name": "product name or null if not found",
    "length_inches": number or null,
    "width_inches": number or null,
    "has_complete_info": boolean,
    "missing_fields": ["list of missing field names"],
    "confidence": 0.0-1.0
}}

If dimensions are mentioned in format like "48x36" or "48 x 36", parse them as length x width.
If only one dimension is mentioned, set the other to null."""

            # Try new OpenAI API format first (v1.0+)
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=settings.AI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts structured information from emails."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                content = response.choices[0].message.content.strip()
            except (ImportError, AttributeError):
                # Fallback to old API format
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts structured information from emails."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            content = re.sub(r'```json\n?', '', content)
            content = re.sub(r'```\n?', '', content)
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"AI extraction failed: {e}. Falling back to regex.")
            return self._regex_extraction(email_body, email_subject)
    
    def detect_email_intent(self, email_body: str, email_subject: str, is_reply_to_us: bool = False) -> Dict:
        """
        Detect the intent of an email - new request, follow-up with info, or other
        
        Returns:
            {
                "intent": "new_request" | "follow_up_with_info" | "follow_up_question" | "duplicate",
                "confidence": float,
                "reason": str
            }
        """
        if not settings.OPENAI_API_KEY:
            # Fallback logic
            text = f"{email_subject} {email_body}".lower()
            if is_reply_to_us:
                # If replying to us, likely providing info or asking follow-up
                if any(word in text for word in ["here", "information", "details", "size", "dimension"]):
                    return {"intent": "follow_up_with_info", "confidence": 0.7, "reason": "Contains info keywords"}
                return {"intent": "follow_up_question", "confidence": 0.6, "reason": "Reply but unclear intent"}
            return {"intent": "new_request", "confidence": 0.8, "reason": "New email"}
        
        try:
            prompt = f"""Analyze this customer email and determine its intent.

Email Subject: {email_subject}
Email Body: {email_body}
Is this a reply to an email we sent? {is_reply_to_us}

Determine the intent:
1. "new_request" - This is a new quote request (first time asking)
2. "follow_up_with_info" - Customer is providing additional information we requested
3. "follow_up_question" - Customer is asking a follow-up question about a previous quote
4. "duplicate" - Customer is repeating the same request we already responded to

Return JSON:
{{
    "intent": "one of the intents above",
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}}"""

            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=settings.AI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes email intent for a quote automation system."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=200
                )
                content = response.choices[0].message.content.strip()
            except (ImportError, AttributeError):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that analyzes email intent for a quote automation system."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=200
                )
                content = response.choices[0].message.content.strip()
            
            content = re.sub(r'```json\n?', '', content)
            content = re.sub(r'```\n?', '', content)
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"AI intent detection failed: {e}. Using fallback.")
            text = f"{email_subject} {email_body}".lower()
            if is_reply_to_us:
                return {"intent": "follow_up_with_info", "confidence": 0.6, "reason": "Reply detected, fallback"}
            return {"intent": "new_request", "confidence": 0.7, "reason": "Fallback detection"}
    
    def _regex_extraction(self, email_body: str, email_subject: str) -> Dict:
        """Fallback regex-based extraction"""
        text = f"{email_subject} {email_body}".lower()
        
        # Extract dimensions (look for patterns like "48x36", "48 x 36", "48\" x 36\"")
        dimension_pattern = r'(\d+(?:\.\d+)?)\s*["\']?\s*[x×]\s*["\']?\s*(\d+(?:\.\d+)?)'
        match = re.search(dimension_pattern, text)
        
        length = None
        width = None
        
        if match:
            length = float(match.group(1))
            width = float(match.group(2))
        
        # Extract product name (look for common keywords)
        product_keywords = [
            r'felt\s+rug',
            r'acrylic\s+tabletop',
            r'custom\s+felt',
            r'rug',
            r'tabletop',
            r'felt'
        ]
        
        product_name = None
        for pattern in product_keywords:
            match = re.search(pattern, text)
            if match:
                product_name = match.group(0).strip()
                break
        
        missing_fields = []
        if not product_name:
            missing_fields.append("product_name")
        if not length:
            missing_fields.append("length_inches")
        if not width:
            missing_fields.append("width_inches")
        
        return {
            "product_name": product_name,
            "length_inches": length,
            "width_inches": width,
            "has_complete_info": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "confidence": 0.7 if (product_name or (length and width)) else 0.3
        }
    
    def generate_response_message(self, quote_data: Dict, missing_fields: list) -> str:
        """Generate a professional response message"""
        if missing_fields:
            # Request missing information
            fields_needed = []
            if "product_name" in missing_fields:
                fields_needed.append("Product name/type")
            if "length_inches" in missing_fields:
                fields_needed.append("Length (in inches)")
            if "width_inches" in missing_fields:
                fields_needed.append("Width (in inches)")
            
            message = f"""Hi {quote_data.get('customer_name', 'there')},

Thank you for your inquiry!

To provide an accurate quote, we need the following information:
{chr(10).join(f'- {field}' for field in fields_needed)}

Once we have these details, we'll send your quote right away!

Best regards,
Kyoto Custom Surfaces"""
        else:
            # Quote generated
            message = f"""Dear {quote_data.get('customer_name', 'Valued Customer')},

Thank you for your inquiry!

Here's your quote:

Product: {quote_data.get('product_name')}
Dimensions: {quote_data.get('length_inches')}" × {quote_data.get('width_inches')}" ({quote_data.get('area_sq_inches', 0):.0f} sq in)
Price: ${quote_data.get('total_price', 0):.2f}

Please find your detailed quote attached as a PDF.

If you have any questions, please don't hesitate to reach out!

Best regards,
Kyoto Custom Surfaces"""
        
        return message


# Singleton instance
ai_service = AIService()

