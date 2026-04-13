import os
import sqlite3

DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM orders")
count = c.fetchone()[0]

print("Total rows in orders table:", count)

c.execute("SELECT * FROM orders")
rows = c.fetchall()

for r in rows:
    print(r)

conn.close()