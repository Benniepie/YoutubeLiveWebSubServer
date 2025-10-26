#!/usr/bin/env python3
"""
Interactive Discord setup script
"""
import os

def setup_discord():
    """Interactive setup for Discord credentials"""
    
    print("=" * 80)
    print("Discord Setup Wizard")
    print("=" * 80)
    print()
    print("Choose your method:")
    print("1. Bot (more control, requires token + channel ID)")
    print("2. Webhook (easier, just one URL)")
    print()
    
    choice = input("Enter 1 or 2: ").strip()
    
    env_lines = []
    
    # Read existing .env
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_lines = f.readlines()
    
    # Remove old Discord config
    env_lines = [line for line in env_lines if not line.startswith('DISCORD_')]
    
    if choice == '1':
        print("\n" + "=" * 80)
        print("Bot Setup")
        print("=" * 80)
        print()
        print("1. Go to: https://discord.com/developers/applications")
        print("2. Click on your application")
        print("3. Click: Bot → Reset Token")
        print()
        
        token = input("Paste your bot token: ").strip()
        
        print()
        print("Now get your channel ID:")
        print("1. In Discord: Settings → Advanced → Enable Developer Mode")
        print("2. Right-click your channel → Copy Channel ID")
        print()
        
        channel_id = input("Paste your channel ID: ").strip()
        
        # Add to .env
        env_lines.append('\n# Discord Bot Configuration\n')
        env_lines.append(f'DISCORD_BOT_TOKEN={token}\n')
        env_lines.append(f'DISCORD_CHANNEL_ID={channel_id}\n')
        
        print("\n✅ Bot credentials saved to .env")
        
    elif choice == '2':
        print("\n" + "=" * 80)
        print("Webhook Setup")
        print("=" * 80)
        print()
        print("1. In Discord, right-click your channel")
        print("2. Edit Channel → Integrations → Webhooks")
        print("3. New Webhook → Copy Webhook URL")
        print()
        
        webhook_url = input("Paste your webhook URL: ").strip()
        
        # Add to .env
        env_lines.append('\n# Discord Webhook Configuration\n')
        env_lines.append(f'DISCORD_WEBHOOK_URL={webhook_url}\n')
        
        print("\n✅ Webhook URL saved to .env")
    
    else:
        print("Invalid choice!")
        return
    
    # Write .env
    with open('.env', 'w') as f:
        f.writelines(env_lines)
    
    print("\n" + "=" * 80)
    print("Testing Discord connection...")
    print("=" * 80)
    
    # Test it
    os.system('python test_discord.py')

if __name__ == '__main__':
    setup_discord()
