"""
Exam session routes - face presence monitoring + detection engine endpoints
(Milestone 2). Owner: Rishabh

Question/answer routes (get_exam, submit_exam) stay in app.py for now, where
they already live. This blueprint is scoped to the Milestone 2 monitoring
pipeline:

  frontend (exam_window.js) --frame--> face_check --> photo_capture.process_exam_frame
                                                    --> (on closed interval) detection_engine.evaluate_face_absence
                                                    --> IntegrityFlags table

/flags lets anything (a future dashboard, this team's own testing) read
back what's been raised for a session.
"""

from flask import Blueprint, request, jsonify, session

from modules import photo_capture, detection_engine

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

    candidate_id = session["candidate_id"]

    try:
        result = photo_capture.process_exam_frame(candidate_id, exam_id, frame)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Face check failed: {str(e)}"}), 500

    flags_raised = []
    if result["interval_logged"]:
        flags_raised = detection_engine.evaluate_face_absence(
            candidate_id, exam_id, result["interval_duration_seconds"]
        )

    return jsonify({"status": "success", "flags_raised": flags_raised, **result}), 200


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


@exam_bp.route("/<int:exam_id>/flags", methods=["GET"])
def flags(exam_id):
    """Returns all suspicious-event flags raised for the current candidate's session."""
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    result = detection_engine.get_flags(session["candidate_id"], exam_id)
    return jsonify({"status": "success", "flags": result}), 200
