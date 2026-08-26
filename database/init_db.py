"""
Initializes database.db from database/schema.sql (Milestone 1, updated
Milestone 4).

Previously this script had its own hardcoded CREATE TABLE statements,
duplicated from and drifting out of sync with database/schema.sql (which
is what tests/ actually use to build their isolated test DBs). That's why
adding the Invigilators table to schema.sql alone didn't create it here -
this script never read that file. Fixed to read schema.sql directly, so
there's exactly one source of truth for the schema from now on.
"""

from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

with open(SCHEMA_PATH) as f:
    conn.executescript(f.read())

conn.commit()
conn.close()

print("Database and tables created successfully!")
