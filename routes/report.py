"""
API route for the AI Integrity Report Agent (Milestone 3). Owner: Rishabh

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
