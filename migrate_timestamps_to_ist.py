"""
Migration: convert existing UTC timestamps in SQLite DB to IST (UTC+5:30).
By default updates `trading_signals`, `option_chain_summary`, `orders`, and `daily_summary`.
Run: python migrate_timestamps_to_ist.py
"""
import sqlite3
from datetime import datetime, timezone, timedelta

DB_PATH = 'trading_bot.db'
TABLES = {
    'trading_signals': ['created_at'],
    'option_chain_summary': ['created_at'],
    'orders': ['created_at','updated_at','closed_at'],
    'daily_summary': ['created_at','updated_at']
}

def parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        # try ISO formats
        return datetime.fromisoformat(dt_str)
    except Exception:
        try:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None


def convert_to_ist(dt):
    if dt.tzinfo is None:
        # assume stored as UTC naive
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=5, minutes=30))).isoformat()


def migrate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for table, cols in TABLES.items():
        # Check table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cur.fetchone():
            print(f"Skipping missing table: {table}")
            continue

        # Select rows (alias rowid to _rowid_ for reliable access)
        cur.execute(f"SELECT rowid AS _rowid_, * FROM {table}")
        rows = cur.fetchall()
        print(f"Processing {len(rows)} rows in {table}")

        for row in rows:
            # row is sqlite3.Row - use the aliased _rowid_
            rowid = row['_rowid_']
            updates = {}
            for col in cols:
                if col not in row.keys():
                    continue
                val = row[col]
                if not val:
                    continue
                dt = parse_dt(val)
                if not dt:
                    continue
                ist = convert_to_ist(dt)
                if ist != val:
                    updates[col] = ist
            if updates:
                set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                params = list(updates.values())
                params.append(rowid)
                sql = f"UPDATE {table} SET {set_clause} WHERE rowid = ?"
                cur.execute(sql, params)
        conn.commit()
    conn.close()
    print('Migration complete')

if __name__ == '__main__':
    migrate()
