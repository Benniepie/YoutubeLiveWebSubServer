#!/usr/bin/env python3
"""
Test Discord bot by sending a simple message
"""
import os
import requests
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

def test_discord_bot():
    """Send a test message to Discord"""
    
    bot_token = os.environ.get('DISCORD_BOT_TOKEN')
    channel_id = os.environ.get('DISCORD_CHANNEL_ID')
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    print("Discord Configuration Check")
    print("=" * 80)
    print(f"Bot Token: {'✅ Set' if bot_token else '❌ Not set'}")
    print(f"Channel ID: {'✅ Set' if channel_id else '❌ Not set'}")
    print(f"Webhook URL: {'✅ Set' if webhook_url else '❌ Not set'}")
    print()
    
    # Try webhook first (easier)
    if webhook_url:
        print("Testing with Webhook...")
        print("-" * 80)
        
        payload = {
            'content': '🧪 **Test Message from YouTube WebSub Bot**\n\nIf you can see this, the webhook is working!',
            'embeds': [{
                'title': '✅ Discord Integration Test',
                'description': 'This is a test embed to verify Discord notifications are working.',
                'color': 0x00FF00,
                'fields': [
                    {'name': 'Status', 'value': 'Connected', 'inline': True},
                    {'name': 'Method', 'value': 'Webhook', 'inline': True}
                ]
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            print("✅ Webhook test successful!")
            print(f"   Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ Webhook test failed: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
    
    # Try bot if webhook not available
    elif bot_token and channel_id:
        print("Testing with Bot...")
        print("-" * 80)
        
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            'Authorization': f'Bot {bot_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'content': '🧪 **Test Message from YouTube WebSub Bot**\n\nIf you can see this, the bot is working!',
            'embeds': [{
                'title': '✅ Discord Integration Test',
                'description': 'This is a test embed to verify Discord notifications are working.',
                'color': 0x00FF00,
                'fields': [
                    {'name': 'Status', 'value': 'Connected', 'inline': True},
                    {'name': 'Method', 'value': 'Bot', 'inline': True}
                ]
            }]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            print("✅ Bot test successful!")
            print(f"   Status: {response.status_code}")
            print(f"   Message ID: {response.json().get('id')}")
            return True
        except Exception as e:
            print(f"❌ Bot test failed: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Status: {e.response.status_code}")
                print(f"   Response: {e.response.text}")
                
                # Common errors
                if e.response.status_code == 401:
                    print("\n💡 Error 401: Invalid bot token")
                elif e.response.status_code == 403:
                    print("\n💡 Error 403: Bot doesn't have permission to send messages")
                    print("   Make sure the bot has 'Send Messages' and 'Embed Links' permissions")
                elif e.response.status_code == 404:
                    print("\n💡 Error 404: Channel not found")
                    print("   Check that the channel ID is correct and the bot is in the server")
    else:
        print("❌ No Discord credentials configured!")
        print("\nPlease add to your .env file:")
        print("\nOption 1 - Webhook (easier):")
        print("  DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...")
        print("\nOption 2 - Bot:")
        print("  DISCORD_BOT_TOKEN=your_bot_token")
        print("  DISCORD_CHANNEL_ID=your_channel_id")
        return False

def test_live_stream_notification():
    """Test a live stream notification"""
    from notifiers import DiscordNotifier
    
    print("\n" + "=" * 80)
    print("Testing Live Stream Notification")
    print("=" * 80)
    
    discord = DiscordNotifier()
    
    # Sample live stream data
    video_data = {
        'video_id': 'TEST123',
        'title': 'BREAKING LIVE: Test Live Stream Notification',
        'video_url': 'https://www.youtube.com/watch?v=TEST123',
        'author_name': 'Example Channel',
        'scheduled_start_time': '2025-10-23T20:00:00Z'
    }
    
    result = discord.send_notification(video_data, 'live_scheduled')
    
    if result['success']:
        print("✅ Live stream notification sent successfully!")
    else:
        print(f"❌ Failed to send notification: {result.get('error')}")

if __name__ == '__main__':
    print("\n🤖 Discord Bot Test\n")
    
    success = test_discord_bot()
    
    if success:
        print("\n" + "=" * 80)
        print("Would you like to test a live stream notification? (y/n)")
        response = input("> ").strip().lower()
        if response == 'y':
            test_live_stream_notification()
    
    print("\n" + "=" * 80)
    print("Test complete!")
