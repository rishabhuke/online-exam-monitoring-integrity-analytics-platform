import math
from collections import Counter

import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


# ============================================================
# VIOLATION WEIGHTS
# ============================================================

VIOLATION_WEIGHTS = {
    "TAB_SWITCH": 4,
    "FOCUS_LOSS": 3,
    "FACE_ABSENCE": 4,
    "MULTIPLE_FACES": 8,
    "SCREENSHOT": 6,
    "FULLSCREEN_EXIT": 5,
    "COPY_PASTE": 6,
    "RIGHT_CLICK": 2,
    "IDENTITY_MISMATCH": 10,
    "OTHER": 3
}


# ============================================================
# NORMALIZE VIOLATION TYPE
# ============================================================

def normalize_violation_type(value):

    if value is None:
        return "OTHER"

    text = str(value).strip().upper()

    text = text.replace("-", "_")
    text = text.replace(" ", "_")

    if "TAB" in text:
        return "TAB_SWITCH"

    if "FOCUS" in text:
        return "FOCUS_LOSS"

    if (
        "NO_FACE" in text
        or "FACE_ABSENCE" in text
        or "FACE_MISSING" in text
    ):
        return "FACE_ABSENCE"

    if (
        "MULTIPLE_FACE" in text
        or "MULTI_FACE" in text
        or "MORE_THAN_ONE_FACE" in text
    ):
        return "MULTIPLE_FACES"

    if "SCREENSHOT" in text:
        return "SCREENSHOT"

    if "FULLSCREEN" in text:
        return "FULLSCREEN_EXIT"

    if (
        "COPY" in text
        or "PASTE" in text
        or "CLIPBOARD" in text
    ):
        return "COPY_PASTE"

    if "RIGHT_CLICK" in text:
        return "RIGHT_CLICK"

    if (
        "IDENTITY" in text
        or "MISMATCH" in text
    ):
        return "IDENTITY_MISMATCH"

    return "OTHER"


# ============================================================
# EVENT WEIGHT
# ============================================================

def get_violation_weight(violation_type):

    normalized = normalize_violation_type(
        violation_type
    )

    return VIOLATION_WEIGHTS.get(
        normalized,
        VIOLATION_WEIGHTS["OTHER"]
    )


# ============================================================
# SEVERITY SCORE
# ============================================================

def calculate_severity_score(events):

    if not events:
        return 0.0

    total = 0

    for event in events:

        violation_type = event.get(
            "violation_type"
        )

        total += get_violation_weight(
            violation_type
        )

    return round(
        float(total),
        2
    )


# ============================================================
# FACE PRESENCE
# ============================================================

def calculate_face_presence(events):

    if not events:
        return 1.0

    face_events = 0
    absent_events = 0
    multiple_face_events = 0

    for event in events:

        violation_type = normalize_violation_type(
            event.get("violation_type")
        )

        face_count = event.get(
            "face_count",
            0
        )

        try:
            face_count = int(
                face_count or 0
            )
        except Exception:
            face_count = 0

        if violation_type == "FACE_ABSENCE":
            absent_events += 1

        elif violation_type == "MULTIPLE_FACES":
            multiple_face_events += 1

        elif face_count >= 1:
            face_events += 1

    total_face_related = (
        face_events
        + absent_events
        + multiple_face_events
    )

    if total_face_related == 0:
        return 1.0

    presence = (
        face_events
        / total_face_related
    )

    return max(
        0.0,
        min(
            1.0,
            presence
        )
    )


# ============================================================
# INTEGRITY SCORE
# ============================================================

def calculate_integrity_score(
    events,
    face_presence_ratio,
    duration_minutes
):

    duration_minutes = max(
        float(duration_minutes or 1),
        1.0
    )

    severity_penalty = calculate_severity_score(
        events
    )

    event_count = len(events)

    # Event frequency normalized by duration.
    event_frequency = (
        event_count
        / duration_minutes
    )

    # Keep frequency penalty bounded.
    frequency_penalty = min(
        event_frequency * 10,
        25
    )

    # Severity penalty.
    severity_penalty_bounded = min(
        severity_penalty,
        50
    )

    # Face penalty.
    face_penalty = (
        (1.0 - face_presence_ratio)
        * 25
    )

    total_penalty = (
        frequency_penalty
        + severity_penalty_bounded
        + face_penalty
    )

    score = 100 - total_penalty

    score = max(
        0,
        min(
            100,
            score
        )
    )

    if score >= 80:
        risk = "Low"

    elif score >= 60:
        risk = "Medium"

    else:
        risk = "High"

    return {
        "score": round(score, 2),
        "risk": risk,
        "severity_penalty": round(
            severity_penalty,
            2
        ),
        "event_penalty": round(
            frequency_penalty,
            2
        ),
        "face_penalty": round(
            face_penalty,
            2
        )
    }


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

