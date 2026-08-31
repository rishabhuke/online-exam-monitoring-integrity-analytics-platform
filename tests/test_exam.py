"""
Tests for the exam session face presence monitoring pipeline (Milestone 2).
Owner: Rishabh

Run with:
    python -m pytest tests/test_exam.py -v

Uses a temporary, isolated SQLite database (same pattern as test_auth.py) so
these tests never touch the real development database. Face detection
itself is monkeypatched to a controllable stub, since reliably faking a
"real face" in a synthetic image isn't practical - the underlying detection
call (contains_face) is already validated against real behaviour in
test_photo_capture.py.
"""

import os
import sys
import sqlite3
import base64
import time

import cv2
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import modules.photo_capture as photo_capture
import modules.detection_engine as detection_engine
import modules.flags_storage as flags_storage
import modules.monitoring_storage as monitoring_storage
import modules.evidence as evidence


def make_fake_data_url():
    """A blank frame - contents don't matter since contains_face is stubbed."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    _, buf = cv2.imencode(".png", img)
    b64 = base64.b64encode(buf).decode("utf-8")
    return f"data:image/png;base64,{b64}"


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    """Points photo_capture.DATABASE at a temp SQLite file with schema applied."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(photo_capture, "DATABASE", test_db)
    monkeypatch.setattr(detection_engine, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)
    monkeypatch.setattr(evidence, "DATABASE", test_db)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    # Seed Candidates/Exams rows for every id these tests reference, since
    # FaceAbsenceEvents has FK constraints on both (matching the rest of
    # this app's schema).
    for cid in (1, 2, 5, 7, 9):
        conn.execute(
            "INSERT INTO Candidates (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (cid, f"Test Candidate {cid}", f"candidate{cid}@example.com", "hash"),
        )
    for eid in (1, 2, 3, 100):
        conn.execute(
            "INSERT INTO Exams (id, title, duration) VALUES (?, ?, ?)",
            (eid, f"Test Exam {eid}", 60),
        )
    conn.commit()
    conn.close()

    # Each test gets a clean in-memory tracking dict too, since it's
    # module-level state shared across calls.
    photo_capture._monitor_sessions.clear()
    detection_engine._identity_mismatch_streaks.clear()

    return test_db


def _rows(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM FaceAbsenceEvents").fetchall()
    conn.close()
    return rows


def test_face_present_logs_nothing(isolated_db, monkeypatch):
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: True)

    result = photo_capture.process_exam_frame(1, 1, make_fake_data_url())

    assert result["face_present"] is True
    assert result["interval_logged"] is False
    assert len(_rows(isolated_db)) == 0


def test_single_absent_frame_does_not_open_interval(isolated_db, monkeypatch):
    """Below ABSENCE_CONFIRM_FRAMES, a lone absent frame should not yet be
    treated as a confirmed interval."""
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: False)
    monkeypatch.setattr(photo_capture, "ABSENCE_CONFIRM_FRAMES", 2)

    result = photo_capture.process_exam_frame(1, 1, make_fake_data_url())

    assert result["face_present"] is False
    assert result["ongoing_absence_seconds"] == 0.0  # not confirmed yet


def test_sustained_absence_then_return_logs_interval(isolated_db, monkeypatch):
    """Simulates: face absent for a few frames, then reappears - one closed
    interval should be persisted to FaceAbsenceEvents."""
    monkeypatch.setattr(photo_capture, "ABSENCE_CONFIRM_FRAMES", 2)

    monkeypatch.setattr(photo_capture, "contains_face", lambda image: False)
    photo_capture.process_exam_frame(5, 2, make_fake_data_url())  # frame 1: absent
    time.sleep(0.05)
    result_confirmed = photo_capture.process_exam_frame(5, 2, make_fake_data_url())  # frame 2: confirmed
    assert result_confirmed["face_present"] is False
    assert result_confirmed["ongoing_absence_seconds"] > 0

    monkeypatch.setattr(photo_capture, "contains_face", lambda image: True)
    result_returned = photo_capture.process_exam_frame(5, 2, make_fake_data_url())  # face back

    assert result_returned["face_present"] is True
    assert result_returned["interval_logged"] is True
    assert result_returned["interval_duration_seconds"] > 0

    rows = _rows(isolated_db)
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == 5
    assert rows[0]["exam_id"] == 2
    assert rows[0]["duration_seconds"] > 0


