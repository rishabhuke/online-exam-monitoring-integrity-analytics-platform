from flask import Blueprint
from flask import jsonify
from flask import request
from flask import session
from datetime import datetime
from collections import defaultdict
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

@api_bp.route("/api/candidate/environment", methods=["GET"])
def get_candidate_environment():

    if "candidate_id" not in session:
        return jsonify({
            "success": False,
            "message": "Candidate not logged in"
        }), 401

    candidate_id = session["candidate_id"]

    conn = get_db()

    try:
        candidate = conn.execute("""
            SELECT
                id,
                name,
                email,
                photo_path
            FROM Candidates
            WHERE id = ?
        """, (candidate_id,)).fetchone()

        if candidate is None:
            return jsonify({
                "success": False,
                "message": "Candidate not found"
            }), 404

        exams = conn.execute("""
            SELECT
                e.id,
                e.title,
                e.topic,
                e.difficulty,
                e.duration,
                e.total_questions,
                e.total_marks,
                e.start_time,
                e.end_time
            FROM Exams e
            LEFT JOIN ExamAttempts a
                ON e.id = a.exam_id
                AND a.candidate_id = ?
            WHERE a.id IS NULL
            ORDER BY e.id DESC
        """, (candidate_id,)).fetchall()

        now = datetime.now()

        available_exams = []

        for row in exams:

            exam = dict(row)

            try:
                start = datetime.fromisoformat(
                    exam["start_time"]
                )

                end = datetime.fromisoformat(
                    exam["end_time"]
                )
            except Exception:
                continue

            if now > end:
                continue

            if now < start:
                exam["status"] = "Upcoming"
            else:
                exam["status"] = "Available"

            available_exams.append(exam)

        return jsonify({
            "success": True,

            "candidate": {
                "id": candidate["id"],
                "name": candidate["name"],
                "email": candidate["email"],
                "photo_path": candidate["photo_path"]
            },

            "requirements": {
                "camera": True,
                "microphone": True,
                "internet": True,
                "browser": True,
                "fullscreen": True,
                "face": True
            },

            "exams": available_exams
        })

    finally:
        conn.close()

@api_bp.route("/api/candidate/support/<int:ticket_id>", methods=["GET"])
def get_candidate_support_ticket(ticket_id):

    if "candidate_id" not in session:
        return jsonify({
            "success": False,
            "message": "Candidate not logged in"
        }), 401

    candidate_id = session["candidate_id"]

    conn = get_db()

    try:

        ticket = conn.execute("""
            SELECT
                s.id,
                s.issue_type,
                s.priority,
                s.subject,
                s.message,
                s.status,
                s.admin_response,
                s.created_at,
                s.updated_at,
                s.resolved_at,
                a.full_name AS admin_name

            FROM SupportTickets s

            LEFT JOIN Admins a
                ON a.id = s.assigned_admin_id

            WHERE s.id = ?
              AND s.candidate_id = ?

        """, (
            ticket_id,
            candidate_id
        )).fetchone()

        if ticket is None:
            return jsonify({
                "success": False,
                "message": "Support ticket not found"
            }), 404

        return jsonify({
            "success": True,
            "ticket": dict(ticket)
        })

    finally:
        conn.close()

@api_bp.route("/api/faqs", methods=["GET"])
def get_faqs():

    conn = get_db()

    try:

        faqs = conn.execute("""
            SELECT
                id,
                question,
                answer,
                category
            FROM FAQs
            WHERE active = 1
            ORDER BY id
        """).fetchall()

        return jsonify({
            "success": True,
            "faqs": [
                dict(faq)
                for faq in faqs
            ]
        })

    finally:
        conn.close()

        
@api_bp.route("/api/candidate/support", methods=["POST"])
def create_candidate_support():

    if "candidate_id" not in session:
        return jsonify({
            "success": False,
            "message": "Candidate not logged in"
        }), 401

    candidate_id = session["candidate_id"]

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400

    issue_type = str(
        data.get("issue_type", "")
    ).strip()

    priority = str(
        data.get("priority", "")
    ).strip()

    subject = str(
        data.get("subject", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    if not issue_type:
        return jsonify({
            "success": False,
            "message": "Issue type is required"
        }), 400

    if not priority:
        return jsonify({
            "success": False,
            "message": "Priority is required"
        }), 400

    if not subject:
        return jsonify({
            "success": False,
            "message": "Subject is required"
        }), 400

    if not message:
        return jsonify({
            "success": False,
            "message": "Message is required"
        }), 400

    allowed_priorities = [
        "Low",
        "Medium",
        "High",
        "Critical"
    ]

    if priority not in allowed_priorities:
        return jsonify({
            "success": False,
            "message": "Invalid priority"
        }), 400

    conn = get_db()

    try:

        cursor = conn.execute("""
            INSERT INTO SupportTickets (
                candidate_id,
                issue_type,
                priority,
                subject,
                message,
                status
            )

            VALUES (?, ?, ?, ?, ?, 'Open')
        """, (
            candidate_id,
            issue_type,
            priority,
            subject,
            message
        ))

        conn.commit()

        ticket_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Support request submitted successfully",
            "ticket_id": ticket_id
        }), 201

    finally:
        conn.close()

