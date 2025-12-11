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

**Note**: The system uses **OAuth authentication** (not passwords) for secure Gmail access. You don't need to provide an IMAP password during registration. Email credentials are configured separately via OAuth in Step 3.

```json
{
  "name": "My Custom Business",
  "email": "info@mybusiness.com",
  "imap_host": "imap.gmail.com",
  "imap_port": 993,
  "poll_interval_minutes": 10
}
```

**Required fields:**
- `name`: Your business name
- `email`: Your business email address

**Optional fields:**
- `imap_host`: IMAP server (default: "imap.gmail.com")
- `imap_port`: IMAP port (default: 993)
- `poll_interval_minutes`: How often to check for new emails (default: 10)

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

### Step 3: Connect Gmail Account via OAuth

The system uses **OAuth 2.0** for secure Gmail access (no passwords needed!). This is more secure and doesn't require app passwords.

**Step 3.1: Get OAuth Authorization URL**

**API Endpoint**: `GET /api/oauth/google/authorize/{business_id}`

This will return an authorization URL that you need to visit in a browser:

```bash
curl "https://api.yourdomain.com/api/oauth/google/authorize/1"
```

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
  "business_id": 1
}
```

**Step 3.2: Authorize Gmail Access**

1. Open the `authorization_url` in a web browser
2. Sign in with the Google account you want to use for receiving quote requests
3. Grant permissions for Gmail access
4. Google will redirect back to your API callback URL
5. The system will automatically save the OAuth tokens

**Step 3.3: Verify OAuth Connection**

**API Endpoint**: `GET /api/oauth/google/status/{business_id}`

```bash
curl "https://api.yourdomain.com/api/oauth/google/status/1"
```

**Response:**
```json
{
  "business_id": 1,
  "is_connected": true,
  "oauth_email": "info@mybusiness.com",
  "oauth_connected_at": "2024-01-01T12:00:00Z",
  "token_expires_at": "2024-01-02T12:00:00Z"
}
```

**Benefits of OAuth:**
- ✅ More secure than passwords
- ✅ No need to generate app passwords
- ✅ Tokens automatically refresh
- ✅ Can revoke access anytime from Google Account settings

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
  // Use your Cloudflare-protected domain (recommended for security)
  // Example: https://api.yourdomain.com/api/wix/quote
  const API_URL = 'https://api.yourdomain.com/api/wix/quote'; // Replace with your API URL
  const API_KEY = 'your-api-key-here'; // Replace with your API key from .env
  
  try {
    const quoteData = await request.body.json();
    
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY // Add API key authentication
      },
      body: JSON.stringify({
        business_id: quoteData.businessId || null, // Optional: specify business ID
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
  // Use your Cloudflare-protected domain (recommended for security)
  const API_URL = 'https://api.yourdomain.com/api/wix/webhook/email';
  
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

### Step 4: Create Get Products Function

Create a function to fetch products dynamically from your API:

```javascript
// wix-backend/http-functions/getProducts.jsw

import { fetch } from 'wix-fetch';

