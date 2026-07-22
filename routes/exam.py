"""
Exam session routes - face presence monitoring endpoints (Milestone 2).
Owner: Rishabh

Question/answer routes (get_exam, submit_exam) stay in app.py for now, where
they already live. This blueprint is scoped to the face-monitoring pipeline
added in Milestone 2: the frontend (exam_window.js) posts a webcam frame
periodically while an exam is in progress, this receives it, runs it
through modules/photo_capture.py (process_exam_frame), and reports back
whether the face-absence tracking state changed.
"""

from flask import Blueprint, request, jsonify, session

from modules import photo_capture

exam_bp = Blueprint("exam", __name__, url_prefix="/api/exam")


@exam_bp.route("/<int:exam_id>/face_check", methods=["POST"])
def face_check(exam_id):
    """
    Called periodically (every ~4s, see exam_window.js) by the exam window
    frontend while a session is active.

    Expects JSON: {"frame": "data:image/png;base64,...."}
    """
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    frame = data.get("frame")
    if not frame:
        return jsonify({"status": "error", "message": "No frame provided"}), 400

    try:
        result = photo_capture.process_exam_frame(session["candidate_id"], exam_id, frame)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Face check failed: {str(e)}"}), 500

    return jsonify({"status": "success", **result}), 200


@exam_bp.route("/<int:exam_id>/end_monitoring", methods=["POST"])
def end_monitoring(exam_id):
    """
    Call when the exam session ends (submit, timeout, or logout) to flush
    any still-open face-absence interval so it doesn't get lost. The
    frontend also fires this via sendBeacon on page unload as a safety net.
    """
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    photo_capture.end_exam_monitoring(session["candidate_id"], exam_id)
    return jsonify({"status": "success", "message": "Monitoring session closed"}), 200
