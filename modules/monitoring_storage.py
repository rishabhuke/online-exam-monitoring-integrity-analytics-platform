import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Face Absence Events
# -----------------------------

def create_face_event(
    candidate_id: int,
    exam_id: int,
    start_time: str,
    end_time: str,
    duration_seconds: float,
) -> Dict[str, Any]:

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO FaceAbsenceEvents
            (candidate_id, exam_id, start_time, end_time, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                exam_id,
                start_time,
                end_time,
                duration_seconds,
            ),
        )

        conn.commit()
        event_id = cursor.lastrowid

        row = conn.execute(
            "SELECT * FROM FaceAbsenceEvents WHERE id=?",
            (event_id,),
        ).fetchone()

        return dict(row)

    finally:
        conn.close()


def get_face_events(
    candidate_id: Optional[int] = None,
    exam_id: Optional[int] = None,
) -> List[Dict[str, Any]]:

    conn = get_db_connection()

    try:
        query = "SELECT * FROM FaceAbsenceEvents WHERE 1=1"
        params = []

        if candidate_id is not None:
            query += " AND candidate_id=?"
            params.append(candidate_id)

        if exam_id is not None:
            query += " AND exam_id=?"
            params.append(exam_id)

        query += " ORDER BY start_time ASC"

        rows = conn.execute(query, params).fetchall()

        return [dict(r) for r in rows]

    finally:
        conn.close()


# -----------------------------
# Browser Events
# -----------------------------

def create_browser_event(
    candidate_id: int,
    exam_id: int,
    event_type: str,
    details: str = "",
    event_timestamp: Optional[str] = None,
) -> Dict[str, Any]:

    if event_timestamp is None:
        event_timestamp = datetime.now().isoformat()

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO BrowserEvents
            (candidate_id, exam_id, event_type, event_timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                exam_id,
                event_type,
                event_timestamp,
                details,
            ),
        )

        conn.commit()

        event_id = cursor.lastrowid

        row = conn.execute(
            "SELECT * FROM BrowserEvents WHERE id=?",
            (event_id,),
        ).fetchone()

        return dict(row)

    finally:
        conn.close()


def get_browser_events(
    candidate_id: Optional[int] = None,
    exam_id: Optional[int] = None,
) -> List[Dict[str, Any]]:

    conn = get_db_connection()

    try:

        query = "SELECT * FROM BrowserEvents WHERE 1=1"
        params = []

        if candidate_id is not None:
            query += " AND candidate_id=?"
            params.append(candidate_id)

        if exam_id is not None:
            query += " AND exam_id=?"
            params.append(exam_id)

        query += " ORDER BY event_timestamp ASC"

        rows = conn.execute(query, params).fetchall()

        return [dict(r) for r in rows]

    finally:
        conn.close()