"""
End-to-end integration test for the full candidate exam journey
(Milestone 5 e2e-testing pass).

Every existing test file exercises exactly one module or route in
isolation (scoring alone, export alone, flags alone, etc.) with data
seeded directly via storage-module calls or raw SQL. None of them prove
that a real candidate session, driven purely through the public HTTP
API in the order the frontend would actually call it, produces a
consistent result across every downstream module.

This test drives ONE session through the real routes, in order:

    1. POST /register            (candidate account + photo)
    2. POST /login                (candidate session established)
    3. GET  /api/exam/<id>/face_check     (monitoring pipeline - face absence)
    4. POST /api/monitoring/browser-event (tab_switch x N -> triggers a flag)
    5. POST /submit_exam           (answers persisted)
    6. POST /api/exam/<id>/end_monitoring (flush open interval)
    7. GET  /api/score/<id>        (candidate's own score, self-service)
    8. GET  /api/report/<id>       (candidate's own AI summary, self-service)
    9. GET  /api/score/dashboard/<candidate_id>/<id>   (invigilator view)
   10. GET  /api/export/<candidate_id>/<id>?format=json (invigilator export)

and asserts the data is consistent end-to-end: the flag raised by the
browser-event route shows up in the score breakdown, the score shown to
the candidate matches the score shown to the invigilator, and the export
payload's embedded score matches both.

Run with:
    python -m pytest tests/test_integration_full_flow.py -v
"""

import os
import sys
import io
import base64
import sqlite3
import pytest
import cv2
import numpy as np
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.photo_capture as photo_capture
import modules.detection_engine as detection_engine
import modules.flags_storage as flags_storage
import modules.monitoring_storage as monitoring_storage
import modules.scoring as scoring
import modules.analytics as analytics
import modules.report_agent as report_agent
import routes.auth as auth_module


def make_fake_photo_data_url():
    img = np.ones((300, 300, 3), dtype=np.uint8) * 255
    _, buf = cv2.imencode(".png", img)
    b64 = base64.b64encode(buf).decode("utf-8")
    return f"data:image/png;base64,{b64}"


@pytest.fixture
def client(monkeypatch, tmp_path):
    test_db = tmp_path / "test_integration.db"

    for module in (
        app_module, auth_module, photo_capture, detection_engine,
        flags_storage, monitoring_storage, scoring, analytics,
    ):
        monkeypatch.setattr(module, "DATABASE", test_db)

    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: True)

    # Force the tab-switch threshold low and deterministic so the flow
    # reliably raises exactly one flag without depending on defaults that
    # might change independently of this test.
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS,
        "max_tab_switches": 3,
    })

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute(
        "INSERT INTO Exams (id, title, duration) VALUES (101, 'Integration Exam', 60)"
    )
    conn.execute(
        "INSERT INTO Questions (id, exam_id, question, option_a, option_b, option_c, option_d, correct_option) "
        "VALUES (1, 101, 'What is 2+2?', '3', '4', '5', '6', 'b')"
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


def test_full_candidate_journey_end_to_end(client):
    exam_id = 101

    # --- 1. Register ---------------------------------------------------
    resp = client.post("/register", json={
        "name": "Integration Candidate",
        "email": "integration@test.com",
        "password": "SecurePass123",
        "photo_data": make_fake_photo_data_url(),
    })
    assert resp.status_code == 201, resp.get_json()
    candidate_id = resp.get_json()["candidate_id"]

    # --- 2. Login --------------------------------------------------------
    resp = client.post("/login", json={
        "email": "integration@test.com",
        "password": "SecurePass123",
    })
    assert resp.status_code == 200
    assert resp.get_json()["candidate"]["candidate_id"] == candidate_id

    # --- 3. Face check (face present -> no absence logged) --------------
    resp = client.post(f"/api/exam/{exam_id}/face_check", json={
        "frame": make_fake_photo_data_url(),
    })
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"

    # --- 4. Browser events: 3 tab switches -> hits threshold of 3 exactly ---
    # (evaluate_tab_switches fires on count == threshold, not >=, so it
    # only raises once rather than re-raising on every switch after)
    for _ in range(3):
        resp = client.post("/api/monitoring/browser-event", json={
            "exam_id": exam_id,
            "event_type": "tab_switch",
        })
        assert resp.status_code == 201

    last_body = resp.get_json()
    assert last_body["flags_raised"], "Expected the 3rd tab switch to raise a flag"

    # --- 5. Submit exam answers -------------------------------------------
    resp = client.post("/submit_exam", json={
        "answers": [{"question_id": 1, "selected_option": "b"}]
    })
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"

    # --- 6. End monitoring (flush any open interval) ----------------------
    resp = client.post(f"/api/exam/{exam_id}/end_monitoring")
    assert resp.status_code == 200

    # --- 7. Candidate views own score --------------------------------------
    resp = client.get(f"/api/score/{exam_id}")
    assert resp.status_code == 200
    candidate_score = resp.get_json()
    assert candidate_score["status"] == "success"
    assert candidate_score["total_flags"] >= 1
    assert candidate_score["integrity_score"] < 100.0  # penalty applied

    # --- 8. Candidate views own AI report -----------------------------
    resp = client.get(f"/api/report/{exam_id}")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"
    assert "summary" in resp.get_json()

    # --- 9. Invigilator views the same candidate's score ------------------
    with client.session_transaction() as sess:
        sess.pop("candidate_id", None)
        sess["invigilator_id"] = 1

    resp = client.get(f"/api/score/dashboard/{candidate_id}/{exam_id}")
    assert resp.status_code == 200
    dashboard_score = resp.get_json()

    # Consistency check: candidate's self-service score and the
    # invigilator's dashboard score must agree on every scoring field.
    for key in ("integrity_score", "face_presence_ratio", "risk_label", "total_flags"):
        assert dashboard_score[key] == candidate_score[key], (
            f"Mismatch on '{key}': candidate saw {candidate_score[key]!r}, "
            f"invigilator dashboard saw {dashboard_score[key]!r}"
        )

    # --- 10. Invigilator exports the full session as JSON ------------------
    resp = client.get(f"/api/export/{candidate_id}/{exam_id}?format=json")
    assert resp.status_code == 200
    export_payload = resp.get_json()
    assert export_payload["status"] == "success"

    # Consistency check: the export's embedded score must match what both
    # the candidate and the invigilator dashboard already saw.
    assert export_payload["integrity_score"]["integrity_score"] == candidate_score["integrity_score"]
    assert export_payload["integrity_score"]["total_flags"] == candidate_score["total_flags"]

    # The tab-switch events we generated in step 4 must be present in the
    # export's raw browser_events list, not just folded into the score.
    tab_switch_events = [
        e for e in export_payload["browser_events"] if e["event_type"] == "tab_switch"
    ]
    assert len(tab_switch_events) == 3
