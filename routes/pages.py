"""
Frontend page routes.
Owner: Prashanthi

All template-rendering pages live here as a Blueprint, so app.py stays thin
and multiple people can add routes without editing the same file.

Note: /login and /register are handled by auth_bp (routes/auth.py) since
those need to process form submissions. This file only renders GET-only
pages that don't touch the database directly.
"""

from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def home():
    return render_template("index.html")


@pages_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@pages_bp.route("/exams")
def exams():
    return render_template("exams.html")


@pages_bp.route("/results")
def results():
    return render_template("results.html")


@pages_bp.route("/analytics")
def analytics():
    return render_template("analytics.html")


@pages_bp.route("/environment-check")
def environment_check():
    return render_template("environment_check.html")


@pages_bp.route("/help-support")
def help_support():
    return render_template("help_support.html")


@pages_bp.route("/start_exam/<int:exam_id>")
def start_exam(exam_id):
    return render_template("exam_window.html", exam_id=exam_id)
