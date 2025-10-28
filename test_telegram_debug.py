#!/usr/bin/env python3
"""
Test the comprehensive Telegram debug notification
Simulates what happens when a WebSub event is processed
"""
from telegram_notifier import TelegramNotifier
from notification_rules import NotificationRules
from database import NotificationDB

# Initialize
telegram_debug = TelegramNotifier(use_test_bot=True)
db = NotificationDB()
rules = NotificationRules(db)

# Test data - simulate a live stream starting
# Use a real video ID so thumbnail works
video_id = "DEhvWCmYMyg"  # Real video from your channel
title = "Ukraine War 🔴 Live Stream: Geopolitical News"
author_name = "ATP Geopolitics"
video_url = f"https://www.youtube.com/watch?v={video_id}"

print("Testing comprehensive Telegram debug notification...")
print("=" * 60)

# Simulate processing log
processing_log = []
processing_log.append("📥 Event: live_started")
processing_log.append("🆕 New: No")
processing_log.append("❌ yt-dlp: Failed after 3 attempts")
processing_log.append("🔄 HTML fallback: Retry with 3s delay")
processing_log.append("✅ HTML fallback: is_live")
processing_log.append("🔴 Status: is_live")
processing_log.append("📤 Sending: live_now")
processing_log.append("✅ Discord: SENT")

# Simulate video data
video_data = {
    'video_id': video_id,
    'title': title,
    'video_url': video_url,
    'author_name': author_name,
    'live_status': 'is_live',
    'scheduled_start_time': None
}

# Build the debug caption (same as in websub_server.py)
status_emoji = {
    'is_live': '🔴 LIVE NOW',
    'is_upcoming': '📅 SCHEDULED',
    'was_live': '📼 ENDED',
    'not_live': '📹 VIDEO'
}.get(video_data.get('live_status', 'not_live'), '❓ UNKNOWN')

debug_caption = f"<b>{title}</b>\n\n"
debug_caption += f"{status_emoji}\n"
debug_caption += f"👤 {author_name}\n\n"

debug_caption += f"<b>📊 Processing Log:</b>\n"
debug_caption += "\n".join(processing_log) + "\n\n"

# Simulate successful notification
notification_type = "live_now"
debug_caption += f"<b>✅ USER NOTIFIED</b>\n"
debug_caption += f"Type: {notification_type}\n"
debug_caption += f"Platform: Discord\n\n"
debug_caption += f"<a href='{video_url}'>Watch Video</a>"

# Send with thumbnail
thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

print("\nSending test notification to Telegram...")
print(f"Thumbnail: {thumbnail_url}")
print(f"\nCaption:\n{debug_caption}")
print("\n" + "=" * 60)

result = telegram_debug.send_photo(thumbnail_url, debug_caption)

if result['success']:
    print("✅ Test notification sent successfully!")
    print("Check your Telegram for the message")
else:
    print(f"❌ Failed to send: {result.get('error')}")

print("\n" + "=" * 60)
print("\nNow testing SKIPPED notification...")
print("=" * 60)

# Test 2: Skipped notification
processing_log2 = []
processing_log2.append("📥 Event: video_published")
processing_log2.append("🆕 New: Yes")
processing_log2.append("✅ yt-dlp: Success")
processing_log2.append("🔴 Status: not_live")
processing_log2.append("⏭️ Skipped: Not a live stream")

video_data2 = {
    'video_id': 'AiQKU446UzU',  # Real video from your channel
    'title': 'Ukraine War Update: Morning News',
    'video_url': 'https://www.youtube.com/watch?v=AiQKU446UzU',
    'author_name': 'ATP Geopolitics',
    'live_status': 'not_live',
}

debug_caption2 = f"<b>{video_data2['title']}</b>\n\n"
debug_caption2 += "📹 VIDEO\n"
debug_caption2 += f"👤 {video_data2['author_name']}\n\n"
debug_caption2 += f"<b>📊 Processing Log:</b>\n"
debug_caption2 += "\n".join(processing_log2) + "\n\n"
debug_caption2 += f"<b>⏭️ NO NOTIFICATION</b>\n"
debug_caption2 += f"Reason: Not a live stream\n\n"
debug_caption2 += f"<a href='{video_data2['video_url']}'>Watch Video</a>"

thumbnail_url2 = f"https://img.youtube.com/vi/{video_data2['video_id']}/maxresdefault.jpg"

result2 = telegram_debug.send_photo(thumbnail_url2, debug_caption2)

if result2['success']:
    print("✅ Skipped notification sent successfully!")
    print("Check your Telegram for the message")
else:
    print(f"❌ Failed to send: {result2.get('error')}")

print("\n" + "=" * 60)
print("Test complete! Check your Telegram for 2 messages:")
print("1. Live stream notification (USER NOTIFIED)")
print("2. Regular video (NO NOTIFICATION)")
print("=" * 60)
