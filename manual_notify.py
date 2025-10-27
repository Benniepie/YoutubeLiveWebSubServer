#!/usr/bin/env python3
"""
Manually send a Discord notification for a live stream
Usage: python manual_notify.py <video_id>
"""
import sys
from notifiers import DiscordNotifier
from notification_rules import NotificationRules
from database import NotificationDB

if len(sys.argv) < 2:
    print("Usage: python manual_notify.py <video_id>")
    print("Example: python manual_notify.py DEhvWCmYMyg")
    sys.exit(1)

video_id = sys.argv[1]
video_url = f"https://www.youtube.com/watch?v={video_id}"

# Create instances
discord = DiscordNotifier()
db = NotificationDB()
rules = NotificationRules(db)

# Create video data for live stream
video_data = {
    'video_id': video_id,
    'title': 'Ukraine War 🔴 Live Stream: Geopolitical News',
    'video_url': video_url,
    'author_name': 'ATP Geopolitics',
    'live_status': 'is_live',
    'scheduled_start_time': None
}

print(f"Sending LIVE NOW notification for: {video_url}")

# Get notification message
message_data = rules.get_notification_message(video_data, 'live_now')

if message_data:
    result = discord.send_notification(video_data, 'live_now', message_data)
    
    if result['success']:
        print("✅ Notification sent successfully!")
        db.mark_delivered(video_id, 'discord', 'success', result.get('response'))
    else:
        print(f"❌ Failed: {result.get('error')}")
else:
    print("❌ Failed to generate message")
