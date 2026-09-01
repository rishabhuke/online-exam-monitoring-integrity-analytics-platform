"""
Frontend page routes.
Owner: Prashanthi

All template-rendering pages live here as a Blueprint, so app.py stays thin
and multiple people can add routes without editing the same file.

Note: /login and /register are handled by auth_bp (routes/auth.py) since
those need to process form submissions. This file only renders GET-only
pages that don't touch the database directly.
"""

from flask import Blueprint, render_template, session, redirect, url_for, request

from routes.auth import invigilator_required, get_db_connection

pages_bp = Blueprint("pages", __name__)


def _get_exam_meta(exam_id):
    """Real exam title/duration for the exam header - falls back to
    generic copy (not fake data) if the exam row can't be found, so a
    bad/removed exam_id still renders instead of 500ing.

    Uses routes.auth.get_db_connection() (rather than a separate DATABASE
    constant here) so it honors the same DB path tests/other code already
    patch via routes.auth.DATABASE.
    """
    conn = get_db_connection()
    row = conn.execute(
        "SELECT title, duration FROM Exams WHERE id = ?", (exam_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return {"title": "Exam", "duration": 60}
    return {"title": row["title"], "duration": row["duration"] or 60}


@pages_bp.route("/")
def home():
    return render_template("index.html")


@pages_bp.route("/dashboard")
def dashboard_page():
    if "candidate_id" not in session:
        return redirect(url_for("auth.login"))
    conn = get_db_connection()
    row = conn.execute(
        "SELECT name FROM Candidates WHERE id = ?", (session["candidate_id"],)
    ).fetchone()
    conn.close()
    candidate_name = row["name"] if row else "Candidate"
    return render_template("dashboard.html", candidate_name=candidate_name)


@pages_bp.route("/exams")
def exams():
    if "candidate_id" not in session:
        return redirect(url_for("auth.login"))
    conn = get_db_connection()
    exam_rows = conn.execute(
        "SELECT e.id, e.title, e.duration, COUNT(q.id) AS question_count "
        "FROM Exams e LEFT JOIN Questions q ON q.exam_id = e.id "
        "GROUP BY e.id, e.title, e.duration "
        "ORDER BY e.id"
    ).fetchall()
    conn.close()
    return render_template("exams.html", exams=exam_rows)


@pages_bp.route("/results")
def results():
    if "candidate_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("results.html")


@pages_bp.route("/analytics")
def analytics():
    if "candidate_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("analytics.html")


@pages_bp.route("/environment-check")
def environment_check():
    exam_id = request.args.get("exam_id", type=int)
    return render_template("environment_check.html", exam_id=exam_id)


@pages_bp.route("/invigilator/dashboard")
@invigilator_required
def invigilator_dashboard():
    return render_template("invigilator_dashboard.html")


@pages_bp.route("/invigilator/evidence/<int:exam_id>")
@invigilator_required
def evidence_viewer(exam_id):
    """
    Evidence viewer (Milestone 5 - P1, admin dashboard additions,
    page 1 of 3). Lists every evidence image captured for this exam
    (see modules/evidence.py, GET /api/alert-evidence/exam/<exam_id>).
    """
    exam = _get_exam_meta(exam_id)
    return render_template("evidence_viewer.html", exam_id=exam_id, exam=exam)


@pages_bp.route("/invigilator/candidate-status/<int:exam_id>")
@invigilator_required
def candidate_status_viewer(exam_id):
    """
    Candidate status viewer (Milestone 5 - P1, admin dashboard additions,
    page 2 of 3). Shows submitted vs. attempted-not-submitted candidates
    for this exam (see modules/analytics.py::get_candidate_status(),
    GET /api/analytics/candidate-status/<exam_id>). No fabricated
    "in progress" or "abandoned" states - see that function's docstring.
    """
    exam = _get_exam_meta(exam_id)
    return render_template("candidate_status.html", exam_id=exam_id, exam=exam)


@pages_bp.route("/invigilator/violations/<int:exam_id>")
@invigilator_required
def violations_log(exam_id):
    """
    Violations log viewer (Milestone 5 - P1, admin dashboard additions,
    page 3 of 3). Lists every integrity flag recorded for this exam
    (see modules/flags_storage.py::get_flags_for_exam(),
    GET /api/flags/exam/<exam_id>).
    """
    exam = _get_exam_meta(exam_id)
    return render_template("violations_log.html", exam_id=exam_id, exam=exam)


@pages_bp.route("/help-support")
def help_support():
    """
    Public page - FAQ/contact info are visible to anyone. The "Report an
    Issue" form and "My Support Tickets" list (Milestone 5 - support
    ticket backend) only render for a logged-in candidate; the template
    checks `candidate_id` for that. contact_name/contact_email prefill
    the form from the candidate's own record (still editable client-side,
    still not trusted server-side - routes/support.py always uses
    session["candidate_id"] as the real owner).
    """
    contact_name = None
    contact_email = None
    if "candidate_id" in session:
        conn = get_db_connection()
        row = conn.execute(
            "SELECT name, email FROM Candidates WHERE id = ?", (session["candidate_id"],)
        ).fetchone()
        conn.close()
        if row:
            contact_name = row["name"]
            contact_email = row["email"]
    return render_template(
        "help_support.html", contact_name=contact_name, contact_email=contact_email
    )


@pages_bp.route("/invigilator/support-tickets")
@invigilator_required
def support_tickets_page():
    """
    Invigilator support-ticket queue (Milestone 5 - support ticket
    backend). Not exam-scoped like evidence/candidate-status/violations
    (a support ticket isn't tied to one exam), so this is a standalone
    page rather than following those pages' /<exam_id> URL pattern.
    """
    return render_template("support_tickets.html")


@pages_bp.route("/report/<int:exam_id>")
def report_page(exam_id):
    if "candidate_id" not in session:
        return redirect(url_for("auth.login"))
    exam = _get_exam_meta(exam_id)
    return render_template("report.html", exam_id=exam_id, exam=exam)


@pages_bp.route("/start_exam/<int:exam_id>")
def start_exam(exam_id):
    if "candidate_id" not in session:
        return redirect(url_for("auth.login"))
    exam = _get_exam_meta(exam_id)
    return render_template("exam_window.html", exam_id=exam_id, exam=exam)
