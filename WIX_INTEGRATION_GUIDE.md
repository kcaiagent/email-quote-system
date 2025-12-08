# Wix Integration Guide

This guide explains how to integrate the Automated Email Quote System with your Wix website.

## Overview

The system now supports **multiple businesses** - each business can have their own:
- Email account for receiving quote requests
- Product catalog with custom pricing formulas
- Automated email quote responses

There are two main integration approaches:

1. **IMAP Email Polling**: System automatically polls Gmail/email accounts for incoming quote requests
2. **Direct API Calls**: Wix frontend calls the API directly to create quotes

## Business Setup

### Step 1: Register Your Business

First, you need to register your business with the system. This can be done via API or through a Wix form.

**API Endpoint**: `POST /api/businesses/`

```json
{
  "name": "My Custom Business",
  "email": "info@mybusiness.com",
  "imap_email": "info@mybusiness.com",
  "imap_password": "your-gmail-app-password",
  "imap_host": "imap.gmail.com",
  "imap_port": 993,
  "poll_interval_minutes": 10
}
```

**Response**:
```json
{
  "id": 1,
  "name": "My Custom Business",
  "email": "info@mybusiness.com",
  "active": true,
  ...
}
```

**Save the `business_id`** - you'll need it for subsequent API calls.

### Step 2: Upload Pricing Document

Upload your pricing document (CSV, PDF, Excel, or Word) to automatically configure products and pricing formulas.

**API Endpoint**: `POST /api/businesses/{business_id}/pricing/upload`

**File Format Example (CSV)**:
```csv
Product,Base Price,Price per Sq Inch,Min Size,Max Size,Formula
Custom Felt Rug,10.00,0.05,100,10000,"base_price + (area * rate)"
Acrylic Tabletop,25.00,0.15,200,5000,"base_price + (area * rate)"
```

The AI will automatically extract products and pricing formulas from your document.

### Step 3: Configure Email Credentials

Set up your Gmail account for automatic email polling:

**API Endpoint**: `POST /api/businesses/{business_id}/email/setup`

```json
{
  "imap_email": "info@mybusiness.com",
  "imap_password": "your-16-character-gmail-app-password",
  "imap_host": "imap.gmail.com",
  "imap_port": 993
}
```

**Note**: Use a Gmail App Password (not your regular password):
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Generate App Password for "Mail"
4. Use the 16-character password

The system will automatically poll your inbox every 10 minutes (configurable) for new quote requests and respond automatically!

## Setup in Wix

### Step 1: Add HTTP Functions to Wix Backend

In your Wix site editor, go to **Dev Mode** → **Backend** → **HTTP Functions**.

### Step 2: Create Quote Creation Function

Create a new HTTP function called `createQuote`:

```javascript
// wix-backend/http-functions/createQuote.jsw

import { fetch } from 'wix-fetch';

export async function post_createQuote(request) {
  const API_URL = 'https://your-api-domain.com/api/wix/quote'; // Replace with your API URL
  
  try {
    const quoteData = await request.body.json();
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer_email: quoteData.email,
        product_name: quoteData.productName,
        length_inches: parseFloat(quoteData.length),
        width_inches: parseFloat(quoteData.width),
        notes: quoteData.notes || null
      })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const result = await response.json();
    
    return {
      status: 200,
      headers: {
        'Content-Type': 'application/json'
      },
      body: {
        success: true,
        quote: result
      }
    };
    
  } catch (error) {
    return {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      },
      body: {
        success: false,
        error: error.message
      }
    };
  }
}
```

### Step 3: Create Email Processing Function

Create a webhook function to process incoming emails:

```javascript
// wix-backend/http-functions/processEmail.jsw

import { fetch } from 'wix-fetch';

export async function post_processEmail(request) {
  const API_URL = 'https://your-api-domain.com/api/wix/webhook/email';
  
  try {
    const emailData = await request.body.json();
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: emailData.from,
        name: emailData.name,
        subject: emailData.subject,
        body: emailData.body,
        received_at: new Date().toISOString()
      })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const result = await response.json();
    
    return {
      status: 200,
      headers: {
        'Content-Type': 'application/json'
      },
      body: {
        success: true,
        message: result.message
      }
    };
    
  } catch (error) {
    return {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      },
      body: {
        success: false,
        error: error.message
      }
    };
  }
}
```

### Step 4: Create Frontend Form

In your Wix page, add a form with these fields:
- Email (email input)
- Product Name (dropdown or text)
- Length (number input)
- Width (number input)
- Notes (textarea, optional)

Then add this code to your page:

