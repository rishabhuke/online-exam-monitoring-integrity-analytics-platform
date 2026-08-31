from flask import Blueprint, jsonify
from modules import flags_storage, monitoring_storage, evidence
from routes.auth import invigilator_required

alert_evidence_bp = Blueprint(
    "alert_evidence",
    __name__,
    url_prefix="/api/alert-evidence"
)

@alert_evidence_bp.route("/flag/<int:flag_id>", methods=["GET"])
@invigilator_required
def get_alert_evidence(flag_id):
    """
    Returns an alert together with all related evidence
    for the candidate/exam session.

    Includes:
    - Flag details
    - Browser events
    - Face absence events
    - Evidence summary

    Gated by @invigilator_required (routes/auth.py, Milestone 4) - this
    endpoint previously had NO auth check at all, meaning anyone (no login
    of any kind) could pull any candidate's flag + evidence data.
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

    evidence_images = evidence.get_evidence_for_session(
        candidate_id=candidate_id, exam_id=exam_id, flag_type=flag["flag_type"]
    )

    return jsonify({
    "status": "success",
    "flag": flag,
    "browser_events": browser_events,
    "face_events": face_events,
    "evidence": evidence_images,
    "summary": {
        "browser_event_count": len(browser_events),
        "face_event_count": len(face_events),
        "evidence_count": len(evidence_images)
    }
})


@alert_evidence_bp.route("/exam/<int:exam_id>", methods=["GET"])
@invigilator_required
def get_exam_evidence(exam_id):
    """
    Returns every evidence image recorded for an exam, most recent first -
    powers the invigilator evidence-viewer dashboard page (as opposed to
    get_alert_evidence() above, which is scoped to one flag).
    """
    evidence_list = evidence.get_evidence_for_exam(exam_id)
    return jsonify({
        "status": "success",
        "exam_id": exam_id,
        "evidence": evidence_list,
        "count": len(evidence_list),
    }), 200