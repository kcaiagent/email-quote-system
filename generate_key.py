"""
Generate security keys for the application
"""
import secrets
from cryptography.fernet import Fernet

print("\n" + "="*50)
print("GENERATING SECURITY KEYS")
print("="*50 + "\n")

# Generate API Key
api_key = secrets.token_urlsafe(32)
print(f"API_KEY={api_key}")

# Generate Webhook Secret
webhook_secret = secrets.token_urlsafe(32)
print(f"WEBHOOK_SECRET={webhook_secret}")

# Generate Encryption Key (for token storage)
encryption_key = Fernet.generate_key().decode()
print(f"ENCRYPTION_KEY={encryption_key}")

print("\n" + "="*50)
print("ADD THESE TO YOUR .env FILE")
print("="*50 + "\n")
print("Copy the keys above and add them to your .env file.")
print("Never commit .env files to Git!\n")

