# Docker Setup Summary

## What's Been Created

### Docker Files
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Service orchestration
- `.dockerignore` - Files to exclude from image

### Security
- `security.py` - IP whitelisting and rate limiting
- Google IP range validation
- HMAC signature verification
- Rate limiting (100 req/min)

### Documentation
- `DEPLOYMENT.md` - Complete deployment guide
- Nginx configuration examples
- Security best practices

## Quick Answers to Your Questions

### 1. Subfolder URLs - YES, it works!

You can use `https://example.com/websub` as your callback URL.

**In your .env:**
```env
CALLBACK_URL_BASE=https://example.com/websub
```

The server will create: `https://example.com/websub/webhook`

**In nginx:**
```nginx
location /websub {
    rewrite ^/websub(/.*)$ $1 break;
    proxy_pass http://tailscale-ip:5001;
    # ... headers ...
}
```

### 2. Security - Multiple Layers

✅ **IP Whitelisting**
- Only accepts requests from Google's IP ranges
- Blocks all other IPs with 403 Forbidden

✅ **HMAC Signature Verification**
- Validates every POST request
- Uses your SECRET_KEY
- Prevents tampering

✅ **Rate Limiting**
- 100 requests per minute per IP
- Prevents abuse

✅ **Nginx Additional Security**
- SSL/TLS encryption
- Additional rate limiting
- Security headers

### 3. CORS - Not Needed

CORS is for browser-based requests. Since Google's servers make direct HTTP requests (not from a browser), CORS headers aren't necessary.

## Deployment Steps

### On Your Linux Server

```bash
# 1. Create directory
mkdir -p ~/youtube-websub
cd ~/youtube-websub

# 2. Copy files (use scp, rsync, or git)
# All .py files, docker files, .env, etc.

# 3. Configure
cp .env.example .env
nano .env  # Update with your values

# 4. Build and run
docker-compose build
docker-compose up -d

# 5. Check logs
docker-compose logs -f
```

### On Your Nginx Server

Add location block to your nginx config:

```nginx
location /websub {
    rewrite ^/websub(/.*)$ $1 break;
    proxy_pass http://your-server-tailscale-ip:5001;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

## Security Features Explained

### Why IP Whitelisting?

Google's PubSubHubbub servers always come from known IP ranges. By only accepting requests from these IPs, you prevent:
- Random internet users hitting your endpoint
- Bots and scanners
- Malicious actors trying to inject fake notifications

### Why HMAC Signatures?

Even if someone spoofs a Google IP, they can't forge the HMAC signature without knowing your SECRET_KEY. This ensures:
- Notifications are genuinely from Google
- Data hasn't been tampered with
- Your SECRET_KEY remains private

### Why Rate Limiting?

Prevents abuse even from legitimate sources:
- Protects against accidental loops
- Prevents resource exhaustion
- Limits impact of any bugs

## Testing

### Test Locally First

```bash
# On Windows (current setup)
python websub_server.py

# Verify it works with real notifications
```

### Test Docker Build

```bash
# Build image
docker-compose build

# Run locally
docker-compose up

# Test endpoint
curl http://localhost:5001/
```

### Test on Server

```bash
# After deployment
curl http://localhost:5001/

# Test through nginx
curl https://example.com/websub/

# Check logs
docker-compose logs -f
```

## Monitoring

### Check Container Status
```bash
docker-compose ps
```

### View Recent Notifications
```bash
docker-compose exec websub-server python view_notifications.py recent 5
```

### Database Query
```bash
docker-compose exec websub-server sqlite3 /app/data/notifications.db \
  "SELECT video_id, title, live_stream_status FROM videos ORDER BY last_updated_at DESC LIMIT 5;"
```

## Backup Strategy

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker cp youtube-websub:/app/data/notifications.db \
  ~/backups/notifications_${DATE}.db
# Keep only last 7 days
find ~/backups -name "notifications_*.db" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

## Troubleshooting

### Container Exits Immediately

Check logs:
```bash
docker-compose logs
```

Common issues:
- Missing .env file
- Invalid environment variables
- Port already in use

### Not Receiving Notifications

1. Check subscription:
   ```bash
   docker-compose logs | grep subscribe
   ```

2. Verify callback URL is accessible from internet

3. Check Google can reach your server

### Database Locked

```bash
# Stop container
docker-compose down

# Check for stale locks
rm data/notifications.db-journal

# Restart
docker-compose up -d
```

## Production Recommendations

1. **Use a strong SECRET_KEY**
   ```bash
   # Generate random key
   openssl rand -hex 32
   ```

2. **Enable SSL/TLS on nginx**
   - Use Let's Encrypt
   - Force HTTPS

3. **Set up log rotation**
   - Docker logs can grow large
   - Configure max-size in docker-compose.yml

4. **Monitor disk space**
   - Database grows over time
   - Logs accumulate

5. **Regular backups**
   - Automate database backups
   - Test restore procedure

## Next Steps

1. ✅ Test current Windows setup works
2. ✅ Copy files to Linux server
3. ✅ Configure .env with production values
4. ✅ Build and run Docker container
5. ✅ Configure nginx reverse proxy
6. ✅ Test end-to-end
7. ✅ Set up monitoring and backups

Your system is ready for production deployment! 🚀