@api_bp.route("/api/candidate/support", methods=["GET"])
def get_candidate_support():

    if "candidate_id" not in session:
        return jsonify({
            "success": False,
            "message": "Candidate not logged in"
        }), 401

    candidate_id = session["candidate_id"]

    conn = get_db()

    try:

        tickets = conn.execute("""
            SELECT
                s.id,
                s.issue_type,
                s.priority,
                s.subject,
                s.message,
                s.status,
                s.admin_response,
                s.created_at,
                s.updated_at,
                s.resolved_at,
                a.full_name AS admin_name

            FROM SupportTickets s

            LEFT JOIN Admins a
                ON a.id = s.assigned_admin_id

            WHERE s.candidate_id = ?

            ORDER BY datetime(s.created_at) DESC
        """, (candidate_id,)).fetchall()

        return jsonify({
            "success": True,
            "tickets": [dict(ticket) for ticket in tickets]
        })

    finally:
        conn.close()


@api_bp.route("/api/candidate/analytics", methods=["GET"])
def get_candidate_analytics():

    if "candidate_id" not in session:
        return jsonify({
            "success": False,
            "message": "Candidate not logged in"
        }), 401

    candidate_id = session["candidate_id"]

    conn = get_db()

    candidate = conn.execute("""
        SELECT
            id,
            name,
            email,
            photo_path
        FROM Candidates
        WHERE id = ?
    """, (candidate_id,)).fetchone()

    if candidate is None:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Candidate not found"
        }), 404

    attempts = conn.execute("""
        SELECT
            a.id,
            a.exam_id,
            a.score,
            a.total_questions,
            a.percentage,
            a.result,
            a.submitted_at,

            e.title,
            e.topic,
            e.difficulty,
            e.total_marks

        FROM ExamAttempts a

        INNER JOIN Exams e
            ON e.id = a.exam_id

        WHERE a.candidate_id = ?

        ORDER BY datetime(a.submitted_at) DESC
    """, (candidate_id,)).fetchall()

    attempts = [dict(row) for row in attempts]

    total_exams = len(attempts)

    percentages = [
        float(attempt["percentage"])
        for attempt in attempts
    ]

    if percentages:
        average_score = round(
            sum(percentages) / len(percentages),
            2
        )

        best_score = round(
            max(percentages),
            2
        )
    else:
        average_score = 0
        best_score = 0

    passed_exams = sum(
        1
        for attempt in attempts
        if str(attempt["result"]).strip().lower()
        in ["pass", "passed", "success"]
    )

    answer_stats = conn.execute("""
        SELECT
            COUNT(*) AS total_answered,

            SUM(
                CASE
                    WHEN UPPER(TRIM(a.selected_option))
                         =
                         UPPER(TRIM(q.correct_option))
                    THEN 1
                    ELSE 0
                END
            ) AS correct_answers

        FROM Answers a

        INNER JOIN Questions q
            ON q.id = a.question_id

        WHERE a.candidate_id = ?

        AND a.selected_option IS NOT NULL

        AND TRIM(a.selected_option) != ''
    """, (candidate_id,)).fetchone()

    total_answered = answer_stats["total_answered"] or 0

    correct_answers = answer_stats["correct_answers"] or 0

    if total_answered > 0:

        accuracy = round(
            (correct_answers / total_answered) * 100,
            2
        )

    else:

        accuracy = 0

    if len(percentages) <= 1:

        consistency = 100

    else:

        avg = sum(percentages) / len(percentages)

        mean_absolute_deviation = (
            sum(
                abs(score - avg)
                for score in percentages
            )
            / len(percentages)
        )

        consistency = round(
            max(
                0,
                100 - (mean_absolute_deviation * 2)
            ),
            2
        )

    if len(attempts) >= 2:

        chronological = sorted(
            attempts,
            key=lambda x: x["submitted_at"]
        )

        first_score = float(
            chronological[0]["percentage"]
        )

        latest_score = float(
            chronological[-1]["percentage"]
        )

        if first_score > 0:

            improvement_rate = round(
                (
                    (latest_score - first_score)
                    / first_score
                ) * 100,
                2
            )

        else:

            improvement_rate = 0

    else:

        improvement_rate = 0

    subject_data = defaultdict(list)

    for attempt in attempts:

        topic = (
            attempt["topic"]
            or "General"
        ).strip()

        subject_data[topic].append(
            float(attempt["percentage"])
        )

    subjects = []

    for topic, scores in subject_data.items():

        average = round(
            sum(scores) / len(scores),
            2
        )

        subjects.append({
            "subject": topic,
            "percentage": average,
            "exam_count": len(scores)
        })

    subjects.sort(
        key=lambda item: item["percentage"],
        reverse=True
    )

    recent_activity = []

    for attempt in attempts[:5]:

        recent_activity.append({
            "exam_id": attempt["exam_id"],
            "title": attempt["title"],
            "topic": attempt["topic"] or "General",
            "difficulty": attempt["difficulty"],
            "score": attempt["score"],
            "total_questions": attempt["total_questions"],
            "percentage": round(
                float(attempt["percentage"]),
                2
            ),
            "result": attempt["result"],
            "submitted_at": attempt["submitted_at"]
        })

    insights = []

    if subjects:

        strongest = subjects[0]

        weakest = subjects[-1]

        insights.append({
            "type": "strength",
            "title": (
                f"Strongest Subject: "
                f"{strongest['subject']}"
            ),
            "description": (
                f"Your average performance in "
                f"{strongest['subject']} is "
                f"{strongest['percentage']}%."
            )
        })

        if weakest["subject"] != strongest["subject"]:

            insights.append({
                "type": "improvement",
                "title": (
                    f"Focus on "
                    f"{weakest['subject']}"
                ),
                "description": (
                    f"{weakest['subject']} is currently "
                    f"your lowest-performing subject "
                    f"with an average of "
                    f"{weakest['percentage']}%."
                )
            })

    if improvement_rate > 0:

        insights.append({
            "type": "progress",
            "title": "Performance is Improving",
            "description": (
                f"Your latest performance is "
                f"{improvement_rate}% higher "
                f"than your first recorded attempt."
            )
        })

    elif improvement_rate < 0:

        insights.append({
            "type": "warning",
            "title": "Performance Needs Attention",
            "description": (
                "Your latest performance is lower "
                "than your first recorded attempt. "
                "Consider revising weaker topics."
            )
        })

    if accuracy >= 85:

        insights.append({
            "type": "accuracy",
            "title": "High Answer Accuracy",
            "description": (
                f"You currently answer "
                f"{accuracy}% of attempted "
                f"questions correctly."
            )
        })

    elif 0 < accuracy < 70:

        insights.append({
            "type": "accuracy",
            "title": "Accuracy Needs Improvement",
            "description": (
                f"Your current answer accuracy "
                f"is {accuracy}%. Review incorrect "
                f"answers and practice more questions."
            )
        })

    suggestions = []

    if subjects:

        weakest = subjects[-1]

        if weakest["percentage"] < 70:

            suggestions.append(
                f"Spend more time practicing "
                f"{weakest['subject']} questions."
            )

        elif weakest["percentage"] < 80:

            suggestions.append(
                f"Revise the core concepts of "
                f"{weakest['subject']} before "
                f"your next assessment."
            )

    if accuracy < 70 and total_answered > 0:

        suggestions.append(
            "Review incorrect answers after each "
            "exam and practice more objective questions."
        )

    elif accuracy < 85 and total_answered > 0:

        suggestions.append(
            "Practice timed questions to improve "
            "accuracy and reduce avoidable mistakes."
        )

    if improvement_rate < 0:

        suggestions.append(
            "Compare your recent results with earlier "
            "attempts and revise your weakest topics."
        )

    elif improvement_rate > 10:

        suggestions.append(
            "Your performance is improving well. "
            "Continue your current preparation strategy."
        )

    if not suggestions:

        suggestions.append(
            "Continue practicing consistently and "
            "review your weaker topics before each exam."
        )

    response = {
        "success": True,

        "candidate": {
            "id": candidate["id"],
            "name": candidate["name"],
            "email": candidate["email"],
            "photo_path": candidate["photo_path"]
        },

        "stats": {
            "total_exams": total_exams,
            "average_score": average_score,
            "best_score": best_score,
            "consistency": consistency
        },

        "overview": {
            "passed_exams": passed_exams,
            "accuracy": accuracy,
            "improvement_rate": improvement_rate
        },

        "subjects": subjects,

        "recent_activity": recent_activity,

        "insights": insights,

        "suggestions": suggestions
    }

    conn.close()

    return jsonify(response)

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