def test_sessions_tracked_independently(isolated_db, monkeypatch):
    """Two different (candidate_id, exam_id) sessions shouldn't interfere
    with each other's absence tracking."""
    monkeypatch.setattr(photo_capture, "ABSENCE_CONFIRM_FRAMES", 1)
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: False)

    photo_capture.process_exam_frame(1, 100, make_fake_data_url())
    photo_capture.process_exam_frame(2, 100, make_fake_data_url())

    assert (1, 100) in photo_capture._monitor_sessions
    assert (2, 100) in photo_capture._monitor_sessions
    assert photo_capture._monitor_sessions[(1, 100)] is not photo_capture._monitor_sessions[(2, 100)]


def test_end_session_flushes_open_interval(isolated_db, monkeypatch):
    """If the exam ends while a face-absence interval is still open (no
    return-of-face frame ever arrived), end_exam_monitoring must still
    persist it."""
    monkeypatch.setattr(photo_capture, "ABSENCE_CONFIRM_FRAMES", 1)
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: False)

    photo_capture.process_exam_frame(9, 3, make_fake_data_url())
    assert len(_rows(isolated_db)) == 0  # still open, nothing persisted yet

    photo_capture.end_exam_monitoring(9, 3)

    rows = _rows(isolated_db)
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == 9
    assert (9, 3) not in photo_capture._monitor_sessions  # state cleared


def test_process_exam_frame_raises_on_bad_frame(isolated_db, monkeypatch):
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: True)
    with pytest.raises(ValueError):
        photo_capture.process_exam_frame(1, 1, "not-a-valid-data-url")


# ---------------------------------------------------------------------------
# Detection engine tests (modules/detection_engine.py)
# ---------------------------------------------------------------------------

def _insert_face_absence_event(db_path, candidate_id, exam_id, duration_seconds):
    """Helper: directly insert a FaceAbsenceEvents row for cumulative-threshold tests."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO FaceAbsenceEvents (candidate_id, exam_id, start_time, end_time, duration_seconds)
        VALUES (?, ?, ?, ?, ?)
        """,
        (candidate_id, exam_id, "2026-01-01T00:00:00", "2026-01-01T00:01:00", duration_seconds),
    )
    conn.commit()
    conn.close()


def test_single_interval_below_threshold_raises_nothing(isolated_db):
    raised = detection_engine.evaluate_face_absence(1, 1, interval_duration_seconds=10)
    assert raised == []
    assert detection_engine.get_flags(1, 1) == []


def test_single_interval_above_threshold_raises_flag(isolated_db, monkeypatch):
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "max_face_absent_seconds": 60,
    })

    raised = detection_engine.evaluate_face_absence(1, 1, interval_duration_seconds=90)

    assert "face_absent_single_interval" in raised
    flags = detection_engine.get_flags(1, 1)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "face_absent_single_interval"
    assert flags[0]["severity"] == "high"


def test_cumulative_absence_across_multiple_intervals_raises_flag(isolated_db, monkeypatch):
    """Several short intervals, individually under threshold, should still
    raise a cumulative flag once their sum crosses max_cumulative_absent_seconds."""
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS,
        "max_face_absent_seconds": 999,       # disable single-interval flag for this test
        "max_cumulative_absent_seconds": 100,
    })

    _insert_face_absence_event(isolated_db, 7, 1, 40)
    _insert_face_absence_event(isolated_db, 7, 1, 40)
    # cumulative so far: 80s, still under 100s threshold
    raised_early = detection_engine.evaluate_face_absence(7, 1, interval_duration_seconds=0)
    assert "face_absent_cumulative" not in raised_early

    _insert_face_absence_event(isolated_db, 7, 1, 30)
    # cumulative now: 110s, over threshold
    raised_final = detection_engine.evaluate_face_absence(7, 1, interval_duration_seconds=30)

    assert "face_absent_cumulative" in raised_final
    flags = detection_engine.get_flags(7, 1)
    assert any(f["flag_type"] == "face_absent_cumulative" for f in flags)


