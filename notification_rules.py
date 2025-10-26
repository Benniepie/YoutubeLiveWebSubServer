"""
Smart notification rules for Discord
Determines when to send notifications based on live stream timing and status
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

class NotificationRules:
    """Determine if and what type of notification to send"""
    
    # Time window for notifications (2 hours)
    NOTIFICATION_WINDOW_HOURS = 2
    
    def __init__(self, db):
        self.db = db
    
    def should_notify(self, video_data: Dict, event_type: str, is_new: bool) -> Tuple[bool, Optional[str]]:
        """
        Determine if we should send a Discord notification
        
        Returns: (should_notify: bool, notification_type: str)
        
        Notification types:
        - 'upcoming' - Stream starting soon (< 2 hours)
        - 'live_now' - Stream just went live
        - 'reschedule' - Previously announced stream changed time
        - None - Don't notify
        """
        video_id = video_data['video_id']
        live_status = video_data.get('live_status', 'not_live')
        scheduled_time = video_data.get('scheduled_start_time')
        
        # Rule 6: Ignore non-live content
        if live_status == 'not_live':
            return (False, None)
        
        # Get delivery history
        delivery_status = self.db.get_delivery_status(video_id)
        already_notified = any(d['platform'] == 'discord' and d['status'] == 'success' 
                              for d in delivery_status)
        
        # Rule 4: Stream just went live
        if live_status == 'is_live':
            # Check if we already sent a "live_now" notification
            live_now_sent = any(
                d['platform'] == 'discord' and 
                d['status'] == 'success' and
                'live_now' in d.get('response_data', '')
                for d in delivery_status
            )
            
            if not live_now_sent:
                return (True, 'live_now')
            else:
                # Rule 7: No duplicates
                return (False, None)
        
        # For upcoming streams, check scheduled time
        if live_status == 'is_upcoming' and scheduled_time:
            scheduled_dt = self._parse_datetime(scheduled_time)
            if not scheduled_dt:
                return (False, None)
            
            now = datetime.now(timezone.utc)
            time_until_start = scheduled_dt - now
            hours_until = time_until_start.total_seconds() / 3600
            
            # Rule 6: Only notify if starting within 2 hours
            if hours_until > self.NOTIFICATION_WINDOW_HOURS:
                return (False, None)
            
            # Rule 1: New stream starting soon
            if is_new and not already_notified:
                return (True, 'upcoming')
            
            # Rule 3: Reschedule notification
            if already_notified:
                # Check if scheduled time changed
                previous_time = self._get_previous_scheduled_time(video_id)
                if previous_time and previous_time != scheduled_time:
                    # Rule 2: New time is within 2 hours
                    return (True, 'reschedule')
            
            # Rule 7: Already notified and time hasn't changed
            return (False, None)
        
        # Rule 5: No notifications for title/description changes
        return (False, None)
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse ISO datetime string to datetime object"""
        try:
            # Handle both 'Z' and '+00:00' formats
            dt_str = dt_str.replace('Z', '+00:00')
            return datetime.fromisoformat(dt_str)
        except:
            return None
    
    def _get_previous_scheduled_time(self, video_id: str) -> Optional[str]:
        """Get the previously stored scheduled time for a video"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT scheduled_start_time FROM videos WHERE video_id = ?',
            (video_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return result['scheduled_start_time'] if result else None
    
    def format_time_until(self, scheduled_time: str) -> str:
        """
        Format time until stream starts
        Returns: "2 hours", "20 minutes", "5 minutes", etc.
        """
        scheduled_dt = self._parse_datetime(scheduled_time)
        if not scheduled_dt:
            return "soon"
        
        now = datetime.now(timezone.utc)
        time_until = scheduled_dt - now
        
        total_seconds = time_until.total_seconds()
        
        if total_seconds < 0:
            return "now"
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        if hours > 0:
            if minutes > 0:
                return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
            return f"{hours} hour{'s' if hours != 1 else ''}"
        elif minutes > 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return "less than a minute"
    
    def format_uk_time(self, scheduled_time: str) -> str:
        """
        Format scheduled time in UK timezone
        Returns: "10:00 PM UK" or "10:00 PM GMT" / "11:00 PM BST"
        """
        scheduled_dt = self._parse_datetime(scheduled_time)
        if not scheduled_dt:
            return "TBD"
        
        # Convert to UK time (this is simplified - you might want to use pytz for proper BST handling)
        # For now, we'll show UTC time with UK label
        # TODO: Add proper UK timezone conversion with BST/GMT detection
        
        time_str = scheduled_dt.strftime('%I:%M %p')
        return f"{time_str} UK"
    
    def get_notification_message(self, video_data: Dict, notification_type: str, custom_emoji: str = ':HELLO_TEAM:', channel_name: str = None) -> Dict:
        """
        Generate the notification message content
        
        Args:
            video_data: Video information
            notification_type: Type of notification
            custom_emoji: Custom Discord emoji (e.g., ':HELLO_TEAM:')
        
        Returns dict with:
        - content: Main message text (with @everyone for live_now)
        - embed: Discord embed object
        """
        title = video_data['title']
        url = video_data['video_url']
        video_id = video_data.get('video_id', '')
        scheduled_time = video_data.get('scheduled_start_time')
        
        # Use channel name from video_data or parameter, fallback to generic
        if not channel_name:
            channel_name = video_data.get('author_name', 'Channel')
        
        # Get YouTube thumbnail
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        if notification_type == 'live_now':
            # Stream is LIVE NOW - RED with urgent emoji
            # Check if @everyone should be included (can be disabled via env var)
            import os
            ping_everyone = os.getenv('DISCORD_PING_EVERYONE', 'true').lower() == 'true'
            mention = "@everyone " if ping_everyone else ""
            content = f"{mention}{custom_emoji} **{channel_name} LIVE stream has started NOW!**\n{url}"
            embed = {
                'title': f'🔴 LIVE NOW: {title}',
                'url': url,  # Makes title clickable
                'color': 0xFF0000,  # Red
                'description': f'🚨 **[WATCH THE STREAM NOW]({url})**',  # Clickable markdown link
                'thumbnail': {'url': thumbnail_url},  # Small thumbnail in corner
                'timestamp': datetime.utcnow().isoformat(),
                'footer': {'text': channel_name}
            }
        
        elif notification_type == 'upcoming':
            # Stream starting soon - GREEN with urgent emoji if <10 min
            time_until = self.format_time_until(scheduled_time)
            uk_time = self.format_uk_time(scheduled_time)
            
            # Check if starting very soon (< 10 minutes)
            scheduled_dt = self._parse_datetime(scheduled_time)
            now = datetime.now(timezone.utc)
            minutes_until = (scheduled_dt - now).total_seconds() / 60 if scheduled_dt else 999
            
            # Add urgent emoji if less than 10 minutes
            title_emoji = '⚡' if minutes_until < 10 else '📅'
            
            content = f"@everyone {custom_emoji} **{channel_name} LIVE stream starting in {time_until}, scheduled for {uk_time}**\n{url}"
            embed = {
                'title': f'{title_emoji} Upcoming: {title}',
                'url': url,  # Makes title clickable
                'color': 0x00FF00,  # Green
                'description': f'**[Click here to set a reminder]({url})**',  # Clickable markdown link
                'thumbnail': {'url': thumbnail_url},  # Small thumbnail in corner
                'fields': [
                    {'name': '⏰ Starting In', 'value': time_until, 'inline': True},
                    {'name': '🕐 Scheduled Time', 'value': uk_time, 'inline': True}
                ],
                'timestamp': datetime.utcnow().isoformat(),
                'footer': {'text': channel_name}
            }
        
        elif notification_type == 'reschedule':
            # Time changed - YELLOW with warning emoji
            time_until = self.format_time_until(scheduled_time)
            uk_time = self.format_uk_time(scheduled_time)
            
            content = f"@everyone {custom_emoji} **{channel_name} LIVE stream time has changed! Now starting in {time_until}, scheduled for {uk_time}**\n{url}"
            embed = {
                'title': f'🔄 Rescheduled: {title}',
                'url': url,  # Makes title clickable
                'color': 0xFFFF00,  # Yellow
                'description': f'⚠️ **Stream time has changed!** [View updated stream]({url})',  # Clickable markdown link
                'thumbnail': {'url': thumbnail_url},  # Small thumbnail in corner
                'fields': [
                    {'name': '⏰ Starting In', 'value': time_until, 'inline': True},
                    {'name': '🕐 New Time', 'value': uk_time, 'inline': True}
                ],
                'timestamp': datetime.utcnow().isoformat(),
                'footer': {'text': channel_name}
            }
        
        else:
            return None
        
        return {
            'content': content,
            'embeds': [embed]
        }
