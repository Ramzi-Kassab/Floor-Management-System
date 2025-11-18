# Security Features Documentation

**Last Updated:** November 18, 2025

## Overview

Comprehensive security features including password validation, login attempt tracking, session management, and security headers.

## Features Implemented

### 1. Password Strength Validation
- Minimum 8 characters (recommended 12+)
- Uppercase/lowercase/numbers/special characters
- Common password detection
- Sequential/repeated character detection
- User attribute similarity checking
- Strength scoring (0-100)

### 2. Login Attempt Tracking
- Configurable max attempts (default: 5)
- Automatic account lockout (default: 15 minutes)
- Per-user and per-IP tracking
- Automatic cleanup of old attempts
- Security event logging

### 3. Session Management
- Track all active sessions per user
- Session activity monitoring
- Concurrent session limits (default: 5)
- Terminate specific or all sessions
- IP and user agent tracking

### 4. Security Middleware
- `SessionActivityMiddleware`: Track session activity
- `IPWhitelistMiddleware`: Enforce IP restrictions
- `SecurityHeadersMiddleware`: Add security headers

### 5. Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: SAMEORIGIN
- X-XSS-Protection: enabled
- Strict-Transport-Security (HTTPS only)
- Content-Security-Policy

## API Endpoints

```
POST /core/api/security/password-strength/      - Validate password strength
GET  /core/api/security/sessions/               - Get active sessions
POST /core/api/security/sessions/<key>/terminate/ - Terminate session
POST /core/api/security/sessions/terminate-all/ - Terminate all sessions
```

## Usage Examples

### Password Validation
```python
from core.security import PasswordValidator

result = PasswordValidator.validate_strength('MyP@ssw0rd123', user=user)
# Returns: {
#     'valid': True,
#     'score': 85,
#     'errors': [],
#     'suggestions': [],
#     'strength': 'Strong'
# }
```

### Login Tracking
```python
from core.security import LoginAttemptTracker

# Check if user is locked out
if LoginAttemptTracker.is_locked_out(username='john', ip_address='192.168.1.1'):
    # Deny access
    pass
```

### Session Management
```python
from core.security import SessionManager

# Get all user sessions
sessions = SessionManager.get_user_sessions(user)

# Terminate all sessions except current
count = SessionManager.terminate_all_sessions(user, except_current=session_key)
```

## Configuration

Add to `settings.py`:

```python
# Security settings
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = 900  # 15 minutes
LOGIN_ATTEMPT_WINDOW = 300  # 5 minutes
MAX_CONCURRENT_SESSIONS = 5

# IP Whitelist (optional)
IP_WHITELIST = [
    '192.168.1.0/24',  # CIDR notation
    '10.0.0.1',        # Specific IP
]
IP_WHITELIST_PATHS = ['/admin/', '/core/system/']

# Middleware
MIDDLEWARE = [
    # ... other middleware
    'core.middleware.SessionActivityMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    # 'core.middleware.IPWhitelistMiddleware',  # Optional
]
```

## Files Created

- `core/security.py` - Security utilities (490 lines)
- `core/middleware.py` - Security middleware (180 lines)
- Security API endpoints in `core/views.py` (+127 lines)
- Security routes in `core/urls.py` (+4 routes)

## Total: ~800 lines of security code
