"""
Tests for IntegrityFlags storage layer and API endpoints (Milestone 2 - Priyanshu's task).

Run with:
    python -m pytest tests/test_flags.py -v
"""

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.flags_storage as flags_storage
import routes.flags as flags_route_module


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    """
    Fixture providing an isolated SQLite database and Flask test client.
    Seeds test candidates and exams for FK constraints.
    """
    test_db = tmp_path / "test_flags.db"

    # Patch database path across app and storage modules
    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)

    # Initialize schema
    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    # Seed candidates and exams for FK consistency
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
        "INSERT INTO Exams (id, title, duration) VALUES (102, 'Data Science Exam', 90)"
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client, test_db


# ---------------------------------------------------------------------------
# Storage Layer Unit Tests (modules/flags_storage.py)
# ---------------------------------------------------------------------------

def test_storage_create_and_get_flag(test_db_and_client):
    _, db_path = test_db_and_client

    flag = flags_storage.create_flag(
        candidate_id=1,
        exam_id=101,
        flag_type="face_absent_single_interval",
        severity="high",
        detail="Face absent for 150 seconds",
        threshold_breached="max_face_absent_seconds=120",
    )

    assert flag is not None
    assert flag["id"] is not None
    assert flag["candidate_id"] == 1
    assert flag["exam_id"] == 101
    assert flag["flag_type"] == "face_absent_single_interval"
    assert flag["severity"] == "high"

    retrieved = flags_storage.get_flag_by_id(flag["id"])
    assert retrieved == flag


def test_storage_get_flags_filtered(test_db_and_client):
    _, _ = test_db_and_client

    flags_storage.create_flag(1, 101, "face_absent", "high", "detail 1", "thresh 1")
    flags_storage.create_flag(1, 101, "tab_switch", "medium", "detail 2", "thresh 2")
    flags_storage.create_flag(2, 101, "face_absent", "high", "detail 3", "thresh 3")
    flags_storage.create_flag(1, 102, "focus_loss", "low", "detail 4", "thresh 4")

    # Filter by candidate 1
    c1_flags = flags_storage.get_flags_filtered(candidate_id=1)
    assert len(c1_flags) == 3

    # Filter by candidate 1 and exam 101
    c1_e101_flags = flags_storage.get_flags_filtered(candidate_id=1, exam_id=101)
    assert len(c1_e101_flags) == 2

    # Filter by severity high
    high_flags = flags_storage.get_flags_filtered(severity="high")
    assert len(high_flags) == 2

    # Filter by flag_type tab_switch
    tab_flags = flags_storage.get_flags_filtered(flag_type="tab_switch")
    assert len(tab_flags) == 1
    assert tab_flags[0]["severity"] == "medium"


def test_storage_delete_flag(test_db_and_client):
    _, _ = test_db_and_client

    flag = flags_storage.create_flag(1, 101, "test_type", "low", "detail", "thresh")
    assert flags_storage.get_flag_by_id(flag["id"]) is not None

    deleted = flags_storage.delete_flag(flag["id"])
    assert deleted is True
    assert flags_storage.get_flag_by_id(flag["id"]) is None

    # Delete non-existent ID
    assert flags_storage.delete_flag(9999) is False


def test_storage_summary_stats(test_db_and_client):
    _, _ = test_db_and_client

    flags_storage.create_flag(1, 101, "face_absent", "high", "", "")
    flags_storage.create_flag(1, 101, "face_absent", "high", "", "")
    flags_storage.create_flag(2, 101, "tab_switch", "medium", "", "")
    flags_storage.create_flag(1, 102, "focus_loss", "low", "", "")

    stats = flags_storage.get_flag_summary_stats()
    assert stats["total_flags"] == 4
    assert stats["by_severity"]["high"] == 2
    assert stats["by_severity"]["medium"] == 1
    assert stats["by_severity"]["low"] == 1
    assert stats["by_flag_type"]["face_absent"] == 2

    # Exam scoped stats
    stats_101 = flags_storage.get_flag_summary_stats(exam_id=101)
    assert stats_101["total_flags"] == 3


