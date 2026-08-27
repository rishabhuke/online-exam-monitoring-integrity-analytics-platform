"""
API route for the AI Integrity Report Agent (Milestone 3/4). Owner: Rishabh

No natural existing home for this (it isn't monitoring storage, flags
storage, or exam-session logic) so it gets its own blueprint, same pattern
as routes/monitoring.py and routes/flags.py.
"""

from flask import Blueprint, jsonify, session

from modules import report_agent, scoring
from routes.auth import invigilator_required

report_bp = Blueprint("report", __name__, url_prefix="/api/report")


@report_bp.route("/<int:exam_id>", methods=["GET"])
def get_report(exam_id):
    """Returns the AI-generated integrity summary for the current candidate's session."""
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    result = report_agent.generate_summary(session["candidate_id"], exam_id)
    return jsonify({"status": "success", **result}), 200


@report_bp.route("/dashboard/<int:candidate_id>/<int:exam_id>", methods=["GET"])
@invigilator_required
def get_dashboard_report(candidate_id, exam_id):
    """
    Milestone 4: returns the AI-generated integrity summary for an
    ARBITRARY candidate's session, for the invigilator dashboard.

    Gated by @invigilator_required (routes/auth.py) - only a logged-in
    invigilator can call this, not just any candidate.
    """
    result = report_agent.generate_summary(candidate_id, exam_id)
    return jsonify({"status": "success", **result}), 200


# ---------------------------------------------------------------------------
# Integrity Score API (Milestone 4). Owner: Rishabh
#
# Exposes Priyanshu's modules.scoring.calculate_session_score() directly,
# full breakdown (integrity_score, face_presence_ratio, risk_label, flag/
# event counts, per-category penalties) rather than the partial subset
# report_agent.py folds into its AI summary.
# ---------------------------------------------------------------------------

score_bp = Blueprint("score", __name__, url_prefix="/api/score")


@score_bp.route("/<int:exam_id>", methods=["GET"])
def get_score(exam_id):
    """Returns the current candidate's own integrity score breakdown."""
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    result = scoring.calculate_session_score(session["candidate_id"], exam_id)
    return jsonify({"status": "success", **result}), 200


@score_bp.route("/dashboard/<int:candidate_id>/<int:exam_id>", methods=["GET"])
@invigilator_required
def get_dashboard_score(candidate_id, exam_id):
    """
    Milestone 4: returns the full integrity score breakdown for an
    ARBITRARY candidate's session, for the invigilator dashboard.

    Gated by @invigilator_required (routes/auth.py) - only a logged-in
    invigilator can call this, not just any candidate.
    """
    result = scoring.calculate_session_score(candidate_id, exam_id)
    return jsonify({"status": "success", **result}), 200
