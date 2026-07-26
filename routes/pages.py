"""
Frontend page routes.
Owner: Prashanthi
"""

from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for
)


pages_bp = Blueprint(
    "pages",
    __name__
)


# ==========================================================
# HOME PAGE
# ==========================================================

@pages_bp.route("/")
def home():

    return render_template("index.html")


# ==========================================================
# DASHBOARD
# ==========================================================

@pages_bp.route("/dashboard")
def dashboard_page():

    if "candidate_id" not in session:

        return redirect(url_for("auth.login"))

    return render_template("dashboard.html")


# ==========================================================
# EXAMS
# ==========================================================

@pages_bp.route("/exams")
def exams():

    if "candidate_id" not in session:

        return redirect(url_for("auth.login"))

    return render_template("exams.html")


# ==========================================================
# RESULTS
# ==========================================================

@pages_bp.route("/results")
def results():

    if "candidate_id" not in session:

        return redirect(url_for("auth.login"))

    return render_template("results.html")


# ==========================================================
# ANALYTICS
# ==========================================================

@pages_bp.route("/analytics")
def analytics():

    if "candidate_id" not in session:

        return redirect(url_for("auth.login"))

    return render_template("analytics.html")


# ==========================================================
# ENVIRONMENT CHECK
# ==========================================================

@pages_bp.route("/environment-check")
def environment_check():

    if "candidate_id" not in session:

        return redirect(url_for("auth.login"))

    return render_template("environment_check.html")


# ==========================================================
# HELP AND SUPPORT
# ==========================================================

@pages_bp.route("/help-support")
def help_support():

    if "candidate_id" not in session:

        return redirect(url_for("auth.login"))

    return render_template("help_support.html")


# ==========================================================
# EXAM WINDOW
# ==========================================================

@pages_bp.route("/start_exam/<int:exam_id>")
def start_exam(exam_id):

    if "candidate_id" not in session:

        return redirect(url_for("auth.login"))

    return render_template(
        "exam_window.html",
        exam_id=exam_id
    )
# ==========================================================
# VIEW ANSWERS
# ==========================================================

@pages_bp.route("/view_answers/<int:exam_id>")
def view_answers(exam_id):

    if "candidate_id" not in session:

        return redirect(url_for("auth.login"))

    return render_template(
        "view_answers.html",
        exam_id=exam_id
    )

@pages_bp.route("/quiz_generator")
def quiz_generator():
    return render_template("quiz_generator.html")