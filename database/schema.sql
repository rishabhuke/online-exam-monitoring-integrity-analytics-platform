-- ======================================================
-- CANDIDATES
-- ======================================================

CREATE TABLE IF NOT EXISTS Candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    photo_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================================================
-- EXAMS
-- ======================================================

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
);

-- ======================================================
-- QUESTIONS
-- ======================================================

CREATE TABLE IF NOT EXISTS Questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL,
    FOREIGN KEY(exam_id)
        REFERENCES Exams(id)
        ON DELETE CASCADE
);

-- ======================================================
-- ANSWERS
-- ======================================================

CREATE TABLE IF NOT EXISTS Answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_option TEXT,
    FOREIGN KEY(candidate_id)
        REFERENCES Candidates(id)
        ON DELETE CASCADE,
    FOREIGN KEY(question_id)
        REFERENCES Questions(id)
        ON DELETE CASCADE
);

-- ======================================================
-- SESSION LOGS
-- ======================================================

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
);

-- ======================================================
-- VIOLATION LOGS
-- ======================================================

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
);

-- ======================================================
-- EXAM ATTEMPTS
-- ======================================================

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
);

-- ======================================================
-- INTEGRITY SCORES
-- ======================================================

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
);

-- ======================================================
-- ADMINS
-- ======================================================

CREATE TABLE IF NOT EXISTS Admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    employee_id TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ======================================================
-- ADMIN INVITE IDS
-- ======================================================

CREATE TABLE IF NOT EXISTS AdminInviteIDs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT UNIQUE NOT NULL,
    used INTEGER DEFAULT 0,
    used_at TIMESTAMP
);

-- ======================================================
-- AI GENERATED REPORTS
-- ======================================================

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
);
