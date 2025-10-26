#!/usr/bin/env python3
"""
Test notification rules logic
"""
from datetime import datetime, timedelta, timezone
from database import NotificationDB
from notification_rules import NotificationRules

def test_rules():
    """Test various notification scenarios"""
    
    db = NotificationDB()
    rules = NotificationRules(db)
    
    print("Testing Notification Rules")
    print("=" * 80)
    
    now = datetime.now(timezone.utc)
    
    # Test 1: New stream starting in 10 minutes
    print("\n1. New stream starting in 10 minutes")
    print("-" * 80)
    scheduled_time = (now + timedelta(minutes=10)).isoformat()
    video_data = {
        'video_id': 'TEST001',
        'title': 'Test Live Stream',
        'video_url': 'https://youtube.com/watch?v=TEST001',
        'live_status': 'is_upcoming',
        'scheduled_start_time': scheduled_time
    }
    should_notify, notif_type = rules.should_notify(video_data, 'video_published', is_new=True)
    print(f"Should notify: {should_notify}")
    print(f"Type: {notif_type}")
    if should_notify:
        msg = rules.get_notification_message(video_data, notif_type)
        print(f"Message: {msg['content'][:100]}...")
    
    # Test 2: New stream starting in 3 hours (too far)
    print("\n2. New stream starting in 3 hours (should NOT notify)")
    print("-" * 80)
    scheduled_time = (now + timedelta(hours=3)).isoformat()
    video_data['scheduled_start_time'] = scheduled_time
    video_data['video_id'] = 'TEST002'
    should_notify, notif_type = rules.should_notify(video_data, 'video_published', is_new=True)
    print(f"Should notify: {should_notify}")
    print(f"Type: {notif_type}")
    
    # Test 3: Stream just went live
    print("\n3. Stream just went live")
    print("-" * 80)
    video_data = {
        'video_id': 'TEST003',
        'title': 'Test Live Stream',
        'video_url': 'https://youtube.com/watch?v=TEST003',
        'live_status': 'is_live',
        'scheduled_start_time': now.isoformat()
    }
    should_notify, notif_type = rules.should_notify(video_data, 'live_started', is_new=False)
    print(f"Should notify: {should_notify}")
    print(f"Type: {notif_type}")
    if should_notify:
        msg = rules.get_notification_message(video_data, notif_type)
        print(f"Message: {msg['content'][:100]}...")
    
    # Test 4: Regular video (not live)
    print("\n4. Regular video (should NOT notify)")
    print("-" * 80)
    video_data = {
        'video_id': 'TEST004',
        'title': 'Regular Video',
        'video_url': 'https://youtube.com/watch?v=TEST004',
        'live_status': 'not_live'
    }
    should_notify, notif_type = rules.should_notify(video_data, 'video_published', is_new=True)
    print(f"Should notify: {should_notify}")
    print(f"Type: {notif_type}")
    
    # Test time formatting
    print("\n" + "=" * 80)
    print("Time Formatting Tests")
    print("=" * 80)
    
    test_times = [
        (now + timedelta(minutes=5), "5 minutes"),
        (now + timedelta(minutes=20), "20 minutes"),
        (now + timedelta(hours=1, minutes=30), "1 hour 30 minutes"),
        (now + timedelta(hours=2), "2 hours"),
    ]
    
    for test_time, expected in test_times:
        formatted = rules.format_time_until(test_time.isoformat())
        print(f"{expected:20} → {formatted}")
    
    print("\n" + "=" * 80)
    print("Tests complete!")

if __name__ == '__main__':
    test_rules()
