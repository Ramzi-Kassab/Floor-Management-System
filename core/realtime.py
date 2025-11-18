"""
Real-time Updates Infrastructure for Floor Management System.

Note: Full WebSocket implementation requires channels/daphne.
This provides the framework and helpers.

Features:
- WebSocket connection helpers
- Real-time notification delivery
- Live dashboard updates
- Presence system
"""

import json
from django.core.cache import cache
from datetime import datetime


class RealtimeChannel:
    """Real-time communication channel."""
    
    @staticmethod
    def send_to_user(user_id, event_type, data):
        """Send event to specific user (via cache for simple impl)."""
        key = f'realtime:user:{user_id}'
        events = cache.get(key, [])
        
        events.append({
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 100 events
        events = events[-100:]
        cache.set(key, events, timeout=3600)
        
    @staticmethod
    def send_to_group(group_name, event_type, data):
        """Send event to group."""
        key = f'realtime:group:{group_name}'
        events = cache.get(key, [])
        
        events.append({
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        events = events[-100:]
        cache.set(key, events, timeout=3600)
        
    @staticmethod
    def get_user_events(user_id, since=None):
        """Get events for user."""
        key = f'realtime:user:{user_id}'
        events = cache.get(key, [])
        
        if since:
            events = [e for e in events if e['timestamp'] > since]
            
        return events
        
    @staticmethod
    def broadcast(event_type, data):
        """Broadcast to all connected users."""
        key = 'realtime:broadcast'
        events = cache.get(key, [])
        
        events.append({
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        events = events[-100:]
        cache.set(key, events, timeout=3600)


class PresenceTracker:
    """Track online users."""
    
    @staticmethod
    def user_online(user_id):
        """Mark user as online."""
        key = 'presence:online_users'
        users = cache.get(key, set())
        users.add(user_id)
        cache.set(key, users, timeout=300)  # 5 min timeout
        
    @staticmethod
    def user_offline(user_id):
        """Mark user as offline."""
        key = 'presence:online_users'
        users = cache.get(key, set())
        users.discard(user_id)
        cache.set(key, users, timeout=300)
        
    @staticmethod
    def get_online_users():
        """Get list of online users."""
        key = 'presence:online_users'
        return list(cache.get(key, set()))
        
    @staticmethod
    def is_user_online(user_id):
        """Check if user is online."""
        return user_id in PresenceTracker.get_online_users()
