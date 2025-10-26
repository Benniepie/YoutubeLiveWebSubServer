#!/usr/bin/env python3
"""
Simple script to view notifications stored in the database
"""
from database import NotificationDB
from datetime import datetime
import sys

def print_separator():
    print("=" * 80)

def format_datetime(dt_str):
    """Format ISO datetime string to readable format"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        return dt_str

def view_recent_videos(limit=20):
    """View recent videos"""
    db = NotificationDB()
    videos = db.get_recent_videos(limit)
    
    print(f"\n📺 RECENT VIDEOS (Last {limit})")
    print_separator()
    
    for video in videos:
        print(f"\nTitle: {video['title']}")
        print(f"Video ID: {video['video_id']}")
        print(f"URL: {video['video_url']}")
        print(f"Published: {format_datetime(video['published_time'])}")
        print(f"First Seen: {format_datetime(video['first_seen_at'])}")
        print(f"Last Updated: {format_datetime(video['last_updated_at'])}")
        print(f"Notification Count: {video['notification_count']}")
        print(f"Is Live Stream: {'Yes' if video['is_live_stream'] else 'No'}")
        print(f"Status: {video['live_stream_status']}")
        
        # Show delivery status
        delivery = db.get_delivery_status(video['video_id'])
        if delivery:
            print(f"Delivered to: {', '.join([d['platform'] for d in delivery])}")
        
        print("-" * 80)

def view_video_events(video_id):
    """View all events for a specific video"""
    db = NotificationDB()
    events = db.get_video_events(video_id)
    
    print(f"\n📋 EVENTS FOR VIDEO: {video_id}")
    print_separator()
    
    for i, event in enumerate(events, 1):
        print(f"\nEvent #{i}")
        print(f"Received: {format_datetime(event['received_at'])}")
        print(f"Published: {format_datetime(event['published_time'])}")
        if event['updated_time']:
            print(f"Updated: {format_datetime(event['updated_time'])}")
        print(f"Event Type: {event['event_type']}")
        print("-" * 80)

def view_live_streams():
    """View all live streams"""
    db = NotificationDB()
    streams = db.get_live_streams()
    
    print(f"\n🔴 LIVE STREAMS")
    print_separator()
    
    for stream in streams:
        print(f"\nTitle: {stream['title']}")
        print(f"Video ID: {stream['video_id']}")
        print(f"URL: {stream['video_url']}")
        print(f"Status: {stream['live_stream_status']}")
        print(f"Notification Count: {stream['notification_count']}")
        print(f"First Seen: {format_datetime(stream['first_seen_at'])}")
        print(f"Last Updated: {format_datetime(stream['last_updated_at'])}")
        
        # Show scheduled time if available
        if stream.get('scheduled_start_time'):
            print(f"Scheduled Start: {format_datetime(stream['scheduled_start_time'])}")
        
        # Show duration if available
        if stream.get('duration'):
            print(f"Duration: {stream['duration']}")
        
        # Show view count if available
        if stream.get('view_count'):
            print(f"Views: {stream['view_count']:,}")
        
        # Show all events for this stream
        events = db.get_video_events(stream['video_id'])
        print(f"Events: {' → '.join([e['event_type'] for e in events])}")
        
        print("-" * 80)

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'recent':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            view_recent_videos(limit)
        elif command == 'events':
            if len(sys.argv) < 3:
                print("Usage: python view_notifications.py events <video_id>")
                return
            video_id = sys.argv[2]
            view_video_events(video_id)
        elif command == 'live':
            view_live_streams()
        else:
            print("Unknown command. Use: recent, events, or live")
    else:
        # Default: show recent videos
        view_recent_videos(10)
        print("\n💡 Usage:")
        print("  python view_notifications.py recent [limit]  - View recent videos")
        print("  python view_notifications.py events <video_id> - View events for a video")
        print("  python view_notifications.py live - View all live streams")

if __name__ == '__main__':
    main()
