#!/usr/bin/env python3
"""
Quickly fix remaining import errors by updating views to import what actually exists.
"""
import re
from pathlib import Path

# Define fixes for each module based on our earlier analysis
fixes = {
    'gps_system': {
        'file': 'floor_app/operations/gps_system/views.py',
        'pattern': r'from \.models import \([^)]+\)',
        'replacement': 'from .models import LocationVerification, GeofenceDefinition, GPSTrackingLog',
    },
    'hiring': {
        'file': 'floor_app/operations/hiring/views.py',
        'find_replace': [
            ('from .models import (', 'from .models import ('),  # Already fixed earlier
        ]
    },
}

# For modules where we just need to use the actual model names:
simple_replacements = [
    # GPS module - already correct in models but import line might be malformed
    ('floor_app/operations/gps_system/views.py', [
        ('LocationVerification, GeofenceDefinition, GPSTrackingLog', 'LocationVerification,\n    GeofenceDefinition,\n    GPSTrackingLog'),
    ]),
]

# Read and fix files
for file_path, replacements in simple_replacements:
    p = Path(file_path)
    if p.exists():
        content = p.read_text()
        for old, new in replacements:
            content = content.replace(old, new)
        p.write_text(content)
        print(f"Fixed {file_path}")

print("Done!")