# ---------------------------------------------------------------------------
# Flask API Endpoint Tests (routes/flags.py)
#
# Auth boundary (added after these routes were found to have NO auth at
# all): list/create/delete/summary are invigilator-only; GET by id is
# self-service for the owning candidate, or open to any invigilator.
# ---------------------------------------------------------------------------

def _as_invigilator(client):
    with client.session_transaction() as sess:
        sess.clear()
        sess["invigilator_id"] = 1


def _as_candidate(client, candidate_id):
    with client.session_transaction() as sess:
        sess.clear()
        sess["candidate_id"] = candidate_id


def test_api_create_flag_requires_invigilator(test_db_and_client):
    client, _ = test_db_and_client

    res = client.post("/api/flags", json={
        "candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"
    })
    assert res.status_code == 401

    _as_candidate(client, 1)
    res = client.post("/api/flags", json={
        "candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"
    })
    assert res.status_code == 401


def test_api_create_flag_success(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)

    payload = {
        "candidate_id": 1,
        "exam_id": 101,
        "flag_type": "face_absent_single_interval",
        "severity": "high",
        "detail": "Absence logged for 140s",
        "threshold_breached": "max_face_absent_seconds=120"
    }

    res = client.post("/api/flags", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["status"] == "success"
    assert data["flag"]["candidate_id"] == 1
    assert data["flag"]["severity"] == "high"


def test_api_create_flag_validation_errors(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)

    # Missing required field
    res = client.post("/api/flags", json={"candidate_id": 1, "exam_id": 101})
    assert res.status_code == 400
    assert "Missing required fields" in res.get_json()["message"]

    # Invalid integer IDs
    res = client.post("/api/flags", json={
        "candidate_id": "invalid",
        "exam_id": 101,
        "flag_type": "type",
        "severity": "high"
    })
    assert res.status_code == 400


def test_api_list_flags_requires_invigilator(test_db_and_client):
    client, _ = test_db_and_client

    res = client.get("/api/flags")
    assert res.status_code == 401

    _as_candidate(client, 1)
    res = client.get("/api/flags")
    assert res.status_code == 401


def test_api_list_flags_with_filtering(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)

    client.post("/api/flags", json={"candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"})
    client.post("/api/flags", json={"candidate_id": 1, "exam_id": 101, "flag_type": "tab_switch", "severity": "medium"})
    client.post("/api/flags", json={"candidate_id": 2, "exam_id": 101, "flag_type": "face_absent", "severity": "high"})

    # All flags
    res = client.get("/api/flags")
    assert res.status_code == 200
    assert res.get_json()["count"] == 3

    # Filter candidate_id=1
    res = client.get("/api/flags?candidate_id=1")
    assert res.status_code == 200
    assert res.get_json()["count"] == 2

    # Filter severity=high
    res = client.get("/api/flags?severity=high")
    assert res.status_code == 200
    assert res.get_json()["count"] == 2


def test_api_get_flag_by_id_requires_auth(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)
    post_res = client.post("/api/flags", json={
        "candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"
    })
    flag_id = post_res.get_json()["flag"]["id"]

    with client.session_transaction() as sess:
        sess.clear()

    res = client.get(f"/api/flags/{flag_id}")
    assert res.status_code == 401


def test_api_get_flag_by_id_rejects_other_candidate(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)
    post_res = client.post("/api/flags", json={
        "candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"
    })
    flag_id = post_res.get_json()["flag"]["id"]

    _as_candidate(client, 2)
    res = client.get(f"/api/flags/{flag_id}")
    assert res.status_code == 403


def test_api_get_flag_by_id(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)

    post_res = client.post("/api/flags", json={
        "candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"
    })
    flag_id = post_res.get_json()["flag"]["id"]

    # Invigilator can fetch any flag
    res = client.get(f"/api/flags/{flag_id}")
    assert res.status_code == 200
    assert res.get_json()["flag"]["id"] == flag_id

    # Owning candidate can fetch their own flag
    _as_candidate(client, 1)
    res = client.get(f"/api/flags/{flag_id}")
    assert res.status_code == 200
    assert res.get_json()["flag"]["id"] == flag_id

    # Fetch non-existent flag (still as an authenticated candidate)
    res_404 = client.get("/api/flags/99999")
    assert res_404.status_code == 404


def test_api_delete_flag_requires_invigilator(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)
    post_res = client.post("/api/flags", json={
        "candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"
    })
    flag_id = post_res.get_json()["flag"]["id"]

    _as_candidate(client, 1)
    res = client.delete(f"/api/flags/{flag_id}")
    assert res.status_code == 401


def test_api_delete_flag(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)

    post_res = client.post("/api/flags", json={
        "candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"
    })
    flag_id = post_res.get_json()["flag"]["id"]

    res = client.delete(f"/api/flags/{flag_id}")
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"

    # Verify deleted
    get_res = client.get(f"/api/flags/{flag_id}")
    assert get_res.status_code == 404


def test_api_summary_stats_requires_invigilator(test_db_and_client):
    client, _ = test_db_and_client

    res = client.get("/api/flags/summary")
    assert res.status_code == 401


def test_api_summary_stats(test_db_and_client):
    client, _ = test_db_and_client
    _as_invigilator(client)

    client.post("/api/flags", json={"candidate_id": 1, "exam_id": 101, "flag_type": "face_absent", "severity": "high"})
    client.post("/api/flags", json={"candidate_id": 2, "exam_id": 101, "flag_type": "tab_switch", "severity": "medium"})

    res = client.get("/api/flags/summary")
    assert res.status_code == 200
    summary = res.get_json()["summary"]
    assert summary["total_flags"] == 2
    assert summary["by_severity"]["high"] == 1
    assert summary["by_severity"]["medium"] == 1

    res_101 = client.get("/api/flags/summary?exam_id=101")
    assert res_101.status_code == 200
    assert res_101.get_json()["summary"]["total_flags"] == 2


# --- GET /api/flags/exam/<exam_id> -----------------------------------------
# Lists every flag for an exam (unfiltered by candidate), joined with the
# candidate's name - powers the invigilator violations-log dashboard page.

def test_api_get_flags_for_exam_requires_invigilator(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/flags/exam/101")
    assert resp.status_code == 401


def test_api_get_flags_for_exam_returns_joined_candidate_name(test_db_and_client):
    client, db_path = test_db_and_client

    flags_storage.create_flag(
        candidate_id=1,
        exam_id=101,
        flag_type="face_absent_single_interval",
        severity="medium",
        detail="face missing 12s",
        threshold_breached="10s",
    )
    flags_storage.create_flag(
        candidate_id=2,
        exam_id=101,
        flag_type="tab_switch",
        severity="high",
        detail="switched tabs 4 times",
        threshold_breached="3",
    )
    # Different exam - must not appear in the exam 101 results.
    flags_storage.create_flag(
        candidate_id=2,
        exam_id=102,
        flag_type="tab_switch",
        severity="low",
        detail="switched tabs once",
        threshold_breached="3",
    )

    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/flags/exam/101")
    assert resp.status_code == 200
    body = resp.get_json()

    assert body["status"] == "success"
    assert body["exam_id"] == 101
    assert body["count"] == 2

    flags_by_candidate = {f["candidate_id"]: f for f in body["flags"]}
    assert flags_by_candidate[1]["candidate_name"] == "Alice"
    assert flags_by_candidate[2]["candidate_name"] == "Bob"
    assert all(f["exam_id"] == 101 for f in body["flags"])


def test_api_get_flags_for_exam_empty_exam_returns_empty_list(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/flags/exam/999")
    assert resp.status_code == 200
    body = resp.get_json()

    assert body["count"] == 0
    assert body["flags"] == []
