"""
Tests for the Milestone 4 Data Science Analytics routes
(analytics_bp, url_prefix /api/analytics). Owner: Rishabh

Seeds a small cohort (4 candidates) with varied browser events, face
absence, and flags so distribution/heatmap/clustering all have real
data to work with, not just single-candidate edge cases.

Run with:
    python -m pytest tests/test_analytics_route.py -v
"""

import os
import sys
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.analytics as analytics
import modules.scoring as scoring


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    test_db = tmp_path / "test_analytics_route.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(analytics, "DATABASE", test_db)
    monkeypatch.setattr(scoring, "DATABASE", test_db)

    import routes.auth as auth_module
    monkeypatch.setattr(auth_module, "DATABASE", test_db)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute(
        "INSERT INTO Exams (id, title, duration) VALUES (101, 'Python Fundamentals Exam', 60)"
    )
    conn.execute(
        "INSERT INTO Invigilators (id, name, email, password_hash) VALUES (1, 'Invig', 'invig@test.com', ?)",
        (generate_password_hash("SecurePass123"),)
    )

    # Cohort of 4 candidates with varied behavior:
    # 1: clean session (low risk)
    # 2: some tab switches (medium risk)
    # 3: heavy flags + face absence (high risk)
    # 4: clean, like candidate 1
    for i in range(1, 5):
        conn.execute(
            "INSERT INTO Candidates (id, name, email, password_hash) VALUES (?, ?, ?, 'hash')",
            (i, f"Candidate{i}", f"c{i}@test.com")
        )

    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, details, event_timestamp) "
        "VALUES (2, 101, 'tab_switch', 'x', '2026-01-01T10:00:00')"
    )
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, details, event_timestamp) "
        "VALUES (3, 101, 'tab_switch', 'x', '2026-01-01T10:00:00')"
    )
    conn.execute(
        "INSERT INTO IntegrityFlags (candidate_id, exam_id, flag_type, severity, created_at) "
        "VALUES (3, 101, 'excessive_tab_switching', 'high', '2026-01-01T10:00:05')"
    )
    conn.execute(
        "INSERT INTO FaceAbsenceEvents (candidate_id, exam_id, start_time, end_time, duration_seconds) "
        "VALUES (3, 101, '2026-01-01T10:01:00', '2026-01-01T10:02:00', 60.0)"
    )
    # Candidate 4 gets one harmless browser event so they're in the cohort
    # (only candidates with SOME monitoring data are considered).
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, details, event_timestamp) "
        "VALUES (4, 101, 'focus_loss', 'x', '2026-01-01T10:00:00')"
    )
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, details, event_timestamp) "
        "VALUES (1, 101, 'focus_loss', 'x', '2026-01-01T10:00:00')"
    )

    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client, test_db


def _login_invigilator(client):
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1


# --- Auth gating (shared pattern across all 3 endpoints) -------------------

@pytest.mark.parametrize("path", [
    "/api/analytics/distribution/101",
    "/api/analytics/heatmap/101",
    "/api/analytics/clusters/101",
])
def test_analytics_endpoints_require_invigilator_auth(test_db_and_client, path):
    client, _ = test_db_and_client
    resp = client.get(path)
    assert resp.status_code == 401


@pytest.mark.parametrize("path", [
    "/api/analytics/distribution/101",
    "/api/analytics/heatmap/101",
    "/api/analytics/clusters/101",
])
def test_analytics_endpoints_reject_candidate_session(test_db_and_client, path):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get(path)
    assert resp.status_code == 401


# --- Score distribution -----------------------------------------------------

def test_distribution_returns_cohort_stats(test_db_and_client):
    client, _ = test_db_and_client
    _login_invigilator(client)

    resp = client.get("/api/analytics/distribution/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert body["cohort_size"] == 4
    assert len(body["scores"]) == 4
    assert body["mean"] is not None
    assert len(body["histogram"]["counts"]) == 10


def test_distribution_empty_cohort(test_db_and_client):
    client, _ = test_db_and_client
    _login_invigilator(client)

    resp = client.get("/api/analytics/distribution/999")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["cohort_size"] == 0
    assert body["scores"] == []


# --- Event frequency heatmap -------------------------------------------------

def test_heatmap_returns_matrix_shape(test_db_and_client):
    client, _ = test_db_and_client
    _login_invigilator(client)

    resp = client.get("/api/analytics/heatmap/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert len(body["candidate_ids"]) == 4
    assert len(body["matrix"]) == 4
    for row in body["matrix"]:
        assert len(row) == len(body["event_types"])
    assert "tab_switch" in body["event_types"]
    assert "excessive_tab_switching" in body["event_types"]


# --- K-Means clustering -------------------------------------------------------

def test_clusters_assigns_every_candidate(test_db_and_client):
    client, _ = test_db_and_client
    _login_invigilator(client)

    resp = client.get("/api/analytics/clusters/101")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert body["cohort_size"] == 4
    assert len(body["assignments"]) == 4
    for a in body["assignments"]:
        assert a["cluster_id"] is not None
        assert a["cluster_risk_label"] in ("Low", "Medium", "High")


def test_clusters_candidate_3_ranked_highest_risk(test_db_and_client):
    """Candidate 3 has the most flags/events/face-absence - should land
    in the cluster with the highest risk label."""
    client, _ = test_db_and_client
    _login_invigilator(client)

    resp = client.get("/api/analytics/clusters/101")
    body = resp.get_json()

    c3 = next(a for a in body["assignments"] if a["candidate_id"] == 3)
    assert c3["cluster_risk_label"] == "High"


def test_clusters_insufficient_data_for_small_cohort(test_db_and_client):
    """exam_id 999 has zero cohort - should return empty assignments,
    not error."""
    client, _ = test_db_and_client
    _login_invigilator(client)

    resp = client.get("/api/analytics/clusters/999")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["cohort_size"] == 0
    assert body["assignments"] == []


def test_get_exams_requires_invigilator_auth(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/analytics/exams")
    assert resp.status_code == 401


def test_get_exams_returns_seeded_exam(test_db_and_client):
    client, _ = test_db_and_client
    _login_invigilator(client)

    resp = client.get("/api/analytics/exams")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert {"id": 101, "title": "Python Fundamentals Exam", "duration": 60} in body["exams"]
