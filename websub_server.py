import os
import hmac
import hashlib
import threading
import time
import requests
import xml.etree.ElementTree as ET
from flask import Flask, request, Response
from database import NotificationDB
from notifiers import DiscordNotifier, WhatsAppNotifier, FacebookNotifier, EmailNotifier, PostizNotifier
from youtube_metadata import YouTubeMetadata
from notification_rules import NotificationRules
from security import require_google_ip, rate_limit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Load from environment variables (set in .env file)
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
CALLBACK_URL_BASE = os.getenv("CALLBACK_URL_BASE")
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
postiz = PostizNotifier()
youtube = YouTubeMetadata()
notification_rules = NotificationRules(db)

# Import Telegram for debug monitoring
from telegram_notifier import TelegramNotifier
telegram_debug = TelegramNotifier(use_test_bot=True)  # Use test bot for monitoring

# --- Locking Mechanism ---
video_locks = {}
video_locks_mutex = threading.Lock()

def get_video_lock(video_id):
    with video_locks_mutex:
        if video_id not in video_locks:
            video_locks[video_id] = threading.Lock()
        return video_locks[video_id]

def trigger_postiz(video_data):
    """
    Trigger Postiz notifications if not already sent.
    """
    video_id = video_data['video_id']
    print(f"  - Checking Postiz for video {video_id}...")
    
    # Check delivery status to avoid duplicates
    delivery_status = db.get_delivery_status(video_id)
    already_processed = any(d['platform'].startswith('postiz') for d in delivery_status)
    
    if already_processed:
        print(f"    ℹ️  Postiz already processed for {video_id}. Skipping.")
        return

    print(f"  - Sending Postiz notifications for {video_id}...")
    try:
        results = postiz.send_notification(video_data)
        
        for platform, result in results.items():
            status = 'success' if result['success'] else 'failed'
            error = result.get('error')
            response = result.get('response')
            
            db.mark_delivered(
                video_id, 
                f"postiz_{platform}", 
                status, 
                response, 
                error
            )
            
            if status == 'success':
                print(f"    ✅ Postiz ({platform}): Sent")
            else:
                print(f"    ❌ Postiz ({platform}): Failed - {error}")
                
    except Exception as e:
        print(f"    ❌ Postiz Error: {e}")
        import traceback
        traceback.print_exc()

