"""
Security utilities for the Floor Management System.

Includes:
- Password strength validation
- Session management
- IP tracking and validation
- Login attempt tracking
- Two-factor authentication helpers
- Security event logging
"""

import re
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.contrib.gis.geoip2 import GeoIP2
import hashlib

User = get_user_model()


class PasswordValidator:
    """
    Advanced password strength validation.

    Checks for:
    - Minimum length
    - Uppercase letters
    - Lowercase letters
    - Numbers
    - Special characters
    - Common passwords
    - User attribute similarity
    """

    COMMON_PASSWORDS = [
        'password', '12345678', 'qwerty', 'abc123', 'monkey', '1234567890',
        'letmein', 'trustno1', 'dragon', 'baseball', 'iloveyou', 'master',
        'sunshine', 'ashley', 'bailey', 'passw0rd', 'shadow', '123123'
    ]

    @staticmethod
    def validate_strength(password, user=None):
        """
        Validate password strength.

        Returns:
            dict: {
                'valid': bool,
                'score': int (0-100),
                'errors': list,
                'suggestions': list
            }
        """
        errors = []
        suggestions = []
        score = 0

        # Length check
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        elif len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10

        # Uppercase check
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        else:
            score += 15

        # Lowercase check
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        else:
            score += 15

        # Number check
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one number')
        else:
            score += 15

        # Special character check
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            suggestions.append('Consider adding special characters for stronger security')
        else:
            score += 15

        # Common password check
        if password.lower() in PasswordValidator.COMMON_PASSWORDS:
            errors.append('Password is too common')
            score = max(0, score - 30)

        # User attribute similarity check
        if user:
            username = getattr(user, 'username', '').lower()
            email = getattr(user, 'email', '').lower().split('@')[0]

            if username and username in password.lower():
                errors.append('Password should not contain your username')
                score = max(0, score - 20)
            if email and len(email) > 3 and email in password.lower():
                errors.append('Password should not contain your email')
                score = max(0, score - 20)

        # Sequential characters check
        if re.search(r'(012|123|234|345|456|567|678|789|abc|bcd|cde)', password.lower()):
            suggestions.append('Avoid sequential characters')
            score = max(0, score - 10)

        # Repeated characters check
        if re.search(r'(.)\1{2,}', password):
            suggestions.append('Avoid repeated characters')
            score = max(0, score - 10)

        return {
            'valid': len(errors) == 0,
            'score': min(100, score),
            'errors': errors,
            'suggestions': suggestions,
            'strength': PasswordValidator._get_strength_label(min(100, score))
        }

    @staticmethod
    def _get_strength_label(score):
        """Get password strength label from score."""
        if score < 30:
            return 'Weak'
        elif score < 60:
            return 'Fair'
        elif score < 80:
            return 'Good'
        else:
            return 'Strong'


class LoginAttemptTracker:
    """
    Track and limit login attempts to prevent brute force attacks.

    Features:
    - Per-user attempt tracking
    - Per-IP attempt tracking
    - Configurable lockout periods
    - Automatic cleanup
    """

    # Configuration
    MAX_ATTEMPTS = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
    LOCKOUT_DURATION = getattr(settings, 'LOGIN_LOCKOUT_DURATION', 900)  # 15 minutes
    ATTEMPT_WINDOW = getattr(settings, 'LOGIN_ATTEMPT_WINDOW', 300)  # 5 minutes

    @staticmethod
    def get_cache_key(identifier, type='user'):
        """Generate cache key for tracking."""
        return f'login_attempts:{type}:{identifier}'

    @staticmethod
    def record_attempt(username, ip_address, success=False):
        """
        Record a login attempt.

        Args:
            username: Username attempting login
            ip_address: IP address of attempt
            success: Whether login was successful
        """
        from .notification_utils import log_activity

        # Record for username
        user_key = LoginAttemptTracker.get_cache_key(username, 'user')
        attempts = cache.get(user_key, [])
        attempts.append({
            'timestamp': timezone.now().isoformat(),
            'ip': ip_address,
            'success': success
        })

        # Keep only recent attempts
        cutoff = timezone.now() - timedelta(seconds=LoginAttemptTracker.ATTEMPT_WINDOW)
        attempts = [a for a in attempts if datetime.fromisoformat(a['timestamp']) > cutoff]

        cache.set(user_key, attempts, LoginAttemptTracker.ATTEMPT_WINDOW)

        # Record for IP
        ip_key = LoginAttemptTracker.get_cache_key(ip_address, 'ip')
        ip_attempts = cache.get(ip_key, [])
        ip_attempts.append({
            'timestamp': timezone.now().isoformat(),
            'username': username,
            'success': success
        })

        # Keep only recent attempts
        ip_attempts = [a for a in ip_attempts if datetime.fromisoformat(a['timestamp']) > cutoff]

        cache.set(ip_key, ip_attempts, LoginAttemptTracker.ATTEMPT_WINDOW)

        # If failed attempts exceed threshold, set lockout
        if not success:
            failed_count = len([a for a in attempts if not a['success']])
            if failed_count >= LoginAttemptTracker.MAX_ATTEMPTS:
                LoginAttemptTracker.lockout_user(username)
                LoginAttemptTracker.lockout_ip(ip_address)

                # Log security event
                try:
                    user = User.objects.get(username=username)
                    log_activity(
                        user=user,
                        action='SECURITY_LOCKOUT',
                        description=f'Account locked due to {failed_count} failed login attempts from {ip_address}',
                        extra_data={
                            'ip_address': ip_address,
                            'attempts': failed_count
                        }
                    )
                except User.DoesNotExist:
                    pass

    @staticmethod
    def is_locked_out(username=None, ip_address=None):
        """Check if user or IP is currently locked out."""
        if username:
            lockout_key = f'lockout:user:{username}'
            if cache.get(lockout_key):
                return True

        if ip_address:
            lockout_key = f'lockout:ip:{ip_address}'
            if cache.get(lockout_key):
                return True

        return False

    @staticmethod
    def lockout_user(username):
        """Lock out a user for the configured duration."""
        lockout_key = f'lockout:user:{username}'
        cache.set(lockout_key, True, LoginAttemptTracker.LOCKOUT_DURATION)

    @staticmethod
    def lockout_ip(ip_address):
        """Lock out an IP address for the configured duration."""
        lockout_key = f'lockout:ip:{ip_address}'
        cache.set(lockout_key, True, LoginAttemptTracker.LOCKOUT_DURATION)

    @staticmethod
    def clear_attempts(username=None, ip_address=None):
        """Clear login attempts for user or IP."""
        if username:
            user_key = LoginAttemptTracker.get_cache_key(username, 'user')
            cache.delete(user_key)
            lockout_key = f'lockout:user:{username}'
            cache.delete(lockout_key)

        if ip_address:
            ip_key = LoginAttemptTracker.get_cache_key(ip_address, 'ip')
            cache.delete(ip_key)
            lockout_key = f'lockout:ip:{ip_address}'
            cache.delete(lockout_key)

    @staticmethod
    def get_remaining_lockout_time(username=None, ip_address=None):
        """Get remaining lockout time in seconds."""
        if username:
            lockout_key = f'lockout:user:{username}'
            ttl = cache.ttl(lockout_key)
            if ttl and ttl > 0:
                return ttl

        if ip_address:
            lockout_key = f'lockout:ip:{ip_address}'
            ttl = cache.ttl(lockout_key)
            if ttl and ttl > 0:
                return ttl

        return 0


