"""
Tests for the invigilator-facing exam attempt/grading summary API
(attempt_bp, url_prefix /api/attempt). Owner: Rishabh

Run with:
    python -m pytest tests/test_get_attempt.py -v
"""

import os
import sys
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.grading as grading


@pytest.fixture
def client(monkeypatch, tmp_path):
    test_db = tmp_path / "test_get_attempt.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(grading, "DATABASE", test_db)

    import routes.auth as auth_module
    monkeypatch.setattr(auth_module, "DATABASE", test_db)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (1, 'Alice', 'alice@test.com', 'hash')"
    )
    conn.execute(
        "INSERT INTO Exams (id, title, duration) VALUES (101, 'Python Fundamentals Exam', 60)"
    )
    conn.execute(
        "INSERT INTO Questions (id, exam_id, question, option_a, option_b, option_c, option_d, correct_option) "
        "VALUES (10, 101, 'What is 2+2?', '3', '4', '5', '6', 'b')"
    )
    conn.execute(
        "INSERT INTO Questions (id, exam_id, question, option_a, option_b, option_c, option_d, correct_option) "
        "VALUES (11, 101, 'What is 3+3?', '5', '6', '7', '8', 'b')"
    )
    conn.execute(
        "INSERT INTO Invigilators (id, name, email, password_hash) VALUES (1, 'Invig', 'invig@test.com', ?)",
        (generate_password_hash("SecurePass123"),)
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    app_module.app.secret_key = "test-secret"

    with app_module.app.test_client() as test_client:
        yield test_client


def _seed_attempt_and_answers(db_path, score, total_questions, percentage, status, answers):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO ExamAttempts (candidate_id, exam_id, score, total_questions, percentage, status)
        VALUES (1, 101, ?, ?, ?, ?)
    """, (score, total_questions, percentage, status))
    for question_id, selected_option in answers:
        conn.execute("""
            INSERT INTO Answers (candidate_id, question_id, selected_option)
            VALUES (1, ?, ?)
        """, (question_id, selected_option))
    conn.commit()
    conn.close()


def _login_as_invigilator(client):
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1


def test_get_dashboard_attempt_requires_invigilator_auth(client):
    resp = client.get("/api/attempt/dashboard/1/101")
    assert resp.status_code == 401


def test_get_dashboard_attempt_rejects_candidate_session(client):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/attempt/dashboard/1/101")
    assert resp.status_code == 401


def test_get_dashboard_attempt_not_submitted(client):
    """No ExamAttempts row exists - the sharpest gap this feature closes."""
    _login_as_invigilator(client)

    resp = client.get("/api/attempt/dashboard/1/101")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["status"] == "success"
    assert data["submitted"] is False
    assert data["exam_id"] == 101
    assert data["candidate_id"] == 1
    assert "score" not in data
    assert "percentage" not in data


def test_get_dashboard_attempt_full_marks(client, tmp_path):
    db_path = tmp_path / "test_get_attempt.db"
    _seed_attempt_and_answers(
        db_path, score=2, total_questions=2, percentage=100.0, status="Passed",
        answers=[(10, "b"), (11, "b")]
    )
    _login_as_invigilator(client)

    resp = client.get("/api/attempt/dashboard/1/101")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["submitted"] is True
    assert data["score"] == 2
    assert data["total_questions"] == 2
    assert data["percentage"] == 100.0
    assert data["result"] == "Passed"
    assert data["correct"] == 2
    assert data["incorrect"] == 0
    assert data["unanswered"] == 0
    assert data["submitted_at"] is not None


def test_get_dashboard_attempt_partial_with_unanswered_and_wrong(client, tmp_path):
    db_path = tmp_path / "test_get_attempt.db"
    _seed_attempt_and_answers(
        db_path, score=1, total_questions=2, percentage=50.0, status="Passed",
        answers=[(10, "b"), (11, "a")]  # question 11's correct answer is "b", "a" is wrong
    )
    _login_as_invigilator(client)

    resp = client.get("/api/attempt/dashboard/1/101")
    data = resp.get_json()

    assert data["correct"] == 1
    assert data["incorrect"] == 1
    assert data["unanswered"] == 0


def test_get_dashboard_attempt_with_unanswered_questions(client, tmp_path):
    db_path = tmp_path / "test_get_attempt.db"
    _seed_attempt_and_answers(
        db_path, score=1, total_questions=2, percentage=50.0, status="Passed",
        answers=[(10, "b")]  # question 11 never answered
    )
    _login_as_invigilator(client)

    resp = client.get("/api/attempt/dashboard/1/101")
    data = resp.get_json()

    assert data["correct"] == 1
    assert data["incorrect"] == 0
    assert data["unanswered"] == 1


def test_get_exam_attempt_summary_module_function_directly(client, tmp_path):
    """Direct unit test of modules.grading, not just the HTTP layer."""
    db_path = tmp_path / "test_get_attempt.db"
    _seed_attempt_and_answers(
        db_path, score=1, total_questions=2, percentage=50.0, status="Failed",
        answers=[(10, "b")]
    )

    result = grading.get_exam_attempt_summary(1, 101)
    assert result["submitted"] is True
    assert result["correct"] == 1
    assert result["unanswered"] == 1


# ---------------------------------------------------------------------------
# Candidate self-service answer review: GET /api/attempt/<exam_id>/answers
# (Milestone 5 P2). candidate_id always comes from session, never the URL -
# only exam_id is a path parameter, so authorization tests below confirm
# session-scoping rather than a candidate_id-in-URL check that doesn't exist.
# ---------------------------------------------------------------------------

def _login_as_candidate(client, candidate_id=1):
    with client.session_transaction() as sess:
        sess["candidate_id"] = candidate_id


def test_get_own_answer_review_requires_auth(client):
    resp = client.get("/api/attempt/101/answers")
    assert resp.status_code == 401


def test_get_own_answer_review_not_submitted(client):
    """No ExamAttempts row - candidate hasn't submitted this exam yet."""
    _login_as_candidate(client)

    resp = client.get("/api/attempt/101/answers")
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["status"] == "success"
    assert data["submitted"] is False
    assert "questions" not in data


def test_get_own_answer_review_resolves_option_text(client, tmp_path):
    db_path = tmp_path / "test_get_attempt.db"
    _seed_attempt_and_answers(
        db_path, score=1, total_questions=2, percentage=50.0, status="Passed",
        answers=[(10, "b"), (11, "a")]  # Q10 correct (b), Q11 wrong (correct is b)
    )
    _login_as_candidate(client)

    resp = client.get("/api/attempt/101/answers")
    data = resp.get_json()

    assert data["submitted"] is True
    assert data["score"] == 1
    assert data["total_questions"] == 2
    assert data["result"] == "Passed"
    assert len(data["questions"]) == 2

    q10 = next(q for q in data["questions"] if q["question_id"] == 10)
    assert q10["selected_option"] == "b"
    assert q10["selected_text"] == "4"   # option_b for "What is 2+2?"
    assert q10["correct_text"] == "4"
    assert q10["answered"] is True
    assert q10["is_correct"] is True

    q11 = next(q for q in data["questions"] if q["question_id"] == 11)
    assert q11["selected_option"] == "a"
    assert q11["selected_text"] == "5"   # option_a for "What is 3+3?"
    assert q11["correct_text"] == "6"    # correct_option is "b"
    assert q11["is_correct"] is False


def test_get_own_answer_review_marks_unanswered_questions(client, tmp_path):
    db_path = tmp_path / "test_get_attempt.db"
    _seed_attempt_and_answers(
        db_path, score=1, total_questions=2, percentage=50.0, status="Failed",
        answers=[(10, "b")]  # question 11 never answered
    )
    _login_as_candidate(client)

    resp = client.get("/api/attempt/101/answers")
    data = resp.get_json()

    q11 = next(q for q in data["questions"] if q["question_id"] == 11)
    assert q11["answered"] is False
    assert q11["selected_option"] is None
    assert q11["selected_text"] is None
    assert q11["is_correct"] is False
    assert q11["correct_text"] == "6"


def test_get_own_answer_review_scoped_to_session_candidate_not_other_candidates(client, tmp_path):
    """The only path parameter is exam_id - a candidate cannot see another
    candidate's answers by changing anything in the URL, since candidate_id
    never appears there. This confirms candidate 2's session only ever
    resolves candidate 2's own (empty, in this case) submission."""
    db_path = tmp_path / "test_get_attempt.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (2, 'Bob', 'bob@test.com', 'hash2')"
    )
    conn.commit()
    conn.close()

    _seed_attempt_and_answers(
        db_path, score=2, total_questions=2, percentage=100.0, status="Passed",
        answers=[(10, "b"), (11, "b")]
    )
    _login_as_candidate(client, candidate_id=2)

    resp = client.get("/api/attempt/101/answers")
    data = resp.get_json()

    # Candidate 1 (seeded above) submitted; candidate 2 never did - same
    # URL, different session, genuinely different (and correct) result.
    assert data["submitted"] is False
    assert data["candidate_id"] == 2


def test_get_answer_review_dedups_duplicate_answer_rows_to_latest(client, tmp_path):
    """Direct unit test of modules.grading.get_answer_review()'s dedup
    safeguard: if Answers somehow has more than one row for the same
    (candidate_id, question_id) - which the schema doesn't prevent, since
    Answers has no attempt_id - the review must resolve to the LATEST row,
    not silently pick an arbitrary one or double-count the question."""
    db_path = tmp_path / "test_get_attempt.db"
    _seed_attempt_and_answers(
        db_path, score=1, total_questions=2, percentage=50.0, status="Passed",
        answers=[(10, "a"), (11, "b")]  # question 10's first (wrong) answer
    )
    # Simulate a second submission's answer for the same question arriving
    # later (higher id) with a different, now-correct, selection.
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO Answers (candidate_id, question_id, selected_option) VALUES (1, 10, 'b')"
    )
    conn.commit()
    conn.close()

    result = grading.get_answer_review(1, 101)

    assert result["submitted"] is True
    assert len(result["questions"]) == 2  # not 3 - one row per question, not per Answers row

    q10 = next(q for q in result["questions"] if q["question_id"] == 10)
    assert q10["selected_option"] == "b"  # the later row, not the first "a"
    assert q10["is_correct"] is True
