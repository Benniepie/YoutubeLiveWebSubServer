#!/usr/bin/env python3
"""
Backfill metadata for existing videos in the database using yt-dlp
"""
from database import NotificationDB
from ytdlp_metadata import YTDLPMetadata
import time

def backfill_all_videos():
    """Fetch and update metadata for ALL videos in the database"""
    db = NotificationDB()
    ytdlp = YTDLPMetadata()
    
    videos = db.get_recent_videos(limit=1000)  # Get all videos
    
    print(f"Found {len(videos)} videos to backfill")
    print("=" * 80)
    
    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        title = video['title']
        
        print(f"\n[{i}/{len(videos)}] {title[:60]}...")
        print(f"Video ID: {video_id}")
        
        # Check if already has metadata
        if video.get('scheduled_start_time') or video.get('view_count'):
            print("  ✓ Already has metadata, skipping")
            continue
        
        print("  Fetching metadata with yt-dlp...")
        details = ytdlp.get_video_details(video_id)
        
        if details:
            metadata = {
                'scheduled_start_time': details.get('scheduled_start_time'),
                'live_status': details.get('live_status'),
                'duration': details.get('duration_string'),
                'view_count': details.get('view_count'),
                'like_count': details.get('like_count'),
                'is_live': details.get('is_live'),
                'was_live': details.get('was_live')
            }
            
            db.update_video_metadata(video_id, metadata)
            
            print(f"  ✅ Updated!")
            if details.get('scheduled_start_time'):
                print(f"     📅 Scheduled: {details['scheduled_start_time']}")
            print(f"     🔴 Status: {details.get('live_status')}")
            if details.get('duration_string'):
                print(f"     ⏱️  Duration: {details['duration_string']}")
        else:
            print("  ❌ Failed to fetch metadata")
        
        # Be nice to YouTube - small delay between requests
        if i < len(videos):
            time.sleep(1)
    
    print("\n" + "=" * 80)
    print("Backfill complete!")

if __name__ == '__main__':
    backfill_all_videos()
