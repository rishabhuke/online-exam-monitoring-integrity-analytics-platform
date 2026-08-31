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
