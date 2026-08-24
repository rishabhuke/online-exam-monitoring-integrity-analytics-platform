"""
Creates an Invigilator account (Milestone 4). Owner: Rishabh

Invigilators don't self-register (unlike candidates) - accounts are
provisioned by whoever administers the deployment, using this script.

Usage:
    python create_invigilator.py --name "Jane Doe" --email jane@college.edu --password "changeme123"

Or interactively (prompts for each field, hides password input):
    python create_invigilator.py
"""

import argparse
import getpass
import re
import sqlite3
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def create_invigilator(name: str, email: str, password: str) -> None:
    name = name.strip()
    email = email.strip().lower()

    if not name:
        print("Error: name is required.")
        sys.exit(1)
    if not EMAIL_REGEX.match(email):
        print("Error: invalid email format.")
        sys.exit(1)
    if len(password) < 8:
        print("Error: password must be at least 8 characters.")
        sys.exit(1)

    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        existing = conn.execute(
            "SELECT id FROM Invigilators WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            print(f"Error: an invigilator with email '{email}' already exists.")
            sys.exit(1)

        hashed = generate_password_hash(password)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Invigilators (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hashed),
        )
        conn.commit()
        print(f"Created invigilator '{name}' <{email}> (id={cur.lastrowid}).")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Create an Invigilator account.")
    parser.add_argument("--name")
    parser.add_argument("--email")
    parser.add_argument("--password", help="If omitted, you'll be prompted (hidden input).")
    args = parser.parse_args()

    name = args.name or input("Name: ")
    email = args.email or input("Email: ")
    password = args.password or getpass.getpass("Password (min 8 chars): ")

    create_invigilator(name, email, password)


if __name__ == "__main__":
    main()
