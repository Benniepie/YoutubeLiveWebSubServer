import re
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Map Flair Keys to Environment Variables for Reddit IDs
REDDIT_FLAIR_ENV_MAP = {
    "ORANGE_HITS":  "REDDIT_FLAIR_ID_HITS",
    "GREEN_AID":    "REDDIT_FLAIR_ID_AID",
    "BLUE_MAP":     "REDDIT_FLAIR_ID_MAP",
    "PINK_GEO":     "REDDIT_FLAIR_ID_GEO",
    "RED_BREAKING": "REDDIT_FLAIR_ID_BREAKING",
    "YELLOW_EXTRA": "REDDIT_FLAIR_ID_EXTRA",
}

# Map Flair Keys to Category Hashtags
CATEGORY_HASHTAGS = {
    "ORANGE_HITS":  "#HitsAndLosses",
    "GREEN_AID":    "#MilitaryAid",
    "BLUE_MAP":     "#FrontLineMap",
    "PINK_GEO":     "#Geopolitics",
    "RED_BREAKING": "#BreakingNews",
    "YELLOW_EXTRA": "#UpdateExtra",
}

def get_reddit_flair_id(flair_key: Optional[str]) -> Optional[str]:
    if not flair_key:
        return os.environ.get("REDDIT_FLAIR_ID_DEFAULT")
    env_var = REDDIT_FLAIR_ENV_MAP.get(flair_key)
    if env_var:
        return os.environ.get(env_var)
    return None

def extract_hashtags(description: str, max_count: int = 5) -> List[str]:
    """Extract hashtags from description."""
    if not description:
        return []
    # Find all hashtags
    tags = re.findall(r'#\w+', description)
    # Return unique tags, preserving order, up to max_count
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique_tags.append(tag)
            if len(unique_tags) >= max_count:
                break
    return unique_tags

def format_duration_until(target_time_str: str) -> str:
    """Calculate minutes until scheduled time."""
    try:
        target = datetime.fromisoformat(target_time_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = target - now
        minutes = int(diff.total_seconds() / 60)
        if minutes < 0:
            return "Started"
        
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"
    except:
        return "Soon"

def build_post_content(platform: str, video_data: Dict, flair_key: Optional[str]) -> Dict:
    """
    Build the content string and other metadata for a post.
    Returns a dict with 'content', 'title', 'flair_id', etc.
    """
    title = video_data.get('title', '')
    url = video_data.get('video_url', '')
    description = video_data.get('description', '')
    is_live = video_data.get('is_live_stream', False)
    scheduled_start = video_data.get('scheduled_start_time')
    
    # 1. Hashtags
    hashtags = extract_hashtags(description, max_count=5)
    
    # Add Category Hashtag
    if flair_key and flair_key in CATEGORY_HASHTAGS:
        hashtags.append(CATEGORY_HASHTAGS[flair_key])
        
    # Add Live Hashtag
    if is_live:
        hashtags.append("#livestream")
        
    hashtag_str = " ".join(hashtags)
    
    # 2. Base Content Construction
    content_parts = []
    
    # Header / Title
    if is_live and scheduled_start:
        time_until = format_duration_until(scheduled_start)
        # Convert scheduled time to readable (simple)
        try:
            dt = datetime.fromisoformat(scheduled_start.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d %H:%M UTC')
        except:
            date_str = scheduled_start
            
        content_parts.append(f"🔴 LIVE STREAM: {title}")
        content_parts.append(f"📅 {date_str} (Starts in {time_until})")
    else:
        content_parts.append(f"New Video: {title}")

    # Description (Optional per platform, user requested hashtags mostly)
    # User said: "populate a #hashtag in Instagram, X, Blue Sky, Facebook, Threads, Telegram"
    # And "capture the #hashtags from the video description... included at the end"
    
    # 3. Platform Specifics
    
    if platform == 'reddit':
        # Reddit uses title and url separately. Content is description.
        # User said: "post content should contain the text of the video description"
        return {
            'title': title,
            'content': description, # Full description for Reddit
            'url': url,
            'flair_id': get_reddit_flair_id(flair_key)
        }
        
    elif platform == 'twitter': # X
        # Two tweets.
        # Tweet 1: Title + Image (handled by notifier) + Hashtags (if space)
        # Tweet 2: URL
        # User said: "option to overlflow into the 2nd Tweet" for hashtags.
        # For simplicity, we'll put hashtags in Tweet 1 if short, else Tweet 2.
        
        tweet1 = f"{content_parts[0]}" # Just Title/Header
        if is_live and len(content_parts) > 1:
             tweet1 += f"\n{content_parts[1]}" # Add schedule info
             
        tweet2 = f"{url}"
        
        # Try adding hashtags to Tweet 1
        if len(tweet1) + len(hashtag_str) < 270: # Conservative limit
            tweet1 += f"\n\n{hashtag_str}"
        else:
            tweet2 += f"\n\n{hashtag_str}"
            
        return {
            'tweet1': tweet1,
            'tweet2': tweet2
        }
        
    elif platform == 'threads':
        # 5 hashtags 1 topic tag. Topic tag is usually a tag without # in API, 
        # but Postiz might just take text. User said "populate 'topic_tags': 'video_category'".
        # We'll return the content string and the topic tag separately.
        
        full_text = "\n".join(content_parts)
        full_text += f"\n{url}"
        full_text += f"\n\n{hashtag_str}"
        
        topic_tag = None
        if flair_key:
            # Map flair key to a clean topic tag (e.g. "Geopolitics" instead of "#Geopolitics")
            topic_tag = CATEGORY_HASHTAGS.get(flair_key, "").replace("#", "")
            
        return {
            'content': full_text,
            'topic_tag': topic_tag
        }
        
    else: # Facebook, Instagram, Telegram, Blue Sky
        # Standard format: Header + URL (except IG) + Hashtags
        
        full_text = "\n".join(content_parts)
        
        if platform != 'instagram':
            full_text += f"\n{url}"
        else:
            full_text += "\nlink in bio"
            
        full_text += f"\n\n{hashtag_str}"
        
        return {'content': full_text}
