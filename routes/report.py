"""
API route for the AI Integrity Report Agent (Milestone 3/4). Owner: Rishabh

No natural existing home for this (it isn't monitoring storage, flags
storage, or exam-session logic) so it gets its own blueprint, same pattern
as routes/monitoring.py and routes/flags.py.
"""

from flask import Blueprint, jsonify, session

from modules import report_agent

report_bp = Blueprint("report", __name__, url_prefix="/api/report")


@report_bp.route("/<int:exam_id>", methods=["GET"])
def get_report(exam_id):
    """Returns the AI-generated integrity summary for the current candidate's session."""
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    result = report_agent.generate_summary(session["candidate_id"], exam_id)
    return jsonify({"status": "success", **result}), 200


@report_bp.route("/dashboard/<int:candidate_id>/<int:exam_id>", methods=["GET"])
def get_dashboard_report(candidate_id, exam_id):
    """
    Milestone 4: returns the AI-generated integrity summary for an
    ARBITRARY candidate's session, for the invigilator dashboard.

    TODO(auth): this endpoint is intentionally NOT gated by an invigilator/
    admin role, because no such role exists in the codebase yet (flagged to
    the team - candidates can currently only view their own session via
    get_report() above; there's no auth path for reviewing someone else's).
    Until that's decided and built, this endpoint is open to anyone with a
    valid candidate session, which is NOT safe for production - it exists
    now purely so dashboard work (Prashanthi/Pavani) has something to call
    while the frontend and auth model are worked out in parallel. Do not
    ship this without a real role check.
    """
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    result = report_agent.generate_summary(candidate_id, exam_id)
    return jsonify({"status": "success", **result}), 200
