"""
Photo capture, validation & face presence monitoring module.
Owner: Rishabh

Two related jobs live here, both built on the same OpenCV Haar Cascade:

1. Registration photo capture (Milestone 1) - the browser (webcam.js)
   captures an image and sends it to the backend as a base64-encoded PNG.
   This module decodes it, verifies a face is actually present (basic
   sanity check against blank/invalid captures), and saves it to disk. The
   saved file path is what gets stored in candidates.photo_path.

2. Live face presence monitoring (Milestone 2) - while an exam session is
   active, the frontend (exam_window.js) periodically captures a webcam
   frame and POSTs it to /api/exam/<exam_id>/face_check (routes/exam.py).
   process_exam_frame() below runs the same face-detection check on each
   frame and tracks continuous face-absent intervals per
   (candidate_id, exam_id) session, persisting each closed interval to the
   FaceAbsenceEvents table with start/end timestamps. This only answers
   "is a face visible right now" - no face recognition or liveness check,
   consistent with the milestone scope.

Monitoring design notes:
- Tracking state is kept in-memory, keyed by (candidate_id, exam_id). This
  assumes a single Flask process (same assumption the rest of this app
  makes via Flask's built-in `session`). If this ever needs to run across
  multiple workers/processes, this state should move into the DB or a
  shared cache (e.g. Redis) instead.
- An absence interval is only opened after ABSENCE_CONFIRM_FRAMES
  consecutive absent frames, to avoid false positives from a single
  dropped/blurry frame. Once confirmed, the interval's start time is
  back-dated to the first absent frame in that streak, so logged durations
  reflect actual absence time rather than detection-confirmation lag.
"""

import os
import base64
import uuid
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

PHOTO_DIR = os.path.join("static", "uploads", "photos")
os.makedirs(PHOTO_DIR, exist_ok=True)

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"

# OpenCV's built-in Haar Cascade for frontal face detection.
# Shared by both registration capture and live exam monitoring below.
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def decode_base64_image(data_url: str) -> np.ndarray:
    """
    Converts a base64 data URL (e.g. 'data:image/png;base64,....')
    into an OpenCV-readable image (numpy array, BGR).
    """
    header, encoded = data_url.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image


def contains_face(image: np.ndarray) -> bool:
    """
    Runs face detection on the captured image.
    Returns True if at least one face is detected, False otherwise.
    Used both as a registration-time sanity check and as the presence
    check during live exam monitoring below.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    return len(faces) > 0


def save_candidate_photo(data_url: str, candidate_email: str) -> str:
    """
    Decodes, validates, and saves the candidate's registration photo.

    Returns:
        The relative file path to store in the database.

    Raises:
        ValueError: if no face is detected in the captured image.
    """
    image = decode_base64_image(data_url)

    if image is None:
        raise ValueError("Could not decode captured image.")

    if not contains_face(image):
        raise ValueError(
            "No face detected in the captured photo. Please retake it with "
            "your face clearly visible and try again."
        )

    # Unique filename to avoid collisions between candidates
    safe_email = candidate_email.replace("@", "_at_").replace(".", "_")
    filename = f"{safe_email}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(PHOTO_DIR, filename)

    cv2.imwrite(filepath, image)

    return filepath


# ---------------------------------------------------------------------------
# Live face presence monitoring (Milestone 2)
# ---------------------------------------------------------------------------

# Number of consecutive absent frames required before an interval is
# confirmed and opened. At a ~4s frontend polling interval this is ~8s
# of sustained absence before anything is logged.
ABSENCE_CONFIRM_FRAMES = 2

_monitor_lock = threading.Lock()
_monitor_sessions = {}  # key: (candidate_id, exam_id) -> _MonitorSessionState


class _MonitorSessionState:
    """In-memory tracking state for a single candidate's exam session."""

    def __init__(self):
        self.consecutive_absent = 0
        self.first_absent_seen = None  # datetime of first absent frame in current streak
        self.absence_start = None      # datetime once the streak is confirmed, else None


def _get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _log_absence_interval(candidate_id: int, exam_id: int, start_time: datetime, end_time: datetime) -> float:
    """Persists a closed face-absence interval to FaceAbsenceEvents. Returns duration in seconds."""
    duration = (end_time - start_time).total_seconds()
    conn = _get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO FaceAbsenceEvents
                (candidate_id, exam_id, start_time, end_time, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
            """,
            (candidate_id, exam_id, start_time.isoformat(), end_time.isoformat(), duration),
        )
        conn.commit()
    finally:
        conn.close()
    return duration


def process_exam_frame(candidate_id: int, exam_id: int, data_url: str) -> dict:
    """
    Entry point called on every frame the frontend sends during an exam
    session (see routes/exam.py: face_check). Updates in-memory tracking
    state and, when a face-absence interval closes (face reappears),
    persists it to the database.

    Returns:
        {
          "face_present": bool,
          "ongoing_absence_seconds": float,   # 0 while face is present
          "interval_logged": bool,            # True if an interval just closed & was saved
          "interval_duration_seconds": float | None,
        }

    Raises:
        ValueError: if the frame could not be decoded.
    """
    image = decode_base64_image(data_url)
    if image is None:
        raise ValueError("Could not decode frame.")

    present = contains_face(image)
    now = datetime.now()
    key = (candidate_id, exam_id)

    with _monitor_lock:
        state = _monitor_sessions.setdefault(key, _MonitorSessionState())
        result = {
            "face_present": present,
            "ongoing_absence_seconds": 0.0,
            "interval_logged": False,
            "interval_duration_seconds": None,
        }

        if present:
            if state.absence_start is not None:
                duration = _log_absence_interval(candidate_id, exam_id, state.absence_start, now)
                result["interval_logged"] = True
                result["interval_duration_seconds"] = duration
            state.consecutive_absent = 0
            state.first_absent_seen = None
            state.absence_start = None
        else:
            if state.consecutive_absent == 0:
                state.first_absent_seen = now
            state.consecutive_absent += 1

            if state.consecutive_absent >= ABSENCE_CONFIRM_FRAMES and state.absence_start is None:
                state.absence_start = state.first_absent_seen

            if state.absence_start is not None:
                result["ongoing_absence_seconds"] = (now - state.absence_start).total_seconds()

        return result


def end_exam_monitoring(candidate_id: int, exam_id: int) -> None:
    """
    Call when an exam session ends (submit, timeout, or logout) to flush any
    still-open face-absence interval so it isn't lost, and clear in-memory
    tracking state for that session.
    """
    now = datetime.now()
    key = (candidate_id, exam_id)
    with _monitor_lock:
        state = _monitor_sessions.get(key)
        if state and state.absence_start is not None:
            _log_absence_interval(candidate_id, exam_id, state.absence_start, now)
        _monitor_sessions.pop(key, None)

