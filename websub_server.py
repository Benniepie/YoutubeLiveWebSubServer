import os
import hmac
import hashlib
import threading
import time
import requests
import xml.etree.ElementTree as ET
from flask import Flask, request, Response
from database import NotificationDB
from notifiers import DiscordNotifier, WhatsAppNotifier, FacebookNotifier, EmailNotifier
from ytdlp_metadata import YTDLPMetadata
from notification_rules import NotificationRules
from security import require_google_ip, rate_limit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# TODO: Replace these values with your own.
# You can find the Channel ID in the source code of a channel's homepage,
# look for "channelId".
YOUTUBE_CHANNEL_ID = "UCBJycsmduvYEL83R_U4JriQ" # Example: Google Developers channel
# This must be your publicly accessible URL. When using Tailscale, this will
# be the URL they provide, e.g., "https://your-tailnet-name.ts.net"
CALLBACK_URL_BASE = "https://laptop.shark-ray.ts.net"
# A secret key used to verify the authenticity of notifications.
# Keep this private.
SECRET_KEY = "a_very_secret_key_12345"

# --- Constants ---
HUB_URL = "https://pubsubhubbub.appspot.com/subscribe"
TOPIC_URL = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"

# --- Flask Application ---
app = Flask(__name__)

# --- Initialize Database and Notifiers ---
db = NotificationDB()
discord = DiscordNotifier()
whatsapp = WhatsAppNotifier()
facebook = FacebookNotifier()
email = EmailNotifier()
ytdlp = YTDLPMetadata()
notification_rules = NotificationRules(db)

@app.route('/')
def home():
    """A simple homepage to show the server is running."""
    return "YouTube WebSub Server is running!"

@app.route('/webhook', methods=['GET', 'POST'])
@require_google_ip  # Only allow requests from Google's IP ranges
@rate_limit(max_requests=100, window_seconds=60)  # Rate limiting
def webhook():
    """
    This endpoint handles both the verification GET request from the hub
    and the notification POST requests.
    
    Security:
    - Only accepts requests from Google's IP ranges
    - Rate limited to 100 requests per minute
    - Verifies HMAC signature on POST requests
    """
    if request.method == 'GET':
        # --- Handle Subscription Verification ---
        print("Received GET request from Hub for verification.")
        challenge_token = request.args.get('hub.challenge')
        if not challenge_token:
            print("  - Error: No challenge token found.")
            return "Error: Missing hub.challenge parameter.", 400

        print(f"  - Hub Mode: {request.args.get('hub.mode')}")
        print(f"  - Hub Topic: {request.args.get('hub.topic')}")
        print("  - Responding with challenge token to verify.")
        return Response(challenge_token, mimetype='text/plain')

    elif request.method == 'POST':
        # --- Handle Incoming Notification ---
        print("\n---")
        print("Received POST request: A potential new video notification!")

        # 1. Verify the signature to ensure the request is from a trusted source
        signature_header = request.headers.get('X-Hub-Signature', '')
        if not verify_signature(signature_header, request.data):
            print("  - Error: Invalid signature. Ignoring request.")
            return "Error: Invalid signature.", 403

        print("  - Signature is valid!")
        
        # DEBUG: Print raw XML to see all available fields
        print("\n=== RAW XML ===")
        print(request.data.decode('utf-8'))
        print("=== END RAW XML ===\n")

        # 2. Parse the XML notification data
        try:
            xml_root = ET.fromstring(request.data)
            # Namespace for Atom feeds
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015'
            }
            entry = xml_root.find('atom:entry', ns)

            if entry is not None:
                title = entry.find('atom:title', ns).text
                video_id = entry.find('yt:videoId', ns).text
                channel_id = entry.find('yt:channelId', ns).text
                video_url = entry.find('atom:link', ns).attrib['href']
                published_time = entry.find('atom:published', ns).text
                updated_time = entry.find('atom:updated', ns).text
                
                # Try to get author info
                author = entry.find('atom:author', ns)
                author_name = author.find('atom:name', ns).text if author is not None else None
                author_uri = author.find('atom:uri', ns).text if author is not None else None

                # Prepare video data
                video_data = {
                    'video_id': video_id,
                    'channel_id': channel_id,
                    'title': title,
                    'video_url': video_url,
                    'published_time': published_time,
                    'updated_time': updated_time,
                    'author_name': author_name,
                    'author_uri': author_uri,
                    'is_live_stream': 'LIVE' in title.upper()
                }

                print(f"  - Title: {title}")
                print(f"  - Video ID: {video_id}")
                print(f"  - Channel ID: {channel_id}")
                print(f"  - URL: {video_url}")
                print(f"  - Published: {published_time}")
                print(f"  - Updated: {updated_time}")
                print(f"  - Author: {author_name}")
                
                # Save to database
                raw_xml = request.data.decode('utf-8')
                video_id_result, is_new, event_type = db.save_notification(video_data, raw_xml)
                
                print(f"  - Event Type: {event_type}")
                print(f"  - Is New: {is_new}")
                
                # ALWAYS fetch metadata with yt-dlp for accurate live detection
                # This is cheap - only ~12 calls per day for your channel
                print("  - Fetching metadata with yt-dlp...")
                ytdlp_details = ytdlp.get_video_details(video_id)
                
                if ytdlp_details:
                    # Update database with metadata
                    metadata = {
                        'scheduled_start_time': ytdlp_details.get('scheduled_start_time'),
                        'live_status': ytdlp_details.get('live_status'),
                        'duration': ytdlp_details.get('duration_string'),
                        'view_count': ytdlp_details.get('view_count'),
                        'like_count': ytdlp_details.get('like_count'),
                        'is_live': ytdlp_details.get('is_live'),
                        'was_live': ytdlp_details.get('was_live')
                    }
                    db.update_video_metadata(video_id, metadata)
                    
                    # Update video_data with accurate live detection
                    actual_live_status = ytdlp_details.get('live_status', 'not_live')
                    is_actually_live = actual_live_status in ['is_live', 'is_upcoming', 'was_live']
                    
                    print(f"    🔴 Live Status: {actual_live_status}")
                    if ytdlp_details.get('scheduled_start_time'):
                        print(f"    📅 Scheduled: {ytdlp_details['scheduled_start_time']}")
                    if ytdlp_details.get('duration_string'):
                        print(f"    ⏱️  Duration: {ytdlp_details['duration_string']}")
                    if ytdlp_details.get('view_count'):
                        print(f"    👁️  Views: {ytdlp_details['view_count']:,}")
                    
                    # Override title-based detection with yt-dlp data
                    video_data['is_live_stream'] = is_actually_live
                    video_data['scheduled_start_time'] = ytdlp_details.get('scheduled_start_time')
                    video_data['live_status'] = actual_live_status
                else:
                    print("    ⚠️  Failed to fetch yt-dlp metadata")
                
                # Apply smart notification rules
                should_notify, notification_type = notification_rules.should_notify(
                    video_data, event_type, is_new
                )
                
                if should_notify:
                    print(f"  - Sending Discord notification ({notification_type})...")
                    
                    # Get formatted message
                    message_data = notification_rules.get_notification_message(
                        video_data, notification_type
                    )
                    
                    if message_data:
                        result = discord.send_notification(
                            video_data, notification_type, message_data
                        )
                        
                        if result['success']:
                            print("    ✅ Discord notification sent!")
                            db.mark_delivered(video_id, 'discord', 'success', result.get('response'))
                        else:
                            print(f"    ❌ Discord failed: {result.get('error')}")
                            db.mark_delivered(video_id, 'discord', 'failed', error_message=result.get('error'))
                else:
                    if notification_type:
                        print(f"  - Skipping notification: {notification_type}")
                    else:
                        print("  - No notification needed")
                
                # Priority 2: WhatsApp for live streams (when implemented)
                # Priority 3: Facebook for live streams (when implemented)
                # etc.
                
            else:
                 # This can happen if a video is deleted. The feed is updated but has no <entry>.
                print("  - Notification received, but it might be a deletion (no <entry> tag found).")

        except ET.ParseError as e:
            print(f"  - Error: Failed to parse XML. {e}")
            return "Error: Could not parse XML data.", 400

        print("---\n")
        return "Notification received.", 200

    else:
        return "Method not allowed", 405

