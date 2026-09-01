"""
Storage module for SupportTickets table (Milestone 5 - support ticket
backend port, see docs/feature-port-analysis.md item G / routes/support.py).

Same module shape as modules/flags_storage.py: plain data-access
functions, own DB connection, own DATABASE path patchable by tests.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_ticket(
    candidate_id: int,
    issue_type: str,
    priority: str,
    message: str,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Inserts a new ticket, defaulting status to 'Open'. Returns the
    created ticket as a dict."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO SupportTickets
                (candidate_id, contact_name, contact_email, issue_type, priority, message, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Open')
            """,
            (candidate_id, contact_name, contact_email, issue_type, priority, message),
        )
        conn.commit()
        ticket_id = cursor.lastrowid
        return get_ticket_by_id(ticket_id)
    finally:
        conn.close()


def get_ticket_by_id(ticket_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single ticket by ID, or None if not found."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM SupportTickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_tickets_for_candidate(candidate_id: int) -> List[Dict[str, Any]]:
    """Every ticket a candidate has raised, most recent first. Powers the
    candidate-facing 'My Tickets' list on help_support.html."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM SupportTickets WHERE candidate_id = ? ORDER BY created_at DESC",
            (candidate_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_tickets(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every ticket across all candidates, most recent first, joined with
    candidate name - powers the invigilator support-tickets page. Optional
    status filter (Open / In Progress / Resolved)."""
    conn = get_db_connection()
    try:
        query = """
            SELECT SupportTickets.*, Candidates.name AS candidate_name
            FROM SupportTickets
            LEFT JOIN Candidates ON Candidates.id = SupportTickets.candidate_id
            WHERE 1=1
        """
        params: List[Any] = []
        if status:
            query += " AND SupportTickets.status = ?"
            params.append(status)
        query += " ORDER BY SupportTickets.created_at DESC"

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_ticket(
    ticket_id: int,
    status: Optional[str] = None,
    response: Optional[str] = None,
    responded_by: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Updates status and/or an invigilator's response on a ticket.
    Only the fields passed (non-None) are changed. Returns the updated
    ticket dict, or None if the ticket doesn't exist."""
    if get_ticket_by_id(ticket_id) is None:
        return None

    conn = get_db_connection()
    try:
        fields = []
        params: List[Any] = []

        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if response is not None:
            fields.append("response = ?")
            params.append(response)
        if responded_by is not None:
            fields.append("responded_by = ?")
            params.append(responded_by)

        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(ticket_id)

        conn.execute(
            f"UPDATE SupportTickets SET {', '.join(fields)} WHERE id = ?", params
        )
        conn.commit()
    finally:
        conn.close()

    return get_ticket_by_id(ticket_id)