# --- Core Logic ---
def process_video_event(video_data, raw_xml, event_type, is_new, retry_count=0):
    """
    Process a video notification with locking and retry logic.
    """
    video_id = video_data['video_id']

    # Acquire lock for this video to prevent race conditions (Issue 2)
    lock = get_video_lock(video_id)
    # Use timeout to prevent indefinite hanging
    if not lock.acquire(timeout=30):
        print(f"  ❌ Could not acquire lock for {video_id}, skipping concurrent processing.")
        return

    try:
        print(f"  - Processing event for video {video_id} (Attempt {retry_count})...")

        # Track processing steps for debug notification
        processing_log = []
        processing_log.append(f"📥 Event: {event_type}")
        processing_log.append(f"🆕 New: {'Yes' if is_new else 'No'}")
        if retry_count > 0:
            processing_log.append(f"🔄 Retry: {retry_count}")

        # Fetch metadata with YouTube API
        print(f"  - Fetching metadata with YouTube API (Attempt {retry_count})...")
        youtube_details = youtube.get_video_details(video_id)

        # Issue 1: Retry logic for missing scheduled start time on new videos
        if is_new and retry_count == 0:
            should_retry = False
            if not youtube_details:
                should_retry = True
            elif not youtube_details.get('scheduled_start_time'):
                 should_retry = True

            if should_retry:
                print(f"  - No scheduled start time found for new video. Retrying in 60 seconds...")
                processing_log.append("⏳ Retrying in 60s (missing schedule)")

                # Release lock before scheduling retry
                lock.release()

                # Schedule retry in separate thread
                threading.Timer(60.0, process_video_event, args=[video_data, raw_xml, event_type, is_new, 1]).start()
                return

        if youtube_details:
            processing_log.append(f"✅ YouTube API: Success")

            # Update database with metadata
            metadata = {
                'scheduled_start_time': youtube_details.get('scheduled_start_time'),
                'live_status': youtube_details.get('live_status'),
                'duration': youtube_details.get('duration'),
                'view_count': youtube_details.get('view_count'),
                'like_count': youtube_details.get('like_count'),
                'is_live': youtube_details.get('is_live'),
                'was_live': youtube_details.get('was_live')
            }
            db.update_video_metadata(video_id, metadata)

            # Update video_data with accurate live detection
            actual_live_status = youtube_details.get('live_status', 'not_live')
            is_actually_live = actual_live_status in ['is_live', 'is_upcoming', 'was_live']

            print(f"    🔴 Live Status: {actual_live_status}")
            processing_log.append(f"🔴 Status: {actual_live_status}")

            if youtube_details.get('scheduled_start_time'):
                print(f"    📅 Scheduled: {youtube_details['scheduled_start_time']}")
                processing_log.append(f"📅 Scheduled: {youtube_details['scheduled_start_time']}")
            if youtube_details.get('actual_start_time'):
                print(f"    🔴 Started: {youtube_details['actual_start_time']}")
            if youtube_details.get('actual_end_time'):
                print(f"    ⏹️  Ended: {youtube_details['actual_end_time']}")
            if youtube_details.get('view_count'):
                print(f"    👁️  Views: {int(youtube_details['view_count']):,}")

            # Override title-based detection with YouTube API data
            video_data['is_live_stream'] = is_actually_live
            video_data['scheduled_start_time'] = youtube_details.get('scheduled_start_time')
            video_data['live_status'] = actual_live_status
            video_data['description'] = youtube_details.get('description')

            # --- Postiz Integration ---
            # Post both live & non-live streams, but only once per video.
            # We wait for the "second check" (approx 60s) to ensure metadata is stable.
            if is_new:
                if retry_count == 0:
                    print("  - Scheduling Postiz notification check in 60 seconds...")
                    threading.Timer(60.0, trigger_postiz, args=[video_data]).start()
                else:
                    # We are in the retry/second check, so trigger immediately
                    trigger_postiz(video_data)
        else:
            print("    ⚠️  Failed to fetch YouTube API metadata")
            processing_log.append("❌ YouTube API: Failed")
            # Keep title-based detection as fallback
            if video_data.get('is_live_stream'):
                print("    ℹ️  Using title-based live stream detection as fallback")

        # Apply smart notification rules
        should_notify, notification_type = notification_rules.should_notify(
            video_data, event_type, is_new
        )

        # Build comprehensive debug message
        status_emoji = {
            'is_live': '🔴 LIVE NOW',
            'is_upcoming': '📅 SCHEDULED',
            'was_live': '📼 ENDED',
            'not_live': '📹 VIDEO'
        }.get(video_data.get('live_status', 'not_live'), '❓ UNKNOWN')

        debug_caption = f"<b>{video_data['title']}</b>\n\n"
        debug_caption += f"{status_emoji}\n"
        debug_caption += f"👤 {video_data.get('author_name')}\n\n"

        debug_caption += f"<b>📊 Processing Log:</b>\n"
        debug_caption += "\n".join(processing_log) + "\n\n"

        if should_notify:
            print(f"  - Sending Discord notification ({notification_type})...")
            processing_log.append(f"📤 Sending: {notification_type}")

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
                    processing_log.append("✅ Discord: SENT")

                    debug_caption += f"<b>✅ USER NOTIFIED</b>\n"
                    debug_caption += f"Type: {notification_type}\n"
                    debug_caption += f"Platform: Discord\n\n"
                    debug_caption += f"<a href='{video_data['video_url']}'>Watch Video</a>"
                else:
                    print(f"    ❌ Discord failed: {result.get('error')}")
                    db.mark_delivered(video_id, 'discord', 'failed', error_message=result.get('error'))
                    processing_log.append(f"❌ Discord: FAILED")

                    debug_caption += f"<b>❌ NOTIFICATION FAILED</b>\n"
                    debug_caption += f"Type: {notification_type}\n"
                    debug_caption += f"Error: {result.get('error')[:100]}\n\n"
                    debug_caption += f"<a href='{video_data['video_url']}'>Watch Video</a>"
        else:
            if notification_type:
                print(f"  - Skipping notification: {notification_type}")
                reason = notification_type
            else:
                print("  - No notification needed")
                reason = "Not a live stream or already notified"

            processing_log.append(f"⏭️ Skipped: {reason}")

            debug_caption += f"<b>⏭️ NO NOTIFICATION</b>\n"
            debug_caption += f"Reason: {reason}\n\n"
            debug_caption += f"<a href='{video_data['video_url']}'>Watch Video</a>"

        # Send comprehensive debug notification with thumbnail
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        telegram_debug.send_photo(thumbnail_url, debug_caption)

    except Exception as e:
        print(f"  ❌ Error processing video: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if lock.locked():
            lock.release()

@app.route('/')
def home():
    """A simple homepage to show the server is running."""
    return "YouTube WebSub Server is running!"

@app.route('/webhook', methods=['GET', 'POST'], strict_slashes=False)
@require_google_ip  # Only allow requests from Google's IP ranges
@rate_limit(max_requests=100, window_seconds=60)  # Rate limiting
def webhook():
    """
    This endpoint handles both the verification GET request from the hub
    and the notification POST requests.
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
                
                # Save to database
                raw_xml = request.data.decode('utf-8')
                video_id_result, is_new, event_type = db.save_notification(video_data, raw_xml)
                
                print(f"  - Event Type: {event_type}")
                print(f"  - Is New: {is_new}")
                
                # Dispatch to processing function (handled in current thread but with locking)
                # We could run this in a separate thread to return 200 immediately,
                # but for now we keep it synchronous (mostly) to ensure completion before return,
                # unless a retry is scheduled.
                process_video_event(video_data, raw_xml, event_type, is_new)
                
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

def subscription_maintenance_loop():
    """
    Periodically resubscribes to the hub (Issue 4).
    Subscription lasts 7 days, so we resubscribe every 6 days.
    Also cleans up old locks.
    """
    while True:
        # Wait 6 days
        time.sleep(6 * 24 * 3600)

        # Maintenance tasks
        print("\n--- Maintenance: Renewing YouTube PubSub Subscription ---")
        send_subscription_request("subscribe")

        # Cleanup locks
        with video_locks_mutex:
            # Simple cleanup: remove locks for videos not processed recently?
            # Since we don't track access time, we'll just clear the dictionary.
            # This is safe because if a video is being processed, the thread holds a reference to the lock object
            # (obtained via get_video_lock before we clear here).
            # Any new request will create a new lock.
            # The only risk is if Thread A gets lock L1, we clear dict, Thread B gets new lock L2.
            # Then both run.
            # So clearing is NOT safe without checking if locked.

            # Safe cleanup: remove only if not locked?
            # threading.Lock doesn't strictly expose "is_locked()" in a thread-safe way for this purpose
            # (locked() tells current state, but someone might be about to acquire).
            # Given the low volume, we'll skip aggressive cleanup to avoid race conditions.
            pass

if __name__ == '__main__':
    # Initial subscription
    threading.Timer(2.0, send_subscription_request, args=["subscribe"]).start()

    # Start maintenance loop in a daemon thread
    maintenance_thread = threading.Thread(target=subscription_maintenance_loop, daemon=True)
    maintenance_thread.start()

    print("Starting Flask server on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
