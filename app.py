from dotenv import load_dotenv
import os

load_dotenv()

from flask import Flask, session, redirect, url_for, request, jsonify
import sqlite3
from pathlib import Path
from datetime import timedelta

from routes.auth import auth_bp
from routes.pages import pages_bp
from routes.exam import exam_bp
from routes.flags import flags_bp
from routes.monitoring import monitoring_bp
from routes.report import report_bp, score_bp, attempt_bp
from routes.export import export_bp
from routes.analytics import analytics_bp
from routes.alert_evidence import alert_evidence_bp

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "online_exam_monitoring_2026_secret")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(pages_bp)
app.register_blueprint(exam_bp)
app.register_blueprint(flags_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(report_bp)
app.register_blueprint(score_bp)
app.register_blueprint(attempt_bp)
app.register_blueprint(export_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(alert_evidence_bp)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/exam/<int:exam_id>")
def get_exam(exam_id):
    if "candidate_id" not in session:
        if "application/json" in request.headers.get("Accept", ""):
            return jsonify({"status": "error", "message": "Not authenticated"}), 401
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    questions = conn.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d
        FROM Questions
        WHERE exam_id = ?
    """, (exam_id,)).fetchall()
    conn.close()

    return jsonify([dict(q) for q in questions])


PASS_THRESHOLD_PERCENT = 50.0


@app.route("/api/results")
def get_results():
    """Returns the current candidate's completed exam attempts, most
    recent first, for the /results page."""
    if "candidate_id" not in session:
        if "application/json" in request.headers.get("Accept", ""):
            return jsonify({"status": "error", "message": "Not authenticated"}), 401
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    attempts = conn.execute("""
        SELECT ExamAttempts.id, ExamAttempts.exam_id, Exams.title,
               ExamAttempts.score, ExamAttempts.total_questions,
               ExamAttempts.percentage, ExamAttempts.status,
               ExamAttempts.created_at
        FROM ExamAttempts
        JOIN Exams ON Exams.id = ExamAttempts.exam_id
        WHERE ExamAttempts.candidate_id = ?
        ORDER BY ExamAttempts.created_at DESC
    """, (session["candidate_id"],)).fetchall()
    conn.close()

    return jsonify([dict(a) for a in attempts])


@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    if "candidate_id" not in session:
        print("[DEBUG] submit_exam: User not logged in, redirecting to login page.")
        if request.is_json:
            return jsonify({"status": "error", "message": "Not authenticated"}), 401
        return redirect(url_for("auth.login"))

    data = request.get_json(silent=True)
    print(f"[DEBUG] submit_exam called. candidate_id: {session.get('candidate_id')}")

    if data is None or "answers" not in data or not isinstance(data["answers"], list):
        print("[DEBUG] submit_exam: Invalid payload structure - 'answers' list missing or None.")
        return jsonify({"status": "error", "message": "Invalid request format. 'answers' list is required."}), 400

    exam_id = data.get("exam_id")
    if not isinstance(exam_id, int):
        print("[DEBUG] submit_exam: Missing or invalid 'exam_id'.")
        return jsonify({"status": "error", "message": "A valid 'exam_id' is required."}), 400

    conn = get_db_connection()
    try:
        exam_questions = conn.execute("""
            SELECT id, correct_option FROM Questions WHERE exam_id = ?
        """, (exam_id,)).fetchall()

        if not exam_questions:
            return jsonify({"status": "error", "message": "Exam not found or has no questions."}), 404

        correct_by_id = {q["id"]: q["correct_option"] for q in exam_questions}
        total_questions = len(exam_questions)

        inserted_count = 0
        correct_count = 0
        for idx, answer in enumerate(data["answers"]):
            if not isinstance(answer, dict) or "question_id" not in answer or "selected_option" not in answer:
                print(f"[DEBUG] submit_exam: Skipping invalid answer item at index {idx}: {answer}")
                continue

            question_id = answer["question_id"]
            selected_option = answer["selected_option"]

            if question_id not in correct_by_id:
                print(f"[DEBUG] submit_exam: Skipping answer for question_id {question_id} - does not belong to exam_id {exam_id}.")
                continue

            conn.execute("""
                INSERT INTO Answers (candidate_id, question_id, selected_option)
                VALUES (?, ?, ?)
            """, (
                session["candidate_id"],
                question_id,
                selected_option
            ))
            inserted_count += 1

            if selected_option == correct_by_id[question_id]:
                correct_count += 1

        percentage = round((correct_count / total_questions) * 100, 2)
        status = "Passed" if percentage >= PASS_THRESHOLD_PERCENT else "Failed"

        conn.execute("""
            INSERT INTO ExamAttempts (candidate_id, exam_id, score, total_questions, percentage, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["candidate_id"],
            exam_id,
            correct_count,
            total_questions,
            percentage,
            status
        ))

        conn.commit()
        print(f"[DEBUG] submit_exam: Saved {inserted_count} answers, scored {correct_count}/{total_questions} ({percentage}%, {status}).")
    except Exception as e:
        conn.rollback()
        print(f"[DEBUG] submit_exam: Database error occurred: {str(e)}")
        return jsonify({"status": "error", "message": "Internal database error occurred."}), 500
    finally:
        conn.close()

    return jsonify({
        "message": "Answers submitted successfully",
        "status": "success",
        "score": correct_count,
        "total_questions": total_questions,
        "percentage": percentage,
        "result": status
    })


if __name__ == "__main__":
    app.run(debug=True)