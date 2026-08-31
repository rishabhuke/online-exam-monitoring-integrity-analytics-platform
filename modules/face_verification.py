"""
Face identity verification module (Milestone 5 - integrity analysis port).

Complements modules/photo_capture.py's presence-only check ("is a face
visible") with an identity check ("is it the registered candidate's face").
Uses InsightFace (buffalo_l) to extract face embeddings and compares them
by cosine similarity against the candidate's registration photo.

Design notes:
- InsightFace model is loaded once at import time (same pattern as
  photo_capture.py's module-level _face_cascade), CPU-only (ctx_id=-1) -
  this app has no CUDA/GPU assumption anywhere else, so we don't add one.
- Reuses photo_capture.decode_base64_image() for live-frame decoding
  instead of duplicating base64/OpenCV decode logic.
- Stateless: unlike photo_capture's absence-interval tracking, there is no
  in-memory session state here - each call is independent. Throttling
  (how often this gets called per exam session) is the caller's
  responsibility (see routes/exam.py), not this module's.
- Returns None (not a raised exception) for "no comparison possible"
  cases (missing photo, no face found, etc.) - the caller decides whether
  that itself constitutes a flag-worthy event.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
from insightface.app import FaceAnalysis

from modules.photo_capture import decode_base64_image

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"

SIMILARITY_THRESHOLD = 0.60

# Loaded once, CPU-only - matches this project's no-GPU assumption
# elsewhere (see modules/photo_capture.py's Haar Cascade, also CPU-bound).
_face_app = FaceAnalysis(name="buffalo_l")
_face_app.prepare(ctx_id=-1)


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _get_registered_photo_path(candidate_id: int) -> Optional[str]:
    """Looks up Candidates.photo_path for a given candidate_id."""
    conn = _get_db_connection()
    try:
        row = conn.execute(
            "SELECT photo_path FROM Candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        return row["photo_path"] if row else None
    finally:
        conn.close()


def _cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    denom = np.linalg.norm(emb1) * np.linalg.norm(emb2)
    if denom == 0:
        return 0.0
    return float(np.dot(emb1, emb2) / denom)


def verify_candidate(candidate_id: int, live_frame_data_url: str) -> Dict[str, Any]:
    """
    Compares a live exam-session frame against the candidate's registered
    photo. Called from routes/exam.py's face_check, at a throttled interval
    (not every frame - InsightFace is heavier than the Haar Cascade
    presence check).

    Returns:
        {
          "status": "verified" | "mismatch" | "multiple_faces" | "no_face" | "error",
          "similarity": float | None,
          "message": str,
        }
    """
    photo_path = _get_registered_photo_path(candidate_id)
    if not photo_path:
        return {"status": "error", "similarity": None, "message": "No registered photo on file."}

    import cv2
    registered_image = cv2.imread(photo_path)
    if registered_image is None:
        return {"status": "error", "similarity": None, "message": "Registered photo could not be loaded."}

    live_image = decode_base64_image(live_frame_data_url)
    if live_image is None:
        return {"status": "error", "similarity": None, "message": "Could not decode live frame."}

    registered_faces = _face_app.get(registered_image)
    if len(registered_faces) != 1:
        return {"status": "error", "similarity": None, "message": "Registered photo does not contain exactly one face."}

    live_faces = _face_app.get(live_image)
    if len(live_faces) == 0:
        return {"status": "no_face", "similarity": None, "message": "No face detected in live frame."}
    if len(live_faces) > 1:
        return {"status": "multiple_faces", "similarity": None, "message": f"{len(live_faces)} faces detected in live frame."}

    similarity = _cosine_similarity(registered_faces[0].embedding, live_faces[0].embedding)
    verified = similarity >= SIMILARITY_THRESHOLD

    return {
        "status": "verified" if verified else "mismatch",
        "similarity": round(similarity, 4),
        "message": "Identity verified." if verified else "Identity mismatch.",
    }
