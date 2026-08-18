from flask import Blueprint, jsonify, render_template, request,send_file
import sqlite3
from pathlib import Path
from modules.integrity_ai import (
    generate_behavioural_assessment
)
from modules.integrity_exam_ai import (
    generate_exam_behavioural_assessment
)
from modules.data_science_analytics import (
    generate_analytics
)

# ==========================================================
# BLUEPRINT Integrity_analytics.py
# ==========================================================

integrity_bp = Blueprint(
    "integrity",
    __name__
)


# ==========================================================
# PATH CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = BASE_DIR / "database.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ==========================================================
# HIDDEN INTEGRITY ANALYTICS PAGE
# ==========================================================

@integrity_bp.route(
    "/integrity-analytics",
    methods=["GET"]
)
def integrity_analytics():

    return render_template(
        "integrity_analytics.html"
    )
@integrity_bp.route("/candidate-integrity")
def candidate_integrity_page():

    return render_template(
        "candidate-integrity.html"
    )

# ==========================================================
# GET ALL EXAMS FOR ANALYTICS
# ==========================================================
# ==========================================================
# CANDIDATE INTEGRITY DETAILS
# ==========================================================

@integrity_bp.route(
    "/api/integrity/candidate/<int:candidate_id>",
    methods=["GET"]
)
def get_candidate_integrity(candidate_id):

    exam_id = request.args.get(
        "exam_id",
        type=int
    )

    if exam_id is None:

        return jsonify({
            "success": False,
            "message": "exam_id is required"
        }), 400

    conn = get_db()

    try:

        # ==================================================
        # CANDIDATE
        # ==================================================

        candidate = conn.execute("""
            SELECT
                id,
                name,
                email,
                photo_path,
                created_at
            FROM Candidates
            WHERE id = ?
        """, (
            candidate_id,
        )).fetchone()


        if candidate is None:

            return jsonify({
                "success": False,
                "message": "Candidate not found"
            }), 404


        # ==================================================
        # EXAM
        # ==================================================

        exam = conn.execute("""
            SELECT
                id,
                title,
                topic,
                difficulty,
                description,
                duration,
                total_questions,
                total_marks
            FROM Exams
            WHERE id = ?
        """, (
            exam_id,
        )).fetchone()


        if exam is None:

            return jsonify({
                "success": False,
                "message": "Exam not found"
            }), 404


        # ==================================================
        # EXAM ATTEMPT
        # ==================================================

        attempt = conn.execute("""
            SELECT
                id,
                score,
                total_questions,
                percentage,
                result,
                submitted_at
            FROM ExamAttempts
            WHERE candidate_id = ?
            AND exam_id = ?
            LIMIT 1
        """, (
            candidate_id,
            exam_id
        )).fetchone()


        # ==================================================
        # INTEGRITY SCORE
        # ==================================================

        integrity = conn.execute("""
            SELECT
                id,
                integrity_score,
                face_presence_ratio,
                warning_count,
                risk_label,
                generated_at
            FROM IntegrityScores
            WHERE candidate_id = ?
            AND exam_id = ?
            LIMIT 1
        """, (
            candidate_id,
            exam_id
        )).fetchone()


        # ==================================================
        # ALL VIOLATIONS
        # ==================================================

        violation_rows = conn.execute("""
            SELECT
                id,
                violation_type,
                evidence_image,
                face_count,
                violation_time
            FROM ViolationLogs
            WHERE candidate_id = ?
            AND exam_id = ?
            ORDER BY violation_time ASC
        """, (
            candidate_id,
            exam_id
        )).fetchall()


        # ==================================================
        # VIOLATION CLASSIFIER
        # ==================================================

        def classify_violation(violation_type):

            text = (
                violation_type or ""
            ).strip().lower()


            # ----------------------------------------------
            # TAB SWITCH
            # ----------------------------------------------

            if (
                "tab" in text
                or
                "browser tab" in text
            ):

                return "TAB_SWITCH"


            # ----------------------------------------------
            # FOCUS LOSS
            # ----------------------------------------------

            if (
                "focus" in text
                or
                "window lost" in text
                or
                "blur" in text
            ):

                return "FOCUS_LOSS"


            # ----------------------------------------------
            # FULLSCREEN
            # ----------------------------------------------

            if (
                "fullscreen" in text
                or
                "full screen" in text
            ):

                return "FULLSCREEN_EXIT"


            # ----------------------------------------------
            # FACE ABSENCE
            # ----------------------------------------------

            if (
                "no_face" in text
                or
                "no face" in text
                or
                "face absent" in text
                or
                "face absence" in text
                or
                "face not detected" in text
            ):

                return "FACE_ABSENCE"


            # ----------------------------------------------
            # UNKNOWN / WRONG FACE
            # ----------------------------------------------

            if (
                "unknown_face" in text
                or
                "unknown face" in text
                or
                "identity mismatch" in text
                or
                "mismatch" in text
            ):

                return "IDENTITY_MISMATCH"


            # ----------------------------------------------
            # MULTIPLE FACES
            # ----------------------------------------------

            if (
                "multiple_faces" in text
                or
                "multiple faces" in text
                or
                "more than one face" in text
            ):

                return "MULTIPLE_FACES"


            # ----------------------------------------------
            # COPY / CUT / PASTE
            # ----------------------------------------------

            if (
                "copy" in text
                or
                "paste" in text
                or
                "cut" in text
            ):

                return "COPY_PASTE"


            # ----------------------------------------------
            # SCREENSHOT
            # ----------------------------------------------

            if (
                "screenshot" in text
                or
                "screen shot" in text
                or
                "print screen" in text
                or
                "printscreen" in text
            ):

                return "SCREENSHOT"


            # ----------------------------------------------
            # RIGHT CLICK
            # ----------------------------------------------

            if (
                "right-click" in text
                or
                "right click" in text
                or
                "context menu" in text
            ):

                return "RIGHT_CLICK"


            # ----------------------------------------------
            # OTHER
            # ----------------------------------------------

            return "OTHER"


        # ==================================================
        # VIOLATION BREAKDOWN
        # ==================================================

        breakdown = {

            "tab_switches": 0,

            "focus_loss": 0,

            "face_absence": 0,

            "fullscreen_exit": 0,

            "copy_paste": 0,

            "screenshots": 0,

            "right_click": 0,

            "identity_mismatch": 0,

            "multiple_faces": 0,

            "other": 0

        }


        # ==================================================
        # FORMAT VIOLATIONS
        # ==================================================

        violations = []


        for row in violation_rows:

            category = classify_violation(
                row["violation_type"]
            )


            # ----------------------------------------------
            # INCREMENT CATEGORY
            # ----------------------------------------------

            if category == "TAB_SWITCH":

                breakdown[
                    "tab_switches"
                ] += 1


            elif category == "FOCUS_LOSS":

                breakdown[
                    "focus_loss"
                ] += 1


            elif category == "FACE_ABSENCE":

                breakdown[
                    "face_absence"
                ] += 1


            elif category == "FULLSCREEN_EXIT":

                breakdown[
                    "fullscreen_exit"
                ] += 1


            elif category == "COPY_PASTE":

                breakdown[
                    "copy_paste"
                ] += 1


            elif category == "SCREENSHOT":

                breakdown[
                    "screenshots"
                ] += 1


            elif category == "RIGHT_CLICK":

                breakdown[
                    "right_click"
                ] += 1


            elif category == "IDENTITY_MISMATCH":

                breakdown[
                    "identity_mismatch"
                ] += 1


            elif category == "MULTIPLE_FACES":

                breakdown[
                    "multiple_faces"
                ] += 1


            else:

                breakdown[
                    "other"
                ] += 1


            # ----------------------------------------------
            # EVIDENCE
            # ----------------------------------------------

            evidence = row[
                "evidence_image"
            ]


            violations.append({

                "id":
                    row["id"],

                "type":
                    row["violation_type"],

                "category":
                    category,

                "evidence_image":
                    evidence,

                "face_count":
                    row["face_count"],

                "time":
                    row["violation_time"],

                "has_evidence":
                    bool(evidence)

            })


        # ==================================================
        # TOTAL WARNINGS
        # ==================================================

        total_warnings = len(
            violations
        )


        # ==================================================
        # EVIDENCE COUNT
        # ==================================================

        evidence_count = sum(

            1

            for violation
            in violations

            if violation["has_evidence"]

        )


        # ==================================================
        # INTEGRITY OBJECT
        # ==================================================

        integrity_data = {

            "score":
                (
                    integrity["integrity_score"]
                    if integrity
                    else None
                ),

            "face_presence_ratio":
                (
                    integrity[
                        "face_presence_ratio"
                    ]
                    if integrity
                    else None
                ),

            "warning_count":
                (
                    integrity[
                        "warning_count"
                    ]
                    if integrity
                    else total_warnings
                ),

            "risk_label":
                (
                    integrity["risk_label"]
                    if integrity
                    else "Unknown"
                ),

            "generated_at":
                (
                    integrity["generated_at"]
                    if integrity
                    else None
                )

        }


        # ==================================================
        # RESPONSE
        # ==================================================

        return jsonify({

            "success": True,

            "candidate":
                dict(candidate),

            "exam":
                dict(exam),

            "attempt":
                (
                    dict(attempt)
                    if attempt
                    else None
                ),

            "integrity":
                integrity_data,

            "breakdown":
                breakdown,

            "violations":
                violations,

            "evidence_count":
                evidence_count,

            "total_warnings":
                total_warnings

        })


    except Exception as error:

        print(
            "Candidate integrity error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


    finally:

        conn.close()

@integrity_bp.route(
    "/api/integrity/exams",
    methods=["GET"]
)
def get_integrity_exams():

    conn = get_db()

    try:

        exams = conn.execute(
            """
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
                end_time,
                created_at

            FROM Exams

            ORDER BY id DESC
            """
        ).fetchall()


        exam_list = []

        for exam in exams:

            exam_list.append({

                "id":
                    exam["id"],

                "title":
                    exam["title"],

                "topic":
                    exam["topic"],

                "difficulty":
                    exam["difficulty"],

                "description":
                    exam["description"],

                "duration":
                    exam["duration"],

                "total_questions":
                    exam["total_questions"],

                "total_marks":
                    exam["total_marks"],

                "start_time":
                    exam["start_time"],

                "end_time":
                    exam["end_time"],

                "created_at":
                    exam["created_at"]

            })


        return jsonify({

            "success": True,

            "count":
                len(exam_list),

            "exams":
                exam_list

        }), 200


    except sqlite3.Error as error:

        print(
            "Analytics exam query error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                str(error),

            "exams": []

        }), 500


    finally:

        conn.close()


