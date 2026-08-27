from flask import Blueprint, request, jsonify, session
from modules import monitoring_storage, detection_engine

monitoring_bp = Blueprint(
    "monitoring",
    __name__,
    url_prefix="/api/monitoring"
)

monitoring_bp = Blueprint(
    "monitoring",
    __name__,
    url_prefix="/api/monitoring"
)


@monitoring_bp.route("/face-event", methods=["POST"])
def create_face_event():
    data = request.get_json(silent=True) or {}
    required = [
        "candidate_id",
        "exam_id",
        "start_time",
        "end_time",
        "duration_seconds",
    ]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({
            "status": "error",
            "message": f"Missing fields: {', '.join(missing)}"
        }), 400

    event = monitoring_storage.create_face_event(
        candidate_id=int(data["candidate_id"]),
        exam_id=int(data["exam_id"]),
        start_time=data["start_time"],
        end_time=data["end_time"],
        duration_seconds=float(data["duration_seconds"])
    )

    return jsonify({
        "status": "success",
        "event": event
    }), 201


@monitoring_bp.route("/browser-event", methods=["POST"])
def create_browser_event():
    data = request.get_json(silent=True) or {}
    required = [
        "exam_id",
        "event_type"
    ]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({
            "status": "error",
            "message": f"Missing fields: {', '.join(missing)}"
        }), 400

    candidate_id = int(session["candidate_id"])
    exam_id = int(data["exam_id"])
    event_type_normalized = str(data["event_type"]).strip().lower()

    event = monitoring_storage.create_browser_event(
        candidate_id=candidate_id,
        exam_id=exam_id,
        event_type=event_type_normalized,
        details=data.get("details", ""),
        event_timestamp=data.get("event_timestamp")
    )

    flags_raised = []
    if event_type_normalized == "tab_switch":
        flags_raised = detection_engine.evaluate_tab_switches(candidate_id, exam_id)

    return jsonify({
        "status": "success",
        "event": event,
        "flags_raised": flags_raised
    }), 201


@monitoring_bp.route("/face-events", methods=["GET"])
def get_face_events():
    candidate_id = request.args.get("candidate_id", type=int)
    exam_id = request.args.get("exam_id", type=int)
    events = monitoring_storage.get_face_events(
        candidate_id=candidate_id,
        exam_id=exam_id
    )
    return jsonify({
        "status": "success",
        "count": len(events),
        "events": events
    })


@monitoring_bp.route("/browser-events", methods=["GET"])
def get_browser_events():
    candidate_id = request.args.get("candidate_id", type=int)
    exam_id = request.args.get("exam_id", type=int)
    events = monitoring_storage.get_browser_events(
        candidate_id=candidate_id,
        exam_id=exam_id
    )
    return jsonify({
        "status": "success",
        "count": len(events),
        "events": events
    })