def test_get_flags_scoped_to_candidate_and_exam(isolated_db, monkeypatch):
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "max_face_absent_seconds": 5,
    })

    detection_engine.evaluate_face_absence(1, 1, interval_duration_seconds=50)
    detection_engine.evaluate_face_absence(2, 1, interval_duration_seconds=50)

    assert len(detection_engine.get_flags(1, 1)) == 1
    assert len(detection_engine.get_flags(2, 1)) == 1
    assert len(detection_engine.get_flags(9, 1)) == 0  # candidate with no flags


def test_evaluate_tab_switches_below_threshold_raises_nothing(isolated_db):
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    assert detection_engine.evaluate_tab_switches(1, 1) == []
    assert detection_engine.get_flags(1, 1) == []


def test_evaluate_tab_switches_above_threshold_raises_flag(isolated_db, monkeypatch):
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "max_tab_switches": 2,
    })

    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    assert detection_engine.evaluate_tab_switches(1, 1) == []

    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    raised = detection_engine.evaluate_tab_switches(1, 1)

    assert "excessive_tab_switching" in raised
    flags = detection_engine.get_flags(1, 1)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "excessive_tab_switching"


def test_evaluate_tab_switches_ignores_other_event_types(isolated_db):
    monitoring_storage.create_browser_event(1, 1, event_type="focus_loss")
    monitoring_storage.create_browser_event(1, 1, event_type="focus_loss")
    monitoring_storage.create_browser_event(1, 1, event_type="focus_loss")
    assert detection_engine.evaluate_tab_switches(1, 1) == []


def test_evaluate_focus_loss_below_threshold_raises_nothing(isolated_db):
    monitoring_storage.create_browser_event(1, 1, event_type="focus_loss")
    assert detection_engine.evaluate_focus_loss(1, 1) == []
    assert detection_engine.get_flags(1, 1) == []


def test_evaluate_focus_loss_above_threshold_raises_flag(isolated_db, monkeypatch):
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "max_focus_loss_count": 2,
    })

    monitoring_storage.create_browser_event(1, 1, event_type="focus_loss")
    assert detection_engine.evaluate_focus_loss(1, 1) == []

    monitoring_storage.create_browser_event(1, 1, event_type="focus_loss")
    raised = detection_engine.evaluate_focus_loss(1, 1)

    assert "excessive_focus_loss" in raised
    flags = detection_engine.get_flags(1, 1)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "excessive_focus_loss"
    assert flags[0]["severity"] == "low"


def test_evaluate_focus_loss_ignores_other_event_types(isolated_db):
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    assert detection_engine.evaluate_focus_loss(1, 1) == []


def test_evaluate_focus_loss_counts_case_insensitively(isolated_db, monkeypatch):
    """Mirrors the real frontend payload shape (exam_window.js sends
    'FOCUS_LOSS', uppercase) - evaluate_focus_loss() must count these
    regardless of the storage layer's casing."""
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "max_focus_loss_count": 2,
    })

    monitoring_storage.create_browser_event(1, 1, event_type="FOCUS_LOSS")
    monitoring_storage.create_browser_event(1, 1, event_type="FOCUS_LOSS")
    raised = detection_engine.evaluate_focus_loss(1, 1)

    assert "excessive_focus_loss" in raised


# ---------------------------------------------------------------------------
# Regression test for the browser-event event_type casing bug (fix/browser-
# event-type-casing). The real frontend (exam_window.js) sends "TAB_SWITCH"
# (uppercase), but routes/monitoring.py and detection_engine.py originally
# compared against lowercase "tab_switch" only, so flags never fired in
# production even though every existing test passed (they all constructed
# events with lowercase strings directly, bypassing the real bug).
#
# HTTP-level tests below prove both routes/monitoring.py dispatch paths
# (tab_switch and focus_loss) work correctly against the real frontend
# payload casing.
# ---------------------------------------------------------------------------

