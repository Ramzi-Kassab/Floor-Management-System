# API Documentation

**Version:** 1.0
**Last Updated:** November 18, 2025

## Overview

The Floor Management System provides a comprehensive RESTful API with authentication, rate limiting, and versioning support.

## Base URL

```
Production: https://yourdomain.com/core/api/
Development: http://localhost:8000/core/api/
```

## Authentication

### Method 1: Session Authentication (Web)
Use Django's built-in session authentication for web browsers.

### Method 2: API Key Authentication
For programmatic access, use API keys:

```http
X-API-Key: fms_your_api_key_here
X-API-Secret: your_api_secret_here
```

**Generate API Key:**
```python
from core.api import APIKeyAuth

api_key, api_secret = APIKeyAuth.generate_key(user, name='My App')
# Save these credentials securely!
```

## Rate Limiting

Rate limits apply per user (or IP for unauthenticated requests):

- **Default:** 60 requests per minute
- **Authenticated:** 100 requests per minute
- **API Key:** 1000 requests per minute

Rate limit headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700000000
```

## API Versioning

Specify API version using:

**Method 1: URL Path (Recommended)**
```
GET /core/api/v1/users/
GET /core/api/v2/users/
```

**Method 2: Header**
```http
X-API-Version: 1.0
```

**Method 3: Query Parameter**
```
GET /core/api/users/?version=1.0
```

## Response Format

### Success Response
```json
{
    "success": true,
    "status": 200,
    "message": "Operation successful",
    "data": { },
    "meta": { }
}
```

### Error Response
```json
{
    "success": false,
    "status": 400,
    "message": "Error message",
    "code": "ERROR_CODE",
    "errors": { }
}
```

### Paginated Response
```json
{
    "success": true,
    "status": 200,
    "data": [ ],
    "meta": {
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total_pages": 5,
            "total_items": 100,
            "has_next": true,
            "has_previous": false
        }
    }
}
```

## API Endpoints

### Notifications

#### List Notifications
```http
GET /core/api/notifications/
```

**Parameters:**
- `limit` (int): Items per page (default: 10)
- `offset` (int): Offset for pagination
- `unread_only` (bool): Filter unread notifications

**Response:**
```json
{
    "success": true,
    "data": {
        "notifications": [...],
        "total": 25,
        "has_more": true
    }
}
```

#### Get Unread Count
```http
GET /core/api/notifications/unread-count/
```

#### Mark as Read
```http
POST /core/api/notifications/{id}/read/
```

#### Mark All as Read
```http
POST /core/api/notifications/mark-all-read/
```

#### Delete Notification
```http
POST /core/api/notifications/{id}/delete/
```

### Export

#### Export Data
```http
GET /core/api/export/
```

**Parameters:**
- `model` (required): App.Model (e.g., 'hr.Person')
- `format` (required): 'csv', 'excel', 'pdf'
- `fields` (required): Comma-separated field list
- `headers` (optional): Comma-separated header list
- `filters` (optional): JSON filter object

**Example:**
```
GET /core/api/export/?model=hr.Person&format=excel&fields=id,first_name,last_name,email
```

### Security

#### Validate Password Strength
```http
POST /core/api/security/password-strength/
```

**Body:**
```json
{
    "password": "MyP@ssw0rd123"
}
```

**Response:**
```json
{
    "valid": true,
    "score": 85,
    "strength": "Strong",
    "errors": [],
    "suggestions": []
}
```

#### Get Active Sessions
```http
GET /core/api/security/sessions/
```

#### Terminate Session
```http
POST /core/api/security/sessions/{session_key}/terminate/
```

#### Terminate All Sessions
```http
POST /core/api/security/sessions/terminate-all/
```

### Search

#### Global Search
```http
GET /core/api/search/
```

**Parameters:**
- `q` (required): Search query
- `modules` (optional): Comma-separated module list

### Filters

#### List Saved Filters
```http
GET /core/api/filters/
```

**Parameters:**
- `module` (optional): Filter by module

#### Save Filter
```http
POST /core/api/filters/save/
```

**Body:**
```json
{
    "name": "Active Employees",
    "filters": {"status": "ACTIVE"},
    "module": "hr"
}
```

#### Delete Filter
```http
POST /core/api/filters/{filter_key}/delete/
```

## Error Codes

| Code | Description |
|------|-------------|
| `AUTHENTICATION_REQUIRED` | User must be authenticated |
| `INVALID_API_CREDENTIALS` | API key/secret invalid |
| `MISSING_API_CREDENTIALS` | API key/secret not provided |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `METHOD_NOT_ALLOWED` | HTTP method not allowed |
| `UNSUPPORTED_VERSION` | API version not supported |
| `VALIDATION_ERROR` | Request data validation failed |
| `NOT_FOUND` | Resource not found |
| `PERMISSION_DENIED` | Insufficient permissions |

## Best Practices

1. **Always use HTTPS** in production
2. **Store API credentials securely** (never in code)
3. **Handle rate limiting** (implement exponential backoff)
4. **Version your API calls** (specify version explicitly)
5. **Validate input** on client side before sending
6. **Handle errors gracefully** (check `success` field)
7. **Use pagination** for large datasets
8. **Implement caching** for frequently accessed data

## Examples

### Python (requests library)
```python
import requests

# Session authentication
session = requests.Session()
session.post('https://domain.com/login/', data={
    'username': 'user',
    'password': 'pass'
})

response = session.get('https://domain.com/core/api/notifications/')
data = response.json()

# API Key authentication
headers = {
    'X-API-Key': 'fms_your_key',
    'X-API-Secret': 'your_secret'
}

response = requests.get(
    'https://domain.com/core/api/export/',
    params={
        'model': 'hr.Person',
        'format': 'csv',
        'fields': 'id,first_name,last_name'
    },
    headers=headers
)
```

### JavaScript (fetch)
```javascript
// Session authentication (browser)
fetch('/core/api/notifications/')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(data.data);
        }
    });

// API Key authentication
fetch('/core/api/export/?model=hr.Person&format=excel&fields=id,name', {
    headers: {
        'X-API-Key': 'fms_your_key',
        'X-API-Secret': 'your_secret'
    }
})
    .then(response => response.blob())
    .then(blob => {
        // Download file
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'export.xlsx';
        a.click();
    });
```

### cURL
```bash
# Get notifications
curl -H "X-API-Key: fms_your_key" \
     -H "X-API-Secret: your_secret" \
     https://domain.com/core/api/notifications/

# Export data
curl -H "X-API-Key: fms_your_key" \
     -H "X-API-Secret: your_secret" \
     "https://domain.com/core/api/export/?model=hr.Person&format=csv&fields=id,name" \
     -o export.csv
```

## Support

For API support or to report issues:
- Email: support@yourdomain.com
- Documentation: https://docs.yourdomain.com/api
- Status Page: https://status.yourdomain.com

## Changelog

### Version 1.0 (2025-11-18)
- Initial API release
- Notifications API
- Export API
- Security API
- Search API
- Filter API
- Rate limiting
- API key authentication
- Versioning support
