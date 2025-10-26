#!/usr/bin/env python3
"""
Test live stream notifications in Discord
"""
from datetime import datetime, timedelta, timezone
from notifiers import DiscordNotifier
from notification_rules import NotificationRules
from database import NotificationDB

def test_all_notification_types():
    """Test all types of live stream notifications"""
    
    discord = DiscordNotifier()
    db = NotificationDB()
    rules = NotificationRules(db)
    
    now = datetime.now(timezone.utc)
    
    print("\n" + "=" * 80)
    print("Testing Discord Live Stream Notifications")
    print("=" * 80)
    
    # Test 1: Upcoming stream (20 minutes) - Using real video
    print("\n1. Testing 'Upcoming Stream' notification (20 minutes away)")
    print("-" * 80)
    
    scheduled_time = (now + timedelta(minutes=20)).isoformat()
    video_data = {
        'video_id': 'dQw4w9WgXcQ',  # Example video ID
        'title': 'TEST: Example Live Stream Title',
        'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'author_name': 'Example Channel',
        'live_status': 'is_upcoming',
        'scheduled_start_time': scheduled_time
    }
    
    message = rules.get_notification_message(video_data, 'upcoming', custom_emoji=':HELLO_TEAM:')
    result = discord.send_notification(video_data, 'upcoming', message)
    
    if result['success']:
        print("✅ Upcoming notification sent!")
        print(f"   Message ID: {result['response'].get('id', 'N/A')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
    
    # Test 2: Stream starting in 5 minutes
    print("\n2. Testing 'Upcoming Stream' notification (5 minutes away)")
    print("-" * 80)
    
    scheduled_time = (now + timedelta(minutes=5)).isoformat()
    video_data['video_id'] = 'jNQXAC9IVRw'  # Example video ID
    video_data['title'] = 'TEST: Example Stream Starting Soon'
    video_data['video_url'] = 'https://www.youtube.com/watch?v=jNQXAC9IVRw'
    video_data['scheduled_start_time'] = scheduled_time
    
    message = rules.get_notification_message(video_data, 'upcoming', custom_emoji=':HELLO_TEAM:')
    result = discord.send_notification(video_data, 'upcoming', message)
    
    if result['success']:
        print("✅ Upcoming notification sent!")
        print(f"   Message ID: {result['response'].get('id', 'N/A')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
    
    # Test 3: Stream rescheduled
    print("\n3. Testing 'Rescheduled Stream' notification")
    print("-" * 80)
    
    scheduled_time = (now + timedelta(minutes=30)).isoformat()
    video_data['video_id'] = '9bZkp7q19f0'  # Example video ID
    video_data['title'] = 'TEST: Example Rescheduled Stream'
    video_data['video_url'] = 'https://www.youtube.com/watch?v=9bZkp7q19f0'
    video_data['scheduled_start_time'] = scheduled_time
    
    message = rules.get_notification_message(video_data, 'reschedule', custom_emoji=':HELLO_TEAM:')
    result = discord.send_notification(video_data, 'reschedule', message)
    
    if result['success']:
        print("✅ Reschedule notification sent!")
        print(f"   Message ID: {result['response'].get('id', 'N/A')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
    
    # Test 4: Stream is LIVE NOW
    print("\n4. Testing 'LIVE NOW' notification")
    print("-" * 80)
    
    video_data['video_id'] = 'dQw4w9WgXcQ'  # Example video ID
    video_data['title'] = 'TEST: Example Live Stream NOW'
    video_data['video_url'] = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    video_data['live_status'] = 'is_live'
    video_data['scheduled_start_time'] = now.isoformat()
    
    message = rules.get_notification_message(video_data, 'live_now', custom_emoji=':HELLO_TEAM:')
    result = discord.send_notification(video_data, 'live_now', message)
    
    if result['success']:
        print("✅ LIVE NOW notification sent!")
        print(f"   Message ID: {result['response'].get('id', 'N/A')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
    
    print("\n" + "=" * 80)
    print("All tests complete!")
    print("Check your Discord test channel for the notifications")
    print("=" * 80)

if __name__ == '__main__':
    test_all_notification_types()
