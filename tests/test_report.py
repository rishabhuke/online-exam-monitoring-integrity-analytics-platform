"""
Tests for routes/report.py - both the M3 candidate self-service endpoint
and the M4 invigilator dashboard endpoint (Milestone 3/4). Owner: Rishabh

Run with:
    python -m pytest tests/test_report.py -v
"""

import os
import sys
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.report_agent as report_agent
import modules.flags_storage as flags_storage
import modules.monitoring_storage as monitoring_storage
import modules.scoring as scoring
import modules.analytics as analytics


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    """
    Fixture providing an isolated SQLite database and Flask test client.
    Seeds test candidates, an exam, and an invigilator account for FK
    constraints and auth. Also forces report_agent onto the template path
    (no real LLM call in tests).
    """
    test_db = tmp_path / "test_report.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)
    monkeypatch.setattr(scoring, "DATABASE", test_db)
    monkeypatch.setattr(analytics, "DATABASE", test_db)
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    report_agent._exam_summary_cache.clear()

    import routes.auth as auth_module
    monkeypatch.setattr(auth_module, "DATABASE", test_db)

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
    conn.execute(
        "INSERT INTO Invigilators (id, name, email, password_hash) VALUES (1, 'Invig', 'invig@test.com', ?)",
        (generate_password_hash("SecurePass123"),)
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


# --- New /report/<exam_id> page route (candidate-facing) -------------------

def test_report_page_redirects_when_logged_out(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/report/101")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_report_page_renders_with_candidate_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/report/101")
    assert resp.status_code == 200
    assert b"Python Fundamentals Exam" in resp.data
    # exam_id must reach the JS via the data attribute the new report.js reads
    assert b'data-exam-id="101"' in resp.data


# --- New M4 dashboard endpoint (invigilator-only) --------------------------

def test_get_dashboard_report_requires_invigilator_auth(test_db_and_client):
    """No session at all -> 401."""
    client, _ = test_db_and_client
    resp = client.get("/api/report/dashboard/1/101")
    assert resp.status_code == 401


def test_get_dashboard_report_rejects_candidate_session(test_db_and_client):
    """A valid CANDIDATE session must not satisfy @invigilator_required -
    this is the exact gap the previous TODO(auth) flagged, now closed."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/report/dashboard/2/101")
    assert resp.status_code == 401


def test_get_dashboard_report_allows_invigilator_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

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
        sess["invigilator_id"] = 1

    resp = client.get("/api/report/dashboard/2/101")
    body = resp.get_json()

    scoring_result = scoring.calculate_session_score(2, 101)
    assert body["risk_label"] == scoring_result["risk_label"]


# --- New M5 exam cohort report endpoint (invigilator-only) -----------------

def test_get_exam_cohort_report_requires_invigilator_auth(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/report/exam/101")
    assert resp.status_code == 401


def test_get_exam_cohort_report_rejects_candidate_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/report/exam/101")
    assert resp.status_code == 401


def test_get_exam_cohort_report_allows_invigilator_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/report/exam/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert "summary" in body
    assert "cohort_size" in body
    assert "risk_breakdown" in body


def test_get_exam_cohort_report_reflects_seeded_events(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    monitoring_storage.create_browser_event(2, 101, event_type="tab_switch")
    monitoring_storage.create_browser_event(2, 101, event_type="tab_switch")
    flags_storage.create_flag(2, 101, "excessive_tab_switching", "medium", "2 switches", "max_tab_switches=1")

    resp = client.get("/api/report/exam/101")
    body = resp.get_json()

    assert body["cohort_size"] == 1
    assert body["risk_breakdown"].get("Medium") == 1
    assert "cohort of 1 candidate(s)" in body["summary"]