# ==========================================================
# GET ONE EXAM
# ==========================================================

@integrity_bp.route(
    "/api/integrity/exams/<int:exam_id>",
    methods=["GET", "DELETE"]
)
def get_integrity_exam(
    exam_id
):
    conn = get_db()
    try:
        if request.method == "DELETE":
            exam = conn.execute("SELECT id FROM Exams WHERE id = ?", (exam_id,)).fetchone()
            if not exam:
                return jsonify({"success": False, "message": "Examination not found."}), 404
            conn.execute("DELETE FROM Exams WHERE id = ?", (exam_id,))
            conn.commit()
            return jsonify({"success": True, "message": "Examination deleted successfully."}), 200

        exam = conn.execute(
            """
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
                end_time,
                created_at

            FROM Exams

            WHERE id = ?
            """,
            (exam_id,)
        ).fetchone()


        if exam is None:

            return jsonify({

                "success": False,

                "message":
                    "Exam not found"

            }), 404


        return jsonify({

            "success": True,

            "exam": {

                "id":
                    exam["id"],

                "title":
                    exam["title"],

                "topic":
                    exam["topic"],

                "difficulty":
                    exam["difficulty"],

                "description":
                    exam["description"],

                "duration":
                    exam["duration"],

                "total_questions":
                    exam["total_questions"],

                "total_marks":
                    exam["total_marks"],

                "start_time":
                    exam["start_time"],

                "end_time":
                    exam["end_time"],

                "created_at":
                    exam["created_at"]

            }

        }), 200


    except sqlite3.Error as error:

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


    finally:

        conn.close()

