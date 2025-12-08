# Project Structure

This document explains the structure of the Automated Email Quote System.

## Directory Structure

```
AI EMAIL WEBAPP/
│
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration settings
│   ├── database.py              # Database setup and session management
│   ├── models.py                # SQLAlchemy database models
│   ├── schemas.py               # Pydantic schemas for validation
│   │
│   ├── routers/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── emails.py           # Email processing endpoints
│   │   ├── quotes.py           # Quote management endpoints
│   │   ├── customers.py        # Customer management endpoints
│   │   ├── products.py         # Product management endpoints
│   │   └── wix.py              # Wix integration endpoints
│   │
│   └── services/                # Business logic services
│       ├── __init__.py
│       ├── ai_service.py       # AI-powered email extraction
│       ├── pricing_service.py  # Price calculation logic
│       ├── pdf_service.py      # PDF quote generation
│       ├── email_service.py    # Email sending functionality
│       └── quote_service.py    # Quote creation and processing
│
├── scripts/                      # Utility scripts
│   └── init_db.py              # Database initialization script
│
├── pdf_quotes/                   # Generated PDF quotes (created at runtime)
│
├── requirements.txt              # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── Procfile                     # Deployment configuration
│
├── README.md                    # Main documentation and setup guide
├── WIX_INTEGRATION_GUIDE.md     # Wix integration instructions
└── PROJECT_STRUCTURE.md         # This file (architecture reference)
```

## Key Components

### API Layer (`app/routers/`)

- **businesses.py**: Business account management and OAuth setup
- **oauth.py**: Google OAuth 2.0 authentication endpoints
- **emails.py**: Handles incoming email processing
- **quotes.py**: CRUD operations for quotes
- **customers.py**: Customer management
- **products.py**: Product catalog management
- **wix.py**: Specialized endpoints for Wix integration

### Service Layer (`app/services/`)

- **ai_service.py**: 
  - Extracts product and dimension info from emails using OpenAI
  - Detects email intent (new request, follow-up, duplicate)
  - Falls back to regex if AI is unavailable
  - Generates response messages

- **imap_service.py**:
  - Connects to Gmail via IMAP using OAuth XOAUTH2
  - Fetches unread emails (only after OAuth signup)
  - Extracts thread information (In-Reply-To, References)
  - Marks emails as read after processing

- **oauth_service.py**:
  - Manages Google OAuth 2.0 flow
  - Handles token refresh and storage
  - Encrypts/decrypts OAuth tokens

- **scheduler_service.py**:
  - Background email polling scheduler (every 10 minutes)
  - Manages polling jobs for all active businesses

- **pricing_service.py**:
  - Calculates quote prices based on area and product
  - Validates dimensions against product constraints
  - Applies minimum order amounts

- **pricing_formula_service.py**:
  - Parses and evaluates dynamic pricing formulas
  - Safely executes formulas from uploaded documents

- **document_parser_service.py**:
  - Parses pricing documents (CSV, Excel, PDF, Word)
  - Extracts products and pricing formulas using AI
  - Imports data into product catalog

- **pdf_service.py**:
  - Generates professional PDF quotes using ReportLab
  - Includes customer info, product details, pricing

- **email_service.py**:
  - Sends emails via SMTP (Gmail) using OAuth XOAUTH2
  - Attaches PDF quotes
  - Records email responses with thread tracking
  - Generates Message-IDs for sent emails

- **quote_service.py**:
  - Orchestrates quote creation process
  - Processes emails with thread tracking
  - Detects duplicate requests
  - Handles multi-step flow (incomplete → request → complete)
  - Manages customer recognition (new vs existing)

### Data Layer (`app/models.py`)

Database models:
- **Business**: Business accounts with OAuth configuration and IMAP settings
- **BusinessSettings**: Configuration settings (future use)
- **Product**: Product catalog with pricing formulas (business-specific)
- **Customer**: Customer information (business-specific)
- **EmailInbox**: Raw incoming emails with thread tracking (in_reply_to, thread_id)
- **Quote**: Generated quotes with pricing details
- **EmailResponse**: Outgoing email records with Message-ID and thread tracking

