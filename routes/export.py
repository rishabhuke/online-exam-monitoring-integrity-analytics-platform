"""
Reporting & Export Module (Milestone 4). Owner: Rishabh

Per the project brief: "Generate structured JSON/CSV exports of session
logs, integrity scores, event summaries, cluster assignments, and
AI-generated reports."

Invigilator-only (bulk/investigative tool, not a candidate self-service
feature - matches how the brief groups this with the dashboard, not with
the per-candidate report/score endpoints).

NOTE: "cluster_assignments" is included as null/omitted pending the Data
Science Analytics module (K-Means clustering) - not yet implemented
anywhere in the codebase as of this module's authoring. Wire it in here
once that module lands.
"""

import csv
import io

from flask import Blueprint, jsonify, request, Response

from modules import scoring, monitoring_storage, flags_storage, report_agent
from routes.auth import invigilator_required

export_bp = Blueprint("export", __name__, url_prefix="/api/export")


def _build_export_payload(candidate_id: int, exam_id: int) -> dict:
    """Composes the full export payload from existing modules - no new
    querying logic, purely a merge of already-implemented data sources."""
    score = scoring.calculate_session_score(candidate_id, exam_id)
    face_events = monitoring_storage.get_face_events(candidate_id, exam_id)
    browser_events = monitoring_storage.get_browser_events(candidate_id, exam_id)
    flags = flags_storage.get_flags_filtered(candidate_id=candidate_id, exam_id=exam_id)
    report = report_agent.generate_summary(candidate_id, exam_id)

    return {
        "candidate_id": candidate_id,
        "exam_id": exam_id,
        "integrity_score": score,
        "face_absence_events": face_events,
        "browser_events": browser_events,
        "flags": flags,
        "ai_summary": {
            "summary": report["summary"],
            "risk_label": report["risk_label"],
            "source": report["source"],
        },
        "cluster_assignment": None,  # TODO: wire in once DS Analytics module (K-Means) lands
    }


def _rows_to_csv_section(writer: "csv.writer", title: str, rows: list) -> None:
    """Writes one labeled section of a multi-section CSV: a '# TITLE'
    marker line, a header row from the first row's keys, then data rows.
    Empty sections still get their title + a note, so the file's shape
    is predictable regardless of data."""
    writer.writerow([f"# {title}"])
    if not rows:
        writer.writerow(["(no data)"])
        writer.writerow([])
        return
    headers = list(rows[0].keys())
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    writer.writerow([])


def _build_export_csv(payload: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["# SESSION"])
    writer.writerow(["candidate_id", "exam_id"])
    writer.writerow([payload["candidate_id"], payload["exam_id"]])
    writer.writerow([])

    _rows_to_csv_section(writer, "INTEGRITY_SCORE", [payload["integrity_score"]])
    _rows_to_csv_section(writer, "FACE_ABSENCE_EVENTS", payload["face_absence_events"])
    _rows_to_csv_section(writer, "BROWSER_EVENTS", payload["browser_events"])
    _rows_to_csv_section(writer, "FLAGS", payload["flags"])
    _rows_to_csv_section(writer, "AI_SUMMARY", [payload["ai_summary"]])

    writer.writerow(["# CLUSTER_ASSIGNMENT"])
    writer.writerow(["(pending Data Science Analytics module)"])

    return output.getvalue()


@export_bp.route("/<int:candidate_id>/<int:exam_id>", methods=["GET"])
@invigilator_required
def export_session(candidate_id, exam_id):
    """
    Exports a full session report for an arbitrary candidate's exam.

    Query param: ?format=json (default) or ?format=csv
    """
    fmt = request.args.get("format", "json").strip().lower()

    if fmt not in ("json", "csv"):
        return jsonify({"status": "error", "message": "format must be 'json' or 'csv'"}), 400

    payload = _build_export_payload(candidate_id, exam_id)

    if fmt == "json":
        return jsonify({"status": "success", **payload}), 200

    csv_body = _build_export_csv(payload)
    filename = f"session_export_candidate{candidate_id}_exam{exam_id}.csv"
    return Response(
        csv_body,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
