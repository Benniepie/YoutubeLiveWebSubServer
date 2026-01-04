import os
import requests
import jwt
import datetime as date
from datetime import datetime
import re

import html
import io
import logging
from typing import Dict, Optional, Tuple
import time
import image_utils

# Constants
STOP_LINE = "PLEASE ❤️ LIKE 💬 COMMENT 📣 SHARE"
TAG_MAP = {
    "ORANGE_HITS": "Hits and Losses",
    "GREEN_AID": "Military Aid",
    "BLUE_MAP": "Front Line",
    "PINK_GEO": "Geopolitics",
    "RED_BREAKING": "Breaking News",
    "YELLOW_EXTRA": "Extra"
}

class GhostNotifier:
    """
    Handles posting to Ghost CMS.
    """
    def __init__(self):
        self.api_key = os.getenv("GHOST_ADMIN_API_KEY")
        self.base_url = os.getenv("GHOST_ADMIN_API_BASE_URL", "https://atpgeo.com/ghost/api/admin")
        
        if not self.api_key:
            logging.warning("GHOST_ADMIN_API_KEY not set. Ghost notifications will fail.")

    def _get_token(self) -> str:
        """Generate JWT token for Ghost Admin API"""
        try:
            id, secret = self.api_key.split(':')
        except ValueError:
            raise ValueError("Invalid GHOST_ADMIN_API_KEY format. Expected ID:SECRET")
            
        iat = int(datetime.now().timestamp())
        header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
        payload = {
            'iat': iat,
            'exp': iat + 5 * 60,
            'aud': '/admin/'
        }
        return jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)

    def _get_headers(self) -> Dict[str, str]:
        token = self._get_token()
        return {
            'Authorization': 'Ghost {}'.format(token),
            'Content-Type': 'application/json'
        }

    def _slugify(self, text: str) -> str:
        """Create a slug from text"""
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        text = text.strip('-')
        return text

    def _check_post_exists(self, slug_prefix: str) -> Optional[Dict]:
        """Check if post exists by searching for slug starting with video_id"""
        url = f"{self.base_url}/posts/"
        headers = self._get_headers()
        params = {
            'filter': f"slug:~^'{slug_prefix}'",
            'limit': '1',
            'fields': 'id,slug,updated_at,url'
        }
        try:
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            if data.get('posts'):
                return data['posts'][0]
        except Exception as e:
            logging.error(f"Error checking existing Ghost post: {e}")
        return None

    def _upload_thumbnail(self, video_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Download thumbnail from YouTube and upload to Ghost.
        Returns (ghost_image_url, flair_key).
        """
        thumb_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        img_data = image_utils.download_image(thumb_url)
        
        if not img_data:
            return None, None
        
        # Analyze color
        img_bytes = img_data.getvalue()
        analysis_io = io.BytesIO(img_bytes)
        flair_key = image_utils.detect_flair_from_image(analysis_io)
        
        # Upload
        headers = self._get_headers()
        # Remove Content-Type for multipart upload
        if 'Content-Type' in headers:
            del headers['Content-Type']
            
        url = f"{self.base_url}/images/upload/"
        upload_io = io.BytesIO(img_bytes)
        files = {'file': (f'{video_id}.jpg', upload_io, 'image/jpeg')}
        
        try:
            r = requests.post(url, headers=headers, files=files)
            r.raise_for_status()
            return r.json()['images'][0]['url'], flair_key
        except Exception as e:
            logging.error(f"Error uploading image to Ghost: {e}")
            return None, flair_key

    def send_notification(self, video_data: Dict) -> Dict:
        """
        Create a post on Ghost.
        Input video_data is expected to be a standardized metadata dict (from YouTubeMetadata).
        """
        if not self.api_key:
            return {'success': False, 'error': 'Ghost credentials missing'}

        video_id = video_data['video_id']
        title = video_data['title']
        description = video_data.get('description', '')
        
        # 1. Check if exists
        slug_prefix = video_id.lower()
        existing_post = self._check_post_exists(slug_prefix)
        
        if existing_post:
            return {
                'success': True, 
                'response': {'url': existing_post.get('url'), 'status': 'already_exists'},
                'message': 'Post already exists'
            }

        # 2. Upload Image & Detect Tag
        feature_image_url, flair_key = self._upload_thumbnail(video_id)
        tag_name = TAG_MAP.get(flair_key, "News")
        tagslist = list(tag_name)
        
        # 3. Format Date/Time
        # Logic: If upcoming, add scheduled line.
        is_upcoming = video_data.get('live_status') == 'is_upcoming'
        scheduled_time = video_data.get('scheduled_start_time')
        
        # 4. Content Construction
        desc_intro = description.split(STOP_LINE)[0].strip()
        paragraphs = [p.strip() for p in desc_intro.split('\n\n') if p.strip()]
        
        content_html = ""
        
        # Add Scheduled Notice if upcoming
        if is_upcoming and scheduled_time:
            try:
                # Format: 2025-12-25T15:00:00Z -> readable
                dt = date.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                fmt_time = dt.strftime('%Y-%m-%d %H:%M UTC')
                content_html += f"<p><strong>🔴 LIVE STREAM SCHEDULED FOR {fmt_time}</strong></p>\n"
            except:
                pass

        # Add embed
        embed_url = f"https://www.youtube.com/embed/{video_id}?feature=oembed?ref=atpgeo"
        content_html += (
            f'<figure class="kg-card kg-embed-card kg-card-hascaption">'
            f'<iframe width="200" height="113" src="{embed_url}" frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            f'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen="" title="{html.escape(title)}"></iframe>'
            f'<figcaption><p dir="ltr"><span style="white-space: pre-wrap;"><a href="https://www.youtube.com/watch?v={video_id}?ref=atpgeo">Watch Video on YouTube</a></span></p></figcaption>'
            f'</figure>\n'
        )
        
        # Add Description (First 2 paragraphs)
        for p in paragraphs[:2]:
            content_html += f"<p>{html.escape(p)}</p>\n"

        # 5. Payload Construction
        # Dates
        created_at = datetime.now().isoformat()
        published_at = created_at
        
        # Try to use scheduled time as publish time? 
        # Or just publish now? User said "video published date should be added to created_at and published_at"
        # Since this runs when notification arrives, published_at from YT is appropriate.
        #if video_data.get('published_time'): # API provides publishedAt
            # Ensure ISO format
        published_at = video_data['published_time']
        published_at2 = video_data.get('published_time')
        print(published_at)
        print(published_at2)







        #elif video
        # _data.get('release_timestamp'): # From ytdlp, usually
        #     dt = datetime.fromtimestamp(video_data['release_timestamp'])
        #     published_at = dt.isoformat()
        #     created_at = published_at

        print(published_at)
        # Default to n
        # ow
        #created_at = datetime.now().isoformat()
        #published_at = created_at

        full_slug = f"{video_id}-{self._slugify(title)}"
        custom_excerpt = description[:300] if description else ""

        post_payload = {
            "posts": [
                {
                "title": title,
                "slug": full_slug,
                "tags": [tag_name],
                "lexical": None, 
                "html": content_html,
                "status": "published",
                "visibility": "public",
                "feature_image_alt": "Youtube thumbnail",
                "feature_image_caption": "",
                "custom_excerpt": custom_excerpt,
                "feature_image": feature_image_url,
                "updated_at": None,
                "published_at": published_at,
                "created_at": created_at,
                "authors": [
                    {"id": "1"},
                    {"id": "6666de5fa10c4c5fe1fb9c57"},
                    ],  
                }
            ]
        }

        # 6. Create Post
        url = f"{self.base_url}/posts/"
        params = {
            'source': 'html',
            'formats': 'html'
        }
        headers = self._get_headers()
        print(post_payload)
        print(url)
        print(params)
        print(headers)
        try:
            r = requests.post(url, headers=headers, params=params, json=post_payload)
            r.raise_for_status()
            response_json = r.json()
            return {
                'success': True,
                'response': response_json,
                'url': response_json['posts'][0]['url']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'details': r.text if 'r' in locals() else None
            }
