from flask import (
    Flask,
    render_template,
    session,
    redirect,
    url_for,
    request,
    jsonify
)
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "online_exam_monitoring_2026_secret"

# ----------------------------
# Database Configuration
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================================
# FRONTEND PAGES
# ==========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# PAGE ROUTE -> this is for dashboard "Open Exams" button
@app.route("/exams")
def exams():
    return render_template("exams.html")

@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/environment-check")
def environment_check():
    return render_template("environment_check.html")

@app.route("/help-support")
def help_support():
    return render_template("help_support.html")
    

# PAGE ROUTE -> this is for Start Exam button inside exams.html
@app.route("/start_exam/<int:exam_id>")
def start_exam(exam_id):
    return render_template("exam_window.html", exam_id=exam_id)


# ==========================================================
# TEMP LOGIN
# ==========================================================

@app.route("/login/test")
def test_login():
    session["candidate_id"] = 1
    return redirect(url_for("dashboard"))


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# ==========================================================
# API : GET QUESTIONS FOR AN EXAM
# ==========================================================

@app.route("/api/exam/<int:exam_id>")
def get_exam(exam_id):
    if "candidate_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()

    questions = conn.execute("""
        SELECT
            id,
            question,
            option_a,
            option_b,
            option_c,
            option_d
        FROM Questions
        WHERE exam_id = ?
    """, (exam_id,)).fetchall()

    conn.close()

    return jsonify([dict(q) for q in questions])


# ==========================================================
# API : SUBMIT ANSWERS
# ==========================================================

@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    if "candidate_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    conn = get_db_connection()

    for answer in data["answers"]:
        conn.execute("""
            INSERT INTO Answers
            (candidate_id, question_id, selected_option)
            VALUES (?, ?, ?)
        """, (
            session["candidate_id"],
            answer["question_id"],
            answer["selected_option"]
        ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Answers submitted successfully"})


if __name__ == "__main__":
    app.run(debug=True)