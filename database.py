"""
Database module for storing YouTube notifications and tracking notification delivery
"""
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import json

class NotificationDB:
    def __init__(self, db_path='data/notifications.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def init_db(self):
        """Initialize the database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Videos table - stores all video notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE NOT NULL,
                channel_id TEXT NOT NULL,
                title TEXT NOT NULL,
                video_url TEXT NOT NULL,
                published_time TEXT NOT NULL,
                updated_time TEXT,
                author_name TEXT,
                author_uri TEXT,
                is_live_stream BOOLEAN DEFAULT 0,
                live_stream_status TEXT,
                first_seen_at TEXT NOT NULL,
                last_updated_at TEXT NOT NULL,
                notification_count INTEGER DEFAULT 1,
                raw_xml TEXT,
                scheduled_start_time TEXT,
                actual_start_time TEXT,
                actual_end_time TEXT,
                duration TEXT,
                view_count INTEGER,
                like_count INTEGER,
                api_metadata TEXT
            )
        ''')
        
        # Notification events table - tracks each notification received
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                received_at TEXT NOT NULL,
                published_time TEXT NOT NULL,
                updated_time TEXT,
                event_type TEXT,
                raw_xml TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        ''')
        
        # Delivery tracking table - tracks which platforms we've notified
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS delivery_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                delivered_at TEXT NOT NULL,
                status TEXT NOT NULL,
                response_data TEXT,
                error_message TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(video_id),
                UNIQUE(video_id, platform)
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_id ON videos(video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_channel_id ON videos(channel_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_is_live_stream ON videos(is_live_stream)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notification_events_video_id ON notification_events(video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_delivery_tracking_video_id ON delivery_tracking(video_id)')
        
        conn.commit()
        conn.close()
    
    def save_notification(self, video_data: Dict, raw_xml: str, received_at: Optional[str] = None) -> tuple:
        """
        Save a notification to the database
        Returns: (video_id, is_new, event_type)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        video_id = video_data['video_id']
        now = received_at or datetime.utcnow().isoformat()
        
        # Check if video already exists
        cursor.execute('SELECT id, notification_count, published_time FROM videos WHERE video_id = ?', (video_id,))
        existing = cursor.fetchone()
        
        is_new = existing is None
        event_type = self._determine_event_type(video_data, existing, raw_xml)
        
        if is_new:
            # Insert new video
            cursor.execute('''
                INSERT INTO videos (
                    video_id, channel_id, title, video_url, published_time, updated_time,
                    author_name, author_uri, is_live_stream, live_stream_status,
                    first_seen_at, last_updated_at, notification_count, raw_xml
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                video_data['channel_id'],
                video_data['title'],
                video_data['video_url'],
                video_data['published_time'],
                video_data.get('updated_time'),
                video_data.get('author_name'),
                video_data.get('author_uri'),
                video_data.get('is_live_stream', False),
                event_type,
                now,
                now,
                1,
                raw_xml
            ))
        else:
            # Update existing video
            cursor.execute('''
                UPDATE videos SET
                    title = ?,
                    updated_time = ?,
                    last_updated_at = ?,
                    notification_count = notification_count + 1,
                    live_stream_status = ?,
                    raw_xml = ?
                WHERE video_id = ?
            ''', (
                video_data['title'],
                video_data.get('updated_time'),
                now,
                event_type,
                raw_xml,
                video_id
            ))
        
        # Record the notification event
        cursor.execute('''
            INSERT INTO notification_events (
                video_id, received_at, published_time, updated_time, event_type, raw_xml
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            video_id,
            now,
            video_data['published_time'],
            video_data.get('updated_time'),
            event_type,
            raw_xml
        ))
        
        conn.commit()
        conn.close()
        
        return (video_id, is_new, event_type)
    
    def _determine_event_type(self, video_data: Dict, existing, raw_xml: str) -> str:
        """
        Determine what type of event this notification represents
        Uses yt-dlp live_status if available, falls back to title-based detection
        """
        # Prefer yt-dlp live_status if available
        live_status = video_data.get('live_status', 'not_live')
        is_live_content = video_data.get('is_live_stream', False)
        
        # Fallback: Check if title contains LIVE indicators
        title = video_data['title'].upper()
        has_live_keyword = 'LIVE' in title or 'BREAKING LIVE' in title
        
        # Override with title if yt-dlp data not available
        if live_status == 'not_live' and has_live_keyword:
            is_live_content = True
        
        if existing is None:
            # First notification
            if live_status == 'is_upcoming':
                return 'live_scheduled'
            elif live_status == 'is_live':
                return 'live_started'
            elif is_live_content or has_live_keyword:
                return 'live_scheduled'
            return 'video_published'
        else:
            # Subsequent notifications
            notification_count = existing['notification_count']
            
            if is_live_content or has_live_keyword:
                # Check if published time changed (indicates archive published)
                old_published = existing['published_time']
                new_published = video_data['published_time']
                
                if old_published != new_published:
                    return 'live_archived'
                
                # Use live_status to determine event
                if live_status == 'is_upcoming':
                    return 'live_scheduled'
                elif live_status == 'is_live':
                    if notification_count == 1:
                        return 'live_started'
                    return 'live_ongoing'
                elif live_status == 'was_live':
                    return 'live_ended'
                
                # Fallback to count-based detection
                if notification_count == 1:
                    return 'live_started'
                elif notification_count == 2:
                    return 'live_ongoing'
                elif notification_count == 3:
                    return 'live_ended'
                else:
                    return 'live_update'
            
            return 'video_updated'
    
    def mark_delivered(self, video_id: str, platform: str, status: str = 'success', 
                      response_data: Optional[Dict] = None, error_message: Optional[str] = None):
        """Mark that a notification was delivered to a platform"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        response_json = json.dumps(response_data) if response_data else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO delivery_tracking (
                video_id, platform, delivered_at, status, response_data, error_message
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (video_id, platform, now, status, response_json, error_message))
        
        conn.commit()
        conn.close()
    
    def get_delivery_status(self, video_id: str) -> List[Dict]:
        """Get delivery status for a video across all platforms"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT platform, delivered_at, status, error_message, response_data
            FROM delivery_tracking
            WHERE video_id = ?
            ORDER BY delivered_at DESC
        ''', (video_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_video_events(self, video_id: str) -> List[Dict]:
        """Get all notification events for a specific video"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM notification_events
            WHERE video_id = ?
            ORDER BY received_at ASC
        ''', (video_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_recent_videos(self, limit: int = 50) -> List[Dict]:
        """Get recent videos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM videos
            ORDER BY last_updated_at DESC
            LIMIT ?
        ''', (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_live_streams(self) -> List[Dict]:
        """Get all live stream videos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM videos
            WHERE is_live_stream = 1
            ORDER BY last_updated_at DESC
        ''')
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def update_video_metadata(self, video_id: str, api_metadata: Dict):
        """Update video with metadata from YouTube API"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE videos SET
                scheduled_start_time = ?,
                actual_start_time = ?,
                actual_end_time = ?,
                duration = ?,
                view_count = ?,
                like_count = ?,
                api_metadata = ?
            WHERE video_id = ?
        ''', (
            api_metadata.get('scheduled_start_time'),
            api_metadata.get('actual_start_time'),
            api_metadata.get('actual_end_time'),
            api_metadata.get('duration'),
            api_metadata.get('view_count'),
            api_metadata.get('like_count'),
            json.dumps(api_metadata),
            video_id
        ))
        
        conn.commit()
        conn.close()
