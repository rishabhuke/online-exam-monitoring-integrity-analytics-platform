"""
Rule-based suspicious event detection engine (Milestone 2).
Originally assigned to: Anuradha (no longer on the project - built by Rishabh
as a stand-in, same situation as modules/faker_generator.py).

Consumes events raised elsewhere in the pipeline and evaluates them against
configurable thresholds, raising a "flag" in the IntegrityFlags table when a
threshold is breached.

Currently wired up:
- Face absence (from modules/photo_capture.py's FaceAbsenceEvents): flags a
  single continuous absence interval that exceeds max_face_absent_seconds,
  and separately flags when *cumulative* absence across a session crosses
  max_cumulative_absent_seconds.

Tab-switch / focus-loss counts - now wired up against Pavani/Priyanshu's
BrowserEvents table via modules/monitoring_storage.py. evaluate_tab_switches()
counts "tab_switch" events logged for the session and compares against
THRESHOLDS["max_tab_switches"]. Note the frontend capture that actually
populates BrowserEvents (visibilitychange/blur listeners) is still Pavani's
in-progress carryover task, so in practice this will raise zero flags until
that lands - but the check itself is live and tested.

IntegrityFlags reads/writes go through modules/flags_storage.py (Priyanshu's
Milestone 2 task) rather than touching the table directly, so there's a
single source of truth for flag storage instead of two modules writing to
the same table independently.

Thresholds are kept in one place (THRESHOLDS) so they can be tuned without
touching the evaluation logic.
"""

import sqlite3
from pathlib import Path

from modules import flags_storage, monitoring_storage

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"

# Configurable thresholds - tune here, not in the logic below.
THRESHOLDS = {
    "max_face_absent_seconds": 120,        # single continuous absence
    "max_cumulative_absent_seconds": 180,  # total absence across a session
    "max_tab_switches": 3,
    "max_focus_loss_count": 5,
}


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _raise_flag(candidate_id: int, exam_id: int, flag_type: str, severity: str,
                 detail: str, threshold_breached: str) -> None:
    """Delegates to flags_storage.create_flag() - see module docstring."""
    flags_storage.create_flag(
        candidate_id=candidate_id,
        exam_id=exam_id,
        flag_type=flag_type,
        severity=severity,
        detail=detail,
        threshold_breached=threshold_breached,
    )


def evaluate_face_absence(candidate_id: int, exam_id: int, interval_duration_seconds: float) -> list:
    """
    Call this whenever a face-absence interval closes (i.e. whenever
    photo_capture.process_exam_frame() returns interval_logged=True — see
    the call site in routes/exam.py). Checks the interval that just closed
    against the single-interval threshold, and separately checks the
    candidate's cumulative absence time for this exam against the
    cumulative threshold.

    Returns a list of flag_type strings that were raised (empty if none).
    """
    raised = []

    if interval_duration_seconds >= THRESHOLDS["max_face_absent_seconds"]:
        _raise_flag(
            candidate_id, exam_id,
            flag_type="face_absent_single_interval",
            severity="high",
            detail=f"Face absent for {interval_duration_seconds:.0f}s in one continuous interval",
            threshold_breached=f"max_face_absent_seconds={THRESHOLDS['max_face_absent_seconds']}",
        )
        raised.append("face_absent_single_interval")

    conn = _get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(duration_seconds), 0) AS total
            FROM FaceAbsenceEvents WHERE candidate_id = ? AND exam_id = ?
            """,
            (candidate_id, exam_id),
        ).fetchone()
        cumulative = row["total"] if row else 0
    finally:
        conn.close()

    if cumulative >= THRESHOLDS["max_cumulative_absent_seconds"]:
        _raise_flag(
            candidate_id, exam_id,
            flag_type="face_absent_cumulative",
            severity="high",
            detail=f"Cumulative face-absent time is {cumulative:.0f}s across this session",
            threshold_breached=f"max_cumulative_absent_seconds={THRESHOLDS['max_cumulative_absent_seconds']}",
        )
        raised.append("face_absent_cumulative")

    return raised


def evaluate_tab_switches(candidate_id: int, exam_id: int) -> list:
    """
    Counts "tab_switch" events logged in BrowserEvents for this session
    (via monitoring_storage) and flags when THRESHOLDS["max_tab_switches"]
    is breached. Safe to call repeatedly - callers should call it once per
    new tab-switch event so it only re-raises when the count first crosses
    the threshold (see routes/monitoring.py call site).

    Returns a list of flag_type strings that were raised (empty if none).
    """
    events = monitoring_storage.get_browser_events(candidate_id=candidate_id, exam_id=exam_id)
    tab_switch_count = sum(1 for e in events if e.get("event_type") == "tab_switch")

    if tab_switch_count == THRESHOLDS["max_tab_switches"]:
        _raise_flag(
            candidate_id, exam_id,
            flag_type="excessive_tab_switching",
            severity="medium",
            detail=f"{tab_switch_count} tab switches recorded this session",
            threshold_breached=f"max_tab_switches={THRESHOLDS['max_tab_switches']}",
        )
        return ["excessive_tab_switching"]

    return []


def evaluate_focus_loss(candidate_id: int, exam_id: int) -> list:
    """
    Counts "focus_loss" events logged in BrowserEvents for this session
    (via monitoring_storage) and flags when THRESHOLDS["max_focus_loss_count"]
    is breached. Mirrors evaluate_tab_switches()'s pattern - safe to call
    repeatedly, only re-raises when the count first crosses the threshold.

    Counts case-insensitively since the frontend (exam_window.js) currently
    sends "FOCUS_LOSS" (uppercase) - this does not depend on event_type
    being normalized to lowercase before storage (see fix/browser-event-
    type-casing, a separate PR).

    Returns a list of flag_type strings that were raised (empty if none).
    """
    events = monitoring_storage.get_browser_events(candidate_id=candidate_id, exam_id=exam_id)
    focus_loss_count = sum(
        1 for e in events if str(e.get("event_type", "")).strip().lower() == "focus_loss"
    )

    if focus_loss_count == THRESHOLDS["max_focus_loss_count"]:
        _raise_flag(
            candidate_id, exam_id,
            flag_type="excessive_focus_loss",
            severity="low",
            detail=f"{focus_loss_count} focus-loss events recorded this session",
            threshold_breached=f"max_focus_loss_count={THRESHOLDS['max_focus_loss_count']}",
        )
        return ["excessive_focus_loss"]

    return []


def get_flags(candidate_id: int, exam_id: int) -> list:
    """Returns all flags raised for a given candidate/exam session, oldest first."""
    return flags_storage.get_flags_filtered(candidate_id=candidate_id, exam_id=exam_id)
