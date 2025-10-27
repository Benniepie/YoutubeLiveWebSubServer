"""
HTML fallback for live status detection when yt-dlp fails
Only use this when yt-dlp is blocked by bot detection
"""
import requests

def check_live_status_html(video_id: str) -> dict:
    """
    Fallback method to check if video is live by parsing HTML meta tag.
    Only use when yt-dlp fails with bot detection.
    
    Returns dict with:
    - live_status: 'is_live', 'is_upcoming', 'was_live', or 'not_live'
    - success: bool
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Check for live broadcast meta tag
        if '<meta itemprop="isLiveBroadcast" content="True">' in response.text:
            return {'live_status': 'is_live', 'success': True}
        
        # Check for upcoming (scheduled)
        if 'Premieres' in response.text or 'Scheduled for' in response.text:
            return {'live_status': 'is_upcoming', 'success': True}
        
        # Check if it was a past live stream
        if 'Streamed live on' in response.text:
            return {'live_status': 'was_live', 'success': True}
        
        return {'live_status': 'not_live', 'success': True}
        
    except Exception as e:
        print(f"  ⚠️  HTML fallback failed: {e}")
        return {'live_status': 'not_live', 'success': False}
