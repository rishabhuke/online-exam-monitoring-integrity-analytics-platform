from pathlib import Path

import sqlite3
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = BASE_DIR / "database.db"

CHART_DIR = (
    BASE_DIR
    / "static"
    / "analytics"
)

CHART_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# DATABASE
# ==========================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================================
# EVENT CLASSIFIER
# ==========================================================

def classify_event(
    violation_type
):

    text = (
        str(
            violation_type or ""
        )
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


    if (
        "tab" in text
        or "browser_tab" in text
        or "tab_switch" in text
    ):
        return "Tab Switch"


    if (
        "focus" in text
        or "blur" in text
        or "window_lost_focus" in text
        or "lost_focus" in text
    ):
        return "Focus Loss"


    if (
        "no_face" in text
        or "noface" in text
        or "face_absent" in text
        or "face_missing" in text
        or "face_not_detected" in text
    ):
        return "Face Absence"


    if (
        "fullscreen" in text
        or "full_screen" in text
    ):
        return "Fullscreen Exit"


    if (
        "copy" in text
        or "paste" in text
        or "cut" in text
        or "clipboard" in text
    ):
        return "Copy / Paste"


    if (
        "screenshot" in text
        or "screen_shot" in text
        or "screen_capture" in text
        or "print_screen" in text
    ):
        return "Screenshot"


    if (
        "right_click" in text
        or "rightclick" in text
        or "context_menu" in text
    ):
        return "Right Click"


    if (
        "identity" in text
        or "mismatch" in text
        or "verification_failed" in text
    ):
        return "Identity Mismatch"


    if (
        "multiple_face" in text
        or "multiple_faces" in text
    ):
        return "Multiple Faces"


    return "Other"


# ==========================================================
# LOAD SESSION DATA
# ==========================================================

def load_exam_data(
    exam_id
):

    conn = get_connection()

    try:

        attempts = pd.read_sql_query(
            """
            SELECT
                ea.candidate_id,
                ea.score,
                ea.total_questions,
                ea.percentage,
                ea.result,
                c.name
            FROM ExamAttempts ea

            INNER JOIN Candidates c
                ON c.id = ea.candidate_id

            WHERE ea.exam_id = ?
            """,
            conn,
            params=(exam_id,)
        )


        integrity = pd.read_sql_query(
            """
            SELECT
                candidate_id,
                integrity_score,
                face_presence_ratio,
                warning_count,
                risk_label
            FROM IntegrityScores

            WHERE exam_id = ?
            """,
            conn,
            params=(exam_id,)
        )


        violations = pd.read_sql_query(
            """
            SELECT
                candidate_id,
                violation_type,
                violation_time
            FROM ViolationLogs

            WHERE exam_id = ?

            ORDER BY violation_time
            """,
            conn,
            params=(exam_id,)
        )


        return (
            attempts,
            integrity,
            violations
        )

    finally:

        conn.close()


# ==========================================================
# SCORE DISTRIBUTION
# ==========================================================

def score_distribution(
    exam_id
):

    attempts, _, _ = load_exam_data(
        exam_id
    )


    if attempts.empty:

        return {
            "labels": [],
            "values": []
        }


    scores = (
        pd.to_numeric(
            attempts["percentage"],
            errors="coerce"
        )
        .dropna()
    )


    bins = [
        0,
        20,
        40,
        60,
        80,
        100
    ]

    labels = [
        "0-20",
        "21-40",
        "41-60",
        "61-80",
        "81-100"
    ]


    distribution = pd.cut(
        scores,
        bins=bins,
        labels=labels,
        include_lowest=True
    )


    counts = (
        distribution
        .value_counts()
        .sort_index()
    )


    return {
        "labels": [
            str(x)
            for x in counts.index
        ],
        "values": [
            int(x)
            for x in counts.values
        ]
    }


# ==========================================================
# EVENT FREQUENCY
# ==========================================================

def event_frequency(
    exam_id
):

    _, _, violations = load_exam_data(
        exam_id
    )


    if violations.empty:

        return {}


    violations["event"] = (
        violations[
            "violation_type"
        ]
        .apply(classify_event)
    )


    counts = (
        violations[
            "event"
        ]
        .value_counts()
    )


    return {
        str(key): int(value)
        for key, value
        in counts.items()
    }


# ==========================================================
# EVENT HEATMAP
# ==========================================================

def generate_event_heatmap(
    exam_id
):

    _, _, violations = load_exam_data(
        exam_id
    )


    if violations.empty:

        return None


    violations[
        "event"
    ] = violations[
        "violation_type"
    ].apply(
        classify_event
    )


    violations[
        "timestamp"
    ] = pd.to_datetime(
        violations[
            "violation_time"
        ],
        errors="coerce"
    )


    violations = violations.dropna(
        subset=["timestamp"]
    )


    if violations.empty:

        return None


    violations[
        "hour"
    ] = violations[
        "timestamp"
    ].dt.hour


    event_order = [
        "Tab Switch",
        "Focus Loss",
        "Face Absence",
        "Fullscreen Exit",
        "Copy / Paste",
        "Screenshot",
        "Right Click",
        "Identity Mismatch",
        "Multiple Faces",
        "Other"
    ]


    heatmap = pd.crosstab(
        violations["event"],
        violations["hour"]
    )


    heatmap = heatmap.reindex(
        event_order,
        fill_value=0
    )


    plt.figure(
        figsize=(12, 6)
    )


    sns.heatmap(
        heatmap,
        annot=True,
        fmt="d",
        cmap="rocket_r",
        linewidths=0.5
    )


    plt.title(
        "Examination Event Frequency Heatmap"
    )

    plt.xlabel(
        "Hour of Examination"
    )

    plt.ylabel(
        "Integrity Event"
    )

    plt.tight_layout()


    filename = (
        f"event_heatmap_{exam_id}.png"
    )

    path = (
        CHART_DIR
        / filename
    )


    plt.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )


    plt.close()


    return (
        f"/static/analytics/{filename}"
    )


