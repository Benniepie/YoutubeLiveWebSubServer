# Docker Deployment Guide

## Prerequisites

- Docker and Docker Compose installed on your Linux server
- Tailscale installed and configured
- Domain name with DNS configured (optional, for nginx reverse proxy)

## Quick Start

### 1. Copy Files to Server

```bash
# On your Linux server
mkdir -p ~/youtube-websub
cd ~/youtube-websub

# Copy all files from your Windows machine
# (use scp, rsync, or git clone)
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit configuration
nano .env
```

Update these values:
```env
# Your callback URL (can include subfolder)
CALLBACK_URL_BASE=https://example.com/websub

# Or use Tailscale
CALLBACK_URL_BASE=https://your-server.your-tailnet.ts.net

# YouTube channel to monitor
YOUTUBE_CHANNEL_ID=YOUR_YOUTUBE_CHANNEL_ID_HERE

# Discord credentials
DISCORD_BOT_TOKEN=your_token
DISCORD_CHANNEL_ID=your_channel_id

# Secret key for HMAC verification
SECRET_KEY=change_this_to_a_random_string
```

### 3. Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 4. Verify It's Running

```bash
# Check container status
docker-compose ps

# Test the endpoint
curl http://localhost:5001/

# Should return: "YouTube WebSub Server is running!"
```

## Using with Nginx Reverse Proxy

### Option 1: Root Domain

If using `https://example.com`:

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://your-server-tailscale-ip:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Option 2: Subfolder (Recommended)

If using `https://example.com/websub`:

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /websub {
        # Remove /websub prefix when proxying
        rewrite ^/websub(/.*)$ $1 break;
        
        proxy_pass http://your-server-tailscale-ip:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Important**: When using a subfolder, set your callback URL to include it:
```env
CALLBACK_URL_BASE=https://example.com/websub
```

The server will automatically append `/webhook` to create the full callback URL:
`https://example.com/websub/webhook`

## Security Features

### 1. IP Whitelisting

The server only accepts requests from Google's known IP ranges:
- Blocks all non-Google IPs
- Logs rejected requests
- Returns 403 Forbidden for unauthorized access

### 2. HMAC Signature Verification

All POST requests are verified using HMAC-SHA1:
- Uses your SECRET_KEY
- Prevents tampering
- Rejects invalid signatures

### 3. Rate Limiting

- Maximum 100 requests per minute per IP
- Prevents abuse
- Returns 429 Too Many Requests when exceeded

### 4. Additional Nginx Security

Add to your nginx config:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=websub:10m rate=10r/s;

location /websub {
    # Apply rate limit
    limit_req zone=websub burst=20 nodelay;
    
    # Only allow POST and GET
    limit_except GET POST {
        deny all;
    }
    
    # Additional security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy settings
    proxy_pass http://your-server-tailscale-ip:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Monitoring

### View Logs

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs websub-server
```

### Check Database

```bash
# Enter container
docker-compose exec websub-server bash

# Query database
sqlite3 /app/data/notifications.db "SELECT * FROM videos ORDER BY last_updated_at DESC LIMIT 5;"
```

### Health Check

```bash
# Check container health
docker-compose ps

# Manual health check
curl http://localhost:5001/
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup Database

```bash
# Backup
cp data/notifications.db data/notifications.db.backup

# Or use docker cp
docker cp youtube-websub:/app/data/notifications.db ./backup-$(date +%Y%m%d).db
```

### View Notifications

```bash
# Enter container
docker-compose exec websub-server python view_notifications.py recent 10
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is in use
sudo netstat -tulpn | grep 5001
```

### Not Receiving Notifications

1. Check subscription status:
   ```bash
   docker-compose logs | grep "subscribe"
   ```

2. Verify callback URL is accessible:
   ```bash
   curl https://example.com/websub/webhook
   ```

3. Check Google can reach your server (firewall, DNS)

### Database Issues

```bash
# Reset database
docker-compose down
rm data/notifications.db
docker-compose up -d
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CALLBACK_URL_BASE` | Yes | Your public URL (can include subfolder) |
| `YOUTUBE_CHANNEL_ID` | Yes | YouTube channel to monitor |
| `SECRET_KEY` | Yes | Random string for HMAC verification |
| `DISCORD_BOT_TOKEN` | No | Discord bot token |
| `DISCORD_CHANNEL_ID` | No | Discord channel ID |
| `DISCORD_WEBHOOK_URL` | No | Discord webhook URL (alternative to bot) |
| `PORT` | No | Server port (default: 5001) |

## Production Checklist

- [ ] Change SECRET_KEY to a random string
- [ ] Configure SSL/TLS on nginx
- [ ] Set up log rotation
- [ ] Configure backup schedule for database
- [ ] Monitor disk space for logs and database
- [ ] Set up monitoring/alerting (optional)
- [ ] Test failover/restart procedures
- [ ] Document your specific configuration

## Support

For issues or questions, check:
- Container logs: `docker-compose logs`
- Application logs in `./logs/` directory
- Database: `sqlite3 data/notifications.db`
