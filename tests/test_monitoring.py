"""
Tests for the auth fix on routes/monitoring.py (monitoring_bp,
url_prefix /api/monitoring). Owner: Rishabh

Before this fix:
- POST /face-event had no auth check and trusted candidate_id from the
  request body, letting any unauthenticated client write face-absence
  data for an arbitrary candidate.
- POST /browser-event read session["candidate_id"] with no guard,
  causing an unhandled 500 (KeyError) when called without a session.
- GET /face-events and GET /browser-events had no auth at all, letting
  anyone read any candidate's monitoring history.

Mirrors the fixture/setup pattern in tests/test_score_route.py.

Run with:
    python -m pytest tests/test_monitoring.py -v
"""

import os
import sys
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.monitoring_storage as monitoring_storage


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    test_db = tmp_path / "test_monitoring.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)

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


FACE_EVENT_PAYLOAD = {
    "exam_id": 101,
    "start_time": "2026-01-01T00:00:00",
    "end_time": "2026-01-01T00:06:00",
    "duration_seconds": 360.0,
}


# --- POST /api/monitoring/face-event ----------------------------------------

def test_create_face_event_requires_auth(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.post("/api/monitoring/face-event", json=FACE_EVENT_PAYLOAD)
    assert resp.status_code == 401


def test_create_face_event_uses_session_candidate_id_not_body(test_db_and_client):
    """Even if a caller passes a different candidate_id in the body, the
    event must be attributed to the session's candidate, not the body."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    payload = {**FACE_EVENT_PAYLOAD, "candidate_id": 2}
    resp = client.post("/api/monitoring/face-event", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["event"]["candidate_id"] == 1


def test_create_face_event_missing_fields_rejected(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/monitoring/face-event", json={"exam_id": 101})
    assert resp.status_code == 400


# --- POST /api/monitoring/browser-event -------------------------------------

def test_create_browser_event_requires_auth_no_500(test_db_and_client):
    """Regression test: previously this raised an unhandled 500 (KeyError
    on session['candidate_id']) instead of a clean 401."""
    client, _ = test_db_and_client
    resp = client.post("/api/monitoring/browser-event", json={
        "exam_id": 101, "event_type": "tab_switch"
    })
    assert resp.status_code == 401


def test_create_browser_event_succeeds_with_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/monitoring/browser-event", json={
        "exam_id": 101, "event_type": "tab_switch"
    })
    assert resp.status_code == 201


# --- GET /api/monitoring/face-events -----------------------------------------

def test_get_face_events_requires_invigilator_auth_no_session(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/monitoring/face-events?candidate_id=1&exam_id=101")
    assert resp.status_code == 401


def test_get_face_events_rejects_candidate_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/monitoring/face-events?candidate_id=1&exam_id=101")
    assert resp.status_code == 401


def test_get_face_events_allows_invigilator_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/monitoring/face-events?candidate_id=1&exam_id=101")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"


# --- GET /api/monitoring/browser-events --------------------------------------

def test_get_browser_events_requires_invigilator_auth_no_session(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/monitoring/browser-events?candidate_id=1&exam_id=101")
    assert resp.status_code == 401


def test_get_browser_events_rejects_candidate_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/monitoring/browser-events?candidate_id=1&exam_id=101")
    assert resp.status_code == 401


def test_get_browser_events_allows_invigilator_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/monitoring/browser-events?candidate_id=1&exam_id=101")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"
