"""
Tests for routes/alert_evidence.py (Pavani's Alert & Evidence Management
API, Milestone 3/4). This endpoint previously had NO auth check at all -
these tests cover both the existing behavior and the @invigilator_required
gate added in Milestone 4. Owner: Rishabh (auth fix), Pavani (endpoint).

Run with:
    python -m pytest tests/test_alert_evidence.py -v
"""

import os
import sys
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.flags_storage as flags_storage
import modules.monitoring_storage as monitoring_storage


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    test_db = tmp_path / "test_alert_evidence.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
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


def _create_flag(app_module_ref):
    conn = sqlite3.connect(app_module_ref.DATABASE)
    conn.execute(
        "INSERT INTO IntegrityFlags (candidate_id, exam_id, flag_type, severity, detail, threshold_breached, created_at) "
        "VALUES (1, 101, 'excessive_tab_switching', 'medium', '3 tab switches', 'max_tab_switches=2', '2026-01-01T00:00:00')"
    )
    conn.commit()
    flag_id = conn.execute("SELECT id FROM IntegrityFlags ORDER BY id DESC LIMIT 1").fetchone()[0]
    conn.close()
    return flag_id


def test_get_alert_evidence_requires_invigilator_auth(test_db_and_client):
    """No session at all -> 401. Previously this endpoint had no auth
    check whatsoever; this test would have failed before the Milestone 4
    auth fix (any request would have gotten a 200 or a 404)."""
    client, _ = test_db_and_client
    resp = client.get("/api/alert-evidence/flag/1")
    assert resp.status_code == 401


def test_get_alert_evidence_rejects_candidate_session(test_db_and_client):
    """A valid CANDIDATE session must not be enough - invigilator only."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/alert-evidence/flag/1")
    assert resp.status_code == 401


def test_get_alert_evidence_allows_invigilator_and_returns_evidence(test_db_and_client):
    client, _ = test_db_and_client
    flag_id = _create_flag(app_module)

    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get(f"/api/alert-evidence/flag/{flag_id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert body["flag"]["flag_type"] == "excessive_tab_switching"
    assert "browser_events" in body
    assert "face_events" in body
    assert "summary" in body


def test_get_alert_evidence_404_for_missing_flag(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/alert-evidence/flag/99999")
    assert resp.status_code == 404
