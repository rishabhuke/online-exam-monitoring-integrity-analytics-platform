"""
API routes for the Data Science Analytics Module (Milestone 3/4).
Owner: Rishabh

Cohort-wide data (score distribution, event heatmap, K-Means clustering)
- invigilator-only, same reasoning as routes/export.py: this is a bulk/
investigative tool across an exam's whole candidate pool, not a
candidate's own session.
"""

from flask import Blueprint, jsonify

from modules import analytics
from routes.auth import invigilator_required

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/exams", methods=["GET"])
@invigilator_required
def get_exams():
    """All exams, for populating the invigilator dashboard's exam selector."""
    result = analytics.list_exams()
    return jsonify({"status": "success", "exams": result}), 200


@analytics_bp.route("/distribution/<int:exam_id>", methods=["GET"])
@invigilator_required
def get_distribution(exam_id):
    """Integrity score distribution across the exam's cohort."""
    result = analytics.get_score_distribution(exam_id)
    return jsonify({"status": "success", **result}), 200


@analytics_bp.route("/heatmap/<int:exam_id>", methods=["GET"])
@invigilator_required
def get_heatmap(exam_id):
    """Candidate x event-type frequency matrix for the exam's cohort."""
    result = analytics.get_event_frequency_heatmap(exam_id)
    return jsonify({"status": "success", **result}), 200


@analytics_bp.route("/clusters/<int:exam_id>", methods=["GET"])
@invigilator_required
def get_clusters(exam_id):
    """K-Means cohort risk clustering for the exam."""
    result = analytics.cluster_cohort_risk(exam_id)
    return jsonify({"status": "success", **result}), 200
