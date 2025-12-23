import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ghost_notifier import GhostNotifier
from youtube_metadata import YouTubeMetadata

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def manual_trigger(video_id):
    load_dotenv()
    
    # 1. Fetch Metadata
    logging.info(f"Fetching metadata for {video_id}...")
    yt = YouTubeMetadata()
    video_data = yt.get_video_details(video_id)
    
    if not video_data:
        logging.error("Failed to fetch video metadata.")
        return

    logging.info(f"Title: {video_data['title']}")
    logging.info(f"Live Status: {video_data.get('live_status')}")

    # 2. Trigger Ghost Notifier
    logging.info("Triggering Ghost Notifier...")
    ghost = GhostNotifier()
    result = ghost.send_notification(video_data)
    
    if result['success']:
        logging.info("✅ Success!")
        if 'url' in result:
             logging.info(f"URL: {result['url']}")
        if 'message' in result:
             logging.info(f"Message: {result['message']}")
    else:
        logging.error(f"❌ Failed: {result.get('error')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        manual_trigger(sys.argv[1])
    else:
        print("Usage: python manual_ghost_post.py <VIDEO_ID>")
