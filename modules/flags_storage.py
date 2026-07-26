"""
Storage module for IntegrityFlags table (Milestone 2 - Priyanshu's task).

Provides clean data-access helper functions for creating, querying, filtering,
and deleting suspicious event flags/alerts raised by the detection engine or invigilators.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_flag(
    candidate_id: int,
    exam_id: int,
    flag_type: str,
    severity: str,
    detail: str,
    threshold_breached: str,
    created_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inserts a new flag record into IntegrityFlags.
    Returns the created flag as a dictionary.
    """
    if created_at is None:
        created_at = datetime.now().isoformat()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO IntegrityFlags
                (candidate_id, exam_id, flag_type, severity, detail, threshold_breached, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (candidate_id, exam_id, flag_type, severity, detail, threshold_breached, created_at),
        )
        conn.commit()
        flag_id = cursor.lastrowid
        return get_flag_by_id(flag_id)
    finally:
        conn.close()


def get_flag_by_id(flag_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single flag record by ID, or None if not found."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM IntegrityFlags WHERE id = ?", (flag_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_flags_filtered(
    candidate_id: Optional[int] = None,
    exam_id: Optional[int] = None,
    severity: Optional[str] = None,
    flag_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Queries flags matching optional filter parameters.
    Returns list of matching flag dicts, sorted by created_at (ascending).
    """
    conn = get_db_connection()
    try:
        query = "SELECT * FROM IntegrityFlags WHERE 1=1"
        params = []

        if candidate_id is not None:
            query += " AND candidate_id = ?"
            params.append(candidate_id)
        if exam_id is not None:
            query += " AND exam_id = ?"
            params.append(exam_id)
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        if flag_type:
            query += " AND flag_type = ?"
            params.append(flag_type)

        query += " ORDER BY created_at ASC"

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_flag(flag_id: int) -> bool:
    """
    Deletes a flag record by ID.
    Returns True if deleted, False if flag was not found.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM IntegrityFlags WHERE id = ?", (flag_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_flag_summary_stats(exam_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generates summary metrics for flags/alerts across sessions (or scoped to an exam_id).
    Returns total count, breakdown by severity, and breakdown by flag_type.
    """
    conn = get_db_connection()
    try:
        base_where = " WHERE 1=1"
        params = []
        if exam_id is not None:
            base_where += " AND exam_id = ?"
            params.append(exam_id)

        # Total count
        total_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM IntegrityFlags{base_where}", params
        ).fetchone()
        total_flags = total_row["cnt"] if total_row else 0

        # Severity breakdown
        sev_rows = conn.execute(
            f"SELECT severity, COUNT(*) as cnt FROM IntegrityFlags{base_where} GROUP BY severity",
            params,
        ).fetchall()
        by_severity = {r["severity"]: r["cnt"] for r in sev_rows}

        # Flag type breakdown
        type_rows = conn.execute(
            f"SELECT flag_type, COUNT(*) as cnt FROM IntegrityFlags{base_where} GROUP BY flag_type",
            params,
        ).fetchall()
        by_type = {r["flag_type"]: r["cnt"] for r in type_rows}

        return {
            "total_flags": total_flags,
            "by_severity": by_severity,
            "by_flag_type": by_type,
        }
    finally:
        conn.close()
