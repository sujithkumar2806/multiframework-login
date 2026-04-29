#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."

# Extract connection info from DATABASE_URL
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
DB_PORT=$(echo $DATABASE_URL | grep -oP ':\K\d+(?=/|$)')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\).*/\1/p')
DB_PASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\).*/\1/p')

echo "Connecting to $DB_HOST:$DB_PORT as $DB_USER"

# Wait for PostgreSQL to accept connections
until python3 -c "
import psycopg2
import sys
import os
try:
    conn = psycopg2.connect(
        host='$DB_HOST',
        port='$DB_PORT',
        dbname='$DB_NAME',
        user='$DB_USER',
        password='$DB_PASSWORD'
    )
    conn.close()
    print('Database ready!')
    sys.exit(0)
except Exception as e:
    print(f'Waiting for database... {e}')
    sys.exit(1)
" 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 2
done

echo "Postgres is up - executing command"

# Run migrations if needed
if ! python3 manage.py showmigrations api 2>/dev/null | grep -q "[X]"; then
    echo "Running migrations..."
    python3 manage.py makemigrations api || true
    python3 manage.py migrate || true
else
    echo "Migrations already applied"
fi

echo "Starting Django server..."
exec "$@"
