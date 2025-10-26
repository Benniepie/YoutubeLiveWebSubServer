#!/usr/bin/env python3
"""
Show all available fields from yt-dlp for a video
"""
import subprocess
import json
import sys

def show_all_fields(video_id):
    """Fetch and display ALL fields from yt-dlp"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    print(f"Fetching metadata for: {video_id}")
    print("=" * 80)
    
    try:
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-download', url],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return
        
        data = json.loads(result.stdout)
        
        # Group fields by category
        basic_info = [
            'id', 'title', 'description', 'channel', 'channel_id', 'uploader', 
            'uploader_id', 'uploader_url', 'upload_date', 'timestamp'
        ]
        
        live_fields = [
            'is_live', 'was_live', 'live_status', 'release_timestamp', 
            'release_date', 'start_time', 'end_time'
        ]
        
        duration_fields = [
            'duration', 'duration_string'
        ]
        
        stats_fields = [
            'view_count', 'like_count', 'comment_count', 'repost_count',
            'average_rating', 'concurrent_viewers'
        ]
        
        media_fields = [
            'thumbnail', 'thumbnails', 'width', 'height', 'resolution',
            'fps', 'vcodec', 'acodec', 'ext', 'format', 'format_id'
        ]
        
        metadata_fields = [
            'categories', 'tags', 'availability', 'age_limit', 'webpage_url',
            'original_url', 'webpage_url_basename', 'webpage_url_domain'
        ]
        
        def print_section(title, fields):
            print(f"\n{title}")
            print("-" * 80)
            for field in fields:
                if field in data:
                    value = data[field]
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    elif isinstance(value, list) and len(value) > 5:
                        value = value[:5] + ["..."]
                    print(f"  {field}: {value}")
        
        print_section("📺 BASIC INFO", basic_info)
        print_section("🔴 LIVE STREAMING", live_fields)
        print_section("⏱️  DURATION", duration_fields)
        print_section("📊 STATISTICS", stats_fields)
        print_section("🎬 MEDIA INFO", media_fields)
        print_section("🏷️  METADATA", metadata_fields)
        
        # Show all other fields not in categories
        print("\n🔍 OTHER FIELDS")
        print("-" * 80)
        all_categorized = set(basic_info + live_fields + duration_fields + 
                             stats_fields + media_fields + metadata_fields)
        other_fields = [k for k in data.keys() if k not in all_categorized]
        
        for field in sorted(other_fields):
            value = data[field]
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            elif isinstance(value, (list, dict)) and len(str(value)) > 100:
                value = str(value)[:100] + "..."
            print(f"  {field}: {value}")
        
        print("\n" + "=" * 80)
        print(f"Total fields available: {len(data)}")
        
        # Save full JSON for inspection
        output_file = f"{video_id}_full_metadata.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Full metadata saved to: {output_file}")
        
    except subprocess.TimeoutExpired:
        print("Timeout fetching metadata")
    except FileNotFoundError:
        print("yt-dlp not installed! Install with: pip install yt-dlp")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python show_ytdlp_fields.py <video_id>")
        print("Example: python show_ytdlp_fields.py qERQN8Ven2A")
        sys.exit(1)
    
    video_id = sys.argv[1]
    show_all_fields(video_id)
