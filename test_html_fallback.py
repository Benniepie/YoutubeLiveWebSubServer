#!/usr/bin/env python3
"""
Test HTML fallback for live status detection
Run this to test if YouTube blocks the HTML scraping approach
"""
import requests
import sys

def check_live_status_html(video_id: str) -> dict:
    """
    Fallback method to check if video is live by parsing HTML meta tag.
    
    Returns dict with:
    - live_status: 'is_live', 'is_upcoming', or 'not_live'
    - success: bool
    - error: str (if failed)
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
        
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)} bytes")
        
        # Check for live broadcast meta tag
        if '<meta itemprop="isLiveBroadcast" content="True">' in response.text:
            return {'live_status': 'is_live', 'success': True, 'method': 'isLiveBroadcast meta tag'}
        
        # Check for upcoming (scheduled)
        if 'Premieres' in response.text or 'Scheduled for' in response.text:
            return {'live_status': 'is_upcoming', 'success': True, 'method': 'Premieres/Scheduled text'}
        
        # Check if it was a past live stream
        if 'Streamed live on' in response.text:
            return {'live_status': 'was_live', 'success': True, 'method': 'Streamed live text'}
        
        return {'live_status': 'not_live', 'success': True, 'method': 'default'}
        
    except requests.exceptions.HTTPError as e:
        return {'live_status': 'not_live', 'success': False, 'error': f'HTTP {e.response.status_code}'}
    except requests.exceptions.Timeout:
        return {'live_status': 'not_live', 'success': False, 'error': 'Request timeout'}
    except Exception as e:
        return {'live_status': 'not_live', 'success': False, 'error': str(e)}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_html_fallback.py <video_id>")
        print("\nTest with different video types:")
        print("  - A live stream currently in progress")
        print("  - A scheduled/upcoming stream")
        print("  - A regular video")
        print("  - A past live stream")
        sys.exit(1)
    
    video_id = sys.argv[1]
    
    print("=" * 60)
    print("Testing HTML Fallback for Live Status Detection")
    print("=" * 60)
    print()
    
    result = check_live_status_html(video_id)
    
    print()
    print("=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(f"Video ID: {video_id}")
    print(f"Live Status: {result['live_status']}")
    print(f"Success: {result['success']}")
    
    if result['success']:
        print(f"Detection Method: {result['method']}")
    else:
        print(f"Error: {result['error']}")
    
    print()
    print("Test different video types to verify detection works!")
