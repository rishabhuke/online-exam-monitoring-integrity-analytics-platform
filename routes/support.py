"""
API routes for candidate support tickets (Milestone 5 - support ticket
backend port).

Backs the "Report an Issue" form on help_support.html, which previously
just showed alert() and never persisted anything. Ported capability from
Prashanthi's branch's SupportTickets/admin workflow, rewritten against
this project's actual auth model: candidates create and view only their
own tickets (session["candidate_id"]), invigilators view and respond to
every ticket (session["invigilator_id"], @invigilator_required -
routes/auth.py). Same dual-role auth split already used by
routes/flags.py::get_flag(). No Admins/AdminInviteIDs migration - that
auth model was explicitly not ported, see docs/feature-port-analysis.md's
DON'T PORT list.
"""

from flask import Blueprint, request, jsonify, session
from modules import support_storage
from routes.auth import invigilator_required

support_bp = Blueprint("support", __name__, url_prefix="/api/support")

ALLOWED_STATUSES = {"Open", "In Progress", "Resolved"}


@support_bp.route("", methods=["POST"])
def create_ticket():
    """
    POST /api/support
    Candidate-only. Expects JSON body:
      - issue_type (str, required)
      - priority (str, required)
      - message (str, required)
      - contact_name (str, optional)
      - contact_email (str, optional)
    """
    if "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}

    issue_type = str(data.get("issue_type", "")).strip()
    priority = str(data.get("priority", "")).strip()
    message = str(data.get("message", "")).strip()
    contact_name = str(data.get("contact_name", "")).strip() or None
    contact_email = str(data.get("contact_email", "")).strip() or None

    if not issue_type or not priority or not message:
        return jsonify({
            "status": "error",
            "message": "issue_type, priority, and message are required"
        }), 400

    ticket = support_storage.create_ticket(
        candidate_id=session["candidate_id"],
        issue_type=issue_type,
        priority=priority,
        message=message,
        contact_name=contact_name,
        contact_email=contact_email,
    )
    return jsonify({"status": "success", "ticket": ticket}), 201


@support_bp.route("", methods=["GET"])
def list_tickets():
    """
    GET /api/support
    Candidate session: returns only their own tickets.
    Invigilator session: returns every ticket (optional ?status= filter),
    joined with candidate name - same dual-role split as
    routes/flags.py::get_flag().
    """
    if "invigilator_id" in session:
        status = request.args.get("status", type=str)
        tickets = support_storage.get_all_tickets(status=status)
        return jsonify({"status": "success", "count": len(tickets), "tickets": tickets}), 200

    if "candidate_id" in session:
        tickets = support_storage.get_tickets_for_candidate(session["candidate_id"])
        return jsonify({"status": "success", "count": len(tickets), "tickets": tickets}), 200

    return jsonify({"status": "error", "message": "Not authenticated"}), 401


@support_bp.route("/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """
    GET /api/support/<ticket_id>
    Candidate can view their own ticket only; invigilator can view any.
    Auth is checked before the DB lookup (same order as
    routes/flags.py::get_flag()) so an unauthenticated caller can't use
    the 404/200 split to probe which ticket IDs exist.
    """
    if "invigilator_id" not in session and "candidate_id" not in session:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401

    ticket = support_storage.get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"status": "error", "message": f"Ticket {ticket_id} not found"}), 404

    if "invigilator_id" in session or session.get("candidate_id") == ticket["candidate_id"]:
        return jsonify({"status": "success", "ticket": ticket}), 200

    return jsonify({"status": "error", "message": "Not authorized to view this ticket"}), 403


@support_bp.route("/<int:ticket_id>", methods=["PATCH"])
@invigilator_required
def respond_to_ticket(ticket_id):
    """
    PATCH /api/support/<ticket_id>
    Invigilator-only. Expects JSON body (at least one of):
      - status (str, one of Open / In Progress / Resolved)
      - response (str)
    """
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    response_text = data.get("response")

    if status is None and response_text is None:
        return jsonify({
            "status": "error",
            "message": "Provide at least one of status or response"
        }), 400

    if status is not None and status not in ALLOWED_STATUSES:
        return jsonify({
            "status": "error",
            "message": f"status must be one of {sorted(ALLOWED_STATUSES)}"
        }), 400

    ticket = support_storage.update_ticket(
        ticket_id,
        status=status,
        response=response_text,
        responded_by=session["invigilator_id"],
    )
    if not ticket:
        return jsonify({"status": "error", "message": f"Ticket {ticket_id} not found"}), 404

    return jsonify({"status": "success", "ticket": ticket}), 200
