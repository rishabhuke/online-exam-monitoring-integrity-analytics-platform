"""
AI Quiz Generator routes (Milestone 5 - P1, integrity analysis port).
Owner: Rishabh

Two-step generate -> confirm flow, invigilator-only (mirrors
routes/export.py's auth pattern):

  POST /api/quiz/generate           - AI-generates a preview, NO DB write
  POST /api/quiz/<exam_id>/confirm  - validates the (possibly edited)
                                       preview, inserts into Questions if
                                       and only if every question is valid

This split exists so an AI-authored question set is never trusted
directly into a live exam - an invigilator must review (and can edit)
the generated questions before they're persisted. See
modules/quiz_generator.py's module docstring for the no-partial-insert
guarantee.
"""

from flask import Blueprint, jsonify, request

from modules import quiz_generator
from routes.auth import invigilator_required

quiz_bp = Blueprint("quiz", __name__, url_prefix="/api/quiz")

MIN_COUNT = 1
MAX_COUNT = 20


@quiz_bp.route("/generate", methods=["POST"])
@invigilator_required
def generate():
    """
    Body: {"topic": str, "count": int}
    Returns a preview question list. Never writes to the database.
    """
    data = request.get_json(silent=True) or {}
    topic = data.get("topic")
    count = data.get("count")

    if not isinstance(topic, str) or not topic.strip():
        return jsonify({"status": "error", "message": "'topic' is required and must be a non-empty string"}), 400

    if not isinstance(count, int) or isinstance(count, bool) or not (MIN_COUNT <= count <= MAX_COUNT):
        return jsonify({
            "status": "error",
            "message": f"'count' is required and must be an integer between {MIN_COUNT} and {MAX_COUNT}",
        }), 400

    result = quiz_generator.generate_quiz_questions(topic.strip(), count)

    if result["status"] == "error":
        return jsonify(result), 502

    return jsonify(result), 200


@quiz_bp.route("/<int:exam_id>/confirm", methods=["POST"])
@invigilator_required
def confirm(exam_id):
    """
    Body: {"questions": [...]}  - the (possibly invigilator-edited)
    preview from /generate.

    Validates the entire payload before writing anything. If any question
    is invalid, the whole request is rejected (400) and NOTHING is
    inserted - no partial writes.
    """
    data = request.get_json(silent=True) or {}
    questions = data.get("questions")

    is_valid, errors = quiz_generator.validate_quiz_payload(questions)
    if not is_valid:
        return jsonify({"status": "error", "message": "Validation failed", "errors": errors}), 400

    inserted_count = quiz_generator.insert_questions(exam_id, questions)

    return jsonify({"status": "success", "exam_id": exam_id, "inserted_count": inserted_count}), 201
