# Automated Email Quote System

An intelligent email automation system that connects to Gmail via OAuth, automatically processes incoming quote requests, extracts information using AI, and generates and sends professional quotes via email.

## Features

- ✅ **OAuth Gmail Integration** - Secure connection via Google OAuth 2.0 (no passwords needed)
- ✅ **Automatic Email Polling** - Checks inbox every 10 minutes for new quote requests
- ✅ **AI-Powered Extraction** - Uses GPT-4 to extract product details and dimensions from emails
- ✅ **Dynamic Pricing** - Supports complex pricing formulas from uploaded documents
- ✅ **Thread Tracking** - Prevents duplicate replies and tracks conversation threads
- ✅ **Smart Reply Detection** - Recognizes new requests vs. follow-ups vs. duplicates
- ✅ **Multi-Step Flow** - Handles incomplete requests → request info → send quote
- ✅ **Date Filtering** - Only processes emails received after OAuth signup
- ✅ **PDF Quote Generation** - Creates professional PDF quotes automatically
- ✅ **Multi-Business Support** - Each business has separate configuration and data

## Architecture

- **Backend**: Python FastAPI REST API
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **AI**: OpenAI GPT-4 for email extraction and intent detection
- **Email**: Gmail IMAP (read) and SMTP (send) via OAuth XOAUTH2
- **Authentication**: Google OAuth 2.0
- **Scheduler**: APScheduler for background email polling

## Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud Project (for OAuth)
- OpenAI API key (optional, for AI features)
- Gmail account

### Installation

1. **Install dependencies:**
   ```bash
   py -m pip install -r requirements.txt
   ```

2. **Generate encryption key:**
   ```bash
   py -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Copy the generated key.

3. **Create `.env` file:**
   ```env
   # Database
   DATABASE_URL=sqlite:///./quote_system.db

   # Google OAuth (required)
   GOOGLE_OAUTH_CLIENT_ID=your-client-id
   GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
   GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback
   FRONTEND_URL=http://localhost:3000

   # Encryption (required)
   ENCRYPTION_KEY=your-generated-encryption-key

   # OpenAI (optional, for AI features)
   OPENAI_API_KEY=your-openai-api-key
   AI_MODEL=gpt-4
   ```

4. **Set up Google OAuth:**
   
   **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project (or select existing)
   - Enable Gmail API: "APIs & Services" > "Library" > Search "Gmail API" > Enable
   
   **Configure OAuth Consent Screen:**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" (unless you have Google Workspace)
   - Fill in app name, support email, developer contact
   - Add scope: `https://mail.google.com/` (for IMAP/SMTP access)
   - Add test users (your email) if in testing mode
   
   **Create OAuth Credentials:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: Web application
   - Authorized redirect URI: `http://localhost:8000/api/oauth/google/callback`
   - Copy Client ID and Client Secret to `.env`
   
   **Note:** In testing mode, you'll see a verification warning when authorizing - this is normal. Click "Advanced" → "Go to [App Name] (unsafe)" to proceed.

5. **Initialize database:**
   ```bash
   py scripts/init_db.py
   ```

6. **Start server:**
   ```bash
   py -m app.main
   ```

Server runs at `http://localhost:8000`

## Usage

### 1. Create a Business

```bash
curl -X POST "http://localhost:8000/api/businesses/" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Business", "email": "mybusiness@gmail.com"}'
```

Note the `id` from the response.

### 2. Connect Gmail Account (OAuth)

1. Get authorization URL:
   ```bash
   curl "http://localhost:8000/api/oauth/google/authorize/1"
   ```
   (Replace `1` with your business ID)

2. Copy `authorization_url` and open in browser

3. Sign in with Gmail and grant permissions

4. Verify connection:
   ```bash
   curl "http://localhost:8000/api/oauth/google/status/1"
   ```

### 3. Upload Pricing Document (Optional)

```bash
curl -X POST "http://localhost:8000/api/businesses/1/pricing/upload" \
  -F "file=@pricing.csv"
```

Supports: CSV, Excel (xlsx, xls), PDF, Word (docx, doc)

### 4. System Automatically:

