import sqlite3, json
conn=sqlite3.connect('trading_bot.db')
cur=conn.cursor()
cur.execute('PRAGMA table_info(orders)')
cols=cur.fetchall()
print('orders table columns:')
print(json.dumps(cols, indent=2))
conn.close()
