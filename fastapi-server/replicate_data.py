import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# Source database (your existing RDS)
SOURCE_DB_URL = os.environ.get("DATABASE_URL")
# Target database (the new RDS you will create)
TARGET_DB_URL = os.environ.get("TARGET_DATABASE_URL")

if not SOURCE_DB_URL:
    print("ERROR: SOURCE_DATABASE_URL not set (DATABASE_URL env var)")
    sys.exit(1)
if not TARGET_DB_URL:
    print("ERROR: TARGET_DATABASE_URL not set")
    sys.exit(1)

# Tables to replicate (name, primary key, order column)
TABLES = [
    {"name": "users", "pk": "id", "order_by": "id"},
    {"name": "sessions", "pk": "id", "order_by": "id"}
]

def ensure_control_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS replication_control (
            table_name TEXT PRIMARY KEY,
            last_copied_id BIGINT,
            last_sync TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()

def get_last_copied_id(conn, table_name):
    cur = conn.cursor()
    cur.execute("SELECT last_copied_id FROM replication_control WHERE table_name = %s", (table_name,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else 0

def update_last_copied_id(conn, table_name, last_id):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO replication_control (table_name, last_copied_id, last_sync)
        VALUES (%s, %s, %s)
        ON CONFLICT (table_name) DO UPDATE SET
            last_copied_id = EXCLUDED.last_copied_id,
            last_sync = EXCLUDED.last_sync
    """, (table_name, last_id, datetime.now()))
    conn.commit()
    cur.close()

def replicate_table(src_conn, tgt_conn, table_info):
    table = table_info["name"]
    pk = table_info["pk"]
    order_by = table_info["order_by"]

    last_id = get_last_copied_id(tgt_conn, table)
    print(f"Replicating {table}: last copied id = {last_id}")

    src_cur = src_conn.cursor()
    tgt_cur = tgt_conn.cursor()

    # Fetch new rows from source
    src_cur.execute(f"SELECT * FROM {table} WHERE {pk} > %s ORDER BY {order_by}", (last_id,))
    rows = src_cur.fetchall()
    if not rows:
        print(f"  No new rows in {table}")
        src_cur.close()
        tgt_cur.close()
        return

    # Get column names
    col_names = [desc[0] for desc in src_cur.description]
    placeholders = ",".join(["%s"] * len(col_names))
    columns = ",".join(col_names)

    # Insert/update into target
    for row in rows:
        tgt_cur.execute(f"""
            INSERT INTO {table} ({columns}) VALUES ({placeholders})
            ON CONFLICT ({pk}) DO UPDATE SET
                {", ".join([f"{col}=EXCLUDED.{col}" for col in col_names if col != pk])}
        """, row)

    tgt_conn.commit()
    new_last_id = rows[-1][col_names.index(pk)]
    update_last_copied_id(tgt_conn, table, new_last_id)
    print(f"  Copied {len(rows)} rows to {table}. New last id: {new_last_id}")

    src_cur.close()
    tgt_cur.close()

def main():
    print(f"[{datetime.now()}] Starting data replication")

    src_conn = psycopg2.connect(SOURCE_DB_URL)
    tgt_conn = psycopg2.connect(TARGET_DB_URL)
    src_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    tgt_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    ensure_control_table(tgt_conn)

    for table in TABLES:
        replicate_table(src_conn, tgt_conn, table)

    src_conn.close()
    tgt_conn.close()
    print(f"[{datetime.now()}] Replication finished\n")

if __name__ == "__main__":
    main()
