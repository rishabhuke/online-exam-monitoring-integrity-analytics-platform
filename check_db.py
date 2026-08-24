import sqlite3

DB_PATH = "database.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

try:
    print("\n===== EXAMS TABLE =====")

    rows = conn.execute("""
        SELECT *
        FROM Exams
        ORDER BY id DESC
    """).fetchall()

    for row in rows:
        print(dict(row))

    print("\nTotal examinations:", len(rows))

finally:
    conn.close()