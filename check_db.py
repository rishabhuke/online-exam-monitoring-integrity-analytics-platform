"""
Database Validation and Cleanup Tool (Priyanshu's task).

Provides diagnostic details on database rows and tables,
and allows cleaning up records using the --cleanup flag.

Usage:
    python check_db.py
    python check_db.py --cleanup
"""

import sqlite3
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"

TABLES = [
    "Candidates",
    "Exams",
    "Questions",
    "Answers",
    "SessionLogs",
    "FaceAbsenceEvents",
    "BrowserEvents",
    "IntegrityFlags"
]

def get_db_connection():
    if not DATABASE.exists():
        print(f"Warning: Database file does not exist at {DATABASE}")
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def print_db_summary():
    """Prints diagnostic counts of rows in each database table."""
    print("=" * 50)
    print("DATABASE STATUS DIAGNOSTICS")
    print("=" * 50)
    print(f"Path: {DATABASE.absolute()}")
    print("-" * 50)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row["name"] for row in cursor.fetchall()}
        
        for table in TABLES:
            if table not in existing_tables:
                print(f"Table {table:<20} : DOES NOT EXIST")
                continue
                
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()["cnt"]
            print(f"Table {table:<20} : {count} rows")
            
            # Print a few sample rows if populated
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                rows = [dict(r) for r in cursor.fetchall()]
                print(f"   Samples: {rows}")
    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()
    print("=" * 50)

def clean_database():
    """Deletes all records from all monitoring, authentication, and exam tables."""
    print("Cleaning database tables...")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Disable foreign keys temporarily to clear all tables cleanly
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row["name"] for row in cursor.fetchall()}
        has_sqlite_sequence = "sqlite_sequence" in existing_tables

        for table in TABLES:
            if table not in existing_tables:
                print(f"Skipping missing table: {table}")
                continue

            cursor.execute(f"DELETE FROM {table}")
            # Reset autoincrement sequences (only if sqlite_sequence exists)
            if has_sqlite_sequence:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
            print(f"Cleared table: {table}")
            
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        print("Database cleanup completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error cleaning database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check and clean sqlite database.")
    parser.add_argument(
        "--cleanup", 
        action="store_true", 
        help="Purge all rows from all database tables."
    )
    args = parser.parse_args()

    if args.cleanup:
        clean_database()
        print_db_summary()
    else:
        print_db_summary()
