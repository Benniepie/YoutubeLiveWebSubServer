"""
Notification modules for different platforms
"""
import os
import requests
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

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
