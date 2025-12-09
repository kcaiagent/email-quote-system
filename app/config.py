"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
import os
import json
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()


class Settings(BaseSettings):
    # API Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./quote_system.db"
    
    # CORS - Accepts comma-separated string or JSON array
    ALLOWED_ORIGINS: Union[str, List[str]] = "https://www.wix.com,http://localhost:3000"
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try to parse as JSON first (for pydantic-settings)
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["https://www.wix.com", "http://localhost:3000"]
    
    # Email Settings (Gmail IMAP)
    EMAIL_HOST: str = "imap.gmail.com"
    EMAIL_PORT: int = 993
    EMAIL_USER: str = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")  # Use App Password for Gmail
    EMAIL_FOLDER: str = "INBOX"
    
    # AI Settings (OpenAI)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL: str = "gpt-4"
    
    # PDF Settings
    PDF_OUTPUT_DIR: str = "./pdf_quotes"
    
    # IMAP Polling Settings
    DEFAULT_IMAP_POLL_INTERVAL: int = 10  # Default polling interval in minutes
    IMAP_POLL_TIMEOUT: int = 30  # IMAP connection timeout in seconds
    
    # File Upload Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB max file size
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls", ".pdf", ".docx", ".doc"]
    
    # Encryption Key (for token storage)
    ENCRYPTION_KEY: str = ""
    
    # Google OAuth Settings
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/oauth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Business Settings
    BASE_PRICE_PER_SQ_IN: float = 0.05  # $0.05 per square inch
    MIN_ORDER_AMOUNT: float = 50.00
    
    # API Security
    API_KEY: str = os.getenv("API_KEY", "")  # API key for protected endpoints
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")  # Secret for webhook signature verification
    REQUIRE_API_KEY: bool = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"  # Require API key in production
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Create necessary directories if they don't exist
os.makedirs(settings.PDF_OUTPUT_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "pricing"), exist_ok=True)


