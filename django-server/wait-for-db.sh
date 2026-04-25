#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to accept connections
until python3 -c "
import psycopg2
import sys
try:
    conn = psycopg2.connect(
        host='postgres',
        database='userdb',
        user='admin',
        password='secretpassword'
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

echo "Postgres is up - executing command"

# Check if migrations have been applied
if ! python3 manage.py showmigrations api | grep -q "[X]"; then
    echo "Running migrations..."
    python3 manage.py makemigrations api || true
    python3 manage.py migrate || true
else
    echo "Migrations already applied"
fi

echo "Starting Django server..."
exec "$@"