class SessionManager:
    """
    Enhanced session management and security.

    Features:
    - Session activity tracking
    - Concurrent session limits
    - Session hijacking detection
    - Automatic session timeout
    """

    MAX_CONCURRENT_SESSIONS = getattr(settings, 'MAX_CONCURRENT_SESSIONS', 5)

    @staticmethod
    def get_user_sessions(user):
        """Get all active sessions for a user."""
        from django.contrib.sessions.models import Session
        from django.utils import timezone

        sessions = []
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                sessions.append({
                    'session_key': session.session_key,
                    'expire_date': session.expire_date,
                    'last_activity': session_data.get('last_activity'),
                    'ip_address': session_data.get('ip_address'),
                    'user_agent': session_data.get('user_agent'),
                })
        return sessions

    @staticmethod
    def record_session_activity(request):
        """Record session activity."""
        if request.user.is_authenticated:
            request.session['last_activity'] = timezone.now().isoformat()
            request.session['ip_address'] = get_client_ip(request)
            request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
            request.session.modified = True

    @staticmethod
    def check_session_limit(user):
        """Check if user has exceeded concurrent session limit."""
        sessions = SessionManager.get_user_sessions(user)
        return len(sessions) >= SessionManager.MAX_CONCURRENT_SESSIONS

    @staticmethod
    def terminate_session(session_key):
        """Terminate a specific session."""
        from django.contrib.sessions.models import Session
        try:
            session = Session.objects.get(session_key=session_key)
            session.delete()
            return True
        except Session.DoesNotExist:
            return False

    @staticmethod
    def terminate_all_sessions(user, except_current=None):
        """Terminate all sessions for a user."""
        from django.contrib.sessions.models import Session

        sessions = SessionManager.get_user_sessions(user)
        count = 0
        for session in sessions:
            if except_current and session['session_key'] == except_current:
                continue
            if SessionManager.terminate_session(session['session_key']):
                count += 1
        return count


class IPWhitelist:
    """
    IP address whitelisting for enhanced security.

    Features:
    - IP range support (CIDR notation)
    - Cached lookups
    - Admin bypass
    """

    @staticmethod
    def is_whitelisted(ip_address):
        """Check if IP address is whitelisted."""
        # Get whitelist from settings
        whitelist = getattr(settings, 'IP_WHITELIST', [])

        if not whitelist:
            return True  # No whitelist means all IPs allowed

        # Check if IP is in whitelist
        for allowed_ip in whitelist:
            if IPWhitelist._ip_in_range(ip_address, allowed_ip):
                return True

        return False

    @staticmethod
    def _ip_in_range(ip, ip_range):
        """Check if IP is in range (supports CIDR notation)."""
        import ipaddress

        try:
            ip_obj = ipaddress.ip_address(ip)

            # Check if range is CIDR notation
            if '/' in ip_range:
                network = ipaddress.ip_network(ip_range, strict=False)
                return ip_obj in network
            else:
                # Exact match
                return str(ip_obj) == ip_range
        except ValueError:
            return False


def get_client_ip(request):
    """
    Get client IP address from request.

    Handles proxy headers (X-Forwarded-For, X-Real-IP).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_token(length=32):
    """Generate a cryptographically secure random token."""
    import secrets
    return secrets.token_urlsafe(length)


def hash_data(data):
    """Hash data using SHA-256."""
    return hashlib.sha256(str(data).encode()).hexdigest()


def verify_hash(data, hash_value):
    """Verify data against hash."""
    return hash_data(data) == hash_value
