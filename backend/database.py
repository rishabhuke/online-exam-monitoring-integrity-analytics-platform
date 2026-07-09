import sqlite3
import logging
from typing import Optional, Dict, Any
from config import Config

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection() -> sqlite3.Connection:
    """Establish and return a parameterized connection to the SQLite database."""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        # Enable row factory to access columns by name like dicts
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database at {Config.DATABASE_PATH}: {e}")
        raise

def init_db() -> None:
    """Initialize the database schema, creating the candidate table if it doesn't exist."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS candidate (
        candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        photo_path TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing the database: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def insert_candidate(name: str, email: str, password_hash: str) -> int:
    """
    Insert a new candidate into the candidate table.
    Uses parameterized query to prevent SQL injection.
    """
    insert_query = """
    INSERT INTO candidate (name, email, password_hash)
    VALUES (?, ?, ?)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, (name, email.strip().lower(), password_hash))
        conn.commit()
        last_id = cursor.lastrowid
        logger.info(f"Successfully inserted candidate with ID: {last_id}")
        return last_id if last_id is not None else -1
    except sqlite3.IntegrityError as e:
        logger.warning(f"Integrity error during candidate insertion (email: {email}): {e}")
        raise e
    except sqlite3.Error as e:
        logger.error(f"Database error during candidate insertion: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def get_candidate_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve candidate record by email using a parameterized query.
    Returns a dictionary of column-value mappings if found, or None.
    """
    select_query = "SELECT * FROM candidate WHERE email = ?"
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(select_query, (email.strip().lower(),))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while querying candidate by email ({email}): {e}")
        raise e
    finally:
        if conn:
            conn.close()
