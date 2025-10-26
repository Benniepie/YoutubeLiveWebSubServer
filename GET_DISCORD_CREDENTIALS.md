# Get Discord Credentials - Step by Step

## Step 1: Get Bot Token

1. Go to https://discord.com/developers/applications
2. Click on your application
3. Click **Bot** in the left sidebar
4. Under "TOKEN", click **Reset Token** (or **Copy** if you see it)
5. Copy the token - it looks like: `YOUR_BOT_TOKEN_HERE`

⚠️ **IMPORTANT**: Never share this token publicly! It's like a password.

## Step 2: Get Channel ID

1. Open Discord
2. Go to **User Settings** (gear icon)
3. Go to **Advanced** → Enable **Developer Mode**
4. Go back to your server
5. Right-click on the channel where you want notifications (e.g., "live-server")
6. Click **Copy Channel ID**
7. The ID looks like: `1234567890123456789`

## Step 3: Add to .env File

Open your `.env` file and add:

```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=paste_your_token_here
DISCORD_CHANNEL_ID=paste_your_channel_id_here
```

Example:
```env
DISCORD_BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
DISCORD_CHANNEL_ID=YOUR_ACTUAL_CHANNEL_ID_HERE
```

## Step 4: Test It!

```powershell
python test_discord.py
```

You should see:
- ✅ Bot Token: Set
- ✅ Channel ID: Set
- ✅ Bot test successful!

And a message will appear in your Discord channel!

## Alternative: Use Webhook (Easier!)

If you prefer, you can use a webhook instead:

1. In Discord, right-click your channel
2. **Edit Channel** → **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Name it "YouTube Notifications"
5. **Copy Webhook URL**

Add to `.env`:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
```

Webhooks are simpler but bots give you more control.

## Troubleshooting

### Error 401: Unauthorized
- Bot token is invalid or expired
- Reset the token in Developer Portal

### Error 403: Forbidden
- Bot doesn't have permissions
- In Discord server settings, check bot role has:
  - View Channel
  - Send Messages
  - Embed Links

### Error 404: Not Found
- Channel ID is wrong
- Bot is not in the server
- Re-invite bot with this URL format:
  ```
  https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2048&scope=bot
  ```

### Bot not responding
- Make sure bot is online (green dot in Discord)
- Check bot has proper intents enabled in Developer Portal
