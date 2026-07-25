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

Not yet wired up (blocked on other pieces):
- Tab-switch / focus-loss counts - Pavani's browser event logging table
  doesn't exist yet. evaluate_tab_switches() below is a stub that documents
  the intended check; wire it up once that table lands (see its docstring).

Thresholds are kept in one place (THRESHOLDS) so they can be tuned without
touching the evaluation logic.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"

# Configurable thresholds - tune here, not in the logic below.
THRESHOLDS = {
    "max_face_absent_seconds": 120,        # single continuous absence
    "max_cumulative_absent_seconds": 180,  # total absence across a session
    "max_tab_switches": 3,                 # not yet enforced - see evaluate_tab_switches
}


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _raise_flag(candidate_id: int, exam_id: int, flag_type: str, severity: str,
                 detail: str, threshold_breached: str) -> None:
    conn = _get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO IntegrityFlags
                (candidate_id, exam_id, flag_type, severity, detail, threshold_breached, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (candidate_id, exam_id, flag_type, severity, detail, threshold_breached,
             datetime.now().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


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
    STUB - not wired up yet.

    Pavani's browser event logging (tab-switch / focus-loss table) doesn't
    exist yet. Once it does, this should:
      1. Query the tab-switch count for this candidate/exam session from
         that table.
      2. Compare it against THRESHOLDS["max_tab_switches"].
      3. Call _raise_flag(...) the same way evaluate_face_absence() does
         above if the threshold is breached.

    Left as a no-op stub so routes/exam.py can call it unconditionally
    without erroring, and so wiring it up later is a small addition rather
    than a new integration point.
    """
    return []


def get_flags(candidate_id: int, exam_id: int) -> list:
    """Returns all flags raised for a given candidate/exam session, oldest first."""
    conn = _get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM IntegrityFlags
            WHERE candidate_id = ? AND exam_id = ?
            ORDER BY created_at
            """,
            (candidate_id, exam_id),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
