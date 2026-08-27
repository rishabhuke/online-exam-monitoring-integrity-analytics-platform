"""
Tests for get_exam route in app.py.

Run with:
    python -m pytest tests/test_get_exam.py -v
"""

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Creates a Flask test client backed by a temporary SQLite database,
    and seeds a candidate, exam, and question."""
    test_db = tmp_path / "test_get_exam.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)

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
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    app_module.app.secret_key = "test-secret"

    with app_module.app.test_client() as test_client:
        yield test_client


def test_get_exam_requires_auth_json_returns_401(client):
    """A JSON/fetch request with no session should get a clean 401, not a redirect."""
    resp = client.get("/api/exam/101", headers={"Accept": "application/json"})
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["status"] == "error"


def test_get_exam_requires_auth_redirects_for_browser_navigation(client):
    """A plain browser navigation (no JSON accept header) still redirects to login."""
    resp = client.get("/api/exam/101")
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_get_exam_returns_questions_without_correct_option(client):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/exam/101", headers={"Accept": "application/json"})
    assert resp.status_code == 200

    questions = resp.get_json()
    assert len(questions) == 1
    q = questions[0]
    assert q["id"] == 10
    assert q["question"] == "What is 2+2?"
    assert q["option_a"] == "3"
    assert q["option_b"] == "4"
    assert "correct_option" not in q


def test_get_exam_returns_empty_list_for_exam_with_no_questions(client):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/exam/999", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    assert resp.get_json() == []
