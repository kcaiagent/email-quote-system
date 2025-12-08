# Docker Deployment Quick Reference

## Quick Start Commands

### Initial Setup
```bash
# 1. Clone/upload code to server
cd /opt/email-quote-api

# 2. Create .env file with your configuration
nano .env

# 3. Build and start
docker compose build
docker compose up -d

# 4. Run migrations
docker compose run --rm app alembic upgrade head

# 5. Check status
docker compose ps
docker compose logs -f
```

### Daily Operations

```bash
# View logs
docker compose logs -f app

# Restart application
docker compose restart

# Stop application
docker compose down

# Start application
docker compose up -d

# Rebuild after code changes
docker compose down
docker compose build
docker compose up -d
```

### Updates

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d

# Run migrations if needed
docker compose run --rm app alembic upgrade head
```

### Debugging

```bash
# Access container shell
docker compose exec app bash

# Check container resource usage
docker stats

# View all containers
docker ps -a

# Remove old containers/images
docker system prune -a
```

### Database Operations

```bash
# Run migrations
docker compose run --rm app alembic upgrade head

# Create new migration
docker compose run --rm app alembic revision --autogenerate -m "description"

# Rollback migration
docker compose run --rm app alembic downgrade -1

# Test database connection
docker compose run --rm app python -c "from app.database import engine; engine.connect(); print('Connected!')"
```

### Health Checks

```bash
# Check health endpoint
curl http://localhost:8000/health

# From outside server
curl http://YOUR_SERVER_IP:8000/health
```

## File Locations on Server

- **Application code**: `/opt/email-quote-api`
- **Environment file**: `/opt/email-quote-api/.env`
- **PDF quotes**: `/opt/email-quote-api/pdf_quotes`
- **Uploads**: `/opt/email-quote-api/uploads`
- **Docker logs**: `docker compose logs`

## Environment Variables

All environment variables are in `/opt/email-quote-api/.env`

Key variables:
- `DATABASE_URL` - Supabase PostgreSQL connection string
- `API_KEY` - Your API authentication key
- `OPENAI_API_KEY` - OpenAI API key for AI features
- `GOOGLE_OAUTH_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_OAUTH_CLIENT_SECRET` - Google OAuth client secret

## Troubleshooting

### Container won't start
```bash
docker compose logs app
docker compose ps
```

### Port already in use
```bash
# Find what's using port 8000
netstat -tulpn | grep 8000

# Kill the process or change PORT in .env
```

### Database connection errors
- Check `.env` file has correct `DATABASE_URL`
- Verify Supabase firewall allows your server IP
- Test connection (see Database Operations above)

### Out of memory
- Upgrade Hetzner instance size
- Or add swap space (see deployment guide)

