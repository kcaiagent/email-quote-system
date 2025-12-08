# Deployment Guide - Cloud Server + Wix + Supabase

## Deployment Order

1. ✅ **Supabase Database Setup** (Start Here)
2. ⏳ **Update Database Configuration**
3. ⏳ **Deploy to Cloud Server**
4. ⏳ **Configure Wix Integration**

---

## Step 1: Supabase Database Setup

### 1.1 Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up/Log in
3. Click "New Project"
4. Fill in:
   - **Project Name**: `email-quote-system` (or your choice)
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free tier is fine for testing

### 1.2 Get Database Connection String

1. In your Supabase project dashboard:
   - Go to **Settings** → **Database**
   - Scroll to **Connection String**
   - Select **URI** tab (NOT Connection pooling)
   - Copy the connection string

**Format will be:**
```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Important**: Use **Session Pooling** (port 5432), NOT Transaction Pooling (port 6543).

**Why Session Pooling?**
- ✅ SQLAlchemy ORM requires session state (identity map, lazy loading)
- ✅ Your code uses `db.flush()` which needs session state
- ✅ Supports prepared statements (used by SQLAlchemy)
- ✅ Better for ORM-based applications

**Transaction Pooling (port 6543) limitations:**
- ❌ No prepared statements (SQLAlchemy uses them)
- ❌ No session variables or temporary tables
- ❌ Session state not preserved between operations

### 1.3 Supabase API Keys (NOT NEEDED for Your Current Setup)

**You don't need Supabase API keys** because your app uses Supabase only as a PostgreSQL database via SQLAlchemy. You're connecting directly using the PostgreSQL connection string.

**When would you need API keys?**
- If you want to use Supabase's REST API from your frontend
- If you want to use Supabase Auth, Storage, or Realtime features
- If you want to use Supabase's JavaScript client library

**If you need them later:**
- Go to **Settings** → **API** in your Supabase dashboard
- **anon key** (also called "anon/public key"): 
  - ✅ Safe to expose in client-side code (browser, mobile apps)
  - ✅ Respects Row Level Security (RLS) policies
  - ✅ Use this for frontend applications
- **service_role key**:
  - ⚠️ **NEVER expose this in client-side code**
  - ⚠️ Bypasses all RLS policies
  - ⚠️ Use only in secure server-side code
  - ⚠️ Has full database access

**Note**: There's no separate "publishable key" - the **anon key IS the publishable/public key**.

---

## Step 2: Update Database Configuration

### 2.1 Install PostgreSQL Driver

```powershell
py -m pip install psycopg2-binary
```

### 2.2 Update `.env` File

Add your Supabase connection string:

```env
# Database - Supabase PostgreSQL (Session Pooling - REQUIRED for SQLAlchemy ORM)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Note**: Use port **5432** (Session Pooling), not 6543 (Transaction Pooling). SQLAlchemy ORM requires session state which transaction pooling doesn't support.

**Important**: Replace `[YOUR-PASSWORD]`, `[PROJECT-REF]`, and `[REGION]` with your actual values.

### 2.3 Test Database Connection Locally

```powershell
# Test connection
py -c "from app.database import engine; engine.connect(); print('✓ Database connected!')"
```

### 2.4 Run Migrations

```powershell
# Apply migrations to Supabase
.\alembic.ps1 upgrade head
```

---

## Step 3: Cloud Server Deployment

### 3.1 Prerequisites for Cloud Server

Your cloud server should have:
- ✅ Python 3.11+ installed
- ✅ Git installed
- ✅ Access via SSH
- ✅ Domain name (optional but recommended) or IP address

### 3.2 Deployment Options

**Option A: Simple Deployment (Direct)**
1. SSH into your server
2. Clone your repository
3. Install dependencies
4. Run with `uvicorn`

**Option B: Using PM2 (Recommended for Node.js-style process management)**
1. Install PM2: `npm install -g pm2`
2. Create PM2 ecosystem file
3. Start with PM2

**Option C: Using systemd (Linux service)**
1. Create systemd service file
2. Enable and start service

**Option D: Using Docker (Most robust) - Recommended for Hetzner**

