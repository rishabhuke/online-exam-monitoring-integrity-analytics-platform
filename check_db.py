
import sqlite3

DB_PATH = "database.db"   # CHANGE if your DB path is different

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

tables = [
    "Candidates",
    "Exams",
    "SessionLogs",
    "ViolationLogs",
    "ExamAttempts",
    "IntegrityScores"
]

print("\n========== DATABASE CHECK ==========\n")

for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) AS count FROM {table}")
        count = cursor.fetchone()["count"]
        print(f"{table}: {count}")
    except Exception as e:
        print(f"{table}: ERROR -> {e}")

print("\n========== EXAMS ==========\n")

cursor.execute("""
    SELECT
        id,
        title,
        topic,
        difficulty
    FROM Exams
    ORDER BY id
""")

for row in cursor.fetchall():
    print(dict(row))

print("\n========== INTEGRITY SCORES ==========\n")

cursor.execute("""
    SELECT *
    FROM IntegrityScores
    ORDER BY id
""")

rows = cursor.fetchall()

if not rows:
    print("NO INTEGRITY SCORES FOUND")

for row in rows:
    print(dict(row))

print("\n========== VIOLATIONS ==========\n")

cursor.execute("""
    SELECT
        id,
        candidate_id,
        exam_id,
        violation_type,
        face_count,
        violation_time
    FROM ViolationLogs
    ORDER BY id DESC
""")

for row in cursor.fetchall():
    print(dict(row))

conn.close()

