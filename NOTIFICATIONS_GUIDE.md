# YouTube WebSub Notifications System

## Overview

This system captures YouTube notifications in real-time and distributes them to multiple platforms. It's specifically optimized for live stream notifications.

## How It Works

### Notification Flow

When a YouTube channel activity occurs, you'll receive notifications at different stages:

#### For Live Streams (5 notifications):
1. **live_scheduled** - When the stream is created/scheduled
2. **live_started** - When the scheduled time arrives (may be same as #3)
3. **live_started/live_ongoing** - When the stream actually goes live
4. **live_ended** - When the stream ends
5. **live_archived** - When the archive is published (published time changes)

#### For Regular Videos (1-2 notifications):
1. **video_published** - When the video is uploaded
2. **video_updated** - If the video metadata changes

### Available Data Fields

From the YouTube WebSub feed, you get:

- `video_id` - Unique video identifier
- `channel_id` - Channel identifier
- `title` - Video title
- `video_url` - Full YouTube URL
- `published_time` - When the video was published (ISO 8601 format)
- `updated_time` - When the feed was last updated
- `author_name` - Channel name
- `author_uri` - Channel URL

**Note**: The feed does NOT explicitly tell you if it's a live stream. We detect this by:
- Checking if "LIVE" appears in the title
- Tracking multiple notifications for the same video_id
- Monitoring changes in the published_time

## Database Schema

### Videos Table
Stores all videos with their current state:
- Basic video info (title, URL, IDs)
- `is_live_stream` - Boolean flag
- `live_stream_status` - Current status (live_scheduled, live_started, etc.)
- `notification_count` - How many notifications received
- `first_seen_at` / `last_updated_at` - Timestamps
- `raw_xml` - Full XML for debugging

### Notification Events Table
Tracks every notification received:
- Links to video
- Timestamp of when received
- Event type determined
- Raw XML data

### Delivery Tracking Table
Tracks which platforms were notified:
- Video ID
- Platform (discord, whatsapp, facebook, email)
- Delivery status (success/failed)
- Timestamp
- Response data or error message

## Platform Integration

### Priority Order

1. **Discord** - Live streams (scheduled & started)
2. **WhatsApp** - Live streams (to be implemented)
3. **Facebook Business Page** - Live streams (to be implemented)
4. **Email (Ghost)** - All videos (to be implemented)
5. **Push Notifications** - Mobile users (to be implemented)

### Discord Setup

See `SETUP_DISCORD.md` for detailed instructions.

Quick start:
```powershell
# Option 1: Webhook (easiest)
$env:DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Option 2: Bot
$env:DISCORD_BOT_TOKEN="your_token"
$env:DISCORD_CHANNEL_ID="your_channel_id"
```

### WhatsApp Setup (Coming Soon)

Options:
1. **Twilio API** - Paid service, reliable
2. **WhatsApp Business API** - Official, requires approval
3. **Third-party services** - MessageBird, etc.

### Facebook Business Page Setup (Coming Soon)

Requirements:
1. Facebook Business Page
2. Page Access Token
3. Page ID

### Email via Ghost (Coming Soon)

Ghost has a Members API that can send emails to your mailing list.

### Push Notifications (Coming Soon)

Options:
1. **Firebase Cloud Messaging (FCM)** - Cross-platform
2. **OneSignal** - Easy to use
3. **Custom solution** - Using web push API

## Usage

### Start the Server

```powershell
# Activate your conda environment
conda activate pubsub

# Set your callback URL (from Tailscale)
$env:CALLBACK_URL_BASE="https://your-machine.your-tailnet.ts.net"

# Set Discord credentials
$env:DISCORD_WEBHOOK_URL="your_webhook_url"

# Run the server
python websub_server.py
```

### View Notifications

```powershell
# View recent videos
python view_notifications.py recent 20

# View all live streams
python view_notifications.py live

# View events for a specific video
python view_notifications.py events TctLKlkrDGw
```

### Query the Database Directly

```powershell
# Open SQLite
sqlite3 notifications.db

# Useful queries:
SELECT * FROM videos WHERE is_live_stream = 1;
SELECT * FROM notification_events WHERE video_id = 'TctLKlkrDGw';
SELECT * FROM delivery_tracking;
```

## Understanding Your Logs

Based on your log for video `TctLKlkrDGw`:

```
22:21:03 - live_scheduled (published: 21:20:58)
22:31:06 - live_started (published: 21:20:58)
22:31:08 - live_ongoing (published: 21:20:58)
23:37:30 - live_ended (published: 21:20:58)
23:42:42 - live_archived (published: 22:42:37) ← Note time change!
```

The system correctly identified:
- Stream scheduled at 10:21pm (your time)
- Stream started at 10:31pm
- Stream ended at 11:37pm (1hr 6min duration)
- Archive published at 11:42pm (published time updated)

## Time Zone Notes

- All times in the database are stored in UTC
- YouTube sends times in UTC (with +00:00 or Z suffix)
- Your local time may differ due to daylight savings
- The `view_notifications.py` script shows times in UTC

## Next Steps

1. ✅ **Data Capture** - Working!
2. ✅ **Discord for Live** - Ready to configure
3. ⏳ **WhatsApp for Live** - Need to choose API provider
4. ⏳ **Facebook for Live** - Need access token
5. ⏳ **Email via Ghost** - Need Ghost setup
6. ⏳ **Push Notifications** - Need to choose platform

## Configuration

Copy `config.example.env` to `.env` and fill in your credentials:

```powershell
copy config.example.env .env
notepad .env
```

Then load it in your PowerShell session:
```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

Or use python-dotenv (install with `pip install python-dotenv`).
