"""
Evidence capture module (Milestone 5 - integrity analysis port).

Saves the frame image that triggered a flag-worthy violation, so flags are
auditable/defensible after the fact rather than just a text log entry.
Scope for now: the three identity-check flags added in Milestone 5
(identity_mismatch, identity_check_no_face, identity_check_multiple_faces)
- called from modules/detection_engine.evaluate_identity_check() at the
exact moment each flag is raised. Not wired into face-absence flags yet
(separate, deliberately deferred - see project analysis doc).

Storage: image on disk under static/uploads/evidence/<flag_type>/, DB row
in Evidence with the path + metadata, so evidence is queryable (e.g. "every
mismatch photo for exam 3") rather than filesystem-listing only. Follows
the same split as Candidates.photo_path (path stored in DB, file on disk).

Reuses photo_capture.decode_base64_image() rather than duplicating base64/
OpenCV decode logic - same reuse pattern as modules/face_verification.py.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import cv2

from modules.photo_capture import decode_base64_image

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"
EVIDENCE_DIR = os.path.join("static", "uploads", "evidence")


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def save_evidence_image(candidate_id: int, exam_id: int, flag_type: str, frame_data_url: str) -> str | None:
    """
    Decodes a base64 frame and saves it as evidence for a flag-worthy
    violation, recording it in the Evidence table.

    Returns the saved filepath, or None if the frame could not be decoded
    (evidence-saving failure should not itself block or fail the flag that
    triggered it - the flag is already recorded in IntegrityFlags
    regardless of whether evidence capture succeeds).
    """
    try:
        image = decode_base64_image(frame_data_url)
    except (ValueError, Exception):
        return None
    if image is None:
        return None

    folder = os.path.join(EVIDENCE_DIR, flag_type)
    os.makedirs(folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"candidate{candidate_id}_exam{exam_id}_{timestamp}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(folder, filename)

    cv2.imwrite(filepath, image)

    conn = _get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO Evidence (candidate_id, exam_id, flag_type, filepath)
            VALUES (?, ?, ?, ?)
            """,
            (candidate_id, exam_id, flag_type, filepath),
        )
        conn.commit()
    finally:
        conn.close()

    return filepath


def get_evidence_for_exam(exam_id: int) -> list[dict]:
    """
    Returns every Evidence row for an exam, most recent first, joined with
    the candidate's name so the invigilator evidence viewer doesn't need a
    second round-trip per row.

    Used by GET /api/alert-evidence/exam/<exam_id> (routes/alert_evidence.py)
    to power the evidence-viewer dashboard page - lists all evidence for an
    exam, not scoped to one flag.
    """
    conn = _get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT Evidence.id, Evidence.candidate_id, Evidence.exam_id,
                   Evidence.flag_type, Evidence.filepath, Evidence.created_at,
                   Candidates.name AS candidate_name
            FROM Evidence
            LEFT JOIN Candidates ON Candidates.id = Evidence.candidate_id
            WHERE Evidence.exam_id = ?
            ORDER BY Evidence.created_at DESC
            """,
            (exam_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_evidence_for_session(candidate_id: int, exam_id: int, flag_type: str | None = None) -> list[dict]:
    """
    Returns Evidence rows for one candidate's session on one exam, most
    recent first. If flag_type is given, scopes to just that flag type -
    used by routes/alert_evidence.py's per-flag endpoint to show only the
    evidence relevant to the specific flag being viewed, not every
    evidence image from that candidate's whole session.
    """
    conn = _get_db_connection()
    try:
        query = "SELECT * FROM Evidence WHERE candidate_id = ? AND exam_id = ?"
        params = [candidate_id, exam_id]
        if flag_type:
            query += " AND flag_type = ?"
            params.append(flag_type)
        query += " ORDER BY created_at DESC"

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
