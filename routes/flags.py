"""
API routes for integrity flags/alerts management (Milestone 2 - Priyanshu's task).

Provides HTTP endpoints to ingest, retrieve, filter, summarize, and manage
suspicious event flags raised during online exam monitoring sessions.
"""

from flask import Blueprint, request, jsonify, session
from modules import flags_storage

flags_bp = Blueprint("flags", __name__, url_prefix="/api/flags")


@flags_bp.route("", methods=["GET"])
def list_flags():
    """
    GET /api/flags
    Query parameters (all optional):
      - candidate_id (int)
      - exam_id (int)
      - severity (str: high, medium, low)
      - flag_type (str: face_absent_single_interval, face_absent_cumulative, etc.)
    """
    candidate_id = request.args.get("candidate_id", type=int)
    exam_id = request.args.get("exam_id", type=int)
    severity = request.args.get("severity", type=str)
    flag_type = request.args.get("flag_type", type=str)

    flags = flags_storage.get_flags_filtered(
        candidate_id=candidate_id,
        exam_id=exam_id,
        severity=severity,
        flag_type=flag_type,
    )
    return jsonify({"status": "success", "count": len(flags), "flags": flags}), 200


@flags_bp.route("/<int:flag_id>", methods=["GET"])
def get_flag(flag_id: int):
    """
    GET /api/flags/<flag_id>
    Retrieves detailed record of a specific integrity flag.
    """
    flag = flags_storage.get_flag_by_id(flag_id)
    if not flag:
        return jsonify({"status": "error", "message": f"Flag with ID {flag_id} not found"}), 404

    return jsonify({"status": "success", "flag": flag}), 200


@flags_bp.route("", methods=["POST"])
def create_flag():
    """
    POST /api/flags
    Expects JSON body:
      - candidate_id (int, required)
      - exam_id (int, required)
      - flag_type (str, required)
      - severity (str, required)
      - detail (str, optional)
      - threshold_breached (str, optional)
      - created_at (str, optional ISO timestamp)
    """
    data = request.get_json(silent=True) or {}

    missing_fields = [f for f in ["candidate_id", "exam_id", "flag_type", "severity"] if f not in data]
    if missing_fields:
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    try:
        candidate_id = int(data["candidate_id"])
        exam_id = int(data["exam_id"])
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "candidate_id and exam_id must be integers"}), 400

    flag_type = str(data["flag_type"]).strip()
    severity = str(data["severity"]).strip()
    detail = str(data.get("detail", "")).strip()
    threshold_breached = str(data.get("threshold_breached", "")).strip()
    created_at = data.get("created_at")

    if not flag_type or not severity:
        return jsonify({"status": "error", "message": "flag_type and severity cannot be empty"}), 400

    flag = flags_storage.create_flag(
        candidate_id=candidate_id,
        exam_id=exam_id,
        flag_type=flag_type,
        severity=severity,
        detail=detail,
        threshold_breached=threshold_breached,
        created_at=created_at,
    )

    return jsonify({"status": "success", "message": "Flag created successfully", "flag": flag}), 201


@flags_bp.route("/<int:flag_id>", methods=["DELETE"])
def delete_flag(flag_id: int):
    """
    DELETE /api/flags/<flag_id>
    Dismisses/deletes an integrity flag record by ID.
    """
    deleted = flags_storage.delete_flag(flag_id)
    if not deleted:
        return jsonify({"status": "error", "message": f"Flag with ID {flag_id} not found"}), 404

    return jsonify({"status": "success", "message": f"Flag {flag_id} deleted successfully"}), 200


@flags_bp.route("/summary", methods=["GET"])
def get_flag_summary():
    """
    GET /api/flags/summary
    Query parameter (optional):
      - exam_id (int)
    Returns breakdown of total flags, by severity, and by flag_type.
    """
    exam_id = request.args.get("exam_id", type=int)
    stats = flags_storage.get_flag_summary_stats(exam_id=exam_id)
    return jsonify({"status": "success", "summary": stats}), 200