@pytest.fixture
def http_isolated_db(monkeypatch, tmp_path):
    """Same isolation as isolated_db, but also patches app.DATABASE and
    returns a Flask test client, since this test needs to go through the
    real HTTP route (routes/monitoring.py) rather than calling storage/
    detection functions directly."""
    import app as app_module

    test_db = tmp_path / "test_http.db"
    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(photo_capture, "DATABASE", test_db)
    monkeypatch.setattr(detection_engine, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)
    monkeypatch.setattr(evidence, "DATABASE", test_db)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (1, 'Test Candidate', 'candidate@example.com', 'hash')"
    )
    conn.execute(
        "INSERT INTO Exams (id, title, duration) VALUES (1, 'Test Exam', 60)"
    )
    conn.commit()
    conn.close()

    photo_capture._monitor_sessions.clear()
    detection_engine._identity_mismatch_streaks.clear()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


def test_environment_face_check_requires_auth(http_isolated_db):
    """No candidate_id in session -> 401, matching the existing face_check
    route's auth pattern."""
    client = http_isolated_db
    resp = client.post("/api/exam/environment/face_check", json={
        "frame": make_fake_data_url(),
    })
    assert resp.status_code == 401
    assert resp.get_json()["status"] == "error"


def test_environment_face_check_returns_face_present_true(http_isolated_db, monkeypatch):
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: True)
    client = http_isolated_db

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/exam/environment/face_check", json={
        "frame": make_fake_data_url(),
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["face_present"] is True


def test_environment_face_check_returns_face_present_false(http_isolated_db, monkeypatch):
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: False)
    client = http_isolated_db

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/exam/environment/face_check", json={
        "frame": make_fake_data_url(),
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["face_present"] is False


def test_environment_face_check_missing_frame_returns_400(http_isolated_db):
    client = http_isolated_db
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/exam/environment/face_check", json={})
    assert resp.status_code == 400


def test_environment_face_check_does_not_write_integrity_flags(http_isolated_db, monkeypatch):
    """Critical isolation guarantee: this endpoint must never write to
    FaceAbsenceEvents or IntegrityFlags, since it isn't a real exam
    session - see the route's own docstring."""
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: False)
    client = http_isolated_db

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    for _ in range(5):
        resp = client.post("/api/exam/environment/face_check", json={
            "frame": make_fake_data_url(),
        })
        assert resp.status_code == 200

    conn = sqlite3.connect(photo_capture.DATABASE)
    flags = conn.execute("SELECT COUNT(*) FROM IntegrityFlags").fetchone()[0]
    absences = conn.execute("SELECT COUNT(*) FROM FaceAbsenceEvents").fetchone()[0]
    conn.close()
    assert flags == 0
    assert absences == 0


def test_uppercase_tab_switch_from_frontend_raises_flag(http_isolated_db, monkeypatch):
    """Reproduces the real frontend payload shape (exam_window.js sends
    'TAB_SWITCH', uppercase) through the actual HTTP route, and asserts a
    flag is raised once the threshold is crossed. Before the casing fix,
    this failed silently: the event was stored but 'flags_raised' was
    always [] because 'TAB_SWITCH' != 'tab_switch'."""
    client = http_isolated_db
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "max_tab_switches": 2,
    })

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp1 = client.post("/api/monitoring/browser-event", json={
        "exam_id": 1, "event_type": "TAB_SWITCH", "details": "Exam page became hidden."
    })
    assert resp1.status_code == 201
    assert resp1.get_json()["flags_raised"] == []

    resp2 = client.post("/api/monitoring/browser-event", json={
        "exam_id": 1, "event_type": "TAB_SWITCH", "details": "Exam page became hidden."
    })
    assert resp2.status_code == 201
    body = resp2.get_json()
    assert "excessive_tab_switching" in body["flags_raised"]

    flags = detection_engine.get_flags(1, 1)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "excessive_tab_switching"