@integrity_bp.route(
    "/api/integrity/overview",
    methods=["GET"]
)
def get_integrity_overview():

    exam_id = request.args.get(
        "exam_id",
        type=int
    )

    if exam_id is None:

        return jsonify({
            "success": False,
            "message": "exam_id is required"
        }), 400


    conn = get_db()

    try:

        # ==================================================
        # EXAM
        # ==================================================

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
                end_time,
                created_at
            FROM Exams
            WHERE id = ?
        """, (exam_id,)).fetchone()


        if exam is None:

            return jsonify({
                "success": False,
                "message": "Exam not found"
            }), 404


        # ==================================================
        # ATTEMPTS
        # ==================================================

        attempts = conn.execute("""
            SELECT
                ea.id,
                ea.candidate_id,
                ea.score,
                ea.total_questions,
                ea.percentage,
                ea.result,
                ea.submitted_at,

                c.name,
                c.email

            FROM ExamAttempts ea

            INNER JOIN Candidates c
                ON c.id = ea.candidate_id

            WHERE ea.exam_id = ?

            ORDER BY ea.submitted_at DESC
        """, (exam_id,)).fetchall()


        # ==================================================
        # INTEGRITY SCORES
        # ==================================================

        integrity_rows = conn.execute("""
            SELECT
                id,
                candidate_id,
                exam_id,
                integrity_score,
                face_presence_ratio,
                warning_count,
                risk_label,
                generated_at

            FROM IntegrityScores

            WHERE exam_id = ?

            ORDER BY generated_at DESC
        """, (exam_id,)).fetchall()


        # ==================================================
        # VIOLATIONS
        # ==================================================

        violations = conn.execute("""
            SELECT
                id,
                candidate_id,
                exam_id,
                violation_type,
                evidence_image,
                face_count,
                violation_time

            FROM ViolationLogs

            WHERE exam_id = ?

            ORDER BY violation_time DESC
        """, (exam_id,)).fetchall()
                # ==================================================
        # BEHAVIOURAL EVENT CLASSIFICATION
        # ==================================================

        events = {
            "tab_switches": 0,
            "focus_loss": 0,
            "face_absence": 0,
            "fullscreen_exit": 0,
            "copy_paste": 0,
            "screenshots": 0,
            "right_click": 0,
            "identity_mismatch": 0,
            "multiple_faces": 0,
            "other": 0
        }


        def classify_event(violation_type):

            text = (
                str(violation_type or "")
                .strip()
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
            )


            # ----------------------------------------------
            # TAB SWITCH
            # ----------------------------------------------

            if (
                "tab" in text
                or "tabswitch" in text
                or "tab_switch" in text
                or "browser_tab" in text
            ):
                return "tab_switches"


            # ----------------------------------------------
            # FOCUS LOSS
            # ----------------------------------------------

            if (
                "focus" in text
                or "blur" in text
                or "window_lost_focus" in text
                or "window_focus_loss" in text
                or "lost_focus" in text
            ):
                return "focus_loss"


            # ----------------------------------------------
            # FACE ABSENCE
            # ----------------------------------------------

            if (
                "no_face" in text
                or "noface" in text
                or "no_face_detected" in text
                or "face_absent" in text
                or "face_absence" in text
                or "face_missing" in text
                or "face_not_detected" in text
                or "no_face_detected" in text
            ):
                return "face_absence"


            # ----------------------------------------------
            # MULTIPLE FACES
            # ----------------------------------------------

            if (
                "multiple_face" in text
                or "multiple_faces" in text
                or "more_than_one_face" in text
                or "multiple_person" in text
            ):
                return "multiple_faces"


            # ----------------------------------------------
            # IDENTITY MISMATCH
            # ----------------------------------------------

            if (
                "identity" in text
                or "mismatch" in text
                or "unknown_face" in text
                or "unknown_person" in text
                or "verification_failed" in text
                or "face_verification_failed" in text
            ):
                return "identity_mismatch"


            # ----------------------------------------------
            # FULLSCREEN
            # ----------------------------------------------

            if (
                "fullscreen" in text
                or "full_screen" in text
                or "fullscreen_exit" in text
                or "fullscreen_exited" in text
            ):
                return "fullscreen_exit"


            # ----------------------------------------------
            # COPY / PASTE
            # ----------------------------------------------

            if (
                "copy" in text
                or "paste" in text
                or "cut" in text
                or "clipboard" in text
            ):
                return "copy_paste"


            # ----------------------------------------------
            # SCREENSHOT
            # ----------------------------------------------

            if (
                "screenshot" in text
                or "screen_shot" in text
                or "screen_capture" in text
                or "print_screen" in text
                or "printscreen" in text
            ):
                return "screenshots"


            # ----------------------------------------------
            # RIGHT CLICK
            # ----------------------------------------------

            if (
                "right_click" in text
                or "rightclick" in text
                or "context_menu" in text
            ):
                return "right_click"


            # ----------------------------------------------
            # OTHER
            # ----------------------------------------------

            return "other"


        # ==================================================
        # COUNT EVERY VIOLATION
        # ==================================================

        for row in violations:

            category = classify_event(
                row["violation_type"]
            )

            events[category] += 1


        # ==================================================
        # TOTAL EVENTS
        # ==================================================

        total_event_count = sum(
            events.values()
        )


        print(
            "EXAM EVENT COUNTS:",
            events
        )

        print(
            "TOTAL EVENTS:",
            total_event_count
        )


        # ==================================================
        # SUMMARY
        # ==================================================

        candidate_count = len(attempts)

        if candidate_count > 0:

            average_score = round(
                sum(
                    float(
                        row["percentage"] or 0
                    )
                    for row in attempts
                ) / candidate_count,
                2
            )

        else:

            average_score = 0


        total_violations = len(
            violations
        )


        total_evidence = sum(
            1
            for row in violations
            if row["evidence_image"]
        )


        # ==================================================
        # RISK DISTRIBUTION
        # ==================================================

        low = 0
        medium = 0
        high = 0


        for row in integrity_rows:

            risk = (
                row["risk_label"]
                or ""
            ).strip().lower()


            if risk == "low":

                low += 1

            elif risk == "medium":

                medium += 1

            elif risk == "high":

                high += 1


        # ==================================================
        # SCORE DISTRIBUTION
        # ==================================================

        score_distribution = [

            float(row["integrity_score"])

            for row in integrity_rows

            if row["integrity_score"] is not None

        ]


        # ==================================================
        # CANDIDATE ANALYSIS
        # ==================================================

        candidates = []


        for attempt in attempts:

            candidate_id = (
                attempt["candidate_id"]
            )


            integrity = None


            for row in integrity_rows:

                if (
                    row["candidate_id"]
                    == candidate_id
                ):

                    integrity = row

                    break


            candidate_violations = [

                row

                for row in violations

                if (
                    row["candidate_id"]
                    == candidate_id
                )

            ]


            evidence_count = sum(

                1

                for row
                in candidate_violations

                if row["evidence_image"]

            )


            candidates.append({

                "candidate_id":
                    candidate_id,

                "name":
                    attempt["name"],

                "email":
                    attempt["email"],

                "exam_score":
                    attempt["score"],

                "total_questions":
                    attempt["total_questions"],

                "percentage":
                    attempt["percentage"],

                "result":
                    attempt["result"],

                "submitted_at":
                    attempt["submitted_at"],

                "integrity_score":
                    (
                        integrity["integrity_score"]
                        if integrity
                        else None
                    ),

                "face_presence_ratio":
                    (
                        integrity["face_presence_ratio"]
                        if integrity
                        else None
                    ),

                "warning_count":
                    (
                        integrity["warning_count"]
                        if integrity
                        else len(
                            candidate_violations
                        )
                    ),

                "risk_label":
                    (
                        integrity["risk_label"]
                        if integrity
                        else "Unknown"
                    ),

                "violations":
                    len(candidate_violations),

                "evidence":
                    evidence_count

            })


        # ==================================================
        # FINAL RESPONSE
        # ==================================================

            return jsonify({

            "success": True,

            "exam":
                dict(exam),


            # ==================================================
            # SUMMARY
            # ==================================================

            "summary": {

                "candidates":
                    candidate_count,

                "average_score":
                    average_score,

                "high_risk":
                    high,

                "violations":
                    total_violations,

                "evidence":
                    total_evidence

            },


            # ==================================================
            # BEHAVIOURAL EVENTS
            # ==================================================

            "events": {

                "tab_switches":
                    events["tab_switches"],

                "focus_loss":
                    events["focus_loss"],

                "face_absence":
                    events["face_absence"],

                "fullscreen_exit":
                    events["fullscreen_exit"],

                "copy_paste":
                    events["copy_paste"],

                "screenshots":
                    events["screenshots"],

                "right_click":
                    events["right_click"],

                "identity_mismatch":
                    events["identity_mismatch"],

                "multiple_faces":
                    events["multiple_faces"],

                "other":
                    events["other"]

            },


            # ==================================================
            # TOTAL VIOLATIONS
            # ==================================================

            "total_violations":
                total_violations,


            # ==================================================
            # RISK
            # ==================================================

            "risk_distribution": {

                "low":
                    low,

                "medium":
                    medium,

                "high":
                    high

            },


            # ==================================================
            # SCORE DISTRIBUTION
            # ==================================================

            "score_distribution":
                score_distribution,


            # ==================================================
            # CANDIDATES
            # ==================================================

            "candidates":
                candidates

        })

    except Exception as error:

        print(
            "Integrity overview error:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 500


    finally:

        conn.close()

@integrity_bp.route("/api/integrity/evidence", methods=["GET"])
def get_integrity_evidence():

    evidence_path = request.args.get("path")

    if not evidence_path:
        return jsonify({
            "success": False,
            "error": "Evidence path is required"
        }), 400

    try:

        # --------------------------------------------------
        # Project root
        # --------------------------------------------------

        BASE_DIR = Path(__file__).resolve().parent.parent

        # --------------------------------------------------
        # Normalize Windows / Linux path separators
        # --------------------------------------------------

        evidence_path = evidence_path.replace("\\", "/")

        # Remove leading slash if present
        evidence_path = evidence_path.lstrip("/")

        # --------------------------------------------------
        # Build absolute path
        # --------------------------------------------------

        file_path = (
            BASE_DIR / evidence_path
        ).resolve()

        # --------------------------------------------------
        # Security check
        # Prevent ../ path traversal
        # --------------------------------------------------

        evidence_root = (
            BASE_DIR / "evidence"
        ).resolve()

        try:

            file_path.relative_to(
                evidence_root
            )

        except ValueError:

            return jsonify({
                "success": False,
                "error": "Invalid evidence path"
            }), 403

        # --------------------------------------------------
        # Check file
        # --------------------------------------------------

        if not file_path.exists():

            return jsonify({
                "success": False,
                "error": "Evidence file not found",
                "path": evidence_path,
                "resolved_path": str(file_path)
            }), 404

        # --------------------------------------------------
        # Make sure it is a file
        # --------------------------------------------------

        if not file_path.is_file():

            return jsonify({
                "success": False,
                "error": "Evidence path is not a file"
            }), 400

        # --------------------------------------------------
        # Send image
        # --------------------------------------------------

        return send_file(
            file_path,
            mimetype="image/jpeg"
        )

    except Exception as error:

        print(
            "Evidence error:",
            error
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

# ==========================================================
# LANGCHAIN AI BEHAVIOURAL REPORT
# ==========================================================

@integrity_bp.route(
    "/api/integrity/ai-report",
    methods=["POST"]
)
def generate_ai_report():

    print("=" * 70)
    print(">>> AI REPORT REQUEST RECEIVED")
    print("=" * 70)

    data = request.get_json(silent=True)

    print("REQUEST DATA:", data)

    if not data:

        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400

    candidate_id = data.get("candidate_id")
    exam_id = data.get("exam_id")

    if candidate_id is None or exam_id is None:

        return jsonify({
            "success": False,
            "error":
                "candidate_id and exam_id are required"
        }), 400

    conn = get_db()

    try:

        # ======================================================
        # 1. CANDIDATE
        # ======================================================

        candidate = conn.execute("""
            SELECT
                id,
                name,
                email
            FROM Candidates
            WHERE id = ?
        """, (
            candidate_id,
        )).fetchone()

        if candidate is None:

            return jsonify({
                "success": False,
                "error": "Candidate not found"
            }), 404


        # ======================================================
        # 2. EXAM
        # ======================================================

        exam = conn.execute("""
            SELECT
                id,
                title,
                topic,
                difficulty,
                description,
                duration,
                total_questions,
                total_marks
            FROM Exams
            WHERE id = ?
        """, (
            exam_id,
        )).fetchone()

        if exam is None:

            return jsonify({
                "success": False,
                "error": "Exam not found"
            }), 404


        # ======================================================
        # 3. EXAM ATTEMPT
        # ======================================================

        attempt = conn.execute("""
            SELECT
                score,
                total_questions,
                percentage,
                result,
                submitted_at
            FROM ExamAttempts
            WHERE candidate_id = ?
              AND exam_id = ?
            LIMIT 1
        """, (
            candidate_id,
            exam_id
        )).fetchone()


        if attempt:

            exam_result = dict(attempt)

        else:

            exam_result = {

                "score": 0,

                "total_questions":
                    exam["total_questions"],

                "percentage": 0,

                "result":
                    "NOT SUBMITTED",

                "submitted_at":
                    None
            }


        # ======================================================
        # 4. INTEGRITY SCORE
        # ======================================================

        integrity_row = conn.execute("""
            SELECT
                integrity_score,
                face_presence_ratio,
                warning_count,
                risk_label,
                generated_at
            FROM IntegrityScores
            WHERE candidate_id = ?
              AND exam_id = ?
            LIMIT 1
        """, (
            candidate_id,
            exam_id
        )).fetchone()


        if integrity_row:

            integrity = dict(
                integrity_row
            )

        else:

            # No integrity score generated yet
            integrity = {

                "integrity_score": 0,

                "face_presence_ratio": 0,

                "warning_count": 0,

                "risk_label": "Unknown",

                "generated_at": None
            }


        # ======================================================
        # 5. VIOLATIONS
        # ======================================================

        violation_rows = conn.execute("""
            SELECT
                violation_type
            FROM ViolationLogs
            WHERE candidate_id = ?
              AND exam_id = ?
            ORDER BY violation_time ASC
        """, (
            candidate_id,
            exam_id
        )).fetchall()


        violations = {}


        for row in violation_rows:

            violation_type = (
                row["violation_type"]
                or "UNKNOWN"
            )

            violation_type = (
                violation_type
                .strip()
                .upper()
            )


            violations[
                violation_type
            ] = violations.get(
                violation_type,
                0
            ) + 1


        # ======================================================
        # 6. PREPARE DATA FOR LANGCHAIN
        # ======================================================

        candidate_data = dict(
            candidate
        )

        exam_data = dict(
            exam
        )


        print("=" * 70)
        print("LANGCHAIN INPUT")
        print("=" * 70)

        print(
            "Candidate:",
            candidate_data
        )

        print(
            "Exam:",
            exam_data
        )

        print(
            "Exam Result:",
            exam_result
        )

        print(
            "Integrity:",
            integrity
        )

        print(
            "Violations:",
            violations
        )


        # ======================================================
        # 7. GENERATE AI ASSESSMENT
        # ======================================================

        assessment = (
            generate_behavioural_assessment(

                candidate=
                    candidate_data,

                exam=
                    exam_data,

                exam_result=
                    exam_result,

                integrity=
                    integrity,

                violations=
                    violations

            )
        )


        # ======================================================
        # 8. RETURN RESULT
        # ======================================================

        return jsonify({

            "success": True,

            "candidate_id":
                candidate_id,

            "exam_id":
                exam_id,

            "risk":
                integrity[
                    "risk_label"
                ],

            "integrity_score":
                integrity[
                    "integrity_score"
                ],

            "face_presence_ratio":
                integrity[
                    "face_presence_ratio"
                ],

            "warning_count":
                integrity[
                    "warning_count"
                ],

            "violations":
                violations,

            "assessment":
                assessment

        }), 200


    except Exception as error:

        print("=" * 70)
        print("AI REPORT ERROR")
        print("=" * 70)

        print(
            repr(error)
        )

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


    finally:

        conn.close()

@integrity_bp.route(
    "/api/integrity/exam-ai-report",
    methods=["POST"]
)
def generate_exam_ai_report():

    try:

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "success": False,
                "error":
                    "Request body is required"
            }), 400


        exam_id = data.get(
            "exam_id"
        )


        if exam_id is None:

            return jsonify({
                "success": False,
                "error":
                    "exam_id is required"
            }), 400


        conn = get_db()


        try:

            # ==================================================
            # EXAM
            # ==================================================

            exam = conn.execute("""
                SELECT
                    id,
                    title,
                    topic,
                    difficulty,
                    description,
                    duration,
                    total_questions,
                    total_marks
                FROM Exams
                WHERE id = ?
            """, (
                exam_id,
            )).fetchone()


            if not exam:

                return jsonify({
                    "success": False,
                    "error":
                        "Exam not found"
                }), 404


            # ==================================================
            # EXAM ATTEMPTS
            # ==================================================

            attempts = conn.execute("""
                SELECT
                    candidate_id,
                    score,
                    total_questions,
                    percentage,
                    result
                FROM ExamAttempts
                WHERE exam_id = ?
            """, (
                exam_id,
            )).fetchall()


            # ==================================================
            # INTEGRITY SCORES
            # ==================================================

            integrity_rows = conn.execute("""
                SELECT
                    candidate_id,
                    integrity_score,
                    face_presence_ratio,
                    warning_count,
                    risk_label
                FROM IntegrityScores
                WHERE exam_id = ?
            """, (
                exam_id,
            )).fetchall()


            # ==================================================
            # VIOLATIONS
            # ==================================================

            violation_rows = conn.execute("""
                SELECT
                    candidate_id,
                    violation_type
                FROM ViolationLogs
                WHERE exam_id = ?
            """, (
                exam_id,
            )).fetchall()


            # ==================================================
            # BASIC STATISTICS
            # ==================================================

            candidate_count =len(attempts)


            scores = [
                float(
                    row["percentage"]
                    or 0
                )
                for row in attempts
            ]


            average_score = (
                sum(scores) /
                len(scores)
                if scores
                else 0
            )


            # ==================================================
            # INTEGRITY STATISTICS
            # ==================================================

            integrity_scores = [

                float(
                    row["integrity_score"]
                    or 0
                )

                for row in integrity_rows

            ]


            average_integrity = (

                sum(integrity_scores) /
                len(integrity_scores)

                if integrity_scores

                else 0

            )


            # ==================================================
            # FACE PRESENCE
            # ==================================================

            face_ratios = [

                float(
                    row[
                        "face_presence_ratio"
                    ]
                    or 0
                )

                for row in integrity_rows

            ]


            average_face_presence = (

                sum(face_ratios) /
                len(face_ratios)

                if face_ratios

                else 0

            )


            # ==================================================
            # RISK DISTRIBUTION
            # ==================================================

            risk_distribution = {

                "Low": 0,

                "Medium": 0,

                "High": 0

            }


            for row in integrity_rows:

                risk = (
                    row["risk_label"]
                    or "Unknown"
                )


                normalized =risk.strip().title()


                if normalized in \
                    risk_distribution:

                    risk_distribution[
                        normalized
                    ] += 1


            # ==================================================
            # VIOLATION BREAKDOWN
            # ==================================================

            violations = {}


            for row in violation_rows:

                violation =row["violation_type"]


                violations[
                    violation
                ] = (

                    violations.get(
                        violation,
                        0
                    ) + 1

                )


            # ==================================================
            # CANDIDATE SUMMARY
            # ==================================================

            candidate_summary = []


            for row in integrity_rows:

                candidate_id =row["candidate_id"]


                candidate = conn.execute("""
                        SELECT
                            id,
                            name
                        FROM Candidates
                        WHERE id = ?
                    """, (
                        candidate_id,
                    )).fetchone()


                attempt =conn.execute("""
                        SELECT
                            score,
                            percentage,
                            result
                        FROM ExamAttempts
                        WHERE candidate_id = ?
                        AND exam_id = ?
                    """, (
                        candidate_id,
                        exam_id
                    )).fetchone()


                candidate_summary.append({

                    "candidate_id":
                        candidate_id,

                    "name":
                        candidate["name"]
                        if candidate
                        else "Unknown",

                    "score":
                        attempt["score"]
                        if attempt
                        else 0,

                    "percentage":
                        attempt["percentage"]
                        if attempt
                        else 0,

                    "integrity_score":
                        row[
                            "integrity_score"
                        ],

                    "face_presence":
                        row[
                            "face_presence_ratio"
                        ],

                    "warnings":
                        row[
                            "warning_count"
                        ],

                    "risk":
                        row[
                            "risk_label"
                        ]

                })


            # ==================================================
            # STATISTICS OBJECT
            # ==================================================

            statistics = {

                "candidates":
                    candidate_count,

                "average_score":
                    round(
                        average_score,
                        2
                    ),

                "average_integrity_score":
                    round(
                        average_integrity,
                        2
                    ),

                "average_face_presence":
                    round(
                        average_face_presence,
                        4
                    ),

                "total_violations":
                    len(
                        violation_rows
                    ),

                "evidence_count":
                    sum(
                        1
                        for row in violation_rows
                    )

            }


            # ==================================================
            # GENERATE AI REPORT
            # ==================================================

            report = generate_exam_behavioural_assessment(

                    exam=dict(exam),

                    statistics=statistics,

                    violations=violations,

                    risk_distribution=
                        risk_distribution,

                    candidates=
                        candidate_summary

                )


            # ==================================================
            # RESPONSE
            # ==================================================

            return jsonify({

                "success":
                    True,

                "exam":
                    dict(exam),

                "statistics":
                    statistics,

                "violations":
                    violations,

                "risk_distribution":
                    risk_distribution,

                "report":
                    report

            }), 200


        finally:

            conn.close()


    except Exception as error:

        print(
            "EXAM AI REPORT ERROR:",
            repr(error)
        )


        return jsonify({

            "success":
                False,

            "error":
                str(error)

        }), 500     

@integrity_bp.route(
    "/api/integrity/data-science",
    methods=["GET"]
)
def get_data_science_analytics():

    exam_id = request.args.get(
        "exam_id",
        type=int
    )


    if exam_id is None:

        return jsonify({
            "success": False,
            "error":
                "exam_id is required"
        }), 400


    try:

        analytics = (
            generate_analytics(
                exam_id
            )
        )


        return jsonify({

            "success": True,

            "exam_id":
                exam_id,

            **analytics

        })


    except Exception as error:

        print(
            "DATA SCIENCE ERROR:",
            repr(error)
        )


        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500