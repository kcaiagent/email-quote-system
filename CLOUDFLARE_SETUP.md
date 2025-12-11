# Cloudflare Security Setup Guide

This guide walks you through setting up Cloudflare to protect your API with DDoS protection, WAF, SSL/TLS encryption, and other security features.

## Why Cloudflare?

Cloudflare provides essential security layers for your production API:

- ✅ **DDoS Protection**: Automatic mitigation of DDoS attacks
- ✅ **WAF (Web Application Firewall)**: Blocks malicious requests and SQL injection attempts
- ✅ **SSL/TLS Encryption**: Free SSL certificates, automatic HTTPS
- ✅ **Bot Protection**: Blocks malicious bots and scrapers
- ✅ **Rate Limiting**: Prevents abuse and brute force attacks
- ✅ **IP Reputation**: Blocks requests from known bad IPs
- ✅ **Origin IP Hiding**: Your Hetzner server IP stays hidden
- ✅ **Global CDN**: Faster response times worldwide

## Step 1: Create Cloudflare Account

1. Go to [https://www.cloudflare.com](https://www.cloudflare.com)
2. Click **"Sign Up"**
3. Enter your email and create a password
4. Verify your email address

**Note**: Cloudflare Free plan provides excellent security features. Pro plan ($20/month) adds advanced WAF rules and more rate limiting options.

## Step 2: Add Your Domain to Cloudflare

1. **Add Site**
   - In Cloudflare dashboard, click **"Add a Site"**
   - Enter your domain name (e.g., `yourdomain.com`)
   - Click **"Add site"**

2. **Select Plan**
   - Choose **Free** plan (sufficient for most use cases)
   - Click **"Continue"**

3. **Review DNS Records**
   - Cloudflare will scan your existing DNS records
   - Review and confirm the records
   - Click **"Continue"**

4. **Update Nameservers**
   - Cloudflare will provide you with nameservers (e.g., `alice.ns.cloudflare.com`, `bob.ns.cloudflare.com`)
   - Go to your domain registrar (where you bought the domain)
   - Replace your current nameservers with Cloudflare's nameservers
   - Save changes
   - **Note**: DNS propagation can take 24-48 hours, but usually happens within a few hours

5. **Wait for Activation**
   - Cloudflare will verify your nameservers
   - You'll receive an email when your domain is active on Cloudflare

## Step 3: Configure DNS Records

Once your domain is active on Cloudflare:

1. **Go to DNS → Records**

2. **Add A Record for API Subdomain** (Recommended)
   - **Type**: A
   - **Name**: `api` (or `yourdomain.com` for root domain)
   - **IPv4 address**: Your Hetzner server IP address
   - **Proxy status**: 🟠 **Proxied** (orange cloud) - **IMPORTANT!**
   - **TTL**: Auto
   - Click **"Save"**

   **Example**:
   - If your domain is `yourdomain.com` and server IP is `123.45.67.89`:
   - Create: `api.yourdomain.com` → `123.45.67.89` (Proxied)

3. **Verify DNS**
   - Wait a few minutes for DNS to propagate
   - Test: `ping api.yourdomain.com` (should show Cloudflare IP, not your server IP)

## Step 4: Configure SSL/TLS

1. **Go to SSL/TLS → Overview**

2. **SSL/TLS Encryption Mode**
   - Select **"Full (Strict)"** (recommended for maximum security)
   - This ensures:
     - ✅ HTTPS between client and Cloudflare
     - ✅ HTTPS between Cloudflare and your origin server
     - ✅ Validates your origin SSL certificate

3. **Origin Certificate (Optional but Recommended)**
   - Go to **SSL/TLS → Origin Server**
   - Click **"Create Certificate"**
   - Select:
     - **Private key type**: RSA (2048)
     - **Hostnames**: `api.yourdomain.com` (or your domain)
     - **Validity**: 15 years
   - Click **"Create"**
   - **Save both the Origin Certificate and Private Key** (you'll use these on your server)

4. **Always Use HTTPS**
   - Go to **SSL/TLS → Edge Certificates**
   - Enable **"Always Use HTTPS"** (redirects HTTP to HTTPS)
   - Enable **"Automatic HTTPS Rewrites"**

## Step 5: Configure Security Settings

### 5.1 Web Application Firewall (WAF)

1. **Go to Security → WAF**
2. **Enable Managed Rules** (if on Pro plan)
   - Cloudflare Managed Ruleset: **ON**
   - OWASP Core Ruleset: **ON**
3. **Create Custom Rules** (Free plan can create custom rules)
   - Example: Block requests without API key header
   - Go to **Security → WAF → Custom Rules**
   - Create rule to block requests missing `X-API-Key` header (optional)

### 5.2 DDoS Protection

1. **Go to Security → Settings**
2. **Security Level**: Set to **"Medium"** (recommended)
   - Low: Only challenges obvious threats
   - Medium: Challenges moderate threats (recommended)
   - High: Challenges more threats (may block legitimate users)
   - I'm Under Attack: Maximum protection (use only during attacks)

3. **Bot Fight Mode** (Free plan)
   - Go to **Security → Bots**
   - Enable **"Bot Fight Mode"** (free)
   - Or upgrade to **"Super Bot Fight Mode"** (Pro plan)

### 5.3 Rate Limiting

1. **Go to Security → WAF → Rate limiting rules**
2. **Create Rate Limit Rule**:
   - **Rule name**: "API Rate Limit"
   - **Match**: `(http.request.uri.path contains "/api/")`
   - **Rate**: `100 requests per 1 minute` (adjust as needed)
   - **Action**: Block
   - Click **"Deploy"**

### 5.4 Firewall Rules

1. **Go to Security → WAF → Firewall rules**
2. **Create Rules** (examples):
   - Block requests from specific countries (if needed)
   - Allow only specific IPs (for admin endpoints)
   - Block known bad user agents

## Step 6: Configure Security Headers

1. **Go to Rules → Transform Rules → Modify Response Header**
2. **Create Header Rules** (Cloudflare adds many automatically, but you can add more):
   - **X-Frame-Options**: `DENY`
   - **X-Content-Type-Options**: `nosniff`
   - **Referrer-Policy**: `strict-origin-when-cross-origin`
   - **Permissions-Policy**: Restrict features as needed

**Note**: Your Nginx server can also add these headers (see deployment guide).

## Step 7: Update Your Server Configuration

### 7.1 Update Nginx Configuration

On your Hetzner server, update Nginx to work with Cloudflare:

```bash
# Edit Nginx config
nano /etc/nginx/sites-available/email-quote-api
```

Update the configuration:

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration (use Let's Encrypt certificate)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Cloudflare IP Ranges (optional - for extra security)
    # Only allow requests from Cloudflare IPs
    # See: https://www.cloudflare.com/ips/
    # You can add: allow 173.245.48.0/20; etc.
    # deny all; (then allow Cloudflare IPs)

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Cloudflare-specific headers
        proxy_set_header CF-Connecting-IP $http_cf_connecting_ip;
        proxy_set_header CF-Ray $http_cf_ray;
        proxy_set_header CF-Visitor $http_cf_visitor;
        
        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    }
}
```

### 7.2 Get SSL Certificate for Origin Server

Even though Cloudflare provides SSL, your origin server (Hetzner) should also have SSL:

```bash
# Get Let's Encrypt certificate
certbot --nginx -d api.yourdomain.com

# Test auto-renewal
certbot renew --dry-run
```

### 7.3 Update Environment Variables

Update your `.env` file on the server:

```bash
nano /opt/email-quote-api/.env
```

Update these values:

```env
# Change OAuth redirect URI to use Cloudflare domain
GOOGLE_OAUTH_REDIRECT_URI=https://api.yourdomain.com/api/oauth/google/callback

# Update CORS to include your Cloudflare-protected domain
ALLOWED_ORIGINS=https://your-wix-site.wixsite.com,https://www.wix.com,https://api.yourdomain.com
```

Restart the container:

```bash
docker compose restart
```

## Step 8: Update Google OAuth Configuration

1. **Go to Google Cloud Console** → **APIs & Services** → **Credentials**
2. **Edit your OAuth 2.0 Client**
3. **Authorized redirect URIs**:
   - Add: `https://api.yourdomain.com/api/oauth/google/callback`
   - Remove or keep: `http://localhost:8000/api/oauth/google/callback` (for local dev)

## Step 9: Test Cloudflare Setup

### 9.1 Test DNS

```bash
# Should show Cloudflare IPs, not your server IP
dig api.yourdomain.com
nslookup api.yourdomain.com
```

### 9.2 Test HTTPS

```bash
# Test from your local machine
curl https://api.yourdomain.com/health

# Should return health check response
```

### 9.3 Test Security Headers

```bash
curl -I https://api.yourdomain.com/health

# Should show security headers in response
```

### 9.4 Verify Cloudflare is Active

Visit: `https://api.yourdomain.com` in browser
- Should show Cloudflare SSL certificate
- Check browser developer tools → Network → Headers
- Look for `CF-Ray` header (confirms Cloudflare is proxying)

## Step 10: Monitor and Optimize

### 10.1 Analytics

- **Go to Analytics → Web Traffic**
- Monitor requests, threats blocked, bandwidth
- Review security events

### 10.2 Caching (Optional)

- **Go to Caching → Configuration**
- For API endpoints, set **"Cache Level"** to **"Bypass"** (APIs shouldn't be cached)
- Or create Page Rules to bypass cache for `/api/*` paths

### 10.3 Speed Optimization

- **Go to Speed → Optimization**
- Enable **"Auto Minify"** (HTML, CSS, JavaScript)
- Enable **"Brotli"** compression

## Optional: Cloudflare Tunnel (Most Secure)

Cloudflare Tunnel (formerly Argo Tunnel) allows you to expose your API without opening any ports on your server. This is the most secure option.

### Setup Cloudflare Tunnel

1. **Install cloudflared on your server**:

```bash
# Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
```

2. **Authenticate**:

```bash
cloudflared tunnel login
```

3. **Create Tunnel**:

```bash
cloudflared tunnel create email-quote-api
```

4. **Configure Tunnel**:

```bash
# Create config file
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Add configuration:

```yaml
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: api.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

5. **Route DNS**:

```bash
cloudflared tunnel route dns email-quote-api api.yourdomain.com
```

6. **Run Tunnel**:

```bash
# Test
cloudflared tunnel run email-quote-api

# Or run as service
cloudflared service install
systemctl start cloudflared
systemctl enable cloudflared
```

**Benefits of Tunnel**:
- ✅ No ports need to be open on your server
- ✅ Maximum security (no direct internet access to server)
- ✅ Can close port 8000 in firewall
- ✅ Automatic reconnection if connection drops

## Troubleshooting

### DNS Not Propagating

- Wait 24-48 hours for full propagation
- Check nameservers are correctly set at registrar
- Use `dig` or `nslookup` to verify

### SSL Certificate Errors

- Ensure "Full (Strict)" mode requires valid SSL on origin
- Get Let's Encrypt certificate: `certbot --nginx -d api.yourdomain.com`
- Verify certificate is valid: `openssl s_client -connect api.yourdomain.com:443`

### 502 Bad Gateway

- Check Nginx is running: `systemctl status nginx`
- Check Docker container is running: `docker compose ps`
- Check Nginx logs: `tail -f /var/log/nginx/error.log`
- Verify Cloudflare can reach your server

### API Not Accessible

- Verify DNS is pointing to Cloudflare (orange cloud enabled)
- Check firewall allows Cloudflare IPs (if restricting)
- Test direct server access: `curl http://YOUR_SERVER_IP:8000/health`
- Check Cloudflare firewall rules aren't blocking legitimate traffic

## Security Best Practices

1. ✅ **Always use "Full (Strict)" SSL mode**
2. ✅ **Enable WAF rules** (even basic ones on Free plan)
3. ✅ **Set security level to Medium**
4. ✅ **Enable Bot Fight Mode**
5. ✅ **Configure rate limiting** for API endpoints
6. ✅ **Monitor analytics** for suspicious activity
7. ✅ **Keep Cloudflare dashboard secure** (use 2FA)
8. ✅ **Regularly review firewall rules**

## Summary

After completing this setup:

- ✅ Your API is protected by Cloudflare's global network
- ✅ DDoS attacks are automatically mitigated
- ✅ SSL/TLS encryption is enabled (HTTPS)
- ✅ WAF blocks malicious requests
- ✅ Bot protection is active
- ✅ Rate limiting prevents abuse
- ✅ Your origin server IP is hidden
- ✅ Security headers are configured

Your API is now significantly more secure and ready for production use!







