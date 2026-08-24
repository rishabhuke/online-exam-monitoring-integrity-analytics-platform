from pathlib import Path
import sqlite3

# Database Path
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"

def init_database():
    """Initializes and migrates the database schema safely without data loss."""
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
        exam_id INTEGER NOT NULL,
        login_time TIMESTAMP,
        logout_time TIMESTAMP,
        status TEXT,
        FOREIGN KEY(candidate_id)
            REFERENCES Candidates(id)
            ON DELETE CASCADE,
        FOREIGN KEY(exam_id)
            REFERENCES Exams(id)
            ON DELETE CASCADE
    )
    """)

    # ==========================
    # Violation Logs Table
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ViolationLogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        exam_id INTEGER NOT NULL,
        violation_type TEXT NOT NULL,
        evidence_image TEXT,
        face_count INTEGER DEFAULT 0,
        violation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(candidate_id)
            REFERENCES Candidates(id)
            ON DELETE CASCADE,
        FOREIGN KEY(exam_id)
            REFERENCES Exams(id)
            ON DELETE CASCADE
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
            REFERENCES Candidates(id)
            ON DELETE CASCADE,
        FOREIGN KEY(exam_id)
            REFERENCES Exams(id)
            ON DELETE CASCADE,
        UNIQUE(candidate_id, exam_id)
    )
    """)

    # ==========================
    # Integrity Scores Table
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS IntegrityScores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        exam_id INTEGER NOT NULL,
        integrity_score REAL NOT NULL,
        face_presence_ratio REAL NOT NULL,
        warning_count INTEGER NOT NULL,
        risk_label TEXT NOT NULL,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(candidate_id)
            REFERENCES Candidates(id)
            ON DELETE CASCADE,
        FOREIGN KEY(exam_id)
            REFERENCES Exams(id)
            ON DELETE CASCADE,
        UNIQUE(candidate_id, exam_id)
    )
    """)

    # ==========================
    # Admins Table
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        employee_id TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ==========================
    # Admin Invite IDs Table
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AdminInviteIDs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT UNIQUE NOT NULL,
        used INTEGER DEFAULT 0,
        used_at TIMESTAMP
    )
    """)

    # Default Employee IDs
    default_ids = [
        ("ADM-1001",),
        ("ADM-1002",),
        ("ADM-1003",),
        ("ADM-1004",),
        ("ADM-1005",)
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO AdminInviteIDs (employee_id)
    VALUES (?)
    """, default_ids)

    # ==========================
    # AI Reports Table
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AIReports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER,
        exam_id INTEGER NOT NULL,
        report_type TEXT NOT NULL DEFAULT 'candidate',
        title TEXT NOT NULL,
        risk_label TEXT,
        integrity_score REAL,
        face_presence_ratio REAL,
        warning_count INTEGER DEFAULT 0,
        report_content TEXT NOT NULL,
        model_name TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(candidate_id)
            REFERENCES Candidates(id)
            ON DELETE CASCADE,
        FOREIGN KEY(exam_id)
            REFERENCES Exams(id)
            ON DELETE CASCADE
    )
    """)

    # ==========================================================
    # SAFE MIGRATIONS: Check existing columns in AIReports
    # ==========================================================
    cursor.execute("PRAGMA table_info(AIReports)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if "face_presence_ratio" not in existing_columns:
        cursor.execute("ALTER TABLE AIReports ADD COLUMN face_presence_ratio REAL")

    if "warning_count" not in existing_columns:
        cursor.execute("ALTER TABLE AIReports ADD COLUMN warning_count INTEGER DEFAULT 0")

    if "model_name" not in existing_columns:
        cursor.execute("ALTER TABLE AIReports ADD COLUMN model_name TEXT")

    if "report_type" not in existing_columns:
        cursor.execute("ALTER TABLE AIReports ADD COLUMN report_type TEXT NOT NULL DEFAULT 'candidate'")
    # ==========================
    # Support Tickets Table
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SupportTickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        candidate_id INTEGER NOT NULL,

        issue_type TEXT NOT NULL,

        priority TEXT NOT NULL DEFAULT 'Medium',

        subject TEXT NOT NULL,

        message TEXT NOT NULL,

        status TEXT NOT NULL DEFAULT 'Open',

        admin_response TEXT,

        assigned_admin_id INTEGER,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        resolved_at TIMESTAMP,

        FOREIGN KEY(candidate_id)
            REFERENCES Candidates(id)
            ON DELETE CASCADE,

        FOREIGN KEY(assigned_admin_id)
            REFERENCES Admins(id)
            ON DELETE SET NULL
    )
    """)

    # ==========================
    # FAQs Table
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FAQs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        question TEXT NOT NULL,

        answer TEXT NOT NULL,

        category TEXT,

        active INTEGER DEFAULT 1,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ==========================
    # Default FAQs
    # ==========================
    default_faqs = [
        (
            "How do I start an exam?",
            "Login to your account, open the Exams page, and click Start Exam."
        ),
        (
            "What should I do if my webcam is not detected?",
            "Allow camera permission in your browser and reconnect your webcam before starting the exam."
        ),
        (
            "Can I resume an interrupted exam?",
            "No. Once an exam session is interrupted, contact the administrator for assistance."
        ),
        (
            "How can I view my exam results?",
            "Go to the Results or Analytics page after your exam has been evaluated."
        ),
        (
            "How do I contact support?",
            "Navigate to the Help & Support page and create a new support ticket."
        )
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO FAQs (
            question,
            answer
        )
        VALUES (?, ?)
    """, default_faqs)
    
    # Save Changes
    conn.commit()
    conn.close()
    print("Database initialized and verified successfully!")

if __name__ == "__main__":
    init_database()