export async function get_getProducts(request) {
  // Use your Cloudflare-protected domain
  // Replace {business_id} with your actual business ID, or get it from query params
  const businessId = request.query.business_id || '1'; // Default to business ID 1, or get from query
  const API_URL = `https://api.yourdomain.com/api/businesses/${businessId}/products?active_only=true`;
  
  try {
    const response = await fetch(API_URL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const products = await response.json();
    
    return {
      status: 200,
      headers: {
        'Content-Type': 'application/json'
      },
      body: {
        success: true,
        products: products
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
        error: error.message,
        products: []
      }
    };
  }
}
```

### Step 5: Create Multi-Step Wizard Frontend

Now let's create a beautiful multi-step wizard form with custom CSS, loading states, and animations.

#### Step 5.1: Add Page Elements in Wix Editor

In your Wix page, add the following elements (you can find these in the **Add** panel):

**Container Elements:**
- `#wizardContainer` - Container (Box) for the entire wizard
- `#step1Container` - Container for Step 1 (Product Selection)
- `#step2Container` - Container for Step 2 (Dimensions)
- `#step3Container` - Container for Step 3 (Customer Info)
- `#step4Container` - Container for Step 4 (Review)
- `#loadingOverlay` - Container for loading animation (initially hidden)

**Form Elements:**
- `#productGrid` - Repeater or Container for product cards
- `#lengthInput` - Number input for length
- `#widthInput` - Number input for width
- `#emailInput` - Email input
- `#nameInput` - Text input for customer name (optional)
- `#notesTextarea` - Text area for notes

**Navigation Elements:**
- `#nextButton` - Button to go to next step
- `#prevButton` - Button to go to previous step
- `#submitButton` - Button to submit quote (on Step 4)

**Progress Indicator:**
- `#progressBar` - Progress bar or text element showing step progress
- `#stepIndicator` - Text element showing current step (e.g., "Step 1 of 4")

**Status Elements:**
- `#errorMessage` - Text element for error messages (initially hidden)
- `#loadingSpinner` - Image or HTML element for loading animation

#### Step 5.2: Add Custom CSS

Go to **Settings** → **Custom CSS** and add:

```css
/* Multi-Step Wizard Styles */
#wizardContainer {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

/* Step Containers */
.step-container {
  display: none;
  animation: fadeIn 0.3s ease-in;
}

.step-container.active {
  display: block;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Product Grid */
#productGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.product-card {
  padding: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #ffffff;
  text-align: center;
}

.product-card:hover {
  border-color: #4a90e2;
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.2);
}

.product-card.selected {
  border-color: #4a90e2;
  background: #f0f7ff;
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.product-card h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 18px;
}

.product-card p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

/* Form Inputs */
#lengthInput, #widthInput, #emailInput, #nameInput, #notesTextarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s ease;
  margin-bottom: 20px;
}

#lengthInput:focus, #widthInput:focus, #emailInput:focus, 
#nameInput:focus, #notesTextarea:focus {
  outline: none;
  border-color: #4a90e2;
}

.input-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

/* Buttons */
#nextButton, #prevButton, #submitButton {
  padding: 12px 30px;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

#nextButton, #submitButton {
  background: #4a90e2;
  color: white;
  float: right;
}

#nextButton:hover, #submitButton:hover {
  background: #357abd;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

#prevButton {
  background: #f5f5f5;
  color: #333;
  float: left;
}

#prevButton:hover {
  background: #e0e0e0;
}

#nextButton:disabled, #submitButton:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

/* Progress Bar */
#progressBar {
  width: 100%;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  margin-bottom: 30px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a90e2, #5ba3f5);
  border-radius: 3px;
  transition: width 0.3s ease;
  animation: progressAnimation 1s ease;
}

@keyframes progressAnimation {
  from {
    width: 0;
  }
}

/* Loading Overlay */
#loadingOverlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  display: none;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  animation: fadeIn 0.3s ease;
}

#loadingOverlay.active {
  display: flex;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #4a90e2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 20px;
  font-size: 18px;
  color: #333;
  font-weight: 500;
}

/* Error Message */
#errorMessage {
  padding: 12px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  color: #c33;
  margin-bottom: 20px;
  display: none;
}

#errorMessage.show {
  display: block;
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

/* Review Step */
.review-item {
  padding: 15px;
  margin-bottom: 15px;
  background: #f9f9f9;
  border-radius: 6px;
  border-left: 4px solid #4a90e2;
}

.review-item label {
  font-weight: 600;
  color: #666;
  display: block;
  margin-bottom: 5px;
}

.review-item .value {
  color: #333;
  font-size: 16px;
}

/* Responsive */
@media (max-width: 768px) {
  .input-group {
    grid-template-columns: 1fr;
  }
  
  #productGrid {
    grid-template-columns: 1fr;
  }
}
```

#### Step 5.3: Add JavaScript Code

Go to your page's **Settings** → **Custom Code** → **Page Code** and add:

```javascript
import { createQuote } from 'backend/createQuote';
import { getProducts } from 'backend/getProducts';

let currentStep = 1;
const totalSteps = 4;
let formData = {
  product: null,
  length: null,
  width: null,
  email: null,
  name: null,
  notes: null
};

$w.onReady(async function () {
  // Initialize wizard
  initializeWizard();
  
  // Load products
  await loadProducts();
  
  // Set up event handlers
  setupEventHandlers();
});

function initializeWizard() {
  // Show first step
  showStep(1);
  
  // Hide all step containers initially
  $w('#step2Container').hide();
  $w('#step3Container').hide();
  $w('#step4Container').hide();
  $w('#prevButton').hide();
  $w('#errorMessage').hide();
  $w('#loadingOverlay').hide();
  
  // Update progress
  updateProgress();
}

async function loadProducts() {
  try {
    showLoading('Loading products...');
    
    // Replace '1' with your actual business_id, or get it from a config/setting
    const businessId = '1'; // TODO: Replace with your business ID
    const result = await getProducts({ business_id: businessId });
    
    if (result.success && result.products) {
      displayProducts(result.products);
    } else {
      showError('Failed to load products. Please refresh the page.');
    }
  } catch (error) {
    showError('Error loading products: ' + error.message);
  } finally {
    hideLoading();
  }
}

function displayProducts(products) {
  // Clear existing products
  $w('#productGrid').html = '';
  
  // Create product cards
  products.forEach(product => {
    const card = `
      <div class="product-card" data-product-id="${product.id}" data-product-name="${product.name}">
        <h3>${product.name}</h3>
        ${product.description ? `<p>${product.description}</p>` : ''}
        <p style="margin-top: 10px; color: #4a90e2; font-weight: 600;">
          Starting at $${(product.price_per_sq_in || 0.05).toFixed(2)}/sq in
        </p>
      </div>
    `;
    $w('#productGrid').html += card;
  });
  
  // Add click handlers to product cards
  $w('#productGrid').on('click', '.product-card', function(event) {
    const card = event.target.closest('.product-card');
    if (card) {
      // Remove selected class from all cards
      $w('#productGrid').find('.product-card').removeClass('selected');
      // Add selected class to clicked card
      card.classList.add('selected');
      
      // Store selected product
      formData.product = {
        id: card.dataset.productId,
        name: card.dataset.productName
      };
      
      // Enable next button
      $w('#nextButton').enable();
    }
  });
}

function setupEventHandlers() {
  // Next button
  $w('#nextButton').onClick(() => {
    if (validateCurrentStep()) {
      if (currentStep < totalSteps) {
        currentStep++;
        showStep(currentStep);
      }
    }
  });
  
  // Previous button
  $w('#prevButton').onClick(() => {
    if (currentStep > 1) {
      currentStep--;
      showStep(currentStep);
    }
  });
  
  // Submit button
  $w('#submitButton').onClick(async () => {
    await submitQuote();
  });
  
  // Input change handlers for real-time validation
  $w('#lengthInput').onInput(() => {
    formData.length = parseFloat($w('#lengthInput').value);
    validateStep2();
  });
  
  $w('#widthInput').onInput(() => {
    formData.width = parseFloat($w('#widthInput').value);
    validateStep2();
  });
  
  $w('#emailInput').onInput(() => {
    formData.email = $w('#emailInput').value;
    validateStep3();
  });
  
  $w('#nameInput').onInput(() => {
    formData.name = $w('#nameInput').value;
  });
  
  $w('#notesTextarea').onInput(() => {
    formData.notes = $w('#notesTextarea').value;
  });
}

function showStep(step) {
  // Hide all steps
  $w('#step1Container').hide();
  $w('#step2Container').hide();
  $w('#step3Container').hide();
  $w('#step4Container').hide();
  
  // Show current step
  switch(step) {
    case 1:
      $w('#step1Container').show();
      $w('#prevButton').hide();
      break;
    case 2:
      $w('#step2Container').show();
      $w('#prevButton').show();
      validateStep2();
      break;
    case 3:
      $w('#step3Container').show();
      $w('#prevButton').show();
      validateStep3();
      break;
    case 4:
      $w('#step4Container').show();
      $w('#prevButton').show();
      $w('#nextButton').hide();
      $w('#submitButton').show();
      displayReview();
      break;
  }
  
  // Update progress
  updateProgress();
  
  // Scroll to top
  $w('#wizardContainer').scrollIntoView();
}

function updateProgress() {
  const progress = (currentStep / totalSteps) * 100;
  $w('#progressBar').html = `<div class="progress-fill" style="width: ${progress}%"></div>`;
  $w('#stepIndicator').text = `Step ${currentStep} of ${totalSteps}`;
}

function validateCurrentStep() {
  switch(currentStep) {
    case 1:
      if (!formData.product) {
        showError('Please select a product.');
        return false;
      }
      break;
    case 2:
      return validateStep2();
    case 3:
      return validateStep3();
  }
  hideError();
  return true;
}

function validateStep2() {
  const length = parseFloat($w('#lengthInput').value);
  const width = parseFloat($w('#widthInput').value);
  
  if (!length || length <= 0) {
    $w('#nextButton').disable();
    return false;
  }
  
  if (!width || width <= 0) {
    $w('#nextButton').disable();
    return false;
  }
  
  formData.length = length;
  formData.width = width;
  $w('#nextButton').enable();
  hideError();
  return true;
}

function validateStep3() {
  const email = $w('#emailInput').value;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  if (!email || !emailRegex.test(email)) {
    $w('#nextButton').disable();
    return false;
  }
  
  formData.email = email;
  formData.name = $w('#nameInput').value || null;
  $w('#nextButton').enable();
  hideError();
  return true;
}

function displayReview() {
  const reviewHtml = `
    <div class="review-item">
      <label>Product:</label>
      <div class="value">${formData.product.name}</div>
    </div>
    <div class="review-item">
      <label>Dimensions:</label>
      <div class="value">${formData.length}" × ${formData.width}" (${(formData.length * formData.width).toFixed(0)} sq in)</div>
    </div>
    <div class="review-item">
      <label>Email:</label>
      <div class="value">${formData.email}</div>
    </div>
    ${formData.name ? `
    <div class="review-item">
      <label>Name:</label>
      <div class="value">${formData.name}</div>
    </div>
    ` : ''}
    ${formData.notes ? `
    <div class="review-item">
      <label>Notes:</label>
      <div class="value">${formData.notes}</div>
    </div>
    ` : ''}
  `;
  
  $w('#step4Container').html = reviewHtml;
}

async function submitQuote() {
  if (!validateCurrentStep()) {
    return;
  }
  
  try {
    showLoading('Generating your quote...');
    $w('#submitButton').disable();
    hideError();
    
    // Replace '1' with your actual business_id, or get it from a config/setting
    const businessId = '1'; // TODO: Replace with your business ID
    
    const result = await createQuote({
      businessId: businessId, // Optional: specify business ID
      email: formData.email,
      productName: formData.product.name,
      length: formData.length,
      width: formData.width,
      notes: formData.notes || null
    });
    
    if (result.success) {
      // Store quote data for results page
      const quoteData = {
        quoteNumber: result.quote.quote_number,
        productName: result.quote.product_name,
        dimensions: result.quote.dimensions,
        totalPrice: result.quote.total_price,
        pdfUrl: result.quote.pdf_url,
        status: result.quote.status
      };
      
      // Store in wix-storage for results page
      await wixStorage.session.setItem('quoteData', JSON.stringify(quoteData));
      
      // Redirect to results page
      wixLocation.to('/quote-results');
    } else {
      showError(result.error || 'Failed to generate quote. Please try again.');
      $w('#submitButton').enable();
    }
  } catch (error) {
    showError('Error: ' + error.message);
    $w('#submitButton').enable();
  } finally {
    hideLoading();
  }
}

function showLoading(message = 'Loading...') {
  $w('#loadingOverlay').show();
  $w('#loadingOverlay').addClass('active');
  if ($w('#loadingSpinner').length) {
    $w('#loadingSpinner').html = `
      <div class="loading-spinner"></div>
      <div class="loading-text">${message}</div>
    `;
  }
}

function hideLoading() {
  $w('#loadingOverlay').hide();
  $w('#loadingOverlay').removeClass('active');
}

function showError(message) {
  $w('#errorMessage').text = message;
  $w('#errorMessage').show();
  $w('#errorMessage').addClass('show');
}

function hideError() {
  $w('#errorMessage').hide();
  $w('#errorMessage').removeClass('show');
}
```

### Step 7: Create Results Page

Create a new page in Wix called "Quote Results" (or any name you prefer) with the following elements:

**Elements to add:**
- `#resultsContainer` - Main container
- `#quoteNumber` - Text element for quote number
- `#quoteDetails` - HTML element for quote details
- `#emailStatus` - Container for email status
- `#pdfLink` - Link button for PDF download
- `#newQuoteButton` - Button to start a new quote

**Add this code to the Results Page:**

```javascript
$w.onReady(async function () {
  try {
    // Get quote data from session storage
    const quoteDataStr = await wixStorage.session.getItem('quoteData');
    
    if (!quoteDataStr) {
      // No quote data, redirect to quote form
      $w('#resultsContainer').html = `
        <div style="text-align: center; padding: 40px;">
          <h2>No Quote Found</h2>
          <p>Please create a new quote.</p>
          <button onclick="wixLocation.to('/your-quote-page')">Create New Quote</button>
        </div>
      `;
      return;
    }
    
    const quoteData = JSON.parse(quoteDataStr);
    displayResults(quoteData);
    
    // Check email status (you may need to add an API endpoint for this)
    await checkEmailStatus(quoteData.quoteNumber);
    
  } catch (error) {
    $w('#resultsContainer').html = `
      <div style="text-align: center; padding: 40px; color: #c33;">
        <h2>Error</h2>
        <p>${error.message}</p>
      </div>
    `;
  }
});

function displayResults(quoteData) {
  $w('#quoteNumber').text = `Quote #${quoteData.quoteNumber}`;
  
  const detailsHtml = `
    <div style="background: #f9f9f9; padding: 30px; border-radius: 8px; margin: 20px 0;">
      <div style="margin-bottom: 15px;">
        <strong>Product:</strong> ${quoteData.productName}
      </div>
      <div style="margin-bottom: 15px;">
        <strong>Dimensions:</strong> ${quoteData.dimensions}
      </div>
      <div style="margin-bottom: 15px;">
        <strong>Total Price:</strong> <span style="font-size: 24px; color: #4a90e2; font-weight: bold;">$${quoteData.totalPrice.toFixed(2)}</span>
      </div>
      <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
        <p style="color: #666; margin: 0;">
          <strong>Status:</strong> ${quoteData.status}
        </p>
      </div>
    </div>
  `;
  
  $w('#quoteDetails').html = detailsHtml;
  
  if (quoteData.pdfUrl) {
    $w('#pdfLink').show();
    $w('#pdfLink').link = `https://api.yourdomain.com${quoteData.pdfUrl}`;
  } else {
    $w('#pdfLink').hide();
  }
  
  $w('#newQuoteButton').onClick(() => {
    wixLocation.to('/your-quote-page'); // Replace with your quote form page URL
  });
}

