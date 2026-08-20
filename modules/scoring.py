"""
Integrity Scoring Module (Milestone 3 - Priyanshu's task).

Computes a per-session integrity score based on:
1. Face presence ratio (derived from FaceAbsenceEvents and Exams tables)
2. Severity-weighted suspicious event flags (from IntegrityFlags table)
3. Frequencies of specific browser events (from BrowserEvents table)

Outputs:
- face_presence_ratio: float (0.0 to 1.0)
- integrity_score: float (0.0 to 100.0)
- risk_label: str ("Low", "Medium", "High")
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"

# Configure weights and thresholds for scoring
SEVERITY_WEIGHTS = {
    "high": 30.0,
    "medium": 15.0,
    "low": 5.0
}

EVENT_PENALTIES = {
    "tab_switch": 5.0,
    "focus_loss": 2.0
}

RISK_THRESHOLDS = {
    "low_min_score": 80.0,
    "medium_min_score": 50.0
}

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_session_score(candidate_id: int, exam_id: int) -> Dict[str, Any]:
    """
    Computes the integrity score, face-presence ratio, and risk label
    for a given candidate's exam session using Pandas.
    """
    conn = get_db_connection()
    try:
        # 1. Load exam duration (in minutes, default to 60 if not found)
        exams_df = pd.read_sql_query(
            "SELECT id, duration FROM Exams WHERE id = ?",
            conn,
            params=(exam_id,)
        )
        if exams_df.empty:
            exam_duration_minutes = 60
        else:
            exam_duration_minutes = int(exams_df.iloc[0]["duration"])
        
        exam_duration_seconds = exam_duration_minutes * 60.0

        # 2. Load face absence events
        face_df = pd.read_sql_query(
            "SELECT duration_seconds FROM FaceAbsenceEvents WHERE candidate_id = ? AND exam_id = ?",
            conn,
            params=(candidate_id, exam_id)
        )
        
        if face_df.empty:
            total_absence_seconds = 0.0
        else:
            total_absence_seconds = float(face_df["duration_seconds"].sum())
        
        # Calculate face-presence ratio
        if exam_duration_seconds <= 0:
            face_presence_ratio = 1.0
        else:
            face_presence_ratio = max(0.0, min(1.0, (exam_duration_seconds - total_absence_seconds) / exam_duration_seconds))
        
        # Face absence penalty (up to 100 points)
        absence_penalty = (1.0 - face_presence_ratio) * 100.0

        # 3. Load raised integrity flags
        flags_df = pd.read_sql_query(
            "SELECT severity FROM IntegrityFlags WHERE candidate_id = ? AND exam_id = ?",
            conn,
            params=(candidate_id, exam_id)
        )
        
        if flags_df.empty:
            flags_penalty = 0.0
            total_flags = 0
        else:
            # Map severity to weights (case-insensitive mapping)
            flags_df["weight"] = flags_df["severity"].str.lower().map(SEVERITY_WEIGHTS).fillna(SEVERITY_WEIGHTS["low"])
            flags_penalty = float(flags_df["weight"].sum())
            total_flags = len(flags_df)

        # 4. Load raw browser events
        events_df = pd.read_sql_query(
            "SELECT event_type FROM BrowserEvents WHERE candidate_id = ? AND exam_id = ?",
            conn,
            params=(candidate_id, exam_id)
        )
        
        if events_df.empty:
            events_penalty = 0.0
            total_browser_events = 0
        else:
            events_df["penalty"] = events_df["event_type"].str.lower().map(EVENT_PENALTIES).fillna(0.0)
            events_penalty = float(events_df["penalty"].sum())
            total_browser_events = len(events_df)

        # 5. Compute integrity score (capped between 0.0 and 100.0)
        penalty_score = absence_penalty + flags_penalty + events_penalty
        integrity_score = max(0.0, min(100.0, 100.0 - penalty_score))

        # 6. Determine risk label
        if integrity_score >= RISK_THRESHOLDS["low_min_score"]:
            risk_label = "Low"
        elif integrity_score >= RISK_THRESHOLDS["medium_min_score"]:
            risk_label = "Medium"
        else:
            risk_label = "High"

        return {
            "candidate_id": candidate_id,
            "exam_id": exam_id,
            "integrity_score": round(integrity_score, 2),
            "face_presence_ratio": round(face_presence_ratio, 4),
            "risk_label": risk_label,
            "total_flags": total_flags,
            "total_browser_events": total_browser_events,
            "absence_penalty": round(absence_penalty, 2),
            "flags_penalty": round(flags_penalty, 2),
            "events_penalty": round(events_penalty, 2),
        }

    finally:
        conn.close()
