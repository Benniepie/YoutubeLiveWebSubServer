#!/usr/bin/env python3
"""
Test Telegram notifications with realistic video data
Shows what notifications will look like in production
"""
from telegram_notifier import TelegramNotifier

# Create test bot instance
telegram = TelegramNotifier(use_test_bot=True)

print("Sending test notifications to Telegram...")
print("=" * 60)

# Test 1: Regular video published
print("\n1. Regular video published")
video_data = {
    'video_id': '0VniyiTKZ74',
    'title': 'Ukraine War Update (20251026a): Overnight News - Sinking APCs, Glide Bombs, Air Defence Analysis',
    'video_url': 'https://www.youtube.com/watch?v=0VniyiTKZ74',
    'author_name': 'ATP Geopolitics'
}
result = telegram.send_video_notification(video_data, 'video_published', 'not_live')
print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")

# Test 2: Live stream scheduled
print("\n2. Live stream scheduled")
video_data = {
    'video_id': 'DEhvWCmYMyg',
    'title': 'Ukraine War 🔴 Live Stream: Geopolitical News',
    'video_url': 'https://www.youtube.com/watch?v=DEhvWCmYMyg',
    'author_name': 'ATP Geopolitics'
}
result = telegram.send_video_notification(video_data, 'live_scheduled', 'is_upcoming')
print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")

# Test 3: Live stream started
print("\n3. Live stream started")
video_data = {
    'video_id': 'DEhvWCmYMyg',
    'title': 'Ukraine War 🔴 Live Stream: Geopolitical News',
    'video_url': 'https://www.youtube.com/watch?v=DEhvWCmYMyg',
    'author_name': 'ATP Geopolitics'
}
result = telegram.send_video_notification(video_data, 'live_started', 'is_live')
print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")

# Test 4: Video updated
print("\n4. Video updated")
video_data = {
    'video_id': '0VniyiTKZ74',
    'title': 'Ukraine War Update (20251026a): Overnight News - UPDATED TITLE',
    'video_url': 'https://www.youtube.com/watch?v=0VniyiTKZ74',
    'author_name': 'ATP Geopolitics'
}
result = telegram.send_video_notification(video_data, 'video_updated', 'not_live')
print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")

# Test 5: Live stream ended
print("\n5. Live stream ended")
video_data = {
    'video_id': 'DEhvWCmYMyg',
    'title': 'Ukraine War 🔴 Live Stream: Geopolitical News',
    'video_url': 'https://www.youtube.com/watch?v=DEhvWCmYMyg',
    'author_name': 'ATP Geopolitics'
}
result = telegram.send_video_notification(video_data, 'live_ended', 'was_live')
print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")

print("\n" + "=" * 60)
print("Check your Telegram test bot for all 5 notifications!")
print("These show what you'll see for every WebSub event.")
