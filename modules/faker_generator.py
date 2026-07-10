"""
Synthetic Data Generator.
Owner: Anuradha (built by Rishabh as a stand-in due to unavailability)

Generates fake candidates and session logs using Faker, and inserts them
into the SQLite database. Can be run as a script, or its functions can be
called from a Flask route (e.g. an admin "Generate Sample Data" button).

Usage (standalone):
    python modules/faker_generator.py --candidates 20 --sessions 40
"""

import sqlite3
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta

from faker import Faker
from werkzeug.security import generate_password_hash

fake = Faker()

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def generate_fake_candidates(count: int = 20) -> list[int]:
    """
    Inserts `count` fake candidates into the Candidates table.
    Returns the list of inserted candidate IDs.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    inserted_ids = []

    for _ in range(count):
        name = fake.name()
        email = fake.unique.email()
        password_hash = generate_password_hash("TestPassword123")
        # No real photo for synthetic candidates - left null
        photo_path = None

        try:
            cur.execute(
                """
                INSERT INTO Candidates (name, email, password_hash, photo_path)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, password_hash, photo_path),
            )
            inserted_ids.append(cur.lastrowid)
        except sqlite3.IntegrityError:
            # Duplicate email (rare, since Faker emails are unique) - skip
            continue

    conn.commit()
    conn.close()
    return inserted_ids


def generate_fake_session_logs(candidate_ids: list[int], count: int = 40) -> int:
    """
    Inserts `count` fake session log entries for the given candidate IDs.
    Returns the number of rows inserted.
    """
    if not candidate_ids:
        return 0

    conn = get_db_connection()
    cur = conn.cursor()
    statuses = ["active", "expired", "logged_out"]
    inserted = 0

    for _ in range(count):
        candidate_id = random.choice(candidate_ids)
        login_time = fake.date_time_between(start_date="-30d", end_date="now")
        status = random.choice(statuses)

        if status == "active":
            logout_time = None
        else:
            # Session lasted somewhere between 2 and 90 minutes
            duration = timedelta(minutes=random.randint(2, 90))
            logout_time = login_time + duration

        cur.execute(
            """
            INSERT INTO SessionLogs (candidate_id, login_time, logout_time, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                candidate_id,
                login_time.isoformat(sep=" "),
                logout_time.isoformat(sep=" ") if logout_time else None,
                status,
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def generate_synthetic_data(candidate_count: int = 20, session_count: int = 40) -> dict:
    """
    Convenience function to generate both candidates and session logs
    in one call. Useful for wiring up to a Flask route/button.
    """
    candidate_ids = generate_fake_candidates(candidate_count)
    sessions_inserted = generate_fake_session_logs(candidate_ids, session_count)

    return {
        "candidates_created": len(candidate_ids),
        "sessions_created": sessions_inserted,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic candidates and session logs.")
    parser.add_argument("--candidates", type=int, default=20, help="Number of fake candidates to generate")
    parser.add_argument("--sessions", type=int, default=40, help="Number of fake session logs to generate")
    args = parser.parse_args()

    result = generate_synthetic_data(args.candidates, args.sessions)
    print(f"Created {result['candidates_created']} candidates and "
          f"{result['sessions_created']} session logs.")
