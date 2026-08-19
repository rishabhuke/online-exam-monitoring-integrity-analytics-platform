from flask import Flask, session, redirect, url_for, request, jsonify
import sqlite3
from pathlib import Path
from datetime import timedelta

from routes.auth import auth_bp
from routes.pages import pages_bp
from routes.exam import exam_bp
from routes.flags import flags_bp
from routes.monitoring import monitoring_bp
from routes.report import report_bp

app = Flask(__name__)
app.secret_key = "online_exam_monitoring_2026_secret"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(pages_bp)
app.register_blueprint(exam_bp)
app.register_blueprint(flags_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(report_bp)

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
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    questions = conn.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d
        FROM Questions
        WHERE exam_id = ?
    """, (exam_id,)).fetchall()
    conn.close()

    return jsonify([dict(q) for q in questions])


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

    conn = get_db_connection()
    try:
        inserted_count = 0
        for idx, answer in enumerate(data["answers"]):
            if not isinstance(answer, dict) or "question_id" not in answer or "selected_option" not in answer:
                print(f"[DEBUG] submit_exam: Skipping invalid answer item at index {idx}: {answer}")
                continue

            conn.execute("""
                INSERT INTO Answers (candidate_id, question_id, selected_option)
                VALUES (?, ?, ?)
            """, (
                session["candidate_id"],
                answer["question_id"],
                answer["selected_option"]
            ))
            inserted_count += 1

        conn.commit()
        print(f"[DEBUG] submit_exam: Successfully saved {inserted_count} answers to database.")
    except Exception as e:
        conn.rollback()
        print(f"[DEBUG] submit_exam: Database error occurred: {str(e)}")
        return jsonify({"status": "error", "message": "Internal database error occurred."}), 500
    finally:
        conn.close()

    return jsonify({"message": "Answers submitted successfully", "status": "success"})


if __name__ == "__main__":
    app.run(debug=True)