# ==========================================================
# K-MEANS CLUSTERING
# ==========================================================

def perform_kmeans(
    exam_id
):

    _, integrity, violations = (
        load_exam_data(
            exam_id
        )
    )


    if integrity.empty:

        return {
            "available": False,
            "clusters": [],
            "message":
                "No integrity data available"
        }


    # ------------------------------------------------------
    # Event counts per candidate
    # ------------------------------------------------------

    if not violations.empty:

        violations[
            "event"
        ] = violations[
            "violation_type"
        ].apply(
            classify_event
        )


        event_table = pd.crosstab(
            violations[
                "candidate_id"
            ],
            violations[
                "event"
            ]
        )

    else:

        event_table = pd.DataFrame()


    # ------------------------------------------------------
    # Base features
    # ------------------------------------------------------

    features = integrity[
        [
            "candidate_id",
            "integrity_score",
            "face_presence_ratio",
            "warning_count"
        ]
    ].copy()


    features = features.fillna(0)


    if not event_table.empty:

        features = features.merge(
            event_table,
            left_on="candidate_id",
            right_index=True,
            how="left"
        )


    features = features.fillna(0)


    if len(features) < 2:

        return {
            "available": False,
            "clusters": [],
            "message":
                "At least 2 candidate sessions are required for K-Means"
        }


    feature_columns = [
        column
        for column in features.columns
        if column != "candidate_id"
    ]


    X = features[
        feature_columns
    ]


    # ------------------------------------------------------
    # Scale
    # ------------------------------------------------------

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(
        X
    )


    # ------------------------------------------------------
    # Number of clusters
    # ------------------------------------------------------

    n_clusters = min(
        3,
        len(features)
    )


    model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )


    features[
        "cluster"
    ] = model.fit_predict(
        X_scaled
    )


    # ------------------------------------------------------
    # Cluster labels
    # ------------------------------------------------------

    cluster_profiles = []


    for cluster_id, group in (
        features.groupby("cluster")
    ):

        cluster_profiles.append({

            "cluster":
                int(cluster_id),

            "candidates":
                int(len(group)),

            "avg_integrity":
                round(
                    float(
                        group[
                            "integrity_score"
                        ].mean()
                    ),
                    2
                ),

            "avg_face_presence":
                round(
                    float(
                        group[
                            "face_presence_ratio"
                        ].mean()
                    ),
                    3
                ),

            "avg_warnings":
                round(
                    float(
                        group[
                            "warning_count"
                        ].mean()
                    ),
                    2
                )

        })


    return {

        "available": True,

        "clusters":
            cluster_profiles

    }


# ==========================================================
# COHORT RISK PROFILE
# ==========================================================

def risk_profile(
    exam_id
):

    _, integrity, _ = load_exam_data(
        exam_id
    )


    if integrity.empty:

        return {
            "Low": 0,
            "Medium": 0,
            "High": 0
        }


    risk = (
        integrity[
            "risk_label"
        ]
        .fillna("Unknown")
        .str.strip()
        .str.title()
    )


    counts = (
        risk.value_counts()
    )


    return {

        "Low":
            int(
                counts.get(
                    "Low",
                    0
                )
            ),

        "Medium":
            int(
                counts.get(
                    "Medium",
                    0
                )
            ),

        "High":
            int(
                counts.get(
                    "High",
                    0
                )
            )

    }


# ==========================================================
# COMPLETE ANALYTICS
# ==========================================================

def generate_analytics(
    exam_id
):

    return {

        "score_distribution":
            score_distribution(
                exam_id
            ),

        "event_frequency":
            event_frequency(
                exam_id
            ),

        "event_heatmap":
            generate_event_heatmap(
                exam_id
            ),

        "kmeans":
            perform_kmeans(
                exam_id
            ),

        "risk_profile":
            risk_profile(
                exam_id
            )

    }