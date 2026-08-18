from pathlib import Path
import sqlite3


# ==========================================================
# DATABASE
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==========================================================
# VIOLATION WEIGHTS
# ==========================================================

VIOLATION_WEIGHTS = {

    "tab": 5,

    "focus": 4,

    "fullscreen": 5,

    "no_face": 6,

    "no face": 6,

    "unknown_face": 8,

    "identity mismatch": 8,

    "multiple_faces": 10,

    "copy": 7,

    "paste": 7,

    "cut": 7,

    "right-click": 3
}


# ==========================================================
# GET VIOLATION WEIGHT
# ==========================================================

def get_violation_weight(violation_type):

    text = (
        violation_type or ""
    ).strip().lower()

    for keyword, weight in VIOLATION_WEIGHTS.items():

        if keyword in text:
            return weight

    return 3


# ==========================================================
# CALCULATE INTEGRITY SCORE
# ==========================================================

def calculate_integrity_score(violations):

    score = 100

    warning_count = len(violations)

    event_breakdown = {}

    for violation in violations:

        violation_type = (
            violation["violation_type"]
            or "Unknown"
        )

        weight = get_violation_weight(
            violation_type
        )

        score -= weight

        event_breakdown[violation_type] = (
            event_breakdown.get(
                violation_type,
                0
            ) + 1
        )

    score = max(
        0,
        min(100, score)
    )

    # ------------------------------------------------------
    # RISK LABEL
    # ------------------------------------------------------

    if score >= 80:

        risk_label = "Low"

    elif score >= 60:

        risk_label = "Medium"

    else:

        risk_label = "High"

    return {
        "score": score,
        "warning_count": warning_count,
        "risk": risk_label,
        "event_breakdown": event_breakdown
    }


# ==========================================================
# SAVE INTEGRITY SCORE
# ==========================================================

def save_integrity_score(
    candidate_id,
    exam_id
):

    conn = get_db()

    try:

        # --------------------------------------------------
        # GET VIOLATIONS
        # --------------------------------------------------

        violations = conn.execute(
            """
            SELECT
                id,
                violation_type,
                evidence_image,
                face_count,
                violation_time

            FROM ViolationLogs

            WHERE candidate_id = ?
            AND exam_id = ?

            ORDER BY violation_time
            """,
            (
                candidate_id,
                exam_id
            )
        ).fetchall()


        # --------------------------------------------------
        # CALCULATE SCORE
        # --------------------------------------------------

        result = calculate_integrity_score(
            violations
        )

        integrity_score = result["score"]

        warning_count = result["warning_count"]

        risk_label = result["risk"]


        # --------------------------------------------------
        # FACE PRESENCE
        # --------------------------------------------------
        #
        # Your current database stores face violations,
        # but it does NOT store every successful face check.
        #
        # Therefore a true face-presence percentage cannot
        # yet be calculated.
        #
        # We use an event-derived value for now.
        #
        # This will be replaced when FaceMonitoringLogs
        # are added.
        # --------------------------------------------------

        face_events = 0

        for violation in violations:

            violation_type = (
                violation["violation_type"]
                or ""
            ).lower()

            if (
                "no_face" in violation_type
                or
                "no face" in violation_type
                or
                "unknown_face" in violation_type
                or
                "identity mismatch" in violation_type
                or
                "multiple_faces" in violation_type
            ):

                face_events += 1


        # --------------------------------------------------
        # FACE PRESENCE PROXY
        # --------------------------------------------------

        if face_events == 0:

            face_presence_ratio = 1.0

        else:

            face_presence_ratio = max(
                0.0,
                1.0 - (
                    face_events /
                    max(10, warning_count * 2)
                )
            )


        face_presence_ratio = round(
            face_presence_ratio,
            4
        )


        # --------------------------------------------------
        # SAVE INTO IntegrityScores
        # --------------------------------------------------

        conn.execute(
            """
            INSERT INTO IntegrityScores
            (
                candidate_id,
                exam_id,
                integrity_score,
                face_presence_ratio,
                warning_count,
                risk_label
            )

            VALUES
            (
                ?, ?, ?, ?, ?, ?
            )

            ON CONFLICT(candidate_id, exam_id)

            DO UPDATE SET

                integrity_score =
                    excluded.integrity_score,

                face_presence_ratio =
                    excluded.face_presence_ratio,

                warning_count =
                    excluded.warning_count,

                risk_label =
                    excluded.risk_label,

                generated_at =
                    CURRENT_TIMESTAMP
            """,
            (
                candidate_id,
                exam_id,
                integrity_score,
                face_presence_ratio,
                warning_count,
                risk_label
            )
        )


        conn.commit()


        print("=" * 60)
        print("INTEGRITY SCORE GENERATED")
        print("Candidate ID :", candidate_id)
        print("Exam ID      :", exam_id)
        print("Score        :", integrity_score)
        print("Face Ratio   :", face_presence_ratio)
        print("Warnings     :", warning_count)
        print("Risk         :", risk_label)
        print("=" * 60)


        return {

            "score":
                integrity_score,

            "ratio":
                face_presence_ratio,

            "warnings":
                warning_count,

            "risk":
                risk_label,

            "events":
                result["event_breakdown"]

        }


    except Exception as error:

        conn.rollback()

        print(
            "Integrity scoring error:",
            error
        )

        raise

    finally:

        conn.close()