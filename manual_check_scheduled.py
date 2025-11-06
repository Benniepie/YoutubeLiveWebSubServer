#!/usr/bin/env python3
"""
Manually check a video and send notification if it's scheduled within 2 hours
Usage: 
  python manual_check_scheduled.py <video_id>     # Check specific video
  python manual_check_scheduled.py --last         # Check last video in database
  python manual_check_scheduled.py --force <id>   # Force send even if already sent
"""
import sys
from youtube_metadata import YouTubeMetadata
from notification_rules import NotificationRules
from notifiers import DiscordNotifier
from database import NotificationDB
from datetime import datetime, timezone

# Initialize
db = NotificationDB()

# Parse arguments
force_send = False
video_id = None

if len(sys.argv) < 2:
    print("Usage:")
    print("  python manual_check_scheduled.py <video_id>     # Check specific video")
    print("  python manual_check_scheduled.py --last         # Check last video in database")
    print("  python manual_check_scheduled.py --force <id>   # Force send even if already sent")
    sys.exit(1)

if sys.argv[1] == '--last':
    # Get last video from database
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT video_id, title FROM videos ORDER BY last_updated_at DESC LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        video_id = result['video_id']
        print(f"📋 Last video in database: {result['title']}")
        print(f"   Video ID: {video_id}")
    else:
        print("❌ No videos in database")
        sys.exit(1)
elif sys.argv[1] == '--force':
    if len(sys.argv) < 3:
        print("❌ --force requires a video ID")
        sys.exit(1)
    force_send = True
    video_id = sys.argv[2]
    print("⚠️  FORCE MODE: Will send notification even if already sent")
else:
    video_id = sys.argv[1]

print(f"\nChecking video: {video_id}")
print("=" * 60)

# Initialize other services
youtube = YouTubeMetadata()
rules = NotificationRules(db)
discord = DiscordNotifier()

# Check if already notified
delivery_status = db.get_delivery_status(video_id)
already_notified = any(d['platform'] == 'discord' and d['status'] == 'success' for d in delivery_status)

if already_notified and not force_send:
    print("⚠️  Notification already sent for this video!")
    print("   Use --force to send anyway")
    for d in delivery_status:
        if d['platform'] == 'discord' and d['status'] == 'success':
            print(f"   Sent at: {d.get('delivered_at', 'unknown')}")
    print("\nContinuing with check anyway...")
elif already_notified and force_send:
    print("⚠️  Notification already sent, but FORCE MODE enabled")
    print("   Will send again...")

# Fetch metadata
print("Fetching metadata from YouTube API...")
details = youtube.get_video_details(video_id)

if not details:
    print("❌ Failed to fetch video details")
    sys.exit(1)

print(f"✅ Got video details")
print(f"   Title: {details['title']}")
print(f"   Live Status: {details['live_status']}")
print(f"   Scheduled: {details.get('scheduled_start_time', 'N/A')}")

# Check if it's scheduled and within 2 hours
if details['live_status'] == 'is_upcoming' and details.get('scheduled_start_time'):
    scheduled_dt = datetime.fromisoformat(details['scheduled_start_time'].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    hours_until = (scheduled_dt - now).total_seconds() / 3600
    
    print(f"\n⏰ Stream starts in {hours_until:.1f} hours")
    
    if hours_until <= 2:
        if already_notified and not force_send:
            print("⏭️  Notification already sent - skipping")
        else:
            print("✅ Within 2 hour window - sending notification...")
            
            # Prepare video data
            video_data = {
                'video_id': video_id,
                'title': details['title'],
                'video_url': f"https://www.youtube.com/watch?v={video_id}",
                'author_name': details['channel'],
                'live_status': 'is_upcoming',
                'scheduled_start_time': details['scheduled_start_time']
            }
            
            # Get notification message
            message_data = rules.get_notification_message(video_data, 'upcoming')
            
            if message_data:
                result = discord.send_notification(video_data, 'upcoming', message_data)
                
                if result['success']:
                    print("✅ Notification sent successfully!")
                    if not already_notified:
                        db.mark_delivered(video_id, 'discord', 'success', result.get('response'))
                else:
                    print(f"❌ Failed: {result.get('error')}")
            else:
                print("❌ Failed to generate message")
    else:
        print(f"⏭️  Too far away ({hours_until:.1f} hours) - no notification sent")
else:
    print(f"\n⏭️  Not an upcoming scheduled stream - no notification sent")
    print(f"   Status: {details['live_status']}")
