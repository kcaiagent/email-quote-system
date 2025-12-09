# API Keys and Secrets Guide

## Important: These Are NOT Supabase Keys!

The `API_KEY` and `WEBHOOK_SECRET` are **your own application security keys** - they are **NOT** from Supabase. You need to **generate them yourself**.

## What Each Key Does

### 1. API_KEY
- **Purpose**: Secures your FastAPI endpoints
- **Used for**: Authenticating requests from Wix frontend and other clients
- **Where it's used**: 
  - All protected API endpoints (businesses, quotes, etc.)
  - Sent in `X-API-Key` header or `api_key` query parameter
- **Required**: Yes, for production

### 2. WEBHOOK_SECRET
- **Purpose**: Verifies webhook signatures from Wix
- **Used for**: Ensuring webhook requests are actually from Wix
- **Where it's used**: Wix webhook endpoints
- **Required**: Optional, but recommended for production

### 3. Supabase Keys (You DON'T Need These)
- **anon key**: Only needed if using Supabase REST API (you're not)
- **service_role key**: Only needed for server-side Supabase API calls (you're not)
- **Why you don't need them**: You're using Supabase only as a PostgreSQL database via SQLAlchemy

## How to Generate Secure Keys

### Option 1: Using Python (Recommended)

Create a simple script to generate secure random keys:

```powershell
# Run this in PowerShell
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
```

### Option 2: Using Online Generator

Visit: https://randomkeygen.com/
- Use "CodeIgniter Encryption Keys" or "Fort Knox Passwords"
- Copy a 32+ character random string

### Option 3: Using PowerShell

```powershell
# Generate API_KEY
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Generate WEBHOOK_SECRET
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### Option 4: Using OpenSSL (if installed)

```bash
# Generate API_KEY
openssl rand -base64 32

# Generate WEBHOOK_SECRET
openssl rand -base64 32
```

## Example Generated Keys

After generating, your keys will look like this:

```env
API_KEY=K8mN9pQ2rS5tU7vW0xY1zA3bC4dE6fG8hI9jK0lM1nO2pQ3rS4tU5vW6xY7z
WEBHOOK_SECRET=aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4aB5cD6eF7gH8iJ9kL
```

## Where to Add These Keys

### Local Development (.env file)

Create or update your `.env` file:

```env
# API Security
API_KEY=your-generated-api-key-here
WEBHOOK_SECRET=your-generated-webhook-secret-here
REQUIRE_API_KEY=false  # Set to true in production
```

### Production Server (.env file on Hetzner)

```env
# API Security (REQUIRED in production!)
API_KEY=your-generated-api-key-here
WEBHOOK_SECRET=your-generated-webhook-secret-here
REQUIRE_API_KEY=true
```

## How to Use API_KEY in Your Wix Frontend

When making API calls from Wix, include the API key:

```javascript
// In your Wix frontend code
const API_KEY = 'your-generated-api-key-here';
const API_BASE_URL = 'https://your-api-domain.com/api';

// Example: Create a quote
const response = await fetch(`${API_BASE_URL}/wix/quote`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY  // Include API key in header
  },
  body: JSON.stringify({
    customer_email: 'customer@example.com',
    product_name: 'Custom Surface',
    dimensions: '10x20'
  })
});
```

## Security Best Practices

1. **Never commit keys to Git**
   - ✅ Already in `.gitignore` (`.env` files are ignored)
   - ✅ Never push `.env` files to GitHub

2. **Use different keys for development and production**
   - Development: Can be simpler or even empty (if `REQUIRE_API_KEY=false`)
   - Production: Must be strong, random, and unique

3. **Rotate keys periodically**
   - Change keys every 3-6 months
   - Or immediately if compromised

4. **Store keys securely**
   - Use environment variables (`.env` file)
   - Never hardcode in source code
   - Use secret management services for production (AWS Secrets Manager, etc.)

5. **Restrict API key access**
   - Only share with trusted developers
   - Use different keys for different environments
   - Revoke immediately if exposed

## Quick Setup Script

Create a file `generate_keys.py`:

```python
import secrets
import os

api_key = secrets.token_urlsafe(32)
webhook_secret = secrets.token_urlsafe(32)

print("\n=== Generated Security Keys ===\n")
print(f"API_KEY={api_key}")
print(f"WEBHOOK_SECRET={webhook_secret}")
print("\n=== Add these to your .env file ===\n")
```

Run it:
```powershell
python generate_keys.py
```

## Summary

- ✅ **API_KEY**: Generate yourself - used to secure your API endpoints
- ✅ **WEBHOOK_SECRET**: Generate yourself - used to verify webhook signatures
- ❌ **NOT from Supabase**: Supabase keys are different and you don't need them
- ✅ **Add to .env**: Put both keys in your `.env` file
- ✅ **Keep secret**: Never commit to Git, never share publicly

## Next Steps

1. Generate your keys using one of the methods above
2. Add them to your `.env` file
3. Update your Wix frontend to include the API_KEY in requests
4. Test that authentication works
5. Deploy with keys in production `.env` file






