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


_OPTION_COLUMNS = {"a": "option_a", "b": "option_b", "c": "option_c", "d": "option_d"}


def get_answer_review(candidate_id: int, exam_id: int) -> dict:
    """
    Returns a per-question answer review for a candidate's exam: their
    selected option and the correct option, both resolved to the actual
    option text, for every question in the exam.

    Answers is not attempt-scoped (no attempt_id column, no timestamp),
    so if a candidate ever submitted the same exam more than once, a
    question could have multiple Answers rows. Rather than surface that
    ambiguity to the candidate (or silently pick an arbitrary one), this
    keeps only the latest row per (candidate_id, question_id) - the same
    "most recent wins" resolution get_exam_attempt_summary() above
    implicitly relies on for its ExamAttempts row, applied explicitly
    here since this function returns per-question data where the
    ambiguity would otherwise be visible. This does not add an
    attempt_id column or change what submit_exam/ExamAttempts do - it
    only decides which row this read-only view uses when duplicates
    exist.

    Like get_exam_attempt_summary(), returns only
    {"submitted": False, "exam_id": ..., "candidate_id": ...} if the
    candidate hasn't submitted this exam - no question data, since there
    would be nothing real to show.
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

        question_rows = conn.execute("""
            SELECT id AS question_id, question, option_a, option_b,
                   option_c, option_d, correct_option
            FROM Questions
            WHERE exam_id = ?
            ORDER BY id
        """, (exam_id,)).fetchall()

        # Dedup: latest Answers row per question for this candidate. See
        # this function's docstring for why - Answers has no attempt_id.
        answer_rows = conn.execute("""
            SELECT a.question_id, a.selected_option
            FROM Answers a
            JOIN (
                SELECT question_id, MAX(id) AS max_id
                FROM Answers
                WHERE candidate_id = ?
                GROUP BY question_id
            ) latest ON latest.question_id = a.question_id AND latest.max_id = a.id
        """, (candidate_id,)).fetchall()
        selected_by_question = {row["question_id"]: row["selected_option"] for row in answer_rows}

        def resolve_text(q_row, letter):
            if not letter:
                return None
            column = _OPTION_COLUMNS.get(letter.lower())
            return q_row[column] if column else None

        questions = []
        for q in question_rows:
            selected_letter = selected_by_question.get(q["question_id"])
            correct_letter = q["correct_option"]
            questions.append({
                "question_id": q["question_id"],
                "question": q["question"],
                "selected_option": selected_letter,
                "selected_text": resolve_text(q, selected_letter),
                "correct_option": correct_letter,
                "correct_text": resolve_text(q, correct_letter),
                "answered": selected_letter is not None,
                "is_correct": selected_letter is not None and selected_letter == correct_letter,
            })

        return {
            "submitted": True,
            "exam_id": exam_id,
            "candidate_id": candidate_id,
            "submitted_at": attempt["created_at"],
            "score": attempt["score"],
            "total_questions": attempt["total_questions"],
            "percentage": attempt["percentage"],
            "result": attempt["status"],
            "questions": questions,
        }
    finally:
        conn.close()