async function checkEmailStatus(quoteNumber) {
  try {
    // Note: The current API doesn't automatically send emails when creating quotes via Wix endpoint.
    // You have two options:
    // 1. Modify the backend to send emails automatically when quotes are created
    // 2. Create a separate endpoint to check email status and send emails if needed
    
    // Option 1: Show generic success message (emails are sent automatically)
    $w('#emailStatus').html = `
      <div style="background: #e8f5e9; padding: 15px; border-radius: 6px; border-left: 4px solid #4caf50;">
        <strong>✓ Quote Generated Successfully</strong>
        <p style="margin: 10px 0 0 0; color: #666;">
          Your quote has been generated. An email confirmation will be sent to your email address shortly.
          Please check your inbox (and spam folder).
        </p>
        <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">
          <strong>Quote Number:</strong> ${quoteNumber}
        </p>
      </div>
    `;
    
    // Option 2: If you want to check actual email status, you would need to:
    // - Add an endpoint like GET /api/wix/quote/{quote_number}/email-status
    // - Call it here to get real-time email status
    /*
    const emailStatusResult = await getEmailStatus(quoteNumber);
    if (emailStatusResult.sent) {
      // Show sent status
    } else {
      // Show pending/failed status
    }
    */
  } catch (error) {
    $w('#emailStatus').html = `
      <div style="background: #fff3cd; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107;">
        <strong>Quote Generated</strong>
        <p style="margin: 10px 0 0 0; color: #666;">
          Your quote has been created. Please contact support if you don't receive an email confirmation.
        </p>
      </div>
    `;
  }
}
```

**Add CSS for Results Page:**

```css
#resultsContainer {
  max-width: 700px;
  margin: 0 auto;
  padding: 40px 20px;
  text-align: center;
}