## Data Flow

### Email-to-Quote Flow

1. **Email Received** → `POST /api/emails/process`
2. **Extract Info** → AI service extracts product and dimensions
3. **Find/Create Customer** → Check if customer exists
4. **Validate Info** → Check if all required fields present
5. **Generate Quote** → Calculate price and create PDF
6. **Send Response** → Email customer with quote PDF

### Direct Quote Creation Flow

1. **Wix Request** → `POST /api/wix/quote`
2. **Find/Create Customer** → Lookup by email
3. **Find Product** → Match product name
4. **Calculate Price** → Apply pricing formulas
5. **Generate PDF** → Create quote document
6. **Return Response** → JSON with quote details

## Configuration

### Environment Variables (`.env`)

- `EMAIL_USER`: Gmail address for sending emails
- `EMAIL_PASSWORD`: Gmail App Password
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `DATABASE_URL`: Database connection string
- `HOST`: API host (default: 0.0.0.0)
- `PORT`: API port (default: 8000)
- `DEBUG`: Debug mode (default: True)

### Business Settings

Configurable via database:
- Base price per square inch
- Minimum order amount
- Product pricing
- Quote validity period

## Database Schema

### Core Tables

1. **business_settings**: Key-value configuration
2. **products**: Product catalog
3. **customers**: Customer database
4. **email_inbox**: Incoming emails
5. **quotes**: Generated quotes
6. **email_responses**: Sent emails

## API Endpoints

### Public Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Email Endpoints

- `POST /api/emails/process` - Process incoming email
- `GET /api/emails/` - List emails
- `GET /api/emails/{id}` - Get email by ID

### Quote Endpoints

- `POST /api/quotes/` - Create quote
- `GET /api/quotes/` - List quotes
- `GET /api/quotes/{id}` - Get quote by ID
- `GET /api/quotes/number/{quote_number}` - Get by quote number

### Wix Integration Endpoints

- `POST /api/wix/webhook/email` - Email webhook
- `POST /api/wix/quote` - Create quote from Wix
- `GET /api/wix/quote/{quote_number}` - Get quote for Wix

## Deployment

### Local Development

```bash
py -m app.main
```

### Production (Heroku/Railway/Render)

Uses `Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Extending the System

### Adding New Products

1. Add via API: `POST /api/products/`
2. Or insert directly into database
3. Products are automatically available for quotes

### Customizing Pricing

1. Update `BASE_PRICE_PER_SQ_IN` in config
2. Or set per-product pricing in database
3. Modify `pricing_service.py` for complex formulas

### Adding Email Providers

1. Extend `email_service.py`
2. Add provider-specific configuration
3. Update SMTP settings

### Customizing PDFs

1. Modify `pdf_service.py`
2. Adjust ReportLab templates
3. Add custom branding/styling

## Testing

### Manual Testing

Use the interactive docs at `/docs` or curl commands:

```bash
curl -X POST "http://localhost:8000/api/wix/quote" \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"test@example.com","product_name":"Custom Felt Rug","length_inches":48,"width_inches":36}'
```

### Unit Tests (Future)

Create tests in `tests/` directory:
- Service layer tests
- API endpoint tests
- Integration tests

## Troubleshooting

### Common Issues

1. **Database locked**: Close other connections
2. **Email not sending**: Check Gmail App Password
3. **AI not working**: Verify OpenAI API key
4. **PDF not generating**: Check file permissions

### Logs

- API logs: Console output
- Email logs: Check email service output
- Database logs: SQLAlchemy debug mode

## Support

For issues or questions:
- Check `README_SETUP.md` for detailed setup
- See `WIX_INTEGRATION_GUIDE.md` for Wix help
- Review API docs at `/docs`