- Polls Gmail inbox every 10 minutes
- Processes emails received **after OAuth signup only**
- Extracts quote information using AI
- Generates quotes and sends replies automatically
- Tracks conversation threads to avoid duplicates

## API Documentation

Interactive API docs available at: `http://localhost:8000/docs`

### Key Endpoints

- `GET /api/businesses/` - List businesses
- `POST /api/businesses/` - Create business
- `GET /api/oauth/google/authorize/{business_id}` - Get OAuth URL
- `GET /api/oauth/google/status/{business_id}` - Check OAuth status
- `POST /api/businesses/{business_id}/poll-emails` - Manually trigger email polling
- `GET /api/quotes/` - List quotes
- `GET /api/emails/` - List processed emails

## How It Works

### Email Processing Flow

1. **Email Polling** (every 10 minutes)
   - Connects to Gmail via IMAP XOAUTH2
   - Fetches unread emails received after OAuth signup
   - Only processes emails not already in database

2. **Email Analysis**
   - AI extracts: product name, dimensions, customer info
   - Detects intent: new request, follow-up, or duplicate
   - Checks thread history to avoid duplicate replies

3. **Quote Generation** (if complete info)
   - Finds or creates customer record
   - Matches product from database
   - Calculates price using pricing formula
   - Generates PDF quote
   - Sends email with quote attached

4. **Information Request** (if incomplete info)
   - Sends friendly email asking for missing details
   - Tracks conversation thread
   - Waits for follow-up email with complete info

### Thread Tracking

- Extracts `In-Reply-To` and `References` headers
- Links emails in same conversation thread
- Prevents duplicate quotes in same thread
- Preserves multi-step flow (incomplete → request → complete)

### Smart Features

- **Intent Detection**: Distinguishes new requests from follow-ups
- **Duplicate Prevention**: Avoids sending multiple quotes for same request
- **Date Filtering**: Only processes emails after signup (ignores old emails)
- **Customer Recognition**: Tracks returning customers
- **Business Isolation**: Each business has separate data and configuration

## Configuration

### Email Polling Interval

Default: 10 minutes. Change per business:

```python
business.poll_interval_minutes = 15  # Custom interval
```

### OAuth Scopes

Required scope: `https://mail.google.com/` (for IMAP/SMTP access)

### Environment Variables

See `.env.example` for all available options.

## Database Schema

### Main Tables

- **businesses** - Business accounts and OAuth configuration
- **customers** - Customer records (business-specific)
- **products** - Product catalog with pricing formulas
- **quotes** - Generated quotes
- **email_inbox** - Incoming emails with thread tracking
- **email_responses** - Outgoing emails (quote replies)

## Production Deployment

### Database

Switch to PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### OAuth Redirect URI

Update in Google Cloud Console and `.env`:
```
GOOGLE_OAUTH_REDIRECT_URI=https://yourdomain.com/api/oauth/google/callback
```

### HTTPS Required

OAuth requires HTTPS in production. Use:
- Heroku
- Railway
- Render
- AWS/GCP with SSL

### Environment Variables

Set all required variables in production environment (not in code).

## Troubleshooting

### IMAP Connection Issues

- Verify OAuth connection: `GET /api/oauth/google/status/{business_id}`
- Check email address matches authorized Gmail account
- Ensure `https://mail.google.com/` scope is granted

### Emails Not Processing

- Check server logs for errors
- Verify OAuth tokens are valid
- Ensure emails are unread and received after signup
- Check polling is running (every 10 minutes)

### AI Extraction Failing

- Verify `OPENAI_API_KEY` is set
- Check API quota/billing
- Falls back to regex extraction if AI unavailable

## Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── config.py            # Configuration
├── models.py            # Database models
├── schemas.py           # API schemas
├── routers/             # API endpoints
│   ├── businesses.py
│   ├── oauth.py
│   ├── quotes.py
│   └── ...
└── services/            # Business logic
    ├── imap_service.py      # Email polling
    ├── oauth_service.py     # OAuth handling
    ├── quote_service.py     # Quote processing
    ├── ai_service.py        # AI extraction
    └── ...
```

## License

[Your License Here]

## Support

For issues or questions, check the logs or API docs at `/docs`.