See detailed instructions below in [**Section 3.5: Docker Deployment on Hetzner**](#35-docker-deployment-on-hetzner-detailed-guide)

### 3.3 Environment Variables on Server

Create `.env` file on server with:

```env
# Database (Session Pooling - port 5432, NOT transaction pooling)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# API Security (REQUIRED in production!)
API_KEY=your-strong-production-api-key-here
REQUIRE_API_KEY=true
WEBHOOK_SECRET=your-webhook-secret-here

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=https://your-api-domain.com/api/oauth/google/callback
FRONTEND_URL=https://your-wix-site.wixsite.com

# Encryption Key
ENCRYPTION_KEY=your-encryption-key

# OpenAI (if using AI features)
OPENAI_API_KEY=your-openai-key

# CORS - Update with your Wix domain
ALLOWED_ORIGINS=https://your-wix-site.wixsite.com,https://www.wix.com
```

### 3.4 Server Requirements

- **Memory**: At least 512MB RAM (1GB+ recommended for Docker)
- **CPU**: 1 core minimum
- **Storage**: 1GB minimum (2GB+ recommended for Docker images)
- **Network**: Port 8000 (or your chosen port) accessible

### 3.5 Docker Deployment on Hetzner (Detailed Guide)

This guide walks you through deploying your application using Docker on a Hetzner cloud server.

#### Step 1: Create Hetzner Cloud Server

1. **Log in to Hetzner Cloud Console**
   - Go to [https://console.hetzner.cloud](https://console.hetzner.cloud)
   - Sign in or create an account

2. **Create a New Project**
   - Click "New Project"
   - Name it: `email-quote-system` (or your choice)
   - Click "Create Project"

3. **Create a Server**
   - Click "Add Server"
   - **Location**: Choose closest to your users (e.g., `Falkenstein`, `Nuremberg`, `Helsinki`)
   - **Image**: Select `Ubuntu 22.04` or `Debian 12`
   - **Type**: 
     - **Minimum**: `CX11` (1 vCPU, 2GB RAM, 20GB SSD) - €4.15/month
     - **Recommended**: `CX21` (2 vCPU, 4GB RAM, 40GB SSD) - €8.29/month
   - **SSH Keys**: Add your SSH public key (or create one)
   - **Firewall**: Create firewall rules (or do this after server creation):
     - **Rule 1 - SSH**: 
       - Direction: `Inbound`
       - Protocol: `TCP`
       - Port: `22`
       - Source IPs: `0.0.0.0/0` (or restrict to your IP for security)
       - IPv4: ✅ Enabled
     - **Rule 2 - API**: 
       - Direction: `Inbound`
       - Protocol: `TCP`
       - Port: `8000`
       - Source IPs: `0.0.0.0/0` (allow from anywhere, or restrict as needed)
       - IPv4: ✅ Enabled
     - **Rule 3 - HTTP** (if using reverse proxy): 
       - Direction: `Inbound`
       - Protocol: `TCP`
       - Port: `80`
       - Source IPs: `0.0.0.0/0`
       - IPv4: ✅ Enabled
     - **Rule 4 - HTTPS** (if using reverse proxy): 
       - Direction: `Inbound`
       - Protocol: `TCP`
       - Port: `443`
       - Source IPs: `0.0.0.0/0`
       - IPv4: ✅ Enabled
     
     **Note**: You can also create the firewall rules after server creation in the Hetzner Cloud Console under **Networking → Firewalls**.
   - **Name**: `email-quote-api`
   - Click "Create & Buy Now"

4. **Note Your Server IP and Access Info**
   - Copy the IPv4 address (e.g., `123.45.67.89`)
   - **Important**: Check the server details page for:
     - Root password (if no SSH key was added)
     - Or use the browser-based Console to access the server
   - You'll need this for SSH and API access

#### Step 2: Connect to Your Server

**Quick Access Methods:**

1. **Easiest**: Use Hetzner's browser console (no password needed)
   - Go to your server → Click **"Console"** tab → Click **"Launch Console"**

2. **Check for root password**:
   - Go to your server → Look for **"Root Password"** or **"Access"** section
   - Hetzner may have generated one during server creation

3. **Use SSH** (once you have password or SSH key set up)

**Troubleshooting SSH Access:**

If you're being asked for a password you don't remember, here are the solutions:

**Option 1: Check Hetzner Console for Root Password**

1. Go to Hetzner Cloud Console → Your Server
2. Click on the **Server** tab
3. Look for **"Root Password"** or **"Access"** section
4. Hetzner may have generated a root password that was shown when the server was created
5. Copy this password and use it when prompted

**Option 2: Use Hetzner Console (Browser-based SSH)**

1. Go to Hetzner Cloud Console → Your Server
2. Click **"Console"** tab (or look for "Launch Console" button)
3. This opens a browser-based terminal - no password needed!
4. Once in, you can set up SSH keys properly

**Option 3: Add SSH Key After Server Creation**

If you didn't add an SSH key during server creation:

1. **Generate SSH key on your local machine** (if you don't have one):
   ```powershell
   # On Windows (PowerShell)
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Press Enter twice for no passphrase (or set one)
   ```

2. **Get your public key:**
   ```powershell
   # On Windows
   cat ~/.ssh/id_ed25519.pub
   # Or
   type $env:USERPROFILE\.ssh\id_ed25519.pub
   ```

3. **Add key to Hetzner:**
   - Go to Hetzner Cloud Console → **Security** → **SSH Keys**
   - Click **"Add SSH Key"**
   - Paste your public key
   - Name it (e.g., "My Laptop")
   - Click **"Add SSH Key"**

4. **Attach key to your server:**
   - Go to your Server → **Rescue** tab
   - Or recreate the server with the SSH key selected

**Option 4: Reset Root Password via Hetzner Console**

1. Use Hetzner's browser console (Option 2 above)
2. Once logged in, set a new root password:
   ```bash
   passwd
   # Enter new password twice
   ```

**Once you can access the server, connect via SSH:**

**On Windows (PowerShell):**
```powershell
# Replace with your server IP
ssh root@YOUR_SERVER_IP
# If using a specific SSH key:
ssh -i ~/.ssh/id_ed25519 root@YOUR_SERVER_IP
```

**On Linux/Mac:**
```bash
ssh root@YOUR_SERVER_IP
# If using a specific SSH key:
ssh -i ~/.ssh/id_ed25519 root@YOUR_SERVER_IP
```

**Note**: If you're still having issues, use Hetzner's browser console (Option 2) - it's the easiest way to get initial access!

#### Step 3: Install Docker on Hetzner Server

Once connected to your server, run:

```bash
# Update system packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose (v2)
apt install docker-compose-plugin -y

# Add your user to docker group (if not root)
# usermod -aG docker $USER
# newgrp docker

# Verify installation
docker --version
docker compose version
```

#### Step 4: Clone Your Repository

**First, make sure you've created a Git repository and pushed your code:**
- See `GIT_SETUP_GUIDE.md` for detailed instructions on creating a GitHub repository
- Or use the alternative SCP method below if you prefer not to use Git

**Clone from GitHub:**
```bash
# Install Git if not already installed
apt install git -y

# Clone your repository
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git email-quote-api
# OR if using private repo, use SSH:
# git clone git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git email-quote-api

cd email-quote-api
```

**For private repositories**, you'll need to authenticate:
- Use a GitHub Personal Access Token as the password when prompted
- Or set up SSH keys on the server (see Git Setup Guide)

**Alternative: Upload files via SCP**
If your repo is private or you prefer manual upload:

```powershell
# From your local Windows machine (PowerShell)
# Navigate to your project directory
cd "C:\Users\kyoto\OneDrive\Desktop\AI EMAIL WEBAPP"

# Upload to server (replace with your IP)
scp -r . root@YOUR_SERVER_IP:/opt/email-quote-api
```

#### Step 5: Create Environment File on Server

```bash
cd /opt/email-quote-api

# Create .env file
nano .env
```

Paste your environment variables (from section 3.3 above):

```env
# Database (Session Pooling - port 5432)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# API Security (REQUIRED!)
API_KEY=your-strong-production-api-key-here
REQUIRE_API_KEY=true
WEBHOOK_SECRET=your-webhook-secret-here

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://YOUR_SERVER_IP:8000/api/oauth/google/callback
FRONTEND_URL=https://your-wix-site.wixsite.com

# Encryption Key
ENCRYPTION_KEY=your-encryption-key

# OpenAI
OPENAI_API_KEY=your-openai-key

# CORS
ALLOWED_ORIGINS=https://your-wix-site.wixsite.com,https://www.wix.com
```

**Important**: Replace `YOUR_SERVER_IP` with your actual Hetzner server IP address.

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

#### Step 6: Run Database Migrations

```bash
# Build the Docker image first
docker compose build

# Run migrations inside container
docker compose run --rm app alembic upgrade head
```

#### Step 7: Start the Application

```bash
# Start the container in detached mode (background)
docker compose up -d

# View logs
docker compose logs -f

# Check if container is running
docker compose ps

# Check health
curl http://localhost:8000/health
```

#### Step 8: Configure Firewall

**Option A: Use Hetzner's Built-in Firewall (Recommended)**

Hetzner's firewall is configured at the network level and is more efficient. If you didn't set it up during server creation:

1. Go to Hetzner Cloud Console → Your Server → **Networking** tab
2. Click **Firewalls** → **Create Firewall**
3. Add the rules as specified in Step 3 above (TCP protocol, ports 22, 8000, 80, 443)
4. Attach the firewall to your server

**Option B: Use UFW (Optional - Additional Layer)**

You can also use UFW on the server as an additional security layer:

```bash
# Install UFW if not installed
apt install ufw -y

# Allow SSH
ufw allow 22/tcp

# Allow your API port
ufw allow 8000/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

**Note**: If you use Hetzner's firewall, UFW is optional but can provide defense-in-depth.

#### Step 9: Test Your API

From your local machine, test the API:

```powershell
# Test health endpoint
curl http://YOUR_SERVER_IP:8000/health

# Test root endpoint
curl http://YOUR_SERVER_IP:8000/
```

#### Step 10: Set Up Reverse Proxy (Optional but Recommended)

For production, use Nginx as a reverse proxy with SSL:

```bash
# Install Nginx
apt install nginx certbot python3-certbot-nginx -y

# Create Nginx config
nano /etc/nginx/sites-available/email-quote-api
```

Paste this configuration (replace `your-domain.com` with your domain):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/email-quote-api /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# Get SSL certificate
certbot --nginx -d your-domain.com
```

#### Step 11: Useful Docker Commands

```bash
# View logs
docker compose logs -f app

# Stop the application
docker compose down

# Restart the application
docker compose restart

# Rebuild after code changes
docker compose up -d --build

# Access container shell
docker compose exec app bash

# View container resource usage
docker stats
```

#### Step 12: Update Application (After Code Changes)

```bash
cd /opt/email-quote-api

# Pull latest code
git pull
# OR upload new files via SCP

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d

# Run migrations if needed
docker compose run --rm app alembic upgrade head
```

#### Troubleshooting Docker Deployment

**Container won't start:**
```bash
# Check logs
docker compose logs app

# Check if port is in use
netstat -tulpn | grep 8000

# Check container status
docker compose ps
```

**Database connection errors:**
- Verify `.env` file has correct `DATABASE_URL`
- Check Supabase firewall allows your Hetzner server IP
- Test connection: `docker compose run --rm app python -c "from app.database import engine; engine.connect(); print('Connected!')"`

**Permission errors:**
```bash
# Fix permissions for volumes
chown -R 1000:1000 /opt/email-quote-api/pdf_quotes
chown -R 1000:1000 /opt/email-quote-api/uploads
```

**Out of memory:**
- Upgrade to larger Hetzner instance (CX21 or higher)
- Or add swap space:
```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## Step 4: Wix Integration

### 4.1 Update API Base URL

In your Wix frontend code, update the API base URL:

```javascript
const API_BASE_URL = 'https://your-api-domain.com/api';
// OR
const API_BASE_URL = 'http://your-server-ip:8000/api';
```

### 4.2 Configure API Key

Add API key to Wix HTTP requests:

```javascript
const headers = {
  'X-API-Key': 'your-production-api-key',
  'Content-Type': 'application/json'
};
```

### 4.3 Update OAuth Redirect URI

1. Go to Google Cloud Console
2. Update OAuth redirect URI:
   - Add: `https://your-api-domain.com/api/oauth/google/callback`
   - Remove old `localhost:8000` URI (or keep for development)

### 4.4 Test Wix Integration

1. Test quote creation from Wix
2. Test email webhook (if using)
3. Test OAuth flow (if business users need to connect Gmail)

---

## Quick Deployment Checklist

- [ ] Supabase project created
- [ ] Database connection string copied
- [ ] PostgreSQL driver installed (`psycopg2-binary`)
- [ ] `.env` file updated with Supabase URL
- [ ] Database connection tested locally
- [ ] Migrations run on Supabase
- [ ] Cloud server prepared
- [ ] Code deployed to cloud server
- [ ] Environment variables set on server
- [ ] API accessible from internet
- [ ] Health check endpoint working
- [ ] Wix API URL updated
- [ ] API key configured in Wix
- [ ] OAuth redirect URI updated
- [ ] End-to-end test completed

---

## Troubleshooting

### Database Connection Issues

**Error**: `connection refused`
- Check Supabase project is active
- Verify connection string is correct (use port 5432 for session pooling)
- Check if your IP needs to be whitelisted (Settings → Database → Connection Pooling)
- Ensure you're using the **URI** connection string, not the transaction pooling one

**Error**: `password authentication failed`
- Verify password in connection string
- Reset password in Supabase if needed

### Server Deployment Issues

**Error**: `Module not found`
- Ensure all dependencies in `requirements.txt` are installed
- Check Python version matches

**Error**: `Port already in use`
- Change PORT in `.env`
- Or stop the process using that port

### Wix Integration Issues

**CORS Errors**:
- Verify your Wix domain is in `ALLOWED_ORIGINS`
- Check API is using HTTPS (if Wix site is HTTPS)

**401/403 Errors**:
- Verify API key is correct
- Check `REQUIRE_API_KEY` setting
- Verify `X-API-Key` header is being sent

---

## Next Steps

1. **Start with Supabase Setup** (follow Step 1 above)
2. Share your Supabase connection string format (mask password) when ready
3. We'll proceed with database configuration next