def verify_signature(signature_header, data):
    """
    Verifies the HMAC signature of the incoming request.
    The signature is a SHA1 HMAC of the request body, using our secret key.
    """
    if not signature_header:
        return False
    try:
        # The header is in the format "sha1=..."
        method, signature = signature_header.split('=')
        if method.lower() != 'sha1':
            return False

        # Calculate our expected signature
        expected_signature = hmac.new(
            SECRET_KEY.encode('utf-8'),
            data,
            hashlib.sha1
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
    except (ValueError, IndexError):
        return False


def send_subscription_request(mode="subscribe"):
    """
    Sends a subscription (or unsubscription) request to the PubSubHubbub hub.
    This is a fire-and-forget action. The hub will then contact our /webhook.
    """
    if not CALLBACK_URL_BASE:
        print("\n[ERROR] CALLBACK_URL_BASE is not set!")
        print("Please set the environment variable or edit the script.")
        print("Exiting subscription request.")
        return

    callback_full_url = f"{CALLBACK_URL_BASE.rstrip('/')}/webhook"
    print(f"\nAttempting to {mode}...")
    print(f"  - Hub URL: {HUB_URL}")
    print(f"  - Our Callback: {callback_full_url}")
    print(f"  - Topic: {TOPIC_URL}")

    try:
        response = requests.post(HUB_URL, data={
            'hub.mode': mode,
            'hub.callback': callback_full_url,
            'hub.topic': TOPIC_URL,
            'hub.secret': SECRET_KEY,
            'hub.verify': 'async' # Can also be 'sync'
        })
        if 200 <= response.status_code < 300:
            print(f"  - Successfully sent {mode} request to the hub!")
            print("  - The hub will now send a GET request to your callback URL to verify.")
        else:
            print(f"  - Error sending request to hub: {response.status_code}")
            print(f"  - Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"  - An error occurred: {e}")

if __name__ == '__main__':
    # We run the subscription request in a separate thread after a short delay.
    # This gives the Flask server time to start up and be ready for the
    # hub's verification request.
    threading.Timer(2.0, send_subscription_request, args=["subscribe"]).start()

    # To unsubscribe, you could run:
    # threading.Timer(2.0, send_subscription_request, args=["unsubscribe"]).start()

    print("Starting Flask server on port 5001...")
    app.run(port=5001, debug=True, use_reloader=False)
