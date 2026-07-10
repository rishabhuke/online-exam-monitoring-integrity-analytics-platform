from flask import Flask, session, redirect, url_for, request, jsonify
import sqlite3
from pathlib import Path

from routes.auth import auth_bp
from routes.pages import pages_bp

app = Flask(__name__)
app.secret_key = "online_exam_monitoring_2026_secret"

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(pages_bp)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================================
# API : GET QUESTIONS FOR AN EXAM
# ==========================================================
@app.route("/api/exam/<int:exam_id>")
def get_exam(exam_id):
    if "candidate_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    questions = conn.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d
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
        return redirect(url_for("auth.login"))

    data = request.get_json()
    conn = get_db_connection()

    for answer in data["answers"]:
        conn.execute("""
            INSERT INTO Answers (candidate_id, question_id, selected_option)
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
