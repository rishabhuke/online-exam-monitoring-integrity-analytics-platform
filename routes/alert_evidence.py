from flask import Blueprint, jsonify
from modules import flags_storage, monitoring_storage

alert_evidence_bp = Blueprint(
    "alert_evidence",
    __name__,
    url_prefix="/api/alert-evidence"
)

@alert_evidence_bp.route("/flag/<int:flag_id>", methods=["GET"])
def get_alert_evidence(flag_id):
    """
    Returns an alert together with all related evidence
    for the candidate/exam session.

    Includes:
    - Flag details
    - Browser events
    - Face absence events
    - Evidence summary
    """
    flag = flags_storage.get_flag_by_id(flag_id)

    if not flag:
        return jsonify({
            "status": "error",
            "message": f"Flag with ID {flag_id} not found"
        }), 404

    candidate_id = flag["candidate_id"]
    exam_id = flag["exam_id"]

    browser_events = monitoring_storage.get_browser_events(
        candidate_id=candidate_id,
        exam_id=exam_id
    )

    face_events = monitoring_storage.get_face_events(
        candidate_id=candidate_id,
        exam_id=exam_id
    )

    return jsonify({
    "status": "success",
    "flag": flag,
    "browser_events": browser_events,
    "face_events": face_events,
    "summary": {
        "browser_event_count": len(browser_events),
        "face_event_count": len(face_events)
    }
})