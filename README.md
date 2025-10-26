# YouTube WebSub Notification Server

A production-ready Python Flask server that receives real-time push notifications from YouTube via WebSub (PubSubHubbub) and sends smart Discord notifications for live streams and video uploads.

## Features

- **Real-time YouTube notifications** via WebSub protocol (no API quota usage)
- **Smart Discord notifications** with rule-based filtering to prevent spam
- **Live stream detection** using yt-dlp metadata fetching
- **SQLite database** for event tracking and delivery history
- **Security features** including IP whitelisting and rate limiting
- **Docker deployment** with complete containerization
- **Signature verification** for authentic Google notifications

## How It Works

The WebSub protocol involves three parties:

1. **Publisher (YouTube)**: Publishes content updates to a feed
2. **Hub (Google)**: Sits between publisher and subscriber, pushes updates
3. **Subscriber (This App)**: Receives and processes notifications

**Flow:**
1. Server subscribes to YouTube channel feed via Google Hub
2. Hub verifies subscription with challenge-response
3. YouTube publishes video → Hub sends POST notification
4. Server fetches metadata with yt-dlp (detects live streams)
5. Smart rules determine if Discord notification should be sent
6. All events logged to SQLite database

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file with your settings:

```env
# Required
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxxxxxx
CALLBACK_URL_BASE=https://your-server.example.com

# Discord (optional but recommended)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
# OR
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=123456789

# Security (optional)
ALLOWED_IPS=66.102.0.0/20,66.249.80.0/20,72.14.192.0/18
SECRET_KEY=your-secret-key-here
```

**Finding your YouTube Channel ID:**
1. Go to the channel page (e.g., `https://www.youtube.com/@ChannelName`)
2. View page source (right-click → View Page Source)
3. Search for `"channelId"` - you'll find something like `"channelId":"UCxxxxxxxxxxxxxxxxxxxxxx"`

### 3. Set Up Discord (Optional)

See `GET_DISCORD_CREDENTIALS.md` for detailed instructions on setting up Discord webhooks or bot tokens.

### 4. Run the Server

**Local Development (with Tailscale Funnel):**
```bash
# Terminal 1: Start the server
python websub_server.py

# Terminal 2: Expose with Tailscale
tailscale funnel 5001
```

**Docker Deployment:**
```bash
docker-compose up -d --build
```

See `DEPLOYMENT.md` for production deployment instructions.

## Project Structure

```
├── websub_server.py          # Main Flask server
├── database.py                # SQLite database operations
├── notification_rules.py      # Smart notification logic
├── notifiers.py               # Discord integration
├── ytdlp_metadata.py          # yt-dlp metadata fetching
├── security.py                # IP whitelisting & rate limiting
├── Dockerfile                 # Docker container setup
├── docker-compose.yml         # Docker Compose configuration
└── websub.db                  # SQLite database (auto-created)
```

## Smart Notification Rules

**Typical flow: 2 notifications per stream**
1. When stream is scheduled (within 2 hours of start)
2. When stream goes live

**Edge cases:**
- Stream goes straight to live without scheduling → 1 notification (just live)
- Stream time changes → +1 additional reschedule notification
- Stream ends → Silent (no notification)
- Title/description changes → Silent (no notification)
- Non-live videos → Silent (no notification)

**Notification types:**
- `upcoming` - Stream scheduled within 2 hours (green embed with countdown)
- `live_now` - Stream just went live (red embed with @everyone ping)
- `reschedule` - Stream time changed (yellow embed with new time)

See `NOTIFICATIONS_GUIDE.md` for detailed rule explanations.

## Database Schema

Three tables track all activity:

- **videos**: Video metadata (title, URL, live status, premiere status)
- **events**: All WebSub notifications received
- **notification_deliveries**: Discord notification history

View database contents:
```bash
python view_notifications.py
```

## Testing

```bash
# Test Discord connection
python test_discord.py

# Test notification rules
python test_notification_rules.py

# Test live stream notifications
python test_live_notifications.py

# Backfill metadata for existing videos
python backfill_metadata.py
```

## Security

- **Signature verification**: Validates Google's HMAC-SHA1 signatures
- **IP whitelisting**: Only accepts requests from Google's IP ranges
- **Rate limiting**: Prevents abuse (100 requests/minute per IP)
- **Environment variables**: Sensitive data kept out of code

## Reverse Proxy Setup

If using a reverse proxy (nginx, Caddy, etc.), ensure it forwards to the `/webhook` endpoint:

**Example nginx config:**
```nginx
location /webhook/ {
    proxy_pass http://localhost:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

## Documentation

- `DEPLOYMENT.md` - Production deployment guide
- `NOTIFICATIONS_GUIDE.md` - Notification rules explained
- `GET_DISCORD_CREDENTIALS.md` - Discord setup instructions
- `DOCKER_SETUP_SUMMARY.md` - Docker configuration details

## Troubleshooting

**No notifications received:**
- Check that your callback URL is publicly accessible
- Verify YouTube channel ID is correct
- Check logs for subscription verification
- Ensure Google's IPs aren't blocked by firewall

**Discord notifications not working:**
- Run `python test_discord.py` to verify credentials
- Check webhook URL or bot token is correct
- Verify bot has permission to send messages in channel

**Live stream detection issues:**
- yt-dlp fetches metadata with retry logic
- New videos may take 30-60 seconds to have metadata available
- Check database to see what metadata was captured

## License

MIT License - See LICENSE file for details
