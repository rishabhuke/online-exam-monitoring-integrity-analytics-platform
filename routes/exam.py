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

import threading
from datetime import datetime

from flask import Blueprint, request, jsonify, session

from modules import photo_capture, detection_engine, face_verification

exam_bp = Blueprint("exam", __name__, url_prefix="/api/exam")

# Identity verification runs on a throttle - InsightFace is heavier than
# the Haar Cascade presence check in photo_capture.py, and doesn't need to
# run on every ~4s frame like presence does. State kept local to this
# module, separate from photo_capture's absence tracker (different concern).
IDENTITY_CHECK_INTERVAL_SECONDS = 15
_identity_check_lock = threading.Lock()
_last_identity_check = {}  # key: (candidate_id, exam_id) -> datetime of last check


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

    identity_result = None
    key = (candidate_id, exam_id)
    now = datetime.now()
    with _identity_check_lock:
        last_check = _last_identity_check.get(key)
        should_check = (
            last_check is None
            or (now - last_check).total_seconds() >= IDENTITY_CHECK_INTERVAL_SECONDS
        )
        if should_check:
            _last_identity_check[key] = now

    if should_check:
        identity_result = face_verification.verify_candidate(candidate_id, frame)
        identity_flags = detection_engine.evaluate_identity_check(candidate_id, exam_id, identity_result, frame=frame)
        flags_raised.extend(identity_flags)

    response = {"status": "success", "flags_raised": flags_raised, **result}
    if identity_result is not None:
        response["identity_check"] = identity_result

    return jsonify(response), 200


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
