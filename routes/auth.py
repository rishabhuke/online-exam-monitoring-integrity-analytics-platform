import re
import sqlite3
from typing import Tuple, Dict, Any, Union
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash

from modules.photo_capture import save_candidate_photo

auth_bp = Blueprint('auth', __name__)

# Regular expression for email validation
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# Resolve DB path relative to the root folder (one directory up from routes/)
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"

def get_db_connection() -> sqlite3.Connection:
    """Establish and return a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def validate_registration_data(name: str, email: str, password: str) -> Union[None, str]:
    """Helper to validate registration input fields."""
    if not name or not name.strip():
        return "Name is required."
    if not email or not email.strip():
        return "Email is required."
    if not password or not password.strip():
        return "Password is required."
    
    if not EMAIL_REGEX.match(email.strip()):
        return "Invalid email format."
    
    if len(password) < 8:
        return "Password must be at least 8 characters long."
        
    return None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, Response, Tuple[Response, int]]:
    """Candidate registration handler supporting form-encoded and JSON payloads."""
    if request.method == 'GET':
        return render_template('register.html')
        
    # Support both application/json and form-encoded data
    if request.is_json:
        data: Dict[str, Any] = request.get_json() or {}
        name = data.get('name', '')
        email = data.get('email', '')
        password = data.get('password', '')
        photo_data = data.get('photo_data', '')
    else:
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        photo_data = request.form.get('photo_data', '')

    # Validate standard fields
    validation_error = validate_registration_data(name, email, password)
    if validation_error:
        return jsonify({
            "status": "error",
            "message": f"Validation failed: {validation_error}"
        }), 400

    if not photo_data:
        return jsonify({
            "status": "error",
            "message": "Validation failed: Identity verification photo is required."
        }), 400

    # Clean inputs
    name = name.strip()
    email = email.strip().lower()

    # Validate and save candidate photo using OpenCV face check
    try:
        photo_path = save_candidate_photo(photo_data, email)
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Photo processing error: {str(e)}"
        }), 500
    
    conn = get_db_connection()
    try:
        # Check if email already exists
        existing = conn.execute("SELECT id FROM Candidates WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({
                "status": "error",
                "message": "Email already registered."
            }), 409

        # Hash password and store in SQLite
        hashed_password = generate_password_hash(password)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Candidates (name, email, password_hash, photo_path) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, photo_path)
        )
        conn.commit()
        candidate_id = cur.lastrowid
        
        return jsonify({
            "status": "success",
            "message": "Candidate registered successfully",
            "candidate_id": candidate_id
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({
            "status": "error",
            "message": "Email already registered."
        }), 409
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Database error occurred: {str(e)}"
        }), 500
    finally:
        conn.close()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, Response, Tuple[Response, int]]:
    """Candidate login handler supporting JSON APIs and form submissions."""
    if request.method == 'GET':
        return render_template('login.html')

    # Support both application/json and form-encoded data
    if request.is_json:
        data: Dict[str, Any] = request.get_json() or {}
        email = data.get('email', '')
        password = data.get('password', '')
    else:
        email = request.form.get('email', '')
        password = request.form.get('password', '')

    if not email or not password:
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400

    email = email.strip().lower()

    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM Candidates WHERE email = ?", (email,)).fetchone()
        if not row:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        # Verify password
        if not check_password_hash(row['password_hash'], password):
            return jsonify({
                "status": "error",
                "message": "Invalid credentials"
            }), 401

        # Establish candidate session
        session["candidate_id"] = row['id']

        candidate_data = {
            'candidate_id': row['id'],
            'name': row['name'],
            'email': row['email'],
            'photo_path': row['photo_path'],
            'created_at': row['created_at']
        }

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "candidate": candidate_data
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Database error occurred: {str(e)}"
        }), 500
    finally:
        conn.close()


@auth_bp.route('/login/test')
def login_test() -> str:
    """Temporary login route for testing session management."""
    session["candidate_id"] = 1
    return "Session Created Successfully"


@auth_bp.route('/logout')
def logout() -> str:
    """Logout the candidate and clear the session."""
    session.clear()
    return "Logged Out Successfully"