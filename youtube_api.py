"""
YouTube Data API v3 integration to fetch additional video metadata
that's not available in the WebSub feed

Uses OAuth2 authentication with client_secret.json
"""
import os
import pickle
from typing import Dict, Optional
from datetime import datetime
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

class YouTubeAPI:
    """Fetch additional video metadata from YouTube Data API v3"""
    
    def __init__(self, client_secrets_file: str = "client_secret.json"):
        self.client_secrets_file = client_secrets_file
        self.credentials = None
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate using OAuth2 with token caching"""
        # Token file stores the user's access and refresh tokens
        token_file = 'token.pickle'
        
        # Try to load existing credentials
        if os.path.exists(token_file):
            print(f"  📄 Loading credentials from {token_file}")
            with open(token_file, 'rb') as token:
                self.credentials = pickle.load(token)
        else:
            raise FileNotFoundError(f"Token file not found: {token_file}. Run authentication locally first.")
        
        # If credentials expired, try to refresh
        if not self.credentials.valid:
            if self.credentials.expired and self.credentials.refresh_token:
                print(f"  🔄 Refreshing expired credentials...")
                try:
                    self.credentials.refresh(Request())
                    # Save refreshed token
                    with open(token_file, 'wb') as token:
                        pickle.dump(self.credentials, token)
                    print(f"  ✅ Credentials refreshed")
                except Exception as e:
                    raise Exception(f"Failed to refresh credentials: {e}. Re-authenticate locally.")
            else:
                raise Exception(f"Invalid credentials and cannot refresh. Re-authenticate locally.")
            
            # Save credentials for next run
            with open(token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
        
        # Build the YouTube service
        self.youtube = googleapiclient.discovery.build(
            'youtube', 'v3', credentials=self.credentials)
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """
        Fetch detailed video information including:
        - Live streaming details (scheduled start time, actual start time, actual end time)
        - Video category
        - Duration
        - View count, like count
        - Tags
        
        Quota cost: 1 unit
        """
        if not self.youtube:
            print("  ⚠️  YouTube API not authenticated")
            return None
        
        try:
            request = self.youtube.videos().list(
                part='snippet,contentDetails,liveStreamingDetails,statistics,status',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                print(f"  ⚠️  No video found with ID: {video_id}")
                return None
            
            video = response['items'][0]
            
            # Extract relevant fields
            snippet = video.get('snippet', {})
            live_details = video.get('liveStreamingDetails', {})
            content_details = video.get('contentDetails', {})
            statistics = video.get('statistics', {})
            status = video.get('status', {})
            
            result = {
                # Basic info
                'video_id': video_id,
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'channel_id': snippet.get('channelId'),
                'channel_title': snippet.get('channelTitle'),
                'published_at': snippet.get('publishedAt'),
                'category_id': snippet.get('categoryId'),
                'tags': snippet.get('tags', []),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                
                # Live streaming details (if applicable)
                'is_live_content': live_details != {},
                'scheduled_start_time': live_details.get('scheduledStartTime'),
                'actual_start_time': live_details.get('actualStartTime'),
                'actual_end_time': live_details.get('actualEndTime'),
                'concurrent_viewers': live_details.get('concurrentViewers'),
                
                # Content details
                'duration': content_details.get('duration'),
                'definition': content_details.get('definition'),
                
                # Statistics
                'view_count': statistics.get('viewCount'),
                'like_count': statistics.get('likeCount'),
                'comment_count': statistics.get('commentCount'),
                
                # Status
                'upload_status': status.get('uploadStatus'),
                'privacy_status': status.get('privacyStatus'),
                'license': status.get('license'),
                'embeddable': status.get('embeddable'),
                'public_stats_viewable': status.get('publicStatsViewable'),
            }
            
            return result
            
        except googleapiclient.errors.HttpError as e:
            print(f"  ❌ YouTube API error: {e}")
            return None
        except Exception as e:
            print(f"  ❌ Error fetching video details: {e}")
            return None
    
    def format_live_details(self, video_details: Dict) -> str:
        """Format live streaming details for display"""
        if not video_details or not video_details.get('is_live_content'):
            return "Not a live stream"
        
        lines = []
        
        if video_details.get('scheduled_start_time'):
            scheduled = self._format_datetime(video_details['scheduled_start_time'])
            lines.append(f"📅 Scheduled: {scheduled}")
        
        if video_details.get('actual_start_time'):
            started = self._format_datetime(video_details['actual_start_time'])
            lines.append(f"🔴 Started: {started}")
        
        if video_details.get('actual_end_time'):
            ended = self._format_datetime(video_details['actual_end_time'])
            lines.append(f"⏹️  Ended: {ended}")
            
            # Calculate duration
            if video_details.get('actual_start_time'):
                start = datetime.fromisoformat(video_details['actual_start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(video_details['actual_end_time'].replace('Z', '+00:00'))
                duration = end - start
                hours = duration.seconds // 3600
                minutes = (duration.seconds % 3600) // 60
                lines.append(f"⏱️  Duration: {hours}h {minutes}m")
        
        if video_details.get('concurrent_viewers'):
            lines.append(f"👥 Peak Viewers: {video_details['concurrent_viewers']:,}")
        
        return "\n".join(lines) if lines else "Live stream (no timing details yet)"
    
    def _format_datetime(self, dt_str: str) -> str:
        """Format ISO datetime string to readable format"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            return dt_str


# Example usage
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python youtube_api.py <video_id>")
        print("Example: python youtube_api.py TctLKlkrDGw")
        sys.exit(1)
    
    video_id = sys.argv[1]
    
    api = YouTubeAPI()
    details = api.get_video_details(video_id)
    
    if details:
        print(f"\n📺 Video: {details['title']}")
        print(f"Channel: {details['channel_title']}")
        print(f"Published: {details['published_at']}")
        print(f"\n{api.format_live_details(details)}")
        
        if details.get('view_count'):
            print(f"\n📊 Stats:")
            print(f"  Views: {int(details['view_count']):,}")
            if details.get('like_count'):
                print(f"  Likes: {int(details['like_count']):,}")
    else:
        print("Failed to fetch video details")
