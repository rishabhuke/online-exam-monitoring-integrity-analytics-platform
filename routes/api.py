from flask import Blueprint
from flask import jsonify
from flask import request
from flask import session
from datetime import datetime

import sqlite3

from pathlib import Path

from modules.face_verification import FaceVerifier
import os
from modules.face_monitor import FaceMonitor
import os

from services.quiz_generator import generate_quiz

api_bp = Blueprint("api", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = BASE_DIR / "database.db"
verifier = FaceVerifier()
monitor = FaceMonitor()


def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ---------------------------------------------
# Existing API
# ---------------------------------------------
@api_bp.route("/api/exams", methods=["GET"])
def get_exams():

    if "candidate_id" not in session:
        return jsonify([]), 401

    conn = get_db()

    exams = conn.execute("""
        SELECT
            e.id,
            e.title,
            e.topic,
            e.difficulty,
            e.description,
            e.duration,
            e.total_questions,
            e.total_marks,
            e.start_time,
            e.end_time,

            CASE
                WHEN a.id IS NULL THEN 'Available'
                ELSE 'Completed'
            END AS exam_status

        FROM Exams e

        LEFT JOIN ExamAttempts a
            ON e.id = a.exam_id
            AND a.candidate_id = ?

        ORDER BY e.id DESC
    """, (session["candidate_id"],)).fetchall()

    available_exams = []

    now = datetime.now()

    for exam in exams:

        exam = dict(exam)

        start = datetime.fromisoformat(exam["start_time"])
        end = datetime.fromisoformat(exam["end_time"])

        # Hide expired exams
        if now > end:
           continue
 
        # Exam not started yet
        if now < start:
           exam["exam_status"] = "Unavailable"

        available_exams.append(exam)

    conn.close()

    return jsonify(available_exams)

@api_bp.route("/api/exam/<int:exam_id>", methods=["GET"])
def get_exam(exam_id):

    conn = get_db()

    exam = conn.execute("""
        SELECT
            id,
            title,
            topic,
            difficulty,
            description,
            duration,
            total_questions,
            total_marks,
            start_time,
            end_time
        FROM Exams
        WHERE id = ?
    """, (exam_id,)).fetchone()

    # Exam not found
    if exam is None:

        conn.close()

        return jsonify({

            "success": False,

            "message": "Exam not found"

        }), 404

    # Check exam availability
    now = datetime.now()

    start = datetime.fromisoformat(exam["start_time"])
    end = datetime.fromisoformat(exam["end_time"])

    if now < start:

        conn.close()

        return jsonify({

            "success": False,

            "message": "Exam is not available yet."

        }), 403

    if now > end:

        conn.close()

        return jsonify({

            "success": False,

            "message": "Exam has expired."

        }), 403

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
        ORDER BY id
    """, (exam_id,)).fetchall()

    conn.close()

    return jsonify({

        "success": True,

        "exam_name": exam["title"],

        "duration": exam["duration"],

        "questions": [

            {
                "question_id": q["id"],
                "question": q["question"],
                "option_a": q["option_a"],
                "option_b": q["option_b"],
                "option_c": q["option_c"],
                "option_d": q["option_d"]
            }

            for q in questions

        ]

    })
# ---------------------------------------------
# Generate Quiz
# ---------------------------------------------

@api_bp.route("/api/monitor_face", methods=["POST"])
def monitor_face():

    if "candidate_id" not in session:

        return jsonify({

            "success": False,

            "message": "Session expired."

        }), 401


    try:

        data = request.get_json()

        image = data.get("image")

        exam_id = data.get("exam_id")

        if not image:

            return jsonify({

                "success": False,

                "message": "Image is required."

            }), 400


        candidate_id = session["candidate_id"]


        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""

            SELECT photo_path

            FROM Candidates

            WHERE id=?

        """, (candidate_id,))


        row = cursor.fetchone()


        if row is None:

            conn.close()

            return jsonify({

                "success": False,

                "message": "Candidate not found."

            }), 404


        photo_path = row["photo_path"]


        result = monitor.monitor(

            registered_photo=photo_path,

            live_image_base64=image,

            candidate_id=candidate_id,

            exam_id=exam_id

        )


        # -----------------------------
        # Save Violation
        # -----------------------------

        if result["status"] == "violation":

            cursor.execute("""

                INSERT INTO ViolationLogs(

                    candidate_id,

                    exam_id,

                    violation_type,

                    evidence_image,

                    face_count,

                    violation_time

                )

                VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)

            """, (

                candidate_id,

                exam_id,

                result["type"],

                result["evidence"],

                0

            ))

            conn.commit()


        conn.close()


        return jsonify({

            "success": True,

            "result": result

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        }), 500
# ==========================================================
# LOG VIOLATION
# ==========================================================