def build_score_distribution(scores):

    labels = [
        "0-10",
        "10-20",
        "20-30",
        "30-40",
        "40-50",
        "50-60",
        "60-70",
        "70-80",
        "80-90",
        "90-100"
    ]

    values = [
        0
        for _ in labels
    ]

    for score in scores:

        try:
            score = float(score)
        except Exception:
            continue

        if score >= 100:
            index = 9

        else:
            index = int(
                score // 10
            )

            index = max(
                0,
                min(
                    9,
                    index
                )
            )

        values[index] += 1

    return {
        "labels": labels,
        "values": values
    }


# ============================================================
# RISK DISTRIBUTION
# ============================================================

def build_risk_distribution(
    session_results
):

    low = 0
    medium = 0
    high = 0

    for session in session_results:

        risk = str(
            session.get(
                "risk",
                ""
            )
        ).lower()

        if risk == "low":
            low += 1

        elif risk == "medium":
            medium += 1

        elif risk == "high":
            high += 1

    return {
        "low": low,
        "medium": medium,
        "high": high
    }


# ============================================================
# VIOLATION HEATMAP
# ============================================================

def build_violation_heatmap(events):

    event_types = [
        "TAB_SWITCH",
        "FOCUS_LOSS",
        "FACE_ABSENCE",
        "MULTIPLE_FACES",
        "SCREENSHOT",
        "FULLSCREEN_EXIT",
        "COPY_PASTE",
        "RIGHT_CLICK",
        "IDENTITY_MISMATCH",
        "OTHER"
    ]

    matrix = {
        event_type: [
            0
            for _ in range(24)
        ]
        for event_type in event_types
    }

    for event in events:

        event_type = normalize_violation_type(
            event.get(
                "violation_type"
            )
        )

        timestamp = event.get(
            "violation_time"
        )

        if not timestamp:
            continue

        try:

            dt = pd.to_datetime(
                timestamp,
                errors="coerce"
            )

            if pd.isna(dt):
                continue

            hour = int(
                dt.hour
            )

            matrix[event_type][hour] += 1

        except Exception:
            continue

    event_rows = []

    for event_type in event_types:

        event_rows.append({
            "event": event_type,
            "values": matrix[event_type]
        })

    return {
        "hours": list(
            range(24)
        ),
        "events": event_rows
    }


# ============================================================
# K-MEANS CLUSTERING
# ============================================================

def perform_behavioral_clustering(
    session_results
):

    if len(session_results) < 3:
        return []

    df = pd.DataFrame(
        session_results
    )

    feature_columns = [
        "total_events",
        "severity_score",
        "face_presence_ratio",
        "integrity_score"
    ]

    for column in feature_columns:

        if column not in df.columns:
            df[column] = 0

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

    features = df[
        feature_columns
    ]

    scaler = StandardScaler()

    scaled = scaler.fit_transform(
        features
    )

    number_of_clusters = min(
        3,
        len(df)
    )

    model = KMeans(
        n_clusters=number_of_clusters,
        random_state=42,
        n_init=10
    )

    df["cluster"] = model.fit_predict(
        scaled
    )

    result = []

    for cluster_id in sorted(
        df["cluster"].unique()
    ):

        cluster_df = df[
            df["cluster"]
            == cluster_id
        ]

        average_score = float(
            cluster_df[
                "integrity_score"
            ].mean()
        )

        average_events = float(
            cluster_df[
                "total_events"
            ].mean()
        )

        average_severity = float(
            cluster_df[
                "severity_score"
            ].mean()
        )

        average_face = float(
            cluster_df[
                "face_presence_ratio"
            ].mean()
        )

        if average_score >= 80:

            behavior = (
                "Low Risk Behaviour"
            )

        elif average_score >= 60:

            behavior = (
                "Moderate Risk Behaviour"
            )

        else:

            behavior = (
                "High Risk Behaviour"
            )

        result.append({

            "cluster": int(
                cluster_id
            ),

            "count": int(
                len(cluster_df)
            ),

            "average_score": round(
                average_score,
                2
            ),

            "average_events": round(
                average_events,
                2
            ),

            "average_severity": round(
                average_severity,
                2
            ),

            "average_face_presence": round(
                average_face * 100,
                2
            ),

            "behavior": behavior

        })

    return result


# ============================================================
# COHORT ANALYSIS
# ============================================================

def build_cohort_analysis(
    session_results
):

    if not session_results:
        return []

    df = pd.DataFrame(
        session_results
    )

    required = [
        "exam_id",
        "exam_name",
        "session_id",
        "integrity_score",
        "risk"
    ]

    for column in required:

        if column not in df.columns:
            df[column] = 0

    result = []

    grouped = df.groupby(
        [
            "exam_id",
            "exam_name"
        ]
    )

    for (
        exam_id,
        exam_name
    ), group in grouped:

        high_risk = int(
            (
                group["risk"]
                .astype(str)
                .str.lower()
                == "high"
            ).sum()
        )

        result.append({

            "exam_id": int(
                exam_id
            ),

            "exam_name": str(
                exam_name
            ),

            "sessions": int(
                len(group)
            ),

            "average_score": round(
                pd.to_numeric(
                    group[
                        "integrity_score"
                    ],
                    errors="coerce"
                ).fillna(0).mean(),
                2
            ),

            "high_risk": high_risk

        })

    return result