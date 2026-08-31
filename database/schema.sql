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
-- detected during an exam session. Written by modules/photo_capture.py.
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

-- BrowserEvents Table (Milestone 2)
-- Stores browser activity events captured from the exam page.
CREATE TABLE IF NOT EXISTS BrowserEvents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    exam_id INTEGER,
    event_type TEXT NOT NULL,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id),
    FOREIGN KEY(exam_id) REFERENCES Exams(id)
);
-- IntegrityFlags Table (Milestone 2)
-- One row per suspicious-event flag raised by the rule-based detection
-- engine (modules/detection_engine.py) when a configured threshold is
-- breached (e.g. face absent too long, too many tab switches).
CREATE TABLE IF NOT EXISTS IntegrityFlags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    exam_id INTEGER,
    flag_type TEXT,
    severity TEXT,
    detail TEXT,
    threshold_breached TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id),
    FOREIGN KEY(exam_id) REFERENCES Exams(id)
);
-- Invigilators Table (Milestone 4)
-- Separate account type from Candidates. Invigilators are created via
-- scripts/create_invigilator.py (no public self-registration - accounts
-- are provisioned by whoever administers the deployment), and log in via
-- /invigilator/login (routes/auth.py) into a separate session key
-- (session["invigilator_id"]) that never overlaps with candidate sessions.
CREATE TABLE IF NOT EXISTS Invigilators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ExamAttempts Table
-- Represents one completed, graded attempt at an exam. Answers (above)
-- are the raw per-question selections a candidate submitted; this table
-- is the derived summary - score/percentage/status - computed once at
-- submit_exam time. Needed because Answers alone has no concept of "this
-- group of rows constitutes one finished attempt" (no timestamp, no
-- submission boundary), which /results needs to display real completed
-- exams instead of a hardcoded table.
CREATE TABLE IF NOT EXISTS ExamAttempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    exam_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    percentage REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id),
    FOREIGN KEY(exam_id) REFERENCES Exams(id)
);

-- Evidence Table (Milestone 5 - integrity analysis port)
-- One row per evidence image saved when a flag-worthy violation is
-- confirmed (currently: identity_mismatch, identity_check_no_face,
-- identity_check_multiple_faces - see modules/detection_engine.py). The
-- actual image lives on disk; this table stores its path plus metadata so
-- evidence is queryable (e.g. "show me every mismatch photo for exam 3")
-- rather than filesystem-listing only.
CREATE TABLE IF NOT EXISTS Evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    exam_id INTEGER,
    flag_type TEXT NOT NULL,
    filepath TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(candidate_id) REFERENCES Candidates(id),
    FOREIGN KEY(exam_id) REFERENCES Exams(id)
);