def test_uppercase_focus_loss_from_frontend_raises_flag(http_isolated_db, monkeypatch):
    """Reproduces the real frontend payload shape (exam_window.js sends
    'FOCUS_LOSS', uppercase) through the actual HTTP route, and asserts a
    flag is raised once the threshold is crossed."""
    client = http_isolated_db
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "max_focus_loss_count": 2,
    })

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp1 = client.post("/api/monitoring/browser-event", json={
        "exam_id": 1, "event_type": "FOCUS_LOSS", "details": "Exam window lost focus."
    })
    assert resp1.status_code == 201
    assert resp1.get_json()["flags_raised"] == []

    resp2 = client.post("/api/monitoring/browser-event", json={
        "exam_id": 1, "event_type": "FOCUS_LOSS", "details": "Exam window lost focus."
    })
    assert resp2.status_code == 201
    body = resp2.get_json()
    assert "excessive_focus_loss" in body["flags_raised"]

    flags = detection_engine.get_flags(1, 1)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "excessive_focus_loss"


# ---------------------------------------------------------------------------
# Identity verification tests (modules/detection_engine.evaluate_identity_check)
# (Milestone 5 - integrity analysis port)
#
# face_verification.verify_candidate() itself is not exercised here - it
# calls real InsightFace, which is slow and requires the model files/a
# registered photo on disk. Instead we test evaluate_identity_check() with
# fake verification_result dicts of the exact shape verify_candidate()
# returns, same spirit as this file already stubbing contains_face().
# ---------------------------------------------------------------------------

def test_identity_verified_resets_mismatch_streak(isolated_db, monkeypatch):
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "identity_mismatch_confirm_count": 2,
    })

    # Build up one mismatch, then a verified result should reset the streak.
    detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.3})
    raised = detection_engine.evaluate_identity_check(1, 1, {"status": "verified", "similarity": 0.9})

    assert raised == []
    assert detection_engine._identity_mismatch_streaks[(1, 1)] == 0
    assert detection_engine.get_flags(1, 1) == []


def test_single_mismatch_below_confirm_count_raises_nothing(isolated_db, monkeypatch):
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "identity_mismatch_confirm_count": 2,
    })

    raised = detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.2})

    assert raised == []
    assert detection_engine.get_flags(1, 1) == []


def test_confirmed_mismatch_raises_flag_and_resets_streak(isolated_db, monkeypatch):
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "identity_mismatch_confirm_count": 2,
    })

    detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.2})
    raised = detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.25})

    assert "identity_mismatch" in raised
    flags = detection_engine.get_flags(1, 1)
    assert len(flags) == 1
    assert flags[0]["flag_type"] == "identity_mismatch"
    assert flags[0]["severity"] == "high"
    # streak resets after flagging - a third mismatch shouldn't immediately re-flag
    assert detection_engine._identity_mismatch_streaks[(1, 1)] == 0


def test_no_face_during_identity_check_flags_immediately(isolated_db):
    raised = detection_engine.evaluate_identity_check(1, 1, {"status": "no_face", "similarity": None})

    assert raised == ["identity_check_no_face"]
    flags = detection_engine.get_flags(1, 1)
    assert len(flags) == 1
    assert flags[0]["severity"] == "medium"


def test_multiple_faces_during_identity_check_flags_immediately(isolated_db):
    raised = detection_engine.evaluate_identity_check(
        1, 1, {"status": "multiple_faces", "similarity": None, "message": "2 faces detected in live frame."}
    )

    assert raised == ["identity_check_multiple_faces"]
    flags = detection_engine.get_flags(1, 1)
    assert len(flags) == 1
    assert flags[0]["severity"] == "high"


def test_verification_error_status_raises_nothing(isolated_db):
    """error (e.g. no registered photo on file) is not the candidate's
    fault - should never produce a flag."""
    raised = detection_engine.evaluate_identity_check(
        1, 1, {"status": "error", "similarity": None, "message": "No registered photo on file."}
    )

    assert raised == []
    assert detection_engine.get_flags(1, 1) == []