@api_bp.route("/api/log_violation", methods=["POST"])
def log_violation():

    if "candidate_id" not in session:

        return jsonify({

            "status": "error",

            "message": "Unauthorized"

        }), 401

    try:

        data = request.get_json()

        exam_id = data.get("exam_id")

        violation = data.get("violation")

        if not exam_id or not violation:

            return jsonify({

                "status": "error",

                "message": "Invalid Request"

            }), 400

        conn = get_db()

        conn.execute(
            """
            INSERT INTO ViolationLogs
            (
                candidate_id,
                exam_id,
                violation_type
            )

            VALUES
            (
                ?,?,?
            )
            """,
            (
                session["candidate_id"],
                exam_id,
                violation
            )
        )

        conn.commit()

        conn.close()

        return jsonify({

            "status": "success"

        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500
# ==========================================================
# GET VIOLATION COUNT
# ==========================================================

@api_bp.route("/api/violation_count/<int:exam_id>")
def violation_count(exam_id):

    if "candidate_id" not in session:

        return jsonify({

            "status": "error"

        }),401

    conn = get_db()

    count = conn.execute(
        """
        SELECT COUNT(*) AS total

        FROM ViolationLogs

        WHERE candidate_id=?

        AND exam_id=?
        """,
        (
            session["candidate_id"],
            exam_id
        )
    ).fetchone()

    conn.close()

    return jsonify({

        "count":count["total"]

    })
# ==========================================================
# GET VIOLATIONS
# ==========================================================

@api_bp.route("/api/violations/<int:exam_id>")
def get_violations(exam_id):

    if "candidate_id" not in session:

        return jsonify({

            "status":"error"

        }),401

    conn = get_db()

    rows = conn.execute(
        """
        SELECT
            id,
            violation_type,
            violation_time

        FROM ViolationLogs

        WHERE candidate_id=?

        AND exam_id=?

        ORDER BY violation_time
        """,
        (
            session["candidate_id"],
            exam_id
        )
    ).fetchall()

    conn.close()

    return jsonify([dict(r) for r in rows])

# ==========================================================
# VIEW ANSWERS
# ==========================================================

@api_bp.route("/api/view_answers/<int:exam_id>", methods=["GET"])
def view_answers_api(exam_id):

    if "candidate_id" not in session:

        return jsonify({

            "success": False,
            "message": "Unauthorized"

        }),401

    conn = get_db()

    candidate_id = session["candidate_id"]

    try:

        exam = conn.execute("""

            SELECT
                title

            FROM Exams

            WHERE id = ?

        """,(exam_id,)).fetchone()

        if exam is None:

            conn.close()

            return jsonify({

                "success":False,
                "message":"Exam not found"

            }),404

        rows = conn.execute("""

            SELECT

                q.id,

                q.question,

                q.option_a,

                q.option_b,

                q.option_c,

                q.option_d,

                q.correct_option,

                a.selected_option

            FROM Questions q

            LEFT JOIN Answers a

                ON q.id = a.question_id

                AND a.candidate_id = ?

            WHERE q.exam_id = ?

            ORDER BY q.id

        """,

        (

            candidate_id,

            exam_id

        )).fetchall()

        questions=[]

        for row in rows:

            questions.append({

                "question_id":row["id"],

                "question":row["question"],

                "option_a":row["option_a"],

                "option_b":row["option_b"],

                "option_c":row["option_c"],

                "option_d":row["option_d"],

                "correct_option":row["correct_option"],

                "selected_option":row["selected_option"]

            })

        conn.close()

        return jsonify({

            "success":True,

            "exam_name":exam["title"],

            "questions":questions

        })

    except Exception as e:

        conn.close()

        return jsonify({

            "success":False,

            "message":str(e)

        }),500

@api_bp.route("/api/verify_candidate", methods=["POST"])
def verify_candidate():

    if "candidate_id" not in session:

        return jsonify({

            "verified": False,
            "message": "Unauthorized"

        }), 401

    data = request.get_json()

    if not data:

        return jsonify({

            "verified": False,
            "message": "Invalid request."

        }), 400

    image = data.get("image")

    if not image:

        return jsonify({

            "verified": False,
            "message": "Image not received."

        }), 400

    conn = get_db()

    candidate = conn.execute(
        """
        SELECT photo_path
        FROM Candidates
        WHERE id = ?
        """,
        (session["candidate_id"],)
    ).fetchone()

    conn.close()

    if candidate is None:

        return jsonify({

            "verified": False,
            "message": "Candidate not found."

        }), 404

    photo_path = candidate["photo_path"]

    if not photo_path:

        return jsonify({

            "verified": False,
            "message": "Registration photo missing."

        }), 404

    if not os.path.exists(photo_path):

        return jsonify({

            "verified": False,
            "message": "Registration image not found."

        }), 404

    result = verifier.verify(

        photo_path,

        image

    )

    return jsonify(result)

@api_bp.route("/api/results", methods=["GET"])
def get_results():

    print("Candidate in session:", session.get("candidate_id"))

    if "candidate_id" not in session:
        print("No candidate_id in session")
        return jsonify([]), 401

    conn = get_db()

    rows = conn.execute("""
        SELECT
            e.id AS exam_id,
            e.title,
            e.topic,
            e.difficulty,
            a.score,
            a.total_questions,
            a.percentage,
            a.result
        FROM ExamAttempts a
        INNER JOIN Exams e
            ON e.id = a.exam_id
        WHERE a.candidate_id = ?
        ORDER BY a.id DESC
    """, (session["candidate_id"],)).fetchall()

    print("Rows found:", len(rows))
    print([dict(r) for r in rows])

    conn.close()

    return jsonify([dict(r) for r in rows])