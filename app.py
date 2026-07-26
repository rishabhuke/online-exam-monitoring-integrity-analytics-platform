from dotenv import load_dotenv

load_dotenv()

from flask import (
    Flask,
    session,
    request,
    jsonify
)

import sqlite3
from pathlib import Path
from datetime import timedelta

from routes.api import api_bp
from routes.auth import auth_bp
from routes.pages import pages_bp


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)


# ==========================================================
# APPLICATION CONFIGURATION
# ==========================================================

app.secret_key = "online_exam_monitoring_2026_secret"

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)


# ==========================================================
# REGISTER BLUEPRINTS
# ==========================================================

app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(pages_bp)


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE = BASE_DIR / "database.db"

print("=" * 60)
print("DATABASE PATH:", DATABASE)
print("=" * 60)


def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.execute("PRAGMA foreign_keys = ON")

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================================
# API - SUBMIT EXAM
# ==========================================================

@app.route("/submit_exam", methods=["POST"])
def submit_exam():

    if "candidate_id" not in session:
        return jsonify({
            "error": "Unauthorized",
            "message": "Please login before submitting exam."
        }), 401

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Invalid request data"
        }), 400

    exam_id = data.get("exam_id")
    answers = data.get("answers", [])

    if not exam_id:
        return jsonify({
            "error": "Exam ID missing"
        }), 400

    if not answers:
        return jsonify({
            "error": "No answers received"
        }), 400

    conn = get_db_connection()

    try:

        candidate_id = session["candidate_id"]

        # ---------------------------------------------------
        # Check whether exam is already completed
        # ---------------------------------------------------
        existing = conn.execute("""
        SELECT
        score,
        total_questions,
        percentage,
        result
        FROM ExamAttempts
        WHERE candidate_id=?
        AND exam_id=?
        """, (candidate_id, exam_id)).fetchone()

        if existing:

             return jsonify({

             "success": False,
             "already_completed": True,

             "score": existing["score"],
             "total": existing["total_questions"],
             "percentage": existing["percentage"],
             "result": existing["result"],

             "message": "You have already completed this exam."

             }), 200

       
        # ---------------------------------------------------
        # Evaluate Answers
        # ---------------------------------------------------

        correct_option = 0
        total_questions = len(answers)

        for answer in answers:

            question_id = answer.get("question_id")
            selected_option = answer.get("selected_option")

            if question_id is None:
                continue

            correct = conn.execute("""
                SELECT correct_option
                FROM Questions
                WHERE id = ?
            """,
            (question_id,)).fetchone()

            if correct and selected_option == correct["correct_option"]:
                correct_option += 1

            # Save student's answer

            conn.execute("""
                INSERT INTO Answers
                (
                    candidate_id,
                    question_id,
                    selected_option
                )
                VALUES (?,?,?)
            """,
            (
                candidate_id,
                question_id,
                selected_option
            ))
            print("Selected:", answer["selected_option"])
            print("Correct :", correct["correct_option"])
            

        # ---------------------------------------------------
        # Calculate Result
        # ---------------------------------------------------

        wrong_answers = total_questions - correct_option

        percentage = round(
            (correct_option / total_questions) * 100,
            2
        ) if total_questions > 0 else 0

        status = "PASS" if percentage >= 40 else "FAIL"

        # ---------------------------------------------------
        # Save Attempt
        # ---------------------------------------------------

        conn.execute("""
            INSERT INTO ExamAttempts
            (
                candidate_id,
                exam_id,
                score,
                total_questions,
                percentage,
                result
            )
            VALUES (?,?,?,?,?,?)
        """,
        (
            candidate_id,
            exam_id,
            correct_option,
            total_questions,
            percentage,
            status
        ))

        conn.commit()

        return jsonify({
            

            "success": True,

            "score": correct_option,

            "wrong": wrong_answers,

            "total": total_questions,

            "percentage": percentage,

            "result": status

        }), 200

    except sqlite3.Error as error:

        conn.rollback()

        return jsonify({

            "success": False,

            "message": str(error)

        }), 500

    finally:

        conn.close()


# ==========================================================
# ERROR HANDLERS
# ==========================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "error": "Page not found"

    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "error": "Internal server error"

    }), 500


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )