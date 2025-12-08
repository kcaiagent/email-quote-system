"""
Utility functions
"""
from cryptography.fernet import Fernet
import base64
import os
from typing import Optional


def get_encryption_key() -> bytes:
    """Get or generate encryption key for password storage"""
    key_env = os.getenv("ENCRYPTION_KEY")
    if key_env:
        # Strip any whitespace and use the key directly (it's already base64-encoded)
        key_env = key_env.strip()
        try:
            # Fernet key from .env is base64 string, encode to bytes
            return key_env.encode()
        except Exception as e:
            print(f"Error processing encryption key: {e}")
            # Fallback: try to decode if it's double-encoded (shouldn't happen)
            try:
                return base64.urlsafe_b64decode(key_env.encode())
            except Exception:
                pass
    else:
        # Generate a key (for development only - should be set in production)
        # In production, generate once: py -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        default_key = os.getenv("DEFAULT_ENCRYPTION_KEY")
        if default_key:
            return default_key.strip().encode()
        else:
            # For development/testing - generate a static key
            # WARNING: This is insecure for production!
            key = Fernet.generate_key()
            print(f"WARNING: Generated new encryption key. Set ENCRYPTION_KEY env var: {key.decode()}")
            return key


def encrypt_password(password: str) -> str:
    """Encrypt a password for storage"""
    if not password:
        return ""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a stored password"""
    if not encrypted_password:
        return ""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"Error decrypting password: {e}")
        return ""


def encrypt_token(token_data: str) -> str:
    """Encrypt a token (OAuth tokens) for storage"""
    if not token_data:
        return ""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(token_data.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a stored token (OAuth tokens)"""
    if not encrypted_token:
        return ""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"Error decrypting token: {e}")
        return ""

