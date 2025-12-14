import os
import json
import logging
from dotenv import load_dotenv
from notifiers import PostizNotifier
from youtube_metadata import YouTubeMetadata

# Load environment variables
load_dotenv(override=True)

def main():
    print("🚀 Starting manual Postiz trigger with REAL YouTube Data...")
    
    # 1. Setup
    video_id = "63NoYLZXJfY" # User requested video
    postiz = PostizNotifier()
    try:
        yt = YouTubeMetadata() 
    except Exception as e:
        print(f"❌ YouTube API Error (Init): {e}")
        return

    # 2. Fetch Real Data
    print(f"📥 Fetching details for {video_id}...")
    try:
        details = yt.get_video_details(video_id)
    except Exception as e:
        print(f"❌ YouTube API Error (Fetch): {e}")
        return

    if not details:
        print("❌ Could not fetch video details (result is None).")
        return

    # 3. Construct Payload
    # Mimic websub_server.py logic
    # It creates a 'video_data' dict with keys expected by notifiers.
    
    video_data = {
        'video_id': details['video_id'],
        'title': details['title'],
        'video_url': f"https://www.youtube.com/watch?v={details['video_id']}",
        'description': details['description'],
        'published_time': os.environ.get('POSTIZ_API_DATE'), # Use Configured Date OR details['published_at'] if missing
        'is_live_stream': details['live_status'] in ['is_live', 'is_upcoming', 'was_live'],
        'scheduled_start_time': details.get('scheduled_start_time'),
        'live_status': details.get('live_status', 'not_live')
    }
    
    # Fallback for published_time if env var not set (mocking what happens in real flow somewhat, 
    # though in real flow published_time comes from XML feed usually, but here we can just say 'now' or 'scheduled')
    if not video_data['published_time']:
         # In manual trigger, we probably want to assume the user set POSTIZ_API_DATE for testing.
         # If not, we might fail or post "now". 
         pass 

    print("---------------------------------------------------")
    print(f"📊 Video Found: {video_data['title']}")
    print(f"🔗 URL: {video_data['video_url']}")
    print(f"📝 Description Length: {len(video_data['description'])} chars")
    print(f"🏷️  Hashtags in Desc: {(video_data['description'].count('#'))}")
    print(f"🔴 Live Status: {video_data['live_status']}")
    print("---------------------------------------------------")
    
    # 4. Send
    try:
        results = postiz.send_notification(video_data)
        print("\n✅ Execution Complete. Results:")
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