```javascript
import { createQuote } from 'backend/createQuote';

$w.onReady(function () {
  $w('#submitButton').onClick(async () => {
    try {
      // Get form values
      const email = $w('#emailInput').value;
      const productName = $w('#productDropdown').value;
      const length = $w('#lengthInput').value;
      const width = $w('#widthInput').value;
      const notes = $w('#notesTextarea').value;
      
      // Validate
      if (!email || !productName || !length || !width) {
        $w('#statusText').text = 'Please fill in all required fields.';
        return;
      }
      
      // Show loading
      $w('#statusText').text = 'Generating quote...';
      $w('#submitButton').disable();
      
      // Call backend function
      const result = await createQuote({
        email: email,
        productName: productName,
        length: length,
        width: width,
        notes: notes
      });
      
      if (result.success) {
        // Show quote result
        const quote = result.quote;
        $w('#statusText').html = `
          <h3>Quote Generated!</h3>
          <p><strong>Quote Number:</strong> ${quote.quote_number}</p>
          <p><strong>Product:</strong> ${quote.product_name}</p>
          <p><strong>Dimensions:</strong> ${quote.dimensions}</p>
          <p><strong>Total Price:</strong> $${quote.total_price.toFixed(2)}</p>
          ${quote.pdf_url ? `<a href="${quote.pdf_url}" target="_blank">Download PDF Quote</a>` : ''}
        `;
        
        // Reset form
        $w('#emailInput').value = '';
        $w('#lengthInput').value = '';
        $w('#widthInput').value = '';
        $w('#notesTextarea').value = '';
      } else {
        $w('#statusText').text = `Error: ${result.error}`;
      }
      
    } catch (error) {
      $w('#statusText').text = `Error: ${error.message}`;
    } finally {
      $w('#submitButton').enable();
    }
  });
});
```

### Step 5: Configure Wix Email Integration (Optional)

If you want to automatically process emails sent to a Wix email address:

1. Go to **Settings** → **Email** → **Email Routing**
2. Set up email forwarding to trigger the webhook
3. Or use Wix Automations to call the `processEmail` function when new emails arrive

## API Endpoints for Wix

### Create Quote
```
POST /api/wix/quote
Content-Type: application/json

{
  "customer_email": "customer@email.com",
  "product_name": "Custom Felt Rug",
  "length_inches": 48,
  "width_inches": 36,
  "notes": "Optional notes"
}
```

**Response:**
```json
{
  "quote_number": "Q-20240101-ABC123",
  "customer_name": "Customer Name",
  "product_name": "Custom Felt Rug",
  "dimensions": "48\" × 36\"",
  "area_sq_inches": 1728,
  "total_price": 101.40,
  "pdf_url": "/api/quotes/1/pdf",
  "status": "pending",
  "message": "Quote generated successfully"
}
```

### Process Email Webhook
```
POST /api/wix/webhook/email
Content-Type: application/json

{
  "email": "customer@email.com",
  "name": "Customer Name",
  "subject": "Custom Felt Rug Quote",
  "body": "Hi, I need a 48\" x 36\" custom felt rug.",
  "received_at": "2024-01-01T12:00:00Z"
}
```

**Response:**
```json
{
  "status": "received",
  "message": "Email is being processed"
}
```

### Get Quote
```
GET /api/wix/quote/{quote_number}
```

**Response:**
```json
{
  "quote_number": "Q-20240101-ABC123",
  "customer_name": "Customer Name",
  "product_name": "Custom Felt Rug",
  "dimensions": "48\" × 36\"",
  "area_sq_inches": 1728,
  "total_price": 101.40,
  "pdf_url": "/api/quotes/1/pdf",
  "status": "pending",
  "message": "Quote retrieved successfully"
}
```

## CORS Configuration

Make sure your API allows requests from your Wix site. Update `app/config.py`:

```python
ALLOWED_ORIGINS = [
    "https://your-site.wixsite.com",
    "https://www.yourdomain.com",  # If using custom domain
]
```

## Testing

1. Test the quote creation endpoint using Postman or curl
2. Test from Wix frontend using the form
3. Monitor API logs for any errors
4. Check that emails are being sent correctly

## Security Considerations

1. **API Authentication**: Consider adding API keys for production
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Input Validation**: Ensure all inputs are validated
4. **HTTPS**: Always use HTTPS in production
5. **CORS**: Restrict CORS to your specific Wix domain

## Troubleshooting

### CORS Errors
- Verify your Wix domain is in `ALLOWED_ORIGINS`
- Check that the API is using HTTPS

### API Not Responding
- Verify the API URL is correct
- Check that the API server is running
- Verify network connectivity

### Quote Not Generated
- Check API logs for errors
- Verify all required fields are provided
- Check database connectivity

## Support

For more help, refer to:
- Main README: `README.md`
- Setup Guide: `README_SETUP.md`
- API Documentation: `http://your-api-url/docs`


