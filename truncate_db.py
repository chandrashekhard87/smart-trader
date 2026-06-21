"""
Truncate main trading tables and vacuum the SQLite DB.
Run: python truncate_db.py
"""
import sqlite3
DB = 'trading_bot.db'
TABLES = ['orders','option_chain_summary','trading_signals','daily_summary']

conn = sqlite3.connect(DB)
cur = conn.cursor()
for t in TABLES:
    cur.execute(f"DELETE FROM {t}")
    cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'")
    print(f"Truncated {t}")
conn.commit()
cur.execute('VACUUM')
conn.close()
print('Database vacuumed and truncated')
