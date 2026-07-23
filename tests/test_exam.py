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

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    # Seed Candidates/Exams rows for every id these tests reference, since
    # FaceAbsenceEvents has FK constraints on both (matching the rest of
    # this app's schema).
    for cid in (1, 2, 5, 9):
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
