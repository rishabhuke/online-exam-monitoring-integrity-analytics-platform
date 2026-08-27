"""
Tests for the Milestone 4 export endpoint in routes/export.py
(export_bp, url_prefix /api/export). Owner: Rishabh

Mirrors the fixture/setup pattern in tests/test_report.py and
tests/test_score_route.py exactly.

Run with:
    python -m pytest tests/test_export_route.py -v
"""

import os
import sys
import csv
import sqlite3
import io
import json
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
    test_db = tmp_path / "test_export_route.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)
    monkeypatch.setattr(scoring, "DATABASE", test_db)
    monkeypatch.setattr(analytics, "DATABASE", test_db)
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
    # Give candidate 2 some real events/flags so we can check both
    # empty-section and populated-section CSV handling.
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, details, event_timestamp) "
        "VALUES (2, 101, 'tab_switch', 'Exam page hidden.', '2026-01-01T10:00:00')"
    )
    conn.execute(
        "INSERT INTO IntegrityFlags (candidate_id, exam_id, flag_type, severity, created_at) "
        "VALUES (2, 101, 'excessive_tab_switching', 'medium', '2026-01-01T10:00:05')"
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client, test_db


# --- Auth gating -------------------------------------------------------

def test_export_requires_invigilator_auth_no_session(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/export/2/101")
    assert resp.status_code == 401


def test_export_rejects_candidate_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/export/2/101")
    assert resp.status_code == 401


# --- JSON format ---------------------------------------------------------

def test_export_json_default_format(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/export/2/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert body["candidate_id"] == 2
    assert body["exam_id"] == 101
    assert "integrity_score" in body
    assert "face_absence_events" in body
    assert "browser_events" in body
    assert len(body["browser_events"]) == 1
    assert "flags" in body
    assert len(body["flags"]) == 1
    assert "ai_summary" in body
    assert "summary" in body["ai_summary"]
    assert "risk_label" in body["ai_summary"]
    # Cohort here is just 1 candidate (below n_clusters=3 default), so
    # this hits the "Insufficient Data" branch: a dict, not None.
    assert body["cluster_assignment"] is not None
    assert body["cluster_assignment"]["candidate_id"] == 2
    assert body["cluster_assignment"]["cluster_risk_label"] == "Insufficient Data"


def test_export_json_explicit_format(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/export/2/101?format=json")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"


def test_export_rejects_invalid_format(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/export/2/101?format=xml")
    assert resp.status_code == 400


# --- CSV format ------------------------------------------------------------

def test_export_csv_format_headers_and_content_type(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/export/2/101?format=csv")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    assert "attachment" in resp.headers["Content-Disposition"]
    assert "candidate2_exam101" in resp.headers["Content-Disposition"]


def test_export_csv_contains_all_sections(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/export/2/101?format=csv")
    text = resp.get_data(as_text=True)

    for marker in [
        "# SESSION", "# INTEGRITY_SCORE", "# FACE_ABSENCE_EVENTS",
        "# BROWSER_EVENTS", "# FLAGS", "# AI_SUMMARY", "# CLUSTER_ASSIGNMENT",
    ]:
        assert marker in text


def test_export_csv_empty_section_marked_no_data(test_db_and_client):
    """Candidate 2 has no face-absence events seeded - that section
    should still render predictably, not error or vanish."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/export/2/101?format=csv")
    text = resp.get_data(as_text=True)
    reader = list(csv.reader(io.StringIO(text)))

    section_idx = next(i for i, row in enumerate(reader) if row == ["# FACE_ABSENCE_EVENTS"])
    assert reader[section_idx + 1] == ["(no data)"]


def test_export_csv_populated_section_has_data_row(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/export/2/101?format=csv")
    text = resp.get_data(as_text=True)
    reader = list(csv.reader(io.StringIO(text)))

    section_idx = next(i for i, row in enumerate(reader) if row == ["# BROWSER_EVENTS"])
    header_row = reader[section_idx + 1]
    data_row = reader[section_idx + 2]
    assert "event_type" in header_row
    assert "tab_switch" in data_row
