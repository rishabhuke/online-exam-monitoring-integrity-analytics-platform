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
