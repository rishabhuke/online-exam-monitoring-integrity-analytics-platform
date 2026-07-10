"""
This is a REFERENCE snippet for Priyanshu — showing how the registration
route should call the photo_capture module. Not meant to replace his
actual routes/auth.py, just illustrating the integration point.
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from modules.photo_capture import save_candidate_photo
import sqlite3

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    photo_data = request.form.get("photo_data")  # base64 string from webcam.js

    if not all([name, email, password, photo_data]):
        return jsonify({"error": "All fields including photo are required."}), 400

    # Validate + save photo using OpenCV (Rishabh's module)
    try:
        photo_path = save_candidate_photo(photo_data, email)
    except ValueError as e:
        # e.g. no face detected — send this back so frontend can prompt a retake
        return jsonify({"error": str(e)}), 400

    password_hash = generate_password_hash(password)

    conn = sqlite3.connect("database/examguard.db")
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO candidates (name, email, password_hash, photo_path) "
            "VALUES (?, ?, ?, ?)",
            (name, email, password_hash, photo_path),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered."}), 400
    finally:
        conn.close()

    return jsonify({"message": "Registration successful."}), 201
