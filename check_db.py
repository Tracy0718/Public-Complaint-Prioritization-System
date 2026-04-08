import sqlite3
import sys
from pathlib import Path

db = Path("db.sqlite3")
if not db.exists():
    print("No db.sqlite3 found in current directory:", db.resolve())
    sys.exit(1)

conn = sqlite3.connect(str(db))
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cur.fetchall()]

if not tables:
    print("No tables found in the database.")
else:
    print("Tables in db.sqlite3:")
    for t in tables:
        print("-", t)

cur.close()
conn.close()
