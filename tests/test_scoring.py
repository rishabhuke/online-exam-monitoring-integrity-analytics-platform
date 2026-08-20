"""
Tests for the Integrity Scoring Module (Milestone 3 - Priyanshu's task).

Run with:
    python -m pytest tests/test_scoring.py -v
"""

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import modules.scoring as scoring
import modules.flags_storage as flags_storage
import modules.monitoring_storage as monitoring_storage


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    """
    Creates an isolated test database with schema applied,
    and seeds test candidate & exam records.
    """
    test_db = tmp_path / "test_scoring.db"
    monkeypatch.setattr(scoring, "DATABASE", test_db)
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    # Seed candidates & exams
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (1, 'Alice', 'alice@test.com', 'hash')"
    )
    conn.execute(
        "INSERT INTO Exams (id, title, duration) VALUES (101, 'Test Exam', 60)"
    )
    conn.commit()
    conn.close()

    return test_db


def test_calculate_score_perfect_session(isolated_db):
    """A session with zero flags/absences/events should have a score of 100 and Low risk."""
    res = scoring.calculate_session_score(1, 101)

    assert res["integrity_score"] == 100.0
    assert res["face_presence_ratio"] == 1.0
    assert res["risk_label"] == "Low"
    assert res["total_flags"] == 0
    assert res["total_browser_events"] == 0


def test_calculate_score_with_face_absence_only(isolated_db):
    """Face absence of 360 seconds in a 60-minute exam should deduct 10 points."""
    # Insert face absence event of 6 minutes (360 seconds)
    monitoring_storage.create_face_event(1, 101, "2026-01-01T00:00:00", "2026-01-01T00:06:00", 360.0)

    res = scoring.calculate_session_score(1, 101)

    assert res["face_presence_ratio"] == 0.9  # 90% presence
    assert res["absence_penalty"] == 10.0
    assert res["integrity_score"] == 90.0
    assert res["risk_label"] == "Low"  # >= 80 is Low


def test_calculate_score_with_flags_and_browser_events(isolated_db):
    """Deductions from browser events and integrity flags should be calculated correctly."""
    # 2 tab switches = 2 * 5 = 10 points
    monitoring_storage.create_browser_event(1, 101, "tab_switch")
    monitoring_storage.create_browser_event(1, 101, "tab_switch")
    # 1 focus loss = 2 points
    monitoring_storage.create_browser_event(1, 101, "focus_loss")

    # 1 medium integrity flag = 15 points
    flags_storage.create_flag(1, 101, "excessive_tab_switching", "medium", "3 tab switches", "max_tab_switches=2")

    res = scoring.calculate_session_score(1, 101)

    assert res["events_penalty"] == 12.0  # 10 + 2
    assert res["flags_penalty"] == 15.0
    assert res["integrity_score"] == 73.0  # 100 - (12 + 15)
    assert res["risk_label"] == "Medium"  # 50 <= score < 80 is Medium


def test_calculate_score_serious_infractions_high_risk(isolated_db):
    """Multiple severe flags and large face absences should result in a High risk label and capped score."""
    # Face absence of 1800 seconds (30 mins / 50% absence) = 50 points penalty
    monitoring_storage.create_face_event(1, 101, "2026-01-01T00:00:00", "2026-01-01T00:30:00", 1800.0)

    # 1 high severity flag = 30 points
    flags_storage.create_flag(1, 101, "face_absent_single_interval", "high", "detail", "thresh")
    # 2 medium flags = 30 points
    flags_storage.create_flag(1, 101, "excessive_tab_switching", "medium", "detail", "thresh")
    flags_storage.create_flag(1, 101, "excessive_tab_switching", "medium", "detail", "thresh")

    res = scoring.calculate_session_score(1, 101)

    # Penalty = 50 (absence) + 30 (high flag) + 30 (2 medium flags) = 110 points -> capped at 100 penalty
    assert res["integrity_score"] == 0.0
    assert res["risk_label"] == "High"
