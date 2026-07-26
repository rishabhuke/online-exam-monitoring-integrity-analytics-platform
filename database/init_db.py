from pathlib import Path
import sqlite3

# Database Path
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"

# Connect to Database
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# ==========================
# Candidates Table
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    photo_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ==========================
# Exams Table
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Exams (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT NOT NULL,

    topic TEXT,

    difficulty TEXT,

    description TEXT,

    duration INTEGER NOT NULL,

    total_questions INTEGER NOT NULL,

    total_marks INTEGER NOT NULL,

    start_time TEXT NOT NULL,

    end_time TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)
""")

# ==========================
# Questions Table
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL,
    FOREIGN KEY (exam_id) REFERENCES Exams(id) ON DELETE CASCADE
)
""")

# ==========================
# Answers Table
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS Answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_option TEXT,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id) ON DELETE CASCADE,
    FOREIGN KEY(question_id) REFERENCES Questions(id) ON DELETE CASCADE
)
""")

# ==========================
# Session Logs Table
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS SessionLogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    login_time TIMESTAMP,
    logout_time TIMESTAMP,
    status TEXT,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id) ON DELETE CASCADE
)
""")
# ==========================================================
# VIOLATION LOGS
# ==========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS ViolationLogs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    candidate_id INTEGER NOT NULL,

    exam_id INTEGER NOT NULL,

    violation_type TEXT NOT NULL,

    violation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(candidate_id)
        REFERENCES Candidates(id),

    FOREIGN KEY(exam_id)
        REFERENCES Exams(id)

)
""")
# ==========================
# Exam Attempts Table
# ==========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS ExamAttempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    exam_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    percentage REAL NOT NULL,
    result TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(candidate_id)
        REFERENCES Candidates(id) ON DELETE CASCADE,

    FOREIGN KEY(exam_id)
        REFERENCES Exams(id) ON DELETE CASCADE,

    UNIQUE(candidate_id, exam_id)
)
""")

# Save Changes
conn.commit()
conn.close()

print("Database and tables created successfully!")