#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/ubuntu/backups"
BACKUP_FILE="$BACKUP_DIR/users_backup_$TIMESTAMP.sql"

SOURCE_HOST="multiframework-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com"
TARGET_HOST="multiframework-target-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com"
DB_USER="dbadmin"
DB_PASS="SecurePass123!"
DB_NAME="postgres"

mkdir -p $BACKUP_DIR

echo "[$(date)] Step 1: Dumping ONLY users table from SOURCE RDS..."
docker run --rm \
  -e PGPASSWORD=$DB_PASS \
  postgres:15 \
  pg_dump -h $SOURCE_HOST -U $DB_USER -d $DB_NAME \
  --no-owner --no-acl \
  --table=public.users \
  --data-only \
  > $BACKUP_FILE

if [ $? -eq 0 ] && [ -s $BACKUP_FILE ]; then
    echo "[$(date)] Dump successful! Size: $(du -sh $BACKUP_FILE | cut -f1)"
    echo "[$(date)] Preview of dump file:"
    cat $BACKUP_FILE
else
    echo "[$(date)] ERROR: Dump failed!"
    exit 1
fi

echo "[$(date)] Step 2: Restoring users to TARGET RDS..."
docker run --rm \
  -e PGPASSWORD=$DB_PASS \
  -v $BACKUP_FILE:/backup.sql \
  postgres:15 \
  psql -h $TARGET_HOST -U $DB_USER -d $DB_NAME \
  -c "TRUNCATE TABLE users RESTART IDENTITY CASCADE;" \
  -f /backup.sql

if [ $? -eq 0 ]; then
    echo "[$(date)] Restore successful!"
else
    echo "[$(date)] ERROR: Restore failed!"
    exit 1
fi

echo "[$(date)] Step 3: Verify users in TARGET RDS..."
docker run --rm \
  -e PGPASSWORD=$DB_PASS \
  postgres:15 \
  psql -h $TARGET_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT id, username, email, created_at FROM users ORDER BY id;"

find $BACKUP_DIR -name "users_backup_*.sql" -mtime +7 -delete
echo "[$(date)] Done! Backup: $BACKUP_FILE"
