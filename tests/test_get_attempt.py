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
    assert result["result"] == "Failed"
