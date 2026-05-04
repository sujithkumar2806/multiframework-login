#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."

# Wait for database
until python3 -c "
import psycopg2
import sys
import os
try:
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'multiframework-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com'),
        port=os.environ.get('DB_PORT', 5432),
        dbname=os.environ.get('DB_NAME', 'postgres'),
        user=os.environ.get('DB_USER', 'dbadmin'),
        password=os.environ.get('DB_PASSWORD', 'SecurePass123!')
    )
    conn.close()
    print('Database ready!')
    sys.exit(0)
except Exception as e:
    print(f'Waiting for database...')
    sys.exit(1)
" 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Postgres is up - starting Django..."
exec "$@"
