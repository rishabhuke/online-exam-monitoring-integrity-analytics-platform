"""
Tests for routes/report.py - both the M3 candidate self-service endpoint
and the M4 dashboard endpoint (Milestone 3/4). Owner: Rishabh

Run with:
    python -m pytest tests/test_report.py -v
"""

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.report_agent as report_agent
import modules.flags_storage as flags_storage
import modules.monitoring_storage as monitoring_storage
import modules.scoring as scoring


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    """
    Fixture providing an isolated SQLite database and Flask test client.
    Seeds test candidates and exams for FK constraints. Also forces
    report_agent onto the template path (no real LLM call in tests).
    """
    test_db = tmp_path / "test_report.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)
    monkeypatch.setattr(scoring, "DATABASE", test_db)
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (1, 'Alice', 'alice@test.com', 'hash1')"
    )
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (2, 'Bob', 'bob@test.com', 'hash2')"
    )
    conn.execute(
        "INSERT INTO Exams (id, title, duration) VALUES (101, 'Python Fundamentals Exam', 60)"
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client, test_db


# --- Existing M3 self-service endpoint ------------------------------------

def test_get_report_requires_auth(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/report/101")
    assert resp.status_code == 401


def test_get_report_returns_own_session_summary(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/report/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert "summary" in body
    assert "risk_label" in body


# --- New M4 dashboard endpoint ---------------------------------------------

def test_get_dashboard_report_requires_auth(test_db_and_client):
    """Unauthenticated requests are rejected. Note: this only checks that
    *some* session exists, not that the caller is an invigilator - see the
    TODO(auth) in routes/report.py."""
    client, _ = test_db_and_client
    resp = client.get("/api/report/dashboard/1/101")
    assert resp.status_code == 401


def test_get_dashboard_report_returns_any_candidates_summary(test_db_and_client):
    """With a valid session, the dashboard endpoint can fetch a DIFFERENT
    candidate's summary (candidate 2's session, viewed by candidate 1's
    login) - this is the behavior the dashboard needs, and exactly the gap
    flagged in the TODO(auth): there's no role check preventing this."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/report/dashboard/2/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert "summary" in body
    assert "risk_label" in body


def test_get_dashboard_report_matches_scoring_module(test_db_and_client):
    """Sanity check that the dashboard endpoint's risk_label agrees with
    modules.scoring directly, i.e. report_agent is correctly routing
    through Priyanshu's scoring module rather than its own fallback."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/report/dashboard/2/101")
    body = resp.get_json()

    scoring_result = scoring.calculate_session_score(2, 101)
    assert body["risk_label"] == scoring_result["risk_label"]
