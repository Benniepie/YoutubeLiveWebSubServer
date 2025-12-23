"""
YouTube metadata fetcher using YouTube Data API v3
Replaces yt-dlp with reliable OAuth2-based API calls
"""
from typing import Dict, Optional
from datetime import datetime
from youtube_api import YouTubeAPI

class YouTubeMetadata:
    """Fetch video metadata using YouTube Data API v3"""
    
    def __init__(self):
        self.api = YouTubeAPI()
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Fetch video details from YouTube API
        Returns standardized metadata dict
        
        Quota cost: 1 unit per call
        No retries - single reliable call
        """
        api_result = self.api.get_video_details(video_id)
        
        if not api_result:
            return None
        
        # Determine live status from API data
        if api_result.get('actual_end_time'):
            live_status = 'was_live'
            is_live = False
            was_live = True
        elif api_result.get('actual_start_time'):
            live_status = 'is_live'
            is_live = True
            was_live = False
        elif api_result.get('scheduled_start_time'):
            live_status = 'is_upcoming'
            is_live = False
            was_live = False
        elif api_result['is_live_content']:
            # Live content but no timing info yet
            live_status = 'is_upcoming'
            is_live = False
            was_live = False
        else:
            # Fallback: Check title for live stream indicators
            title = api_result.get('title', '').upper()
            if 'LIVE STREAM' in title or '🔴' in title:
                # Likely a scheduled stream that YouTube hasn't processed yet
                live_status = 'is_upcoming'
                is_live = False
                was_live = False
            else:
                live_status = 'not_live'
                is_live = False
                was_live = False
        
        # Return standardized format
        return {
            'video_id': video_id,
            'title': api_result['title'],
            'description': api_result['description'],
            'channel_id': api_result['channel_id'],
            'channel': api_result['channel_title'],
            'published_time': api_result.get('published_time'),
            
            # Live streaming detection
            'is_live': is_live,
            'was_live': was_live,
            'live_status': live_status,
            
            # Timing
            'scheduled_start_time': api_result.get('scheduled_start_time'),
            'actual_start_time': api_result.get('actual_start_time'),
            'actual_end_time': api_result.get('actual_end_time'),
            
            # Statistics
            'view_count': api_result.get('view_count'),
            'like_count': api_result.get('like_count'),
            'comment_count': api_result.get('comment_count'),
            
            # Other
            'duration': api_result.get('duration'),
            'thumbnail': api_result.get('thumbnail_url'),
            'tags': api_result.get('tags', []),
        }
    
    def is_live_content(self, video_id: str) -> Optional[bool]:
        """Quick check if video is/was live content"""
        details = self.get_video_details(video_id)
        if not details:
            return None
        
        return details.get('is_live') or details.get('was_live') or details.get('live_status') != 'not_live'


# Example usage
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python youtube_metadata.py <video_id>")
        print("Example: python youtube_metadata.py DEhvWCmYMyg")
        sys.exit(1)
    
    video_id = sys.argv[1]
    
    fetcher = YouTubeMetadata()
    details = fetcher.get_video_details(video_id)
    
    if details:
        print(f"\n📺 Video: {details['title']}")
        print(f"Channel: {details['channel']}")
        print(f"\n🔍 Live Detection:")
        print(f"  live_status: {details['live_status']}")
        print(f"  is_live: {details['is_live']}")
        print(f"  was_live: {details['was_live']}")
        
        if details.get('scheduled_start_time'):
            print(f"\n📅 Scheduled Start: {details['scheduled_start_time']}")
        if details.get('actual_start_time'):
            print(f"🔴 Actual Start: {details['actual_start_time']}")
        if details.get('actual_end_time'):
            print(f"⏹️  Actual End: {details['actual_end_time']}")
        
        if details.get('view_count'):
            print(f"\n📊 Views: {int(details['view_count']):,}")
    else:
        print("Failed to fetch video details")