#quoteNumber {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin-bottom: 30px;
}

#emailStatus {
  margin: 30px 0;
  text-align: left;
}

#pdfLink {
  display: inline-block;
  padding: 12px 30px;
  background: #4a90e2;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  margin: 20px 0;
  transition: background 0.3s ease;
}

#pdfLink:hover {
  background: #357abd;
}

#newQuoteButton {
  margin-top: 30px;
  padding: 12px 30px;
  background: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s ease;
}

#newQuoteButton:hover {
  background: #e0e0e0;
}
```

### Step 5: Configure Business ID

**Important**: Before using the frontend, you need to configure your Business ID.

1. Get your Business ID from the Business Setup section (Step 1)
2. In the frontend JavaScript code, replace the placeholder `'1'` with your actual business ID in two places:
   - In the `loadProducts()` function
   - In the `submitQuote()` function

Alternatively, you can store the business ID in Wix Settings and retrieve it dynamically.

### Step 6: Configure Wix Email Integration (Optional)

If you want to automatically process emails sent to a Wix email address:

1. Go to **Settings** → **Email** → **Email Routing**
2. Set up email forwarding to trigger the webhook
3. Or use Wix Automations to call the `processEmail` function when new emails arrive

## Important Notes

### Email Sending

**Note**: The current `/api/wix/quote` endpoint creates quotes but does **not automatically send emails**. If you want emails to be sent automatically when quotes are created via the Wix frontend, you have two options:

1. **Modify the Backend** (Recommended): Update the `create_quote_from_wix_request` function in `app/services/quote_service.py` to automatically send emails after quote creation.

2. **Add a Separate Endpoint**: Create a new endpoint that sends emails for existing quotes, and call it after quote creation.

3. **Use Email Polling**: Rely on the IMAP email polling system to process quote requests sent via email instead of direct API calls.

### Business ID Configuration

Make sure to replace the placeholder business ID (`'1'`) in the frontend code with your actual business ID from the Business Setup section.

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

Make sure your API allows requests from your Wix site. Update `.env` file on your server:

```env
ALLOWED_ORIGINS=https://your-site.wixsite.com,https://www.wix.com,https://api.yourdomain.com
```

**Note**: If using Cloudflare (recommended), use your Cloudflare-protected domain (e.g., `https://api.yourdomain.com`) in the API URL and CORS configuration.

## Testing

1. Test the quote creation endpoint using Postman or curl
2. Test from Wix frontend using the form
3. Monitor API logs for any errors
4. Check that emails are being sent correctly

## Security Considerations

1. **Cloudflare Protection** (Recommended): 
   - Use Cloudflare to protect your API with DDoS protection, WAF, and SSL/TLS
   - See `CLOUDFLARE_SETUP.md` for setup instructions
   - Provides bot protection, rate limiting, and hides origin server IP

2. **API Authentication**: Use API keys for production (already implemented)
3. **Rate Limiting**: Cloudflare provides rate limiting, or implement at application level
4. **Input Validation**: Ensure all inputs are validated (already implemented)
5. **HTTPS**: Always use HTTPS in production (Cloudflare provides free SSL)
6. **CORS**: Restrict CORS to your specific Wix domain (configured in `.env`)

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


