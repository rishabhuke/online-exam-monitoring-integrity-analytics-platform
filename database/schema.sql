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

    selected_option TEXT NOT NULL,

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

    login_time TIMESTAMP,

    logout_time TIMESTAMP,

    status TEXT,

    FOREIGN KEY(candidate_id)
        REFERENCES Candidates(id)
        ON DELETE CASCADE

);
CREATE TABLE IF NOT EXISTS ViolationLogs (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    candidate_id INTEGER NOT NULL,

    exam_id INTEGER NOT NULL,

    violation_type TEXT NOT NULL,

    violation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(candidate_id) REFERENCES Candidates(id),

    FOREIGN KEY(exam_id) REFERENCES Exams(id)

);

CREATE TABLE IF NOT EXISTS ExamAttempts (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    candidate_id INTEGER NOT NULL,

    exam_id INTEGER NOT NULL,

    score INTEGER NOT NULL,

    total_questions INTEGER NOT NULL,

    percentage REAL NOT NULL,

    result TEXT NOT NULL,

    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(candidate_id, exam_id)
);
-- ======================================================
-- SAMPLE EXAMS
-- ======================================================

INSERT INTO Exams
(
title,
topic,
difficulty,
description,
duration,
total_questions,
total_marks
)

VALUES

(
'Java Programming',
'Core Java',
'Easy',
'Core Java MCQ Assessment',
60,
10,
10
),

(
'Database Management System',
'SQL and Normalization',
'Medium',
'DBMS Concepts',
45,
10,
10
),

(
'Web Technologies',
'HTML CSS JavaScript',
'Easy',
'Frontend Web Technologies',
30,
10,
10
);

-- ======================================================
-- SAMPLE JAVA QUESTIONS
-- ======================================================

INSERT INTO Questions
(
exam_id,
question,
option_a,
option_b,
option_c,
option_d,
correct_option
)

VALUES

(
1,
'Which keyword is used for inheritance?',
'implements',
'extends',
'super',
'import',
'B'
),

(
1,
'Which method starts a Java program?',
'run()',
'main()',
'start()',
'execute()',
'B'
),

(
1,
'Which package is automatically imported?',
'java.io',
'java.util',
'java.lang',
'java.net',
'C'
),

(
1,
'Which is not a primitive datatype?',
'int',
'double',
'String',
'boolean',
'C'
);

-- ======================================================
-- SAMPLE DBMS QUESTIONS
-- ======================================================

INSERT INTO Questions
(
exam_id,
question,
option_a,
option_b,
option_c,
option_d,
correct_option
)

VALUES

(
2,
'Which normal form removes partial dependency?',
'1NF',
'2NF',
'3NF',
'BCNF',
'B'
),

(
2,
'Which SQL command removes all rows but keeps the table?',
'DELETE',
'DROP',
'TRUNCATE',
'REMOVE',
'C'
);

-- ======================================================
-- SAMPLE WEB QUESTIONS
-- ======================================================

INSERT INTO Questions
(
exam_id,
question,
option_a,
option_b,
option_c,
option_d,
correct_option
)

VALUES

(
3,
'Which language is used for styling web pages?',
'HTML',
'CSS',
'Python',
'SQL',
'B'
),

(
3,
'Which HTML tag is used to include JavaScript?',
'<css>',
'<script>',
'<javascript>',
'<js>',
'B'
);