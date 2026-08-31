"""
Tests for the frontend page routes in routes/pages.py (pages_bp).
Owner: shared (Milestone 5 e2e-testing pass)

routes/pages.py has never had a dedicated test file. Every page route
either has no auth check, a manual `"candidate_id" not in session`
redirect, or (for /invigilator/dashboard) the @invigilator_required
decorator from routes/auth.py - and none of that was verified anywhere
in the existing suite. This mirrors the same risk class already fixed
for routes/flags.py and routes/monitoring.py, just for page rendering
instead of JSON APIs.

Mirrors the fixture/setup pattern in tests/test_auth.py exactly.

Run with:
    python -m pytest tests/test_pages.py -v
"""

import os
import sys
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module


@pytest.fixture
def client(monkeypatch, tmp_path):
    test_db = tmp_path / "test_pages.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)

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
        "INSERT INTO Invigilators (id, name, email, password_hash) VALUES (1, 'Invig', 'invig@test.com', ?)",
        (generate_password_hash("SecurePass123"),)
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    app_module.app.secret_key = "test-secret"

    with app_module.app.test_client() as test_client:
        yield test_client


# --- Public pages: no session required -------------------------------------

@pytest.mark.parametrize("path", ["/", "/environment-check", "/help-support"])
def test_public_pages_accessible_without_session(client, path):
    resp = client.get(path)
    assert resp.status_code == 200


# --- Candidate-gated pages: redirect to login when logged out --------------

@pytest.mark.parametrize("path", ["/dashboard", "/exams", "/results", "/analytics"])
def test_candidate_pages_redirect_when_logged_out(client, path):
    resp = client.get(path)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


@pytest.mark.parametrize("path", ["/dashboard", "/exams", "/results", "/analytics"])
def test_candidate_pages_render_with_candidate_session(client, path):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get(path)
    assert resp.status_code == 200


def test_start_exam_redirects_when_logged_out(client):
    resp = client.get("/start_exam/101")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_start_exam_renders_with_candidate_session(client):
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/start_exam/101")
    assert resp.status_code == 200


# --- Invigilator-gated page: /invigilator/dashboard -------------------------
# Uses @invigilator_required (routes/auth.py), which returns a 401 JSON
# error, NOT a redirect - unlike every other page route above. A test that
# assumed a redirect here would be silently wrong.

def test_invigilator_dashboard_requires_auth_no_session(client):
    resp = client.get("/invigilator/dashboard")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["status"] == "error"


def test_invigilator_dashboard_rejects_candidate_session(client):
    """A valid CANDIDATE session must not satisfy @invigilator_required."""
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/invigilator/dashboard")
    assert resp.status_code == 401


def test_invigilator_dashboard_allows_invigilator_session(client):
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/invigilator/dashboard")
    assert resp.status_code == 200


# --- Invigilator-gated page: /invigilator/evidence/<exam_id> ----------------
# Same @invigilator_required decorator as /invigilator/dashboard above -
# mirrors that test class exactly (401 JSON on no/wrong session, 200 on a
# valid invigilator session).

def test_evidence_viewer_requires_auth_no_session(client):
    resp = client.get("/invigilator/evidence/1")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["status"] == "error"


def test_evidence_viewer_rejects_candidate_session(client):
    """A valid CANDIDATE session must not satisfy @invigilator_required."""
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/invigilator/evidence/1")
    assert resp.status_code == 401


def test_evidence_viewer_allows_invigilator_session(client):
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/invigilator/evidence/1")
    assert resp.status_code == 200


# --- Invigilator-gated page: /invigilator/candidate-status/<exam_id> -------
# Same @invigilator_required decorator as /invigilator/dashboard and
# /invigilator/evidence/<exam_id> above - mirrors both test classes exactly.

def test_candidate_status_viewer_requires_auth_no_session(client):
    resp = client.get("/invigilator/candidate-status/1")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["status"] == "error"


def test_candidate_status_viewer_rejects_candidate_session(client):
    """A valid CANDIDATE session must not satisfy @invigilator_required."""
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/invigilator/candidate-status/1")
    assert resp.status_code == 401


def test_candidate_status_viewer_allows_invigilator_session(client):
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/invigilator/candidate-status/1")
    assert resp.status_code == 200


# --- Invigilator-gated page: /invigilator/violations/<exam_id> -------------
# Same @invigilator_required decorator as the other invigilator pages above.

def test_violations_log_requires_auth_no_session(client):
    resp = client.get("/invigilator/violations/1")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["status"] == "error"


def test_violations_log_rejects_candidate_session(client):
    """A valid CANDIDATE session must not satisfy @invigilator_required."""
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/invigilator/violations/1")
    assert resp.status_code == 401


def test_violations_log_allows_invigilator_session(client):
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/invigilator/violations/1")
    assert resp.status_code == 200
