"""
Telegram notification support
Sends all WebSub events to Telegram for monitoring
"""
import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TelegramNotifier:
    """Send notifications via Telegram bot"""
    
    def __init__(self, use_test_bot: bool = False):
        """
        Initialize Telegram notifier
        
        Args:
            use_test_bot: If True, use test bot credentials instead of production
        """
        if use_test_bot:
            self.bot_token = os.getenv('TELEGRAM_TEST_BOT_TOKEN')
            self.chat_id = os.getenv('TELEGRAM_TEST_CHAT_ID')
            self.bot_name = "Test Bot"
        else:
            self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
            self.bot_name = "Production Bot"
        
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> Dict:
        """
        Send a text message to Telegram
        
        Args:
            text: Message text (supports HTML formatting)
            parse_mode: 'HTML' or 'Markdown'
        
        Returns:
            dict with 'success' and 'response' or 'error'
        """
        if not self.enabled:
            return {'success': False, 'error': f'{self.bot_name} not configured'}
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': parse_mode,
                    'disable_web_page_preview': False
                },
                timeout=10
            )
            response.raise_for_status()
            
            return {'success': True, 'response': response.json()}
            
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            return {'success': False, 'error': f'{str(e)} - {error_detail}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_debug(self, step: str, status: str, details: str = None) -> Dict:
        """
        Send a debug message (for production bot monitoring)
        
        Args:
            step: What step is happening (e.g., "Fetching metadata", "Checking rules")
            status: Status emoji/text (e.g., "✅", "❌", "⏳")
            details: Optional additional details
        
        Returns:
            dict with 'success' and 'response' or 'error'
        """
        if not self.enabled:
            return {'success': False, 'error': f'{self.bot_name} not configured'}
        
        message = f"{status} <b>{step}</b>"
        if details:
            message += f"\n<code>{details}</code>"
        
        return self.send_message(message)
    
    def send_photo(self, photo_url: str, caption: str, parse_mode: str = 'HTML') -> Dict:
        """
        Send a photo with caption to Telegram
        
        Args:
            photo_url: URL of the photo
            caption: Caption text (supports HTML formatting)
            parse_mode: 'HTML' or 'Markdown'
        
        Returns:
            dict with 'success' and 'response' or 'error'
        """
        if not self.enabled:
            return {'success': False, 'error': f'{self.bot_name} not configured'}
        
        try:
            response = requests.post(
                f"{self.api_url}/sendPhoto",
                json={
                    'chat_id': self.chat_id,
                    'photo': photo_url,
                    'caption': caption,
                    'parse_mode': parse_mode
                },
                timeout=10
            )
            response.raise_for_status()
            
            return {'success': True, 'response': response.json()}
            
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            return {'success': False, 'error': f'{str(e)} - {error_detail}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_video_notification(self, video_data: Dict, event_type: str, live_status: str = None) -> Dict:
        """
        Send a formatted video notification with thumbnail
        
        Args:
            video_data: Video information
            event_type: Type of event (video_published, live_started, etc.)
            live_status: Live status if available
        """
        if not self.enabled:
            return {'success': False, 'error': f'{self.bot_name} not configured'}
        
        # Format the message
        title = video_data.get('title', 'Unknown')
        video_url = video_data.get('video_url', '')
        video_id = video_data.get('video_id', '')
        author = video_data.get('author_name', 'Unknown')
        
        # Event type emoji
        event_emoji = {
            'video_published': '📹',
            'live_scheduled': '📅',
            'live_started': '🔴',
            'live_ended': '⏹️',
            'video_updated': '🔄'
        }.get(event_type, '📺')
        
        # Live status emoji
        status_emoji = {
            'is_live': '🔴 LIVE',
            'is_upcoming': '📅 SCHEDULED',
            'was_live': '📼 ENDED',
            'not_live': '📹 VIDEO'
        }.get(live_status, '')
        
        # Build caption
        caption = f"{event_emoji} <b>{event_type.replace('_', ' ').title()}</b>\n\n"
        caption += f"<b>{title}</b>\n\n"
        
        if status_emoji:
            caption += f"{status_emoji}\n"
        
        caption += f"👤 {author}\n"
        caption += f"🔗 <a href='{video_url}'>Watch Video</a>"
        
        # Get thumbnail URL
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        # Send photo with caption
        return self.send_photo(thumbnail_url, caption)


# Test function
if __name__ == '__main__':
    import sys
    
    # Test both bots
    print("Testing Telegram Notifiers\n" + "="*50)
    
    # Test production bot
    print("\n1. Testing Production Bot:")
    prod_bot = TelegramNotifier(use_test_bot=False)
    if prod_bot.enabled:
        result = prod_bot.send_message("✅ <b>Production bot test</b>\n\nThis is a test message from your WebSub server!")
        print(f"   Result: {'Success' if result['success'] else 'Failed'}")
        if not result['success']:
            print(f"   Error: {result['error']}")
    else:
        print("   ❌ Production bot not configured")
    
    # Test test bot
    print("\n2. Testing Test Bot:")
    test_bot = TelegramNotifier(use_test_bot=True)
    if test_bot.enabled:
        result = test_bot.send_message("✅ <b>Test bot test</b>\n\nThis is a test message from your WebSub server!")
        print(f"   Result: {'Success' if result['success'] else 'Failed'}")
        if not result['success']:
            print(f"   Error: {result['error']}")
    else:
        print("   ❌ Test bot not configured")
    
    print("\n" + "="*50)
    print("Check your Telegram for messages!")
