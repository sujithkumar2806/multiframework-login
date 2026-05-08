#!/bin/bash
# Backup SOURCE RDS to dump.sql and restore to TARGET RDS

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/ubuntu/backups"
BACKUP_FILE="$BACKUP_DIR/rds_backup_$TIMESTAMP.sql"

SOURCE_HOST="multiframework-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com"
TARGET_HOST="multiframework-target-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com"
DB_USER="dbadmin"
DB_PASS="SecurePass123!"
DB_NAME="postgres"

mkdir -p $BACKUP_DIR

echo "[$(date)] Step 1: Dumping SOURCE RDS to $BACKUP_FILE..."
PGPASSWORD=$DB_PASS pg_dump \
    -h $SOURCE_HOST \
    -U $DB_USER \
    -d $DB_NAME \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "[$(date)] Dump successful! File size: $(du -sh $BACKUP_FILE | cut -f1)"
else
    echo "[$(date)] ERROR: Dump failed!"
    exit 1
fi

echo "[$(date)] Step 2: Restoring dump to TARGET RDS..."
PGPASSWORD=$DB_PASS psql \
    -h $TARGET_HOST \
    -U $DB_USER \
    -d $DB_NAME \
    -f $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "[$(date)] Restore successful!"
else
    echo "[$(date)] ERROR: Restore failed!"
    exit 1
fi

echo "[$(date)] Step 3: Verifying data in TARGET RDS..."
PGPASSWORD=$DB_PASS psql \
    -h $TARGET_HOST \
    -U $DB_USER \
    -d $DB_NAME \
    -c "SELECT COUNT(*) as total_users FROM users;"

# Keep only last 7 backups
find $BACKUP_DIR -name "rds_backup_*.sql" -mtime +7 -delete
echo "[$(date)] Old backups cleaned. Done!"
