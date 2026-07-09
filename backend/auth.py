import re
import sqlite3
from typing import Tuple, Dict, Any, Union
from flask import Blueprint, request, jsonify, render_template, Response
from werkzeug.security import generate_password_hash, check_password_hash

import database
from models import Candidate

auth_bp = Blueprint('auth', __name__)

# Regular expression for email validation
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

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
    """Candidate registration handler supporting JSON APIs and form submissions."""
    if request.method == 'GET':
        return render_template('register.html')
        
    # Support both application/json and form-encoded data
    if request.is_json:
        data: Dict[str, Any] = request.get_json() or {}
        name = data.get('name', '')
        email = data.get('email', '')
        password = data.get('password', '')
    else:
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')

    # Validate input fields
    validation_error = validate_registration_data(name, email, password)
    if validation_error:
        return jsonify({
            "status": "error",
            "message": f"Validation failed: {validation_error}"
        }), 400

    # Clean inputs
    name = name.strip()
    email = email.strip().lower()
    
    try:
        # Check if email already exists
        existing_user = database.get_candidate_by_email(email)
        if existing_user:
            return jsonify({
                "status": "error",
                "message": "Email already exists"
            }), 409

        # Hash password and store in SQLite
        hashed_password = generate_password_hash(password, method='scrypt')
        candidate_id = database.insert_candidate(name, email, hashed_password)
        
        return jsonify({
            "status": "success",
            "message": "Candidate registered successfully",
            "candidate_id": candidate_id
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({
            "status": "error",
            "message": "Email already exists"
        }), 409
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Database error occurred: {str(e)}"
        }), 500


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

    try:
        candidate_row = database.get_candidate_by_email(email)
        if not candidate_row:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 404
            
        candidate = Candidate.from_db_row(candidate_row)
        
        # Verify password
        if not check_password_hash(candidate.password_hash, password):
            return jsonify({
                "status": "error",
                "message": "Invalid credentials"
            }), 401

        return jsonify({
            "status": "success",
            "message": "Login successful",
            "candidate": candidate.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Database error occurred: {str(e)}"
        }), 500
