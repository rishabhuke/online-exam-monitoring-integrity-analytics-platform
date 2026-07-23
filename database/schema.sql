-- Candidates Table
CREATE TABLE IF NOT EXISTS Candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    photo_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exams Table
CREATE TABLE IF NOT EXISTS Exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    duration INTEGER NOT NULL
);

-- Questions Table
CREATE TABLE IF NOT EXISTS Questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id INTEGER,
    question TEXT NOT NULL,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option TEXT,
    FOREIGN KEY(exam_id) REFERENCES Exams(id)
);

-- Answers Table
CREATE TABLE IF NOT EXISTS Answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    question_id INTEGER,
    selected_option TEXT,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id),
    FOREIGN KEY(question_id) REFERENCES Questions(id)
);

-- SessionLogs Table
CREATE TABLE IF NOT EXISTS SessionLogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    login_time TIMESTAMP,
    logout_time TIMESTAMP,
    status TEXT,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id)
);

-- FaceAbsenceEvents Table (Milestone 2)
-- One row per continuous interval where the candidate's face was not
-- detected during an exam session. Written by modules/face_monitor.py.
CREATE TABLE IF NOT EXISTS FaceAbsenceEvents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    exam_id INTEGER,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds REAL,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id),
    FOREIGN KEY(exam_id) REFERENCES Exams(id)
);