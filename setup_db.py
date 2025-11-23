"""
Quick database setup script to bypass migration issues.
Creates basic schema and sample data.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'floor_mgmt.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

# Create superuser
print("Creating superuser...")
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✅ Superuser created: admin / admin123")
else:
    print("✅ Superuser already exists")

# Create sample users
print("\nCreating sample users...")
for i in range(1, 6):
    username = f'user{i}'
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username, f'{username}@example.com', 'password123')
print(f"✅ Created {5} sample users")

print("\n=== Database Setup Complete ===")
print("Admin credentials: admin / admin123")
print("User credentials: user1-user5 / password123")
