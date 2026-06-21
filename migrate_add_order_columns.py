"""
Add missing columns to `orders` table if they don't exist.
Run: python migrate_add_order_columns.py
"""
import sqlite3
import sys

DB = 'trading_bot.db'
COLUMNS = [
    ('option_entry_price','REAL'),
    ('option_exit_price','REAL'),
    ('underlying_price','REAL')
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Get existing columns
cur.execute("PRAGMA table_info(orders)")
cols = [r[1] for r in cur.fetchall()]

for name, ctype in COLUMNS:
    if name in cols:
        print(f"Column already exists: {name}")
    else:
        try:
            cur.execute(f"ALTER TABLE orders ADD COLUMN {name} {ctype}")
            print(f"Added column: {name} {ctype}")
        except Exception as e:
            print(f"Failed to add {name}: {e}")

conn.commit()
conn.close()
print('Migration complete')
