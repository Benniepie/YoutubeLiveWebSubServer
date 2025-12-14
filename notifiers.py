"""
Notification modules for different platforms
"""
import os
import requests
from typing import Dict, Optional
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv
import image_utils
import post_templates

# Load environment variables
load_dotenv(override=True)

class DiscordNotifier:
    """Send notifications to Discord via webhook or bot"""
    
    def __init__(self, bot_token: Optional[str] = None, webhook_url: Optional[str] = None):
        self.bot_token = bot_token or os.environ.get('DISCORD_BOT_TOKEN')
        self.webhook_url = webhook_url or os.environ.get('DISCORD_WEBHOOK_URL')
        self.channel_id = os.environ.get('DISCORD_CHANNEL_ID')
    
    def send_notification(self, video_data: Dict, notification_type: str, message_data: Dict = None) -> Dict:
        """
        Send a notification to Discord
        
        Args:
            video_data: Video information
            notification_type: Type of notification (for tracking)
            message_data: Pre-formatted message with 'content' and 'embeds'
        
        Returns: {'success': bool, 'response': dict, 'error': str}
        """
        # Use pre-formatted message if provided, otherwise create embed
        if message_data:
            payload = message_data
        else:
            # Fallback to old embed creation
            embed = self._create_embed(video_data, notification_type)
            payload = {'embeds': [embed]}
        
        # Use webhook if available (simpler), otherwise use bot
        if self.webhook_url:
            return self._send_via_webhook_raw(payload, notification_type)
        elif self.bot_token and self.channel_id:
            return self._send_via_bot_raw(payload, notification_type)
        else:
            return {
                'success': False,
                'error': 'No Discord credentials configured'
            }
    
    def _send_via_webhook_raw(self, payload: Dict, notification_type: str) -> Dict:
        """Send notification via Discord webhook"""
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return {
                'success': True,
                'response': {
                    'status_code': response.status_code,
                    'notification_type': notification_type
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_via_bot_raw(self, payload: Dict, notification_type: str) -> Dict:
        """Send notification via Discord bot"""
        url = f"https://discord.com/api/v10/channels/{self.channel_id}/messages"
        headers = {
            'Authorization': f'Bot {self.bot_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {
                'success': True,
                'response': {
                    **response.json(),
                    'notification_type': notification_type
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_embed(self, video_data: Dict, event_type: str) -> Dict:
        """Create a Discord embed for the notification"""
        
        # Determine color and title based on event type
        color_map = {
            'live_scheduled': 0x00FF00,  # Green
            'live_started': 0xFF0000,     # Red (LIVE!)
            'live_ongoing': 0xFF6600,     # Orange
            'live_ended': 0x808080,       # Gray
            'live_archived': 0x0099FF,    # Blue
            'video_published': 0x0099FF,  # Blue
            'video_updated': 0xFFFF00     # Yellow
        }
        
        title_prefix_map = {
            'live_scheduled': '📅 Live Stream Scheduled',
            'live_started': '🔴 LIVE NOW',
            'live_ongoing': '🔴 LIVE',
            'live_ended': '⏹️ Live Stream Ended',
            'live_archived': '📼 Live Stream Archived',
            'video_published': '🎬 New Video',
            'video_updated': '🔄 Video Updated'
        }
        
        color = color_map.get(event_type, 0x0099FF)
        title_prefix = title_prefix_map.get(event_type, '📺')
        
        fields = [
            {
                'name': 'Channel',
                'value': video_data.get('author_name', 'Unknown'),
                'inline': True
            },
            {
                'name': 'Event Type',
                'value': event_type.replace('_', ' ').title(),
                'inline': True
            }
        ]
        
        # Add scheduled time if available
        if video_data.get('scheduled_start_time'):
            fields.append({
                'name': '📅 Scheduled Start',
                'value': video_data['scheduled_start_time'],
                'inline': False
            })
        
        embed = {
            'title': f"{title_prefix}: {video_data['title']}",
            'url': video_data['video_url'],
            'color': color,
            'fields': fields,
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {
                'text': 'YouTube WebSub Notification'
            }
        }
        
        # Add thumbnail if available
        # YouTube thumbnail URL format
        thumbnail_url = f"https://img.youtube.com/vi/{video_data['video_id']}/maxresdefault.jpg"
        embed['thumbnail'] = {'url': thumbnail_url}
        
        return embed


class WhatsAppNotifier:
    """Send notifications to WhatsApp (placeholder for now)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('WHATSAPP_API_KEY')
        # You'll need to set up WhatsApp Business API or use a service like Twilio
    
    def send_notification(self, video_data: Dict, event_type: str) -> Dict:
        """Send notification to WhatsApp group"""
        # TODO: Implement WhatsApp notification
        # Options:
        # 1. Twilio API for WhatsApp
        # 2. WhatsApp Business API
        # 3. Third-party service like MessageBird
        
        return {
            'success': False,
            'error': 'WhatsApp integration not yet implemented'
        }


class FacebookNotifier:
    """Send notifications to Facebook Business Page"""
    
    def __init__(self, page_access_token: Optional[str] = None, page_id: Optional[str] = None):
        self.page_access_token = page_access_token or os.environ.get('FB_PAGE_ACCESS_TOKEN')
        self.page_id = page_id or os.environ.get('FB_PAGE_ID')
    
    def send_notification(self, video_data: Dict, event_type: str) -> Dict:
        """Post to Facebook Business Page"""
        if not self.page_access_token or not self.page_id:
            return {
                'success': False,
                'error': 'Facebook credentials not configured'
            }
        
        message = self._create_message(video_data, event_type)
        
        url = f"https://graph.facebook.com/v18.0/{self.page_id}/feed"
        params = {
            'access_token': self.page_access_token,
            'message': message,
            'link': video_data['video_url']
        }
        
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            return {
                'success': True,
                'response': response.json()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_message(self, video_data: Dict, event_type: str) -> str:
        """Create a message for Facebook post"""
        emoji_map = {
            'live_scheduled': '📅',
            'live_started': '🔴 LIVE NOW',
            'live_ongoing': '🔴',
            'live_ended': '⏹️',
            'live_archived': '📼',
            'video_published': '🎬',
            'video_updated': '🔄'
        }
        
        emoji = emoji_map.get(event_type, '📺')
        
        return f"{emoji} {video_data['title']}\n\nWatch now: {video_data['video_url']}"


class EmailNotifier:
    """Send email notifications (placeholder for Ghost integration)"""
    
    def __init__(self, ghost_api_key: Optional[str] = None, ghost_url: Optional[str] = None):
        self.ghost_api_key = ghost_api_key or os.environ.get('GHOST_API_KEY')
        self.ghost_url = ghost_url or os.environ.get('GHOST_URL')
    
    def send_notification(self, video_data: Dict, event_type: str) -> Dict:
        """Send email via Ghost"""
        # TODO: Implement Ghost email integration
        # Ghost has a Members API that can be used to send emails
        
        return {
            'success': False,
            'error': 'Email/Ghost integration not yet implemented'
        }


class PostizNotifier:
    """Send notifications to Postiz (multi-platform social media manager)"""

    def __init__(self):
        self.api_base = os.environ.get('POSTIZ_API_BASE')
        self.api_key = os.environ.get('POSTIZ_API_KEY')
        self.api_type = os.environ.get('POSTIZ_API_TYPE', 'schedule')
        self.api_date = os.environ.get('POSTIZ_API_DATE')
        
        # Enabled platforms
        self.platforms = {
            'facebook': os.environ.get('POSTIZ_FACEBOOK', 'false').lower() == 'true',
            'telegram': os.environ.get('POSTIZ_TELEGRAM', 'false').lower() == 'true',
            'instagram': os.environ.get('POSTIZ_INSTAGRAM', 'false').lower() == 'true',
            'bluesky': os.environ.get('POSTIZ_BLUESKY', 'false').lower() == 'true',
            'x': os.environ.get('POSTIZ_X', 'false').lower() == 'true',
            'threads': os.environ.get('POSTIZ_THREADS', 'false').lower() == 'true',
            'reddit': os.environ.get('POSTIZ_REDDIT', 'false').lower() == 'true'
        }
        
        self._integrations_map = {
            'bluesky': os.environ.get('POSTIZ_API_ID_BLUESKY'),
            'facebook': os.environ.get('POSTIZ_API_ID_FACEBOOK'),
            'instagram': os.environ.get('POSTIZ_API_ID_INSTAGRAM'),
            'telegram': os.environ.get('POSTIZ_API_ID_TELEGRAM'),
            'threads': os.environ.get('POSTIZ_API_ID_THREADS'),
            'x': os.environ.get('POSTIZ_API_ID_X'),
            'reddit': os.environ.get('POSTIZ_API_ID_REDDIT')
        }
        # Remove None values
        self._integrations_map = {k: v for k, v in self._integrations_map.items() if v}

    def _get_integrations(self) -> Dict[str, str]:
        """Fetch and cache integrations map: {identifier: id}"""
        # If we have all enabled platforms in our map (from env), we don't need to fetch
        enabled_platforms = [p for p, enabled in self.platforms.items() if enabled]
        missing_platforms = [p for p in enabled_platforms if p not in self._integrations_map]
        
        if not missing_platforms:
            return self._integrations_map

        url = f"{self.api_base}/integrations"
        headers = {
            'Authorization': f'{self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Map identifier to ID (e.g., 'facebook' -> 'integration-id')
            # Only update if not already set via env
            for item in data:
                ident = item['identifier']
                # Handle instagram-standalone mapping to instagram if needed
                if ident == 'instagram-standalone' and 'instagram' not in self._integrations_map:
                     self._integrations_map['instagram'] = item['id']
                elif ident not in self._integrations_map:
                    self._integrations_map[ident] = item['id']
            
            return self._integrations_map
        except Exception as e:
            print(f"Error fetching Postiz integrations: {e}")
            return self._integrations_map

    def _upload_file_from_url(self, file_url: str) -> Optional[Dict]:
        """Upload a file from URL to Postiz and return file object {id, path}"""
        url = f"{self.api_base}/upload-from-url"
        headers = {
            'Authorization': f'{self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json={'url': file_url}, headers=headers)
            response.raise_for_status()
            return response.json() # Returns {id, path, ...}
        except Exception as e:
            print(f"Error uploading file from URL to Postiz: {e}")
            return None

    def _upload_file_bytes(self, file_bytes: BytesIO, filename: str) -> Optional[Dict]:
        """Upload a file from memory to Postiz."""
        url = f"{self.api_base}/upload"
        headers = {
            'Authorization': f'{self.api_key}'
        }
        
        file_bytes.seek(0)
        files = {
            'file': (filename, file_bytes, 'image/jpeg')
        }
        
        try:
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()
            return response.json() # Returns {id, path, ...}
        except Exception as e:
            print(f"Error uploading bytes to Postiz: {e}")
            return None

    def send_notification(self, video_data: Dict) -> Dict:
        """
        Send notifications to all enabled platforms via Postiz.
        Returns a summary of results.
        """
        if not self.api_base or not self.api_key:
            return {'success': False, 'error': 'Postiz configuration missing'}

        # Fetch integrations first
        integrations = self._get_integrations()
        if not integrations:
            return {'success': False, 'error': 'Could not fetch Postiz integrations'}

        results = {}
        
        # Determine schedule date
        schedule_date = self.api_date
        if not schedule_date:
            schedule_date = video_data.get('published_time')
        
        # --- Image Processing ---
        thumbnail_url = f"https://img.youtube.com/vi/{video_data['video_id']}/maxresdefault.jpg"
        
        # Download Original
        original_bytes = image_utils.download_image(thumbnail_url)
        
        flair_key = None
        original_image_obj = None
        ig_image_obj = None
        
        if original_bytes:
            # Detect Flair
            flair_key = image_utils.detect_flair_from_image(original_bytes)
            
            # Upload Original (for FB, X, Bluesky)
            # Only needed if FB, X, or Bluesky are enabled
            if self.platforms['facebook'] or self.platforms['x'] or self.platforms['bluesky']:
                original_image_obj = self._upload_file_bytes(original_bytes, "thumbnail.jpg")
            
            # Create & Upload IG Thumbnail (for Instagram)
            if self.platforms['instagram']:
                ig_bytes = image_utils.create_instagram_thumbnail(original_bytes)
                if ig_bytes:
                    ig_image_obj = self._upload_file_bytes(ig_bytes, "ig_thumbnail.jpg")
        else:
            # Fallback: Upload from URL if download failed
            print("Warning: Failed to download thumbnail. Using URL fallback (no flair/IG resize).")
            if self.platforms['facebook'] or self.platforms['x'] or self.platforms['bluesky']:
                original_image_obj = self._upload_file_from_url(thumbnail_url)

        # Common headers
        headers = {
            'Authorization': f'{self.api_key}',
            'Content-Type': 'application/json'
        }

        # 1. Facebook
        if self.platforms['facebook']:
            if 'facebook' in integrations:
                results['facebook'] = self._post_facebook(
                    video_data, headers, schedule_date, integrations['facebook'], flair_key, original_image_obj
                )
            else:
                results['facebook'] = {'success': False, 'error': 'No Facebook integration found'}

        # 2. Telegram
        if self.platforms['telegram']:
            if 'telegram' in integrations:
                results['telegram'] = self._post_telegram(
                    video_data, headers, schedule_date, integrations['telegram'], flair_key
                )
            else:
                results['telegram'] = {'success': False, 'error': 'No Telegram integration found'}

        # 3. Instagram
        if self.platforms['instagram']:
            # Check for 'instagram' or 'instagram-standalone'
            ig_id = integrations.get('instagram') or integrations.get('instagram-standalone')
            if ig_id:
                results['instagram'] = self._post_instagram(
                    video_data, headers, schedule_date, ig_id, flair_key, ig_image_obj
                )
            else:
                results['instagram'] = {'success': False, 'error': 'No Instagram integration found'}

        # 4. Blue Sky
        if self.platforms['bluesky']:
            if 'bluesky' in integrations:
                results['bluesky'] = self._post_bluesky(
                    video_data, headers, schedule_date, integrations['bluesky'], flair_key, original_image_obj
                )
            else:
                results['bluesky'] = {'success': False, 'error': 'No Blue Sky integration found'}

        # 5. X (Twitter)
        if self.platforms['x']:
            if 'x' in integrations:
                results['x'] = self._post_x(
                    video_data, headers, schedule_date, integrations['x'], flair_key, original_image_obj
                )
            else:
                results['x'] = {'success': False, 'error': 'No X integration found'}

        # 6. Threads
        if self.platforms['threads']:
            if 'threads' in integrations:
                results['threads'] = self._post_threads(
                    video_data, headers, schedule_date, integrations['threads'], flair_key
                )
            else:
                results['threads'] = {'success': False, 'error': 'No Threads integration found'}

        # 7. Reddit
        if self.platforms['reddit']:
            if 'reddit' in integrations:
                results['reddit'] = self._post_reddit(
                    video_data, headers, schedule_date, integrations['reddit'], flair_key
                )
            else:
                results['reddit'] = {'success': False, 'error': 'No Reddit integration found'}

        return results

    def _post_facebook(self, video_data: Dict, headers: Dict, schedule_date: str, integration_id: str, flair_key: Optional[str], image: Optional[Dict]) -> Dict:
        content_data = post_templates.build_post_content('facebook', video_data, flair_key)
        
        payload = {
            "type": self.api_type,
            "date": schedule_date,
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": { "id": integration_id },
                    "value": [
                        {
                            "content": content_data['content'],
                            "image": [] # Facebook Link Post doesn't use image array usually, it scrapes URL. But user asked for image?
                            # User originally asked for "Post with link" which scrapes.
                            # If we want to force an image, we'd use "Post with image".
                            # But user requirement: "Post 'A new video...' with the YouTube video URL in the url parameter."
                            # So we stick to Link Post. Image obj is unused here but passed for consistency.
                        }
                    ],
                    "settings": {
                        "__type": "facebook",
                        "url": video_data['video_url']
                    }
                }
            ]
        }
        return self._send_request(payload, headers, "facebook")

    def _post_telegram(self, video_data: Dict, headers: Dict, schedule_date: str, integration_id: str, flair_key: Optional[str]) -> Dict:
        content_data = post_templates.build_post_content('telegram', video_data, flair_key)
        
        # No image for Telegram (Link Preview)
        payload = {
            "type": self.api_type,
            "date": schedule_date,
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": { "id": integration_id },
                    "value": [
                        {
                            "content": content_data['content'],
                            "image": []
                        }
                    ],
                    "settings": {
                        "__type": "telegram"
                    }
                }
            ]
        }
        return self._send_request(payload, headers, "telegram")

    def _post_instagram(self, video_data: Dict, headers: Dict, schedule_date: str, integration_id: str, flair_key: Optional[str], image: Optional[Dict]) -> Dict:
        content_data = post_templates.build_post_content('instagram', video_data, flair_key)
        
        image_data = []
        if image:
            image_data = [{"id": image['id'], "path": image['path']}]
            
        payload = {
            "type": self.api_type,
            "date": schedule_date,
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": { "id": integration_id },
                    "value": [
                        {
                            "content": content_data['content'],
                            "image": image_data
                        }
                    ],
                    "settings": {
                        "__type": "instagram",
                        "post_type": "post",
                        "collaborators": []
                    }
                }
            ]
        }
        return self._send_request(payload, headers, "instagram")

    def _post_bluesky(self, video_data: Dict, headers: Dict, schedule_date: str, integration_id: str, flair_key: Optional[str], image: Optional[Dict]) -> Dict:
        content_data = post_templates.build_post_content('bluesky', video_data, flair_key)
        
        image_data = []
        if image:
            image_data = [{"id": image['id'], "path": image['path']}]
        
        payload = {
            "type": self.api_type,
            "date": schedule_date,
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": { "id": integration_id },
                    "value": [
                        {
                            "content": content_data['content'],
                            "image": image_data
                        }
                    ],
                    "settings": {
                        "__type": "bluesky"
                    }
                }
            ]
        }
        return self._send_request(payload, headers, "bluesky")

    def _post_x(self, video_data: Dict, headers: Dict, schedule_date: str, integration_id: str, flair_key: Optional[str], image: Optional[Dict]) -> Dict:
        content_data = post_templates.build_post_content('twitter', video_data, flair_key)
        
        image_data = []
        if image:
            image_data = [{"id": image['id'], "path": image['path']}]

        payload = {
            "type": self.api_type,
            "date": schedule_date,
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": { "id": integration_id },
                    "value": [
                        {
                            "content": content_data['tweet1'],
                            "image": image_data
                        },
                        {
                            "content": content_data['tweet2'],
                            "image": []
                        }
                    ],
                    "settings": {
                        "__type": "x",
                        "who_can_reply_post": "everyone"
                    }
                }
            ]
        }
        return self._send_request(payload, headers, "x")

    def _post_threads(self, video_data: Dict, headers: Dict, schedule_date: str, integration_id: str, flair_key: Optional[str]) -> Dict:
        content_data = post_templates.build_post_content('threads', video_data, flair_key)
        
        # No image for Threads (Link Preview)
        payload = {
            "type": self.api_type,
            "date": schedule_date,
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": { "id": integration_id },
                    "value": [
                        {
                            "content": content_data['content'],
                            "image": []
                        }
                    ],
                    "settings": {
                        "__type": "threads"
                    }
                }
            ]
        }
        return self._send_request(payload, headers, "threads")

    def _post_reddit(self, video_data: Dict, headers: Dict, schedule_date: str, integration_id: str, flair_key: Optional[str]) -> Dict:
        content_data = post_templates.build_post_content('reddit', video_data, flair_key)
        
        # Reddit Native Embed
        subreddit_settings = {
            "subreddit": "atpgeo", # Hardcoded per user example, or could be env var? User said "atpgeo" in example.
            "title": content_data['title'],
            "type": "link",
            "url": content_data['url'],
            "is_flair_required": False
        }
        
        if content_data['flair_id']:
            subreddit_settings["is_flair_required"] = True
            subreddit_settings["flair"] = { "id": content_data['flair_id'] }

        payload = {
            "type": self.api_type,
            "date": schedule_date,
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": { "id": integration_id },
                    "value": [
                        {
                            "content": content_data['content'],
                            "image": []
                        }
                    ],
                    "settings": {
                        "__type": "reddit",
                        "subreddit": [
                            {
                                "value": subreddit_settings
                            }
                        ]
                    }
                }
            ]
        }
        return self._send_request(payload, headers, "reddit")

    def _send_request(self, payload: Dict, headers: Dict, platform: str) -> Dict:
        url = f"{self.api_base}/posts"
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {
                'success': True,
                'response': response.json()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

