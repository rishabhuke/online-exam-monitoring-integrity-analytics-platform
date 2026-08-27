"""
Tests for the Milestone 4 score endpoints in routes/report.py
(score_bp, url_prefix /api/score). Owner: Rishabh

Mirrors the fixture/setup pattern in tests/test_report.py exactly.

Run with:
    python -m pytest tests/test_score_route.py -v
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


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    test_db = tmp_path / "test_score_route.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)
    monkeypatch.setattr(scoring, "DATABASE", test_db)
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)

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


# --- Self-service endpoint: GET /api/score/<exam_id> ------------------------

def test_get_score_requires_auth(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/score/101")
    assert resp.status_code == 401


def test_get_score_returns_own_session_breakdown(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/score/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert "integrity_score" in body
    assert "face_presence_ratio" in body
    assert "risk_label" in body
    assert "total_flags" in body
    assert "total_browser_events" in body


# --- Dashboard endpoint: GET /api/score/dashboard/<candidate_id>/<exam_id> --

def test_get_dashboard_score_requires_invigilator_auth(test_db_and_client):
    """No session at all -> 401."""
    client, _ = test_db_and_client
    resp = client.get("/api/score/dashboard/1/101")
    assert resp.status_code == 401


def test_get_dashboard_score_rejects_candidate_session(test_db_and_client):
    """A valid CANDIDATE session must not satisfy @invigilator_required."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/score/dashboard/2/101")
    assert resp.status_code == 401


def test_get_dashboard_score_allows_invigilator_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/score/dashboard/2/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert "integrity_score" in body
    assert "risk_label" in body


def test_get_dashboard_score_matches_scoring_module_directly(test_db_and_client):
    """Sanity check that the endpoint's full response matches calling
    modules.scoring.calculate_session_score() directly - i.e. the route
    is a thin passthrough, not silently reshaping the data."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/score/dashboard/2/101")
    body = resp.get_json()

    scoring_result = scoring.calculate_session_score(2, 101)
    for key, value in scoring_result.items():
        assert body[key] == value
