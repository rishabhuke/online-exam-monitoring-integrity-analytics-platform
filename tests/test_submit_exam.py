"""
Tests for submit_exam route in app.py (Priyanshu's task).

Run with:
    python -m pytest tests/test_submit_exam.py -v
"""

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Creates a Flask test client backed by a temporary SQLite database,
    and seeds test records.
    """
    test_db = tmp_path / "test_submit_exam.db"

    # Point the app's DATABASE path to our temp file
    monkeypatch.setattr(app_module, "DATABASE", test_db)

    # Initialize schema
    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    # Seed candidates & exams & questions
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
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    app_module.app.secret_key = "test-secret"

    with app_module.app.test_client() as test_client:
        yield test_client


def _get_answers_count(db_path):
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) as cnt FROM Answers").fetchone()[0]
    conn.close()
    return count


def test_submit_exam_success(client, tmp_path):
    db_path = tmp_path / "test_submit_exam.db"

    # Log in by setting session
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    payload = {
        "exam_id": 101,
        "answers": [
            {"question_id": 10, "selected_option": "b"}
        ]
    }

    response = client.post("/submit_exam", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["message"] == "Answers submitted successfully"
    assert _get_answers_count(db_path) == 1
    assert data["score"] == 1
    assert data["total_questions"] == 1
    assert data["percentage"] == 100.0
    assert data["result"] == "Passed"


def test_submit_exam_partial_answers_saves_only_provided(client, tmp_path):
    """A candidate can submit answers for only some of an exam's questions;
    only the provided answers should be persisted, no error for the rest."""
    db_path = tmp_path / "test_submit_exam.db"

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO Questions (id, exam_id, question, option_a, option_b, option_c, option_d, correct_option) "
        "VALUES (11, 101, 'Q2?', '1', '2', '3', '4', 'a')"
    )
    conn.execute(
        "INSERT INTO Questions (id, exam_id, question, option_a, option_b, option_c, option_d, correct_option) "
        "VALUES (12, 101, 'Q3?', '1', '2', '3', '4', 'd')"
    )
    conn.commit()
    conn.close()

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    payload = {
        "exam_id": 101,
        "answers": [
            {"question_id": 10, "selected_option": "b"}
        ]
    }

    response = client.post("/submit_exam", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert _get_answers_count(db_path) == 1

    # 3 questions now exist for exam 101 (10, 11, 12); only 1 was answered
    # (and correctly, per the fixture's correct_option='b' for question 10),
    # so score should reflect the unanswered ones as wrong, not excluded.
    assert data["score"] == 1
    assert data["total_questions"] == 3
    assert data["percentage"] == round(1 / 3 * 100, 2)
    assert data["result"] == "Failed"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT question_id, selected_option FROM Answers").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0]["question_id"] == 10
    assert rows[0]["selected_option"] == "b"


def test_submit_exam_unauthorized_redirects(client):
    # Do not set session candidate_id
    payload = {
        "answers": [
            {"question_id": 10, "selected_option": "b"}
        ]
    }

    # If it is not a JSON request, it should redirect to login (302)
    response = client.post("/submit_exam", data=payload)
    assert response.status_code == 302
    assert "/login" in response.location


def test_submit_exam_unauthorized_json_returns_401(client):
    payload = {
        "answers": [
            {"question_id": 10, "selected_option": "b"}
        ]
    }

    # If it is a JSON request, it should return 401
    response = client.post("/submit_exam", json=payload)
    assert response.status_code == 401
    data = response.get_json()
    assert data["status"] == "error"
    assert "Not authenticated" in data["message"]


def test_submit_exam_none_payload_handled_gracefully(client, tmp_path):
    db_path = tmp_path / "test_submit_exam.db"

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    # Sending empty body (None payload)
    response = client.post("/submit_exam", data="", content_type="application/json")
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "Invalid request format" in data["message"]
    assert _get_answers_count(db_path) == 0


def test_submit_exam_missing_answers_key_handled_gracefully(client, tmp_path):
    db_path = tmp_path / "test_submit_exam.db"

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    # Payload has JSON but missing "answers" key
    response = client.post("/submit_exam", json={"wrong_key": []})
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "Invalid request format" in data["message"]
    assert _get_answers_count(db_path) == 0


def test_submit_exam_invalid_answers_type_handled_gracefully(client, tmp_path):
    db_path = tmp_path / "test_submit_exam.db"

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    # "answers" is not a list
    response = client.post("/submit_exam", json={"answers": "not-a-list"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert "answers" in data["message"]
    assert _get_answers_count(db_path) == 0


def test_submit_exam_malformed_answers_skipped(client, tmp_path):
    db_path = tmp_path / "test_submit_exam.db"

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    payload = {
        "exam_id": 101,
        "answers": [
            {"wrong_sub_key": 10},  # malformed, should be skipped
            {"question_id": 10, "selected_option": "b"}  # valid
        ]
    }

    response = client.post("/submit_exam", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert _get_answers_count(db_path) == 1
