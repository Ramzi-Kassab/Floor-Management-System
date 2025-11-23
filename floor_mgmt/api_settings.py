"""
API Configuration Settings

Settings for REST Framework and API documentation.
"""

# REST Framework Settings
REST_FRAMEWORK = {
    # Authentication
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],

    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,

    # Filtering
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # Renderers
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],

    # Parsers
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],

    # Throttling
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },

    # Schema
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Error handling
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',

    # Versioning (if needed)
    # 'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',

    # Date/Time formats
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
}

# Spectacular Settings (OpenAPI/Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Floor Management System API',
    'DESCRIPTION': '''
    Complete REST API for Floor Management System

    ## Features
    - HR & Employee Management
    - Leave Request Workflow
    - Asset Management
    - Shift Scheduling
    - Contract Management

    ## Authentication
    This API uses Token Authentication. Include your token in the Authorization header:
    ```
    Authorization: Token your-token-here
    ```

    ## Pagination
    All list endpoints are paginated. Use `page` parameter to navigate:
    - `/api/hr/employees/?page=2`

    ## Filtering & Search
    Most endpoints support filtering and search:
    - `/api/hr/employees/?department=1&status=ACTIVE`
    - `/api/hr/employees/?search=John`

    ## Rate Limiting
    - Anonymous: 100 requests/hour
    - Authenticated: 1000 requests/hour
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    # Schema configuration
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,

    # UI configuration
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },

    # Security schemes
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'TokenAuth': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'Token-based authentication. Format: `Token <your-token>`'
            },
            'SessionAuth': {
                'type': 'apiKey',
                'in': 'cookie',
                'name': 'sessionid',
                'description': 'Session-based authentication using Django sessions'
            }
        }
    },

    # Tags for grouping endpoints
    'TAGS': [
        {'name': 'HR - Persons', 'description': 'Person management endpoints'},
        {'name': 'HR - Employees', 'description': 'Employee management endpoints'},
        {'name': 'HR - Departments', 'description': 'Department management endpoints'},
        {'name': 'HR - Positions', 'description': 'Position management endpoints'},
        {'name': 'HR - Contracts', 'description': 'Employment contract management'},
        {'name': 'HR - Shifts', 'description': 'Shift management and assignments'},
        {'name': 'HR - Assets', 'description': 'Company asset tracking'},
        {'name': 'HR - Leave', 'description': 'Leave management and approvals'},
    ],

    # Custom preprocessing hook
    'PREPROCESSING_HOOKS': [],

    # Custom postprocessing hook
    'POSTPROCESSING_HOOKS': [],

    # Enum handling
    'ENUM_NAME_OVERRIDES': {},

    # Serve permissions
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],

    # Authentication
    'SERVE_AUTHENTICATION': None,
}
