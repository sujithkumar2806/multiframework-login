import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

MIGRATIONS = [
    # Add new migrations here in order — never edit existing ones
    {
        "version": 1,
        "description": "Create users table",
        "sql": """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """
    },
    {
        "version": 2,
        "description": "Create sessions table",
        "sql": """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                token VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP NOT NULL
            );
        """
    },
    # example: add a column later
    # {
    #     "version": 3,
    #     "description": "Add profile_picture to users",
    #     "sql": "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture TEXT;"
    # },
]

def run_migrations():
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Create migrations tracking table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Get already-applied versions
    cur.execute("SELECT version FROM schema_migrations ORDER BY version;")
    applied = {row[0] for row in cur.fetchall()}

    for migration in MIGRATIONS:
        v = migration["version"]
        if v in applied:
            print(f"  [skip] v{v}: {migration['description']} (already applied)")
            continue

        print(f"  [run]  v{v}: {migration['description']}")
        cur.execute(migration["sql"])
        cur.execute(
            "INSERT INTO schema_migrations (version, description) VALUES (%s, %s)",
            (v, migration["description"])
        )
        print(f"  [done] v{v}")

    cur.close()
    conn.close()
    print("All migrations complete.")

if __name__ == "__main__":
    run_migrations()