def test_identity_streaks_tracked_independently_per_session(isolated_db, monkeypatch):
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "identity_mismatch_confirm_count": 2,
    })

    detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.2})
    detection_engine.evaluate_identity_check(2, 1, {"status": "mismatch", "similarity": 0.2})

    assert detection_engine.get_flags(1, 1) == []
    assert detection_engine.get_flags(2, 1) == []

    raised_1 = detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.2})
    assert "identity_mismatch" in raised_1
    # candidate 2's streak should be untouched by candidate 1 reaching threshold
    assert detection_engine._identity_mismatch_streaks[(2, 1)] == 1


# ---------------------------------------------------------------------------
# HTTP-level throttle test for routes/exam.py's face_check identity-check
# wiring. Confirms verify_candidate is only invoked once per throttle
# interval, not on every frame.
# ---------------------------------------------------------------------------

def test_face_check_throttles_identity_verification(http_isolated_db, monkeypatch):
    import routes.exam as exam_routes
    import modules.face_verification as face_verification

    call_count = {"n": 0}

    def fake_verify(candidate_id, frame):
        call_count["n"] += 1
        return {"status": "verified", "similarity": 0.95, "message": "Identity verified."}

    monkeypatch.setattr(face_verification, "verify_candidate", fake_verify)
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: True)
    monkeypatch.setattr(exam_routes, "IDENTITY_CHECK_INTERVAL_SECONDS", 999)
    exam_routes._last_identity_check.clear()

    client = http_isolated_db
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp1 = client.post("/api/exam/1/face_check", json={"frame": make_fake_data_url()})
    assert resp1.status_code == 200
    assert resp1.get_json()["identity_check"]["status"] == "verified"
    assert call_count["n"] == 1

    # Second frame, same session, well within the throttle window -
    # verify_candidate should NOT be called again.
    resp2 = client.post("/api/exam/1/face_check", json={"frame": make_fake_data_url()})
    assert resp2.status_code == 200
    assert "identity_check" not in resp2.get_json()
    assert call_count["n"] == 1


def test_face_check_reruns_identity_verification_after_interval(http_isolated_db, monkeypatch):
    import routes.exam as exam_routes
    import modules.face_verification as face_verification

    call_count = {"n": 0}

    def fake_verify(candidate_id, frame):
        call_count["n"] += 1
        return {"status": "verified", "similarity": 0.95, "message": "Identity verified."}

    monkeypatch.setattr(face_verification, "verify_candidate", fake_verify)
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: True)
    monkeypatch.setattr(exam_routes, "IDENTITY_CHECK_INTERVAL_SECONDS", 0.05)
    exam_routes._last_identity_check.clear()

    client = http_isolated_db
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    client.post("/api/exam/1/face_check", json={"frame": make_fake_data_url()})
    assert call_count["n"] == 1

    time.sleep(0.1)

    resp2 = client.post("/api/exam/1/face_check", json={"frame": make_fake_data_url()})
    assert resp2.get_json()["identity_check"]["status"] == "verified"
    assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# Evidence capture tests (modules/evidence.py + detection_engine wiring)
# (Milestone 5 - integrity analysis port)
#
# save_evidence_image() itself is tested directly with a real (blank,
# synthetic) frame - image encode/decode/save is fast and doesn't need
# InsightFace. The detection_engine wiring tests confirm evidence is (or
# isn't) captured at the right moments, using tmp_path so no real files
# leak outside the test's own temp directory.
# ---------------------------------------------------------------------------

def _evidence_rows(db_path, flag_type=None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM Evidence"
    params = ()
    if flag_type:
        query += " WHERE flag_type = ?"
        params = (flag_type,)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def test_save_evidence_image_writes_file_and_db_row(isolated_db, monkeypatch, tmp_path):
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", str(evidence_dir))

    filepath = evidence.save_evidence_image(1, 1, "identity_mismatch", make_fake_data_url())

    assert filepath is not None
    assert os.path.exists(filepath)
    assert "identity_mismatch" in filepath

    rows = _evidence_rows(isolated_db)
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == 1
    assert rows[0]["exam_id"] == 1
    assert rows[0]["flag_type"] == "identity_mismatch"
    assert rows[0]["filepath"] == filepath


def test_save_evidence_image_returns_none_on_bad_frame(isolated_db, monkeypatch, tmp_path):
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", str(evidence_dir))

    result = evidence.save_evidence_image(1, 1, "identity_mismatch", "not-a-valid-data-url")

    assert result is None
    assert len(_evidence_rows(isolated_db)) == 0


def test_confirmed_mismatch_saves_evidence_when_frame_provided(isolated_db, monkeypatch, tmp_path):
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", str(evidence_dir))
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "identity_mismatch_confirm_count": 2,
    })

    frame = make_fake_data_url()
    detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.2}, frame=frame)
    detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.25}, frame=frame)

    rows = _evidence_rows(isolated_db, "identity_mismatch")
    assert len(rows) == 1
    assert os.path.exists(rows[0]["filepath"])


