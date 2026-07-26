import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

tables = cursor.fetchall()

print(tables)
print("ExamAttempts")
print("----------------")

for row in cursor.execute("SELECT * FROM ExamAttempts"):
    print(row)

print("\nAnswers")
print("----------------")

for row in cursor.execute("SELECT * FROM Answers"):
    print(row)

conn.close()