#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/ubuntu/backups"
BACKUP_FILE="$BACKUP_DIR/rds_backup_$TIMESTAMP.sql"

SOURCE_HOST="multiframework-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com"
TARGET_HOST="multiframework-target-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com"
DB_USER="dbadmin"
DB_PASS="SecurePass123!"
DB_NAME="postgres"

mkdir -p $BACKUP_DIR

echo "[$(date)] Step 1: Dumping SOURCE RDS using postgres:15 Docker image..."
docker run --rm \
  -e PGPASSWORD=$DB_PASS \
  postgres:15 \
  pg_dump -h $SOURCE_HOST -U $DB_USER -d $DB_NAME \
  --no-owner --no-acl --clean --if-exists \
  > $BACKUP_FILE

if [ $? -eq 0 ] && [ -s $BACKUP_FILE ]; then
    echo "[$(date)] Dump successful! Size: $(du -sh $BACKUP_FILE | cut -f1)"
else
    echo "[$(date)] ERROR: Dump failed!"
    exit 1
fi

echo "[$(date)] Step 2: Restoring to TARGET RDS..."
docker run --rm \
  -e PGPASSWORD=$DB_PASS \
  -v $BACKUP_FILE:/backup.sql \
  postgres:15 \
  psql -h $TARGET_HOST -U $DB_USER -d $DB_NAME -f /backup.sql

if [ $? -eq 0 ]; then
    echo "[$(date)] Restore successful!"
else
    echo "[$(date)] ERROR: Restore failed!"
    exit 1
fi

echo "[$(date)] Step 3: Verifying TARGET RDS..."
docker run --rm \
  -e PGPASSWORD=$DB_PASS \
  postgres:15 \
  psql -h $TARGET_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT COUNT(*) as total_users FROM users;"

find $BACKUP_DIR -name "rds_backup_*.sql" -mtime +7 -delete
echo "[$(date)] Done! Backup saved: $BACKUP_FILE"
