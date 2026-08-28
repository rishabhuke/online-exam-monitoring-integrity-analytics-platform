"""
Exam grading/attempt summary module.

Deliberately separate from modules/scoring.py (integrity/proctoring score)
and modules/analytics.py (cohort-level proctoring analytics) - this module
owns exactly one concern: "did this candidate submit this exam, and if so
what did they score." Proctoring data and grading data are independent
streams that the invigilator dashboard combines client-side, not concerns
that get merged in a shared module.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"


def _get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def get_exam_attempt_summary(candidate_id: int, exam_id: int) -> dict:
    """
    Returns a candidate's exam attempt summary for a given exam.

    If the candidate has not submitted this exam, returns only
    {"submitted": False, "exam_id": ..., "candidate_id": ...} - no score
    fields, since a zero would be indistinguishable from a real score of 0.
    """
    conn = _get_db_connection()
    try:
        attempt = conn.execute("""
            SELECT score, total_questions, percentage, status, created_at
            FROM ExamAttempts
            WHERE candidate_id = ? AND exam_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (candidate_id, exam_id)).fetchone()

        if attempt is None:
            return {
                "submitted": False,
                "exam_id": exam_id,
                "candidate_id": candidate_id,
            }

        answered_rows = conn.execute("""
            SELECT Answers.selected_option, Questions.correct_option
            FROM Answers
            JOIN Questions ON Questions.id = Answers.question_id
            WHERE Answers.candidate_id = ? AND Questions.exam_id = ?
        """, (candidate_id, exam_id)).fetchall()

        answered_count = len(answered_rows)
        correct_count = sum(
            1 for row in answered_rows
            if row["selected_option"] == row["correct_option"]
        )
        incorrect_count = answered_count - correct_count
        unanswered_count = attempt["total_questions"] - answered_count

        return {
            "submitted": True,
            "exam_id": exam_id,
            "candidate_id": candidate_id,
            "submitted_at": attempt["created_at"],
            "score": attempt["score"],
            "total_questions": attempt["total_questions"],
            "percentage": attempt["percentage"],
            "result": attempt["status"],
            "correct": correct_count,
            "incorrect": incorrect_count,
            "unanswered": unanswered_count,
        }
    finally:
        conn.close()
