"""
Mobile Optimization and PWA Features for Floor Management System.

Features:
- Progressive Web App (PWA) support
- Offline capabilities
- Mobile-optimized views
- Touch gestures
- Service worker integration
"""

from django.conf import settings
import json


class PWAConfig:
    """PWA manifest and configuration."""
    
    @staticmethod
    def get_manifest():
        """Generate PWA manifest."""
        return {
            "name": "Floor Management System",
            "short_name": "FMS",
            "description": "ERP system for PDC bit manufacturing",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#6366f1",
            "orientation": "portrait",
            "icons": [
                {
                    "src": "/static/img/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/img/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ],
            "screenshots": [],
            "categories": ["business", "productivity"],
            "shortcuts": [
                {
                    "name": "Dashboard",
                    "url": "/",
                    "description": "Main dashboard"
                },
                {
                    "name": "Search",
                    "url": "/core/search/",
                    "description": "Global search"
                }
            ]
        }
    
    @staticmethod
    def get_service_worker():
        """Generate service worker JavaScript."""
        return """
const CACHE_NAME = 'fms-cache-v1';
const urlsToCache = [
    '/',
    '/static/css/app.css',
    '/static/js/app.js',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
"""


class MobileDetector:
    """Detect mobile devices and capabilities."""
    
    @staticmethod
    def is_mobile(request):
        """Check if request is from mobile device."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
        return any(keyword in user_agent for keyword in mobile_keywords)
        
    @staticmethod
    def get_device_type(request):
        """Get device type (mobile, tablet, desktop)."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        elif MobileDetector.is_mobile(request):
            return 'mobile'
        else:
            return 'desktop'
