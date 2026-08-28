"""
Tests for get_results route in app.py.

Run with:
    python -m pytest tests/test_get_results.py -v
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
    seeding a candidate, exam, and two completed attempts."""
    test_db = tmp_path / "test_get_results.db"

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
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (2, 'Bob', 'bob@test.com', 'hash')"
    )
    conn.execute(
        "INSERT INTO Exams (id, title, duration) VALUES (101, 'Python Fundamentals Exam', 60)"
    )
    conn.execute(
        "INSERT INTO ExamAttempts (id, candidate_id, exam_id, score, total_questions, percentage, status, created_at) "
        "VALUES (1, 1, 101, 4, 5, 80.0, 'Passed', '2026-08-01 10:00:00')"
    )
    conn.execute(
        "INSERT INTO ExamAttempts (id, candidate_id, exam_id, score, total_questions, percentage, status, created_at) "
        "VALUES (2, 1, 101, 1, 5, 20.0, 'Failed', '2026-08-02 10:00:00')"
    )
    conn.execute(
        "INSERT INTO ExamAttempts (id, candidate_id, exam_id, score, total_questions, percentage, status, created_at) "
        "VALUES (3, 2, 101, 5, 5, 100.0, 'Passed', '2026-08-01 11:00:00')"
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    app_module.app.secret_key = "test-secret"

    with app_module.app.test_client() as test_client:
        yield test_client


def test_get_results_requires_auth_json_returns_401(client):
    resp = client.get("/api/results", headers={"Accept": "application/json"})
    assert resp.status_code == 401


def test_get_results_requires_auth_redirects_for_browser_navigation(client):
    resp = client.get("/api/results")
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_get_results_returns_only_current_candidates_attempts(client):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/results", headers={"Accept": "application/json"})
    assert resp.status_code == 200

    results = resp.get_json()
    assert len(results) == 2
    assert all(r["exam_id"] == 101 for r in results)
    # Bob's attempt (candidate_id 2) must never appear here
    assert {r["score"] for r in results} == {4, 1}


def test_get_results_ordered_most_recent_first(client):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/results", headers={"Accept": "application/json"})
    results = resp.get_json()

    assert results[0]["created_at"] == "2026-08-02 10:00:00"
    assert results[1]["created_at"] == "2026-08-01 10:00:00"


def test_get_results_includes_exam_title_via_join(client):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/results", headers={"Accept": "application/json"})
    results = resp.get_json()

    assert all(r["title"] == "Python Fundamentals Exam" for r in results)


def test_get_results_returns_empty_list_for_candidate_with_no_attempts(client):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 999  # no attempts seeded

    resp = client.get("/api/results", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    assert resp.get_json() == []
