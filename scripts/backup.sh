#!/bin/bash
# Floor Management System - Database Backup Script

set -e

# Configuration
BACKUP_DIR="/var/backups/floor-mgmt"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="floor_mgmt_db"
DB_USER="floor_mgmt_user"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "================================"
echo "Database Backup Script"
echo "================================"
echo ""

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup filename
BACKUP_FILE="$BACKUP_DIR/floor_mgmt_backup_$DATE.sql"

echo "Backing up database..."
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"
echo ""

# Perform backup
pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE

# Compress backup
echo "Compressing backup..."
gzip $BACKUP_FILE
BACKUP_FILE="$BACKUP_FILE.gz"

echo -e "${GREEN}✓${NC} Backup completed successfully"
echo "Backup saved to: $BACKUP_FILE"

# Get file size
SIZE=$(du -h $BACKUP_FILE | cut -f1)
echo "Backup size: $SIZE"

# Delete backups older than 30 days
echo ""
echo "Cleaning old backups (older than 30 days)..."
find $BACKUP_DIR -name "floor_mgmt_backup_*.sql.gz" -type f -mtime +30 -delete
echo -e "${GREEN}✓${NC} Old backups cleaned"

echo ""
echo "================================"
echo "Backup completed: $DATE"
echo "================================"
