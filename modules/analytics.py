"""
Data Science Analytics Module (Milestone 3/4 - Prashanthi's task, taken
over by the team since her implementation status was never confirmed).
Owner: Rishabh

Per the project brief: "score distribution, event frequency heatmaps,
K-Means clustering, cohort risk profiling" across the examination cohort.

Returns raw JSON-friendly data only - no chart image generation here.
Chart rendering happens client-side (Chart.js) in the invigilator
dashboard template, not in this API layer.

Builds on modules.scoring.calculate_session_score() (Priyanshu's M3
module) rather than re-deriving integrity scores.
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, List

from sklearn.cluster import KMeans
import numpy as np

from modules import scoring

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def list_exams() -> List[Dict[str, Any]]:
    """All exams, for populating the invigilator dashboard's exam selector."""
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT id, title, duration FROM Exams ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _get_cohort_candidate_ids(exam_id: int) -> List[int]:
    """Every candidate who has at least one browser event, face-absence
    event, or integrity flag for this exam - i.e. actually took/attempted
    it under monitoring, not just every registered candidate."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT candidate_id FROM (
                SELECT candidate_id FROM BrowserEvents WHERE exam_id = ?
                UNION
                SELECT candidate_id FROM FaceAbsenceEvents WHERE exam_id = ?
                UNION
                SELECT candidate_id FROM IntegrityFlags WHERE exam_id = ?
            )
            """,
            (exam_id, exam_id, exam_id),
        ).fetchall()
        return [r["candidate_id"] for r in rows]
    finally:
        conn.close()


def get_score_distribution(exam_id: int) -> Dict[str, Any]:
    """
    Integrity score distribution across every candidate in the cohort
    for this exam.
    """
    candidate_ids = _get_cohort_candidate_ids(exam_id)
    scores = [
        scoring.calculate_session_score(cid, exam_id)["integrity_score"]
        for cid in candidate_ids
    ]

    if not scores:
        return {
            "exam_id": exam_id,
            "cohort_size": 0,
            "scores": [],
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "histogram": {"bin_edges": [], "counts": []},
        }

    arr = np.array(scores)
    counts, bin_edges = np.histogram(arr, bins=10, range=(0.0, 100.0))

    return {
        "exam_id": exam_id,
        "cohort_size": len(scores),
        "scores": scores,
        "mean": round(float(np.mean(arr)), 2),
        "median": round(float(np.median(arr)), 2),
        "min": round(float(np.min(arr)), 2),
        "max": round(float(np.max(arr)), 2),
        "histogram": {
            "bin_edges": [round(float(e), 2) for e in bin_edges],
            "counts": [int(c) for c in counts],
        },
    }


def get_event_frequency_heatmap(exam_id: int) -> Dict[str, Any]:
    """
    Candidate x event-type frequency matrix, combining BrowserEvents
    (event_type) and IntegrityFlags (flag_type) - suitable for a heatmap
    where rows are candidates and columns are event/flag types.
    """
    candidate_ids = _get_cohort_candidate_ids(exam_id)
    conn = get_db_connection()
    try:
        event_types = set()
        per_candidate_counts: Dict[int, Dict[str, int]] = {}

        for cid in candidate_ids:
            counts: Dict[str, int] = {}

            browser_rows = conn.execute(
                "SELECT event_type, COUNT(*) as cnt FROM BrowserEvents "
                "WHERE candidate_id = ? AND exam_id = ? GROUP BY event_type",
                (cid, exam_id),
            ).fetchall()
            for r in browser_rows:
                key = r["event_type"]
                counts[key] = counts.get(key, 0) + r["cnt"]
                event_types.add(key)

            flag_rows = conn.execute(
                "SELECT flag_type, COUNT(*) as cnt FROM IntegrityFlags "
                "WHERE candidate_id = ? AND exam_id = ? GROUP BY flag_type",
                (cid, exam_id),
            ).fetchall()
            for r in flag_rows:
                key = r["flag_type"]
                counts[key] = counts.get(key, 0) + r["cnt"]
                event_types.add(key)

            per_candidate_counts[cid] = counts

        event_types_sorted = sorted(event_types)
        matrix = [
            [per_candidate_counts[cid].get(et, 0) for et in event_types_sorted]
            for cid in candidate_ids
        ]

        return {
            "exam_id": exam_id,
            "candidate_ids": candidate_ids,
            "event_types": event_types_sorted,
            "matrix": matrix,
        }
    finally:
        conn.close()


def cluster_cohort_risk(exam_id: int, n_clusters: int = 3) -> Dict[str, Any]:
    """
    K-Means clustering of candidates in this exam's cohort, using each
    candidate's scoring.calculate_session_score() output as the feature
    vector: [integrity_score, face_presence_ratio, total_flags,
    total_browser_events].

    Cluster labels are relabeled Low/Medium/High risk based on each
    cluster's mean integrity_score (lower score = higher risk), so the
    output is meaningful regardless of KMeans's arbitrary internal
    cluster numbering.

    If the cohort is smaller than n_clusters, clustering is skipped and
    every candidate is returned with cluster_risk_label "Insufficient
    Data" - KMeans cannot meaningfully cluster fewer points than clusters.
    """
    candidate_ids = _get_cohort_candidate_ids(exam_id)

    if not candidate_ids:
        return {"exam_id": exam_id, "cohort_size": 0, "assignments": []}

    score_results = [
        scoring.calculate_session_score(cid, exam_id) for cid in candidate_ids
    ]

    if len(candidate_ids) < n_clusters:
        assignments = [
            {
                "candidate_id": cid,
                "integrity_score": sr["integrity_score"],
                "risk_label": sr["risk_label"],
                "cluster_id": None,
                "cluster_risk_label": "Insufficient Data",
            }
            for cid, sr in zip(candidate_ids, score_results)
        ]
        return {"exam_id": exam_id, "cohort_size": len(candidate_ids), "assignments": assignments}

    features = np.array([
        [
            sr["integrity_score"],
            sr["face_presence_ratio"],
            sr["total_flags"],
            sr["total_browser_events"],
        ]
        for sr in score_results
    ])

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features)

    cluster_mean_scores = {}
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        cluster_mean_scores[cluster_id] = float(np.mean(features[mask, 0]))

    ranked_clusters = sorted(cluster_mean_scores, key=lambda c: cluster_mean_scores[c])
    risk_labels_by_rank = ["High", "Medium", "Low"] if n_clusters == 3 else None

    def risk_label_for_cluster(cluster_id: int) -> str:
        rank = ranked_clusters.index(cluster_id)
        if risk_labels_by_rank:
            return risk_labels_by_rank[rank]
        tertile = rank / max(1, n_clusters - 1)
        if tertile < 0.34:
            return "High"
        elif tertile < 0.67:
            return "Medium"
        return "Low"

    assignments = [
        {
            "candidate_id": cid,
            "integrity_score": sr["integrity_score"],
            "risk_label": sr["risk_label"],
            "cluster_id": int(label),
            "cluster_risk_label": risk_label_for_cluster(int(label)),
        }
        for cid, sr, label in zip(candidate_ids, score_results, labels)
    ]

    return {
        "exam_id": exam_id,
        "cohort_size": len(candidate_ids),
        "n_clusters": n_clusters,
        "cluster_mean_scores": {str(k): round(v, 2) for k, v in cluster_mean_scores.items()},
        "assignments": assignments,
    }