def test_unconfirmed_mismatch_does_not_save_evidence(isolated_db, monkeypatch, tmp_path):
    """Below identity_mismatch_confirm_count, no flag is raised - evidence
    should not be saved either, since it's tied to the flag being raised."""
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", str(evidence_dir))
    monkeypatch.setattr(detection_engine, "THRESHOLDS", {
        **detection_engine.THRESHOLDS, "identity_mismatch_confirm_count": 3,
    })

    detection_engine.evaluate_identity_check(1, 1, {"status": "mismatch", "similarity": 0.2}, frame=make_fake_data_url())

    assert len(_evidence_rows(isolated_db)) == 0


def test_no_face_check_saves_evidence_immediately(isolated_db, monkeypatch, tmp_path):
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", str(evidence_dir))

    detection_engine.evaluate_identity_check(1, 1, {"status": "no_face", "similarity": None}, frame=make_fake_data_url())

    rows = _evidence_rows(isolated_db, "identity_check_no_face")
    assert len(rows) == 1


def test_multiple_faces_check_saves_evidence_immediately(isolated_db, monkeypatch, tmp_path):
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", str(evidence_dir))

    detection_engine.evaluate_identity_check(
        1, 1, {"status": "multiple_faces", "similarity": None, "message": "2 faces detected."},
        frame=make_fake_data_url(),
    )

    rows = _evidence_rows(isolated_db, "identity_check_multiple_faces")
    assert len(rows) == 1


def test_no_evidence_saved_when_frame_not_provided(isolated_db):
    """frame defaults to None (backward compatibility) - flagging still
    happens, evidence capture is simply skipped."""
    raised = detection_engine.evaluate_identity_check(1, 1, {"status": "no_face", "similarity": None})

    assert raised == ["identity_check_no_face"]
    assert len(_evidence_rows(isolated_db)) == 0


def test_verified_status_never_saves_evidence(isolated_db, monkeypatch, tmp_path):
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", str(evidence_dir))

    detection_engine.evaluate_identity_check(1, 1, {"status": "verified", "similarity": 0.9}, frame=make_fake_data_url())

    assert len(_evidence_rows(isolated_db)) == 0


def test_face_check_http_route_saves_evidence_end_to_end(http_isolated_db, monkeypatch, tmp_path):
    """Full HTTP path: face_check -> evaluate_identity_check -> evidence
    saved, using the real routes/exam.py wiring (not calling
    detection_engine directly)."""
    import routes.exam as exam_routes
    import modules.face_verification as face_verification_module

    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(evidence, "EVIDENCE_DIR", str(evidence_dir))
    monkeypatch.setattr(photo_capture, "contains_face", lambda image: True)
    monkeypatch.setattr(exam_routes, "IDENTITY_CHECK_INTERVAL_SECONDS", 999)
    exam_routes._last_identity_check.clear()

    def fake_verify(candidate_id, frame):
        return {"status": "no_face", "similarity": None, "message": "No face detected in live frame."}

    monkeypatch.setattr(face_verification_module, "verify_candidate", fake_verify)

    client = http_isolated_db
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/exam/1/face_check", json={"frame": make_fake_data_url()})

    assert resp.status_code == 200
    assert "identity_check_no_face" in resp.get_json()["flags_raised"]

    rows = _evidence_rows(tmp_path / "test_http.db", "identity_check_no_face")
    assert len(rows) == 1
    assert os.path.exists(rows[0]["filepath"])
