"""
Use yt-dlp to fetch video metadata without using YouTube API quota
"""
import subprocess
import json
from typing import Dict, Optional
from datetime import datetime
from html_fallback import check_live_status_html

class YTDLPMetadata:
    """Fetch video metadata using yt-dlp (no API quota required!)"""
    
    def get_video_details(self, video_id: str, expected_live: bool = False) -> Optional[Dict]:
        """
        Fetch detailed video information using yt-dlp
        Returns all the same info as YouTube API but without quota cost!
        
        Args:
            video_id: YouTube video ID
            expected_live: If True, HTML fallback will retry if it gets 'not_live' (timing lag mitigation)
        """
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            # Run yt-dlp to get JSON metadata
            # Increased timeout and added retry logic
            result = subprocess.run(
                ['yt-dlp', '--dump-json', '--no-download', '--no-warnings', url],
                capture_output=True,
                text=True,
                timeout=30  # Increased from 10 to 30 seconds
            )
            
            if result.returncode != 0:
                error_msg = result.stderr
                print(f"  ❌ yt-dlp error: {error_msg}")
                
                # Check if it's a scheduled live stream (not an error, just info)
                if "live event will begin" in error_msg.lower():
                    print(f"  📅 Scheduled live stream detected - parsing time...")
                    
                    # Extract minutes from error message
                    import re
                    minutes_match = re.search(r'begin in (\d+) minute', error_msg)
                    
                    scheduled_time = None
                    if minutes_match:
                        minutes = int(minutes_match.group(1))
                        # Only use if reasonable (< 120 minutes = 2 hours)
                        if minutes <= 120:
                            from datetime import datetime, timedelta, timezone
                            scheduled_dt = datetime.now(timezone.utc) + timedelta(minutes=minutes)
                            scheduled_time = scheduled_dt.isoformat().replace('+00:00', 'Z')
                            print(f"  ⏰ Calculated start time: {minutes} minutes from now")
                    
                    # Return data indicating it's upcoming with calculated time
                    return {
                        'video_id': video_id,
                        'live_status': 'is_upcoming',
                        'is_live': False,
                        'was_live': False,
                        'scheduled_start_time': scheduled_time,
                    }
                
                # Check if it's a bot detection error
                if "Sign in to confirm you're not a bot" in error_msg or "cookies" in error_msg.lower():
                    print(f"  🔄 Bot detection - trying HTML fallback...")
                    
                    # Use retry logic for HTML fallback to handle timing lag
                    # Retry if we expect it might be live (based on context from caller)
                    html_result = check_live_status_html(video_id, retry_on_not_live=expected_live)
                    
                    if html_result['success']:
                        print(f"  ✅ HTML fallback succeeded: {html_result['live_status']}")
                        # Return minimal metadata with live status from HTML
                        return {
                            'video_id': video_id,
                            'live_status': html_result['live_status'],
                            'is_live': html_result['live_status'] == 'is_live',
                            'was_live': html_result['live_status'] == 'was_live',
                            'scheduled_start_time': None,  # Can't get from HTML
                        }
                    else:
                        print(f"  ❌ HTML fallback also failed")
                
                return None
            
            data = json.loads(result.stdout)
            
            # Extract relevant fields
            result = {
                # Basic info
                'video_id': video_id,
                'title': data.get('title'),
                'description': data.get('description'),
                'channel_id': data.get('channel_id'),
                'channel': data.get('channel'),
                'uploader': data.get('uploader'),
                'upload_date': data.get('upload_date'),
                'thumbnail': data.get('thumbnail'),
                
                # Live streaming detection and details
                'is_live': data.get('is_live', False),
                'was_live': data.get('was_live', False),
                'live_status': data.get('live_status'),  # 'is_live', 'is_upcoming', 'was_live', 'not_live'
                'release_timestamp': data.get('release_timestamp'),  # Scheduled start time!
                'release_date': data.get('release_date'),
                
                # Duration
                'duration': data.get('duration'),
                'duration_string': data.get('duration_string'),
                
                # Statistics
                'view_count': data.get('view_count'),
                'like_count': data.get('like_count'),
                'comment_count': data.get('comment_count'),
                
                # Other useful fields
                'categories': data.get('categories', []),
                'tags': data.get('tags', []),
                'availability': data.get('availability'),
                'age_limit': data.get('age_limit'),
            }
            
            # Convert release_timestamp to ISO format if available
            if result['release_timestamp']:
                result['scheduled_start_time'] = datetime.fromtimestamp(
                    result['release_timestamp']
                ).isoformat() + 'Z'
            else:
                result['scheduled_start_time'] = None
            
            return result
            
        except subprocess.TimeoutExpired:
            print(f"  ⏱️  yt-dlp timeout for video {video_id} - retrying once...")
            # Retry once with even longer timeout
            try:
                result = subprocess.run(
                    ['yt-dlp', '--dump-json', '--no-download', '--no-warnings', url],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    # Process data same as above...
                    result_dict = self._extract_metadata(data, video_id)
                    return result_dict
            except:
                pass
            print(f"  ❌ yt-dlp timeout after retry for video {video_id}")
            return None
        except FileNotFoundError:
            print(f"  ❌ yt-dlp not installed! Install with: pip install yt-dlp")
            return None
        except json.JSONDecodeError as e:
            print(f"  ❌ Failed to parse yt-dlp output: {e}")
            print(f"  Output was: {result.stdout[:200]}")
            return None
        except Exception as e:
            print(f"  ❌ Error fetching metadata: {e}")
            return None
    
    def _extract_metadata(self, data: dict, video_id: str) -> Dict:
        """Extract and format metadata from yt-dlp JSON response"""
    
    def is_live_content(self, video_id: str) -> Optional[bool]:
        """Quick check if video is/was live content"""
        details = self.get_video_details(video_id)
        if not details:
            return None
        
        return details.get('is_live') or details.get('was_live') or details.get('live_status') != 'not_live'
    
    def format_live_details(self, video_details: Dict) -> str:
        """Format live streaming details for display"""
        if not video_details:
            return "No metadata available"
        
        live_status = video_details.get('live_status', 'not_live')
        
        if live_status == 'not_live' and not video_details.get('was_live'):
            return "Not a live stream"
        
        lines = []
        
        # Live status
        status_emoji = {
            'is_live': '🔴 LIVE NOW',
            'is_upcoming': '📅 SCHEDULED',
            'was_live': '📼 ARCHIVED',
            'not_live': '📹 VIDEO'
        }
        lines.append(f"Status: {status_emoji.get(live_status, live_status)}")
        
        # Scheduled start time
        if video_details.get('scheduled_start_time'):
            lines.append(f"📅 Scheduled: {video_details['scheduled_start_time']}")
        
        # Duration (for archived streams)
        if video_details.get('duration_string'):
            lines.append(f"⏱️  Duration: {video_details['duration_string']}")
        
        # View count
        if video_details.get('view_count'):
            lines.append(f"👁️  Views: {video_details['view_count']:,}")
        
        return "\n".join(lines)


# Example usage and testing
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ytdlp_metadata.py <video_id>")
        print("Example: python ytdlp_metadata.py TctLKlkrDGw")
        sys.exit(1)
    
    video_id = sys.argv[1]
    
    fetcher = YTDLPMetadata()
    details = fetcher.get_video_details(video_id)
    
    if details:
        print(f"\n📺 Video: {details['title']}")
        print(f"Channel: {details['channel']}")
        print(f"\n{fetcher.format_live_details(details)}")
        
        print(f"\n🔍 Live Detection:")
        print(f"  is_live: {details['is_live']}")
        print(f"  was_live: {details['was_live']}")
        print(f"  live_status: {details['live_status']}")
        
        if details.get('scheduled_start_time'):
            print(f"\n📅 Scheduled Start: {details['scheduled_start_time']}")
    else:
        print("Failed to fetch video details")
