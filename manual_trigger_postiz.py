import os
import json
from dotenv import load_dotenv
from notifiers import PostizNotifier

# Load environment variables
load_dotenv(override=True)

def main():
    print("🚀 Starting manual Postiz trigger...")
    
    # Initialize Notifier
    postiz = PostizNotifier()
    
    # Sample Video Data (Rick Roll ID for testing)
    video_data = {
        'video_id': 'dQw4w9WgXcQ',
        'title': 'Global Geopolitics Update - TEST',
        'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'description': 'This is a manual test of the Postiz integration. #Ukraine #Russia #Test \n\nCheck out the updates.',
        'published_time': '2025-12-31T12:00:00Z', # Future date for scheduling
        'is_live_stream': False,
        'scheduled_start_time': None
    }
    
    # Optional: Override with live stream data if you want to test live logic
    # video_data['is_live_stream'] = True
    # video_data['scheduled_start_time'] = '2025-12-31T12:00:00Z'
    
    print(f"📊 Testing with Video ID: {video_data['video_id']}")
    print(f"📝 Title: {video_data['title']}")
    
    # Send Notification
    try:
        results = postiz.send_notification(video_data)
        
        print("\n✅ Execution Complete. Results:")
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
