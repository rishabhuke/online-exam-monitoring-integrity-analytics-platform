"""
API route for the AI Integrity Report Agent (Milestone 3/4). Owner: Rishabh

No natural existing home for this (it isn't monitoring storage, flags
storage, or exam-session logic) so it gets its own blueprint, same pattern
as routes/monitoring.py and routes/flags.py.
"""

from flask import Blueprint, jsonify, session

from modules import report_agent, scoring, grading
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


@report_bp.route("/exam/<int:exam_id>", methods=["GET"])
@invigilator_required
def get_exam_cohort_report(exam_id):
    """
    Milestone 5: returns an AI-generated cohort-level integrity summary
    for an entire exam - every candidate with monitoring data for this
    exam, aggregated into one summary, rather than one report per
    candidate. Cached for 30s (see modules.report_agent's cache comment).

    Gated by @invigilator_required (routes/auth.py) - only a logged-in
    invigilator can call this.
    """
    result = report_agent.generate_exam_summary(exam_id)
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


# ---------------------------------------------------------------------------
# Exam Attempt / Grading Summary API
#
# Separate concern from the Integrity Score API above - this exposes
# modules.grading.get_exam_attempt_summary() (exam correctness/completion),
# not proctoring signal. Invigilator-only: no candidate self-service route,
# since /api/results already serves that need for the candidate's own view.
# ---------------------------------------------------------------------------

attempt_bp = Blueprint("attempt", __name__, url_prefix="/api/attempt")


@attempt_bp.route("/dashboard/<int:candidate_id>/<int:exam_id>", methods=["GET"])
@invigilator_required
def get_dashboard_attempt(candidate_id, exam_id):
    """
    Returns an ARBITRARY candidate's exam attempt/grading summary, for the
    invigilator dashboard.

    Gated by @invigilator_required (routes/auth.py) - only a logged-in
    invigilator can call this, not just any candidate.
    """
    result = grading.get_exam_attempt_summary(candidate_id, exam_id)
    return jsonify({"status": "success", **result}), 200


@attempt_bp.route("/<int:exam_id>/answers", methods=["GET"])
def get_own_answer_review(exam_id):
    """
    Milestone 5 (P2): candidate self-service per-question answer review
    for the CURRENT candidate's own session.

    candidate_id always comes from session["candidate_id"], never from
    the URL - exam_id is the only URL parameter, so there is no way to
    request another candidate's answers by changing the path. Mirrors
    get_score()/get_report() above in routes/report.py, not the
    dashboard_* routes (which are invigilator-only and take an arbitrary
    candidate_id because an invigilator is allowed to see any
    candidate's data - a candidate is not).
    """
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    result = grading.get_answer_review(session["candidate_id"], exam_id)
    return jsonify({"status": "success", **result}), 200
