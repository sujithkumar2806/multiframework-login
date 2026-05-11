#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# ========== CONFIGURATION ==========
SOURCE_DB_URL = os.environ.get("DATABASE_URL")
TARGET_DB_URL = os.environ.get("TARGET_DATABASE_URL")

if not SOURCE_DB_URL or not TARGET_DB_URL:
    print("ERROR: Both DATABASE_URL and TARGET_DATABASE_URL must be set.")
    sys.exit(1)

TABLES = [
    {"name": "users", "pk": "id", "order_by": "id", "timestamp_col": "updated_at"},
    {"name": "sessions", "pk": "id", "order_by": "id", "timestamp_col": "created_at"}
]

CONTROL_TABLE = "replication_control"

def get_connection(url):
    conn = psycopg2.connect(url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

def ensure_control_table(conn):
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {CONTROL_TABLE} (
            table_name TEXT PRIMARY KEY,
            last_sync TIMESTAMP,
            last_copied_id BIGINT,
            last_updated TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()

def get_last_sync_info(conn, table_name):
    cur = conn.cursor()
    cur.execute(f"SELECT last_sync, last_copied_id FROM {CONTROL_TABLE} WHERE table_name = %s", (table_name,))
    row = cur.fetchone()
    cur.close()
    return row if row else (None, 0)

def update_last_sync(conn, table_name, last_sync_time, last_copied_id):
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {CONTROL_TABLE} (table_name, last_sync, last_copied_id, last_updated)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (table_name) DO UPDATE SET
            last_sync = EXCLUDED.last_sync,
            last_copied_id = EXCLUDED.last_copied_id,
            last_updated = EXCLUDED.last_updated
    """, (table_name, last_sync_time, last_copied_id, datetime.now()))
    conn.commit()
    cur.close()

def sync_schema(src_conn, tgt_conn, table_name):
    """Ensure target table has same columns as source (idempotent)."""
    # Get column names from source
    cur = src_conn.cursor()
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position;
    """, (table_name,))
    src_cols = cur.fetchall()
    cur.close()

    # Get existing columns in target
    cur = tgt_conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public';
    """, (table_name,))
    tgt_cols = {row[0] for row in cur.fetchall()}
    cur.close()

    if not tgt_cols:
        # Table doesn't exist – create it with all columns
        cols_def = []
        for col_name, data_type, is_nullable, col_default in src_cols:
            col_def = f"{col_name} {data_type}"
            if is_nullable == 'NO':
                col_def += " NOT NULL"
            if col_default:
                col_def += f" DEFAULT {col_default}"
            cols_def.append(col_def)
        create_sql = f"CREATE TABLE {table_name} ({', '.join(cols_def)});"
        tgt_conn.cursor().execute(create_sql)
        tgt_conn.commit()
        print(f"  Created table {table_name} in target.")
    else:
        # Add missing columns
        for col_name, data_type, is_nullable, col_default in src_cols:
            if col_name not in tgt_cols:
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {data_type}"
                if col_default:
                    alter_sql += f" DEFAULT {col_default}"
                if is_nullable == 'NO':
                    alter_sql += " NOT NULL"
                tgt_conn.cursor().execute(alter_sql)
                tgt_conn.commit()
                print(f"  Added column {col_name} to {table_name}.")

def sync_data(src_conn, tgt_conn, table_info):
    table = table_info["name"]
    pk = table_info["pk"]
    order_by = table_info["order_by"]
    ts_col = table_info.get("timestamp_col")

    last_sync_time, last_copied_id = get_last_sync_info(tgt_conn, table)

    # Build query for new/updated rows
    src_cur = src_conn.cursor()
    if last_sync_time and ts_col:
        src_cur.execute(f"""
            SELECT * FROM {table} 
            WHERE {pk} > %s OR {ts_col} > %s
            ORDER BY {order_by}
        """, (last_copied_id, last_sync_time))
    else:
        # First run – copy everything
        src_cur.execute(f"SELECT * FROM {table} ORDER BY {order_by}")

    rows = src_cur.fetchall()
    if not rows:
        print(f"  No new data for {table}")
        src_cur.close()
        return

    # Get column names
    col_names = [desc[0] for desc in src_cur.description]
    placeholders = ','.join(['%s'] * len(col_names))
    columns = ','.join(col_names)

    tgt_cur = tgt_conn.cursor()
    for row in rows:
        # Upsert: INSERT ... ON CONFLICT UPDATE
        updates = ', '.join([f"{col}=EXCLUDED.{col}" for col in col_names if col != pk])
        tgt_cur.execute(f"""
            INSERT INTO {table} ({columns}) VALUES ({placeholders})
            ON CONFLICT ({pk}) DO UPDATE SET {updates}
        """, row)

    tgt_conn.commit()
    last_id = rows[-1][col_names.index(pk)]
    # Use current timestamp as last_sync (or max(updated_at) from rows – omitted for simplicity)
    update_last_sync(tgt_conn, table, datetime.now(), last_id)
    print(f"  Copied {len(rows)} rows to {table}. New last id: {last_id}")

    src_cur.close()
    tgt_cur.close()

def main():
    print(f"[{datetime.now()}] Starting schema + data replication")

    src_conn = get_connection(SOURCE_DB_URL)
    tgt_conn = get_connection(TARGET_DB_URL)

    ensure_control_table(tgt_conn)

    for table_info in TABLES:
        table = table_info["name"]
        print(f"\nSyncing {table}:")
        print("  Schema sync")
        sync_schema(src_conn, tgt_conn, table)
        print("  Data sync")
        sync_data(src_conn, tgt_conn, table_info)

    src_conn.close()
    tgt_conn.close()
    print(f"[{datetime.now()}] Replication finished\n")

if __name__ == "__main__":
    main()