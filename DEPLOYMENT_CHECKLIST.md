# Deployment Checklist

Use this checklist to track your deployment progress.

## Phase 1: Supabase Setup ✅

- [ ] Create Supabase account/project
- [ ] Save database password securely
- [ ] Copy database connection string
- [ ] Note project region and reference ID

## Phase 2: Local Database Configuration

- [ ] Install `psycopg2-binary` package
- [ ] Update `.env` with Supabase connection string
- [ ] Test database connection locally
- [ ] Run Alembic migrations: `.\alembic.ps1 upgrade head`
- [ ] Verify tables created in Supabase dashboard

## Phase 3: Cloud Server Preparation

- [ ] Choose deployment method (PM2/systemd/Docker/direct)
- [ ] **If using Docker**: Install Docker and Docker Compose on server
- [ ] **If NOT using Docker**: Ensure Python 3.11+ installed on server
- [ ] Ensure Git installed on server
- [ ] Open required ports (8000 or custom)
- [ ] Configure firewall (UFW or Hetzner firewall)
- [ ] Set up domain/SSL certificate (required for Cloudflare)
- [ ] **Cloudflare Setup** (Recommended for security):
  - [ ] Create Cloudflare account
  - [ ] Add domain to Cloudflare
  - [ ] Update nameservers at domain registrar
  - [ ] Configure DNS A record (api subdomain → server IP)
  - [ ] Enable Cloudflare proxy (orange cloud)
  - [ ] Configure SSL/TLS mode (Full Strict)
  - [ ] Enable security features (WAF, Bot Protection, Rate Limiting)

## Phase 4: Code Deployment

- [ ] SSH into cloud server
- [ ] Clone repository (or upload files)
- [ ] **If using Docker**:
  - [ ] Create `.env` file with production variables
  - [ ] Build Docker image: `docker compose build`
  - [ ] Run migrations: `docker compose run --rm app alembic upgrade head`
  - [ ] Start container: `docker compose up -d`
- [ ] **If NOT using Docker**:
  - [ ] Install dependencies: `pip install -r requirements.txt`
  - [ ] Create `.env` file with production variables
  - [ ] Run migrations: `alembic upgrade head`
- [ ] Generate strong API key for production
- [ ] Set `DEBUG=false` in `.env`
- [ ] Configure CORS with Wix domain
- [ ] Update OAuth redirect URI with server IP/domain

## Phase 5: Reverse Proxy & Cloudflare

- [ ] Install Nginx on server
- [ ] Configure Nginx reverse proxy
- [ ] Get SSL certificate (Let's Encrypt via Certbot)
- [ ] Test Nginx configuration: `nginx -t`
- [ ] **If using Cloudflare**:
  - [ ] Verify DNS propagation (check with `dig` or `nslookup`)
  - [ ] Test Cloudflare SSL: `curl https://api.yourdomain.com/health`
  - [ ] Verify Cloudflare is proxying (check for CF-Ray header)
  - [ ] Update `.env` with Cloudflare domain URLs
  - [ ] Update Google OAuth redirect URI to Cloudflare domain
  - [ ] Restart Docker container: `docker compose restart`

## Phase 6: Start Server

- [ ] Start server (using chosen method)
  - **Docker**: `docker compose up -d` (already done in Phase 4)
  - **Direct**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - **PM2/systemd**: Start service
- [ ] Test health endpoint locally: `curl http://localhost:8000/health`
- [ ] Test health endpoint from internet: 
  - **With Cloudflare**: `curl https://api.yourdomain.com/health`
  - **Without Cloudflare**: `curl http://YOUR_SERVER_IP:8000/health`
- [ ] Verify API is accessible from internet
- [ ] Check server logs for errors
  - **Docker**: `docker compose logs -f`
  - **Direct**: Check terminal output

## Phase 7: Wix Integration

- [ ] Update Wix frontend with production API URL (use Cloudflare domain if configured)
- [ ] Add API key to Wix HTTP requests
- [ ] Update Google OAuth redirect URI in Google Cloud Console (use Cloudflare domain)
- [ ] Test quote creation from Wix
- [ ] Test OAuth flow (if applicable)

## Phase 8: Verification

- [ ] Test health check endpoint
- [ ] Test API key authentication
- [ ] Test quote creation via API
- [ ] Test email processing (if applicable)
- [ ] Verify data is saving to Supabase
- [ ] Check server logs for any errors
- [ ] Monitor server resources (CPU, memory)

## Current Status

**Next Action**: Start with Supabase Setup (Phase 1)

---

**Questions to Answer:**
1. What cloud server provider are you using? (Hetzner, AWS, DigitalOcean, etc.)
2. Do you have SSH access to your server?
3. What domain/IP will your API be accessible at?
4. Are you using Docker? (Recommended for Hetzner)

**For Hetzner + Docker Deployment:**
- See detailed guide in `DEPLOYMENT_GUIDE.md` Section 3.5
- Quick reference: `DOCKER_DEPLOYMENT.md`

**For Cloudflare Security Setup:**
- See detailed guide: `CLOUDFLARE_SETUP.md`
- Provides DDoS protection, WAF, SSL/TLS, bot protection

