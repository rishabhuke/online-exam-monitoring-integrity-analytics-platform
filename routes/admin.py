import os
import re
import sqlite3

from pathlib import Path
from typing import Dict, Any
from functools import wraps

from dotenv import load_dotenv

from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# BLUEPRINT
# ============================================================

admin_bp = Blueprint("admin", __name__)


# ============================================================
# CONFIGURATION
# ============================================================

EMAIL_REGEX = re.compile(
    r"^[\w\.-]+@[\w\.-]+\.\w+$"
)

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE = BASE_DIR / "database.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# ADMIN AUTH DECORATORS
# ============================================================

def admin_login_required(function):
    """Decorator for HTML page routes: redirects unauthenticated requests to /admin/login."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin.admin_login_page"))
        return function(*args, **kwargs)
    return wrapper


def admin_api_required(function):
    """Decorator for JSON API routes: returns a JSON 401 response if unauthenticated."""
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return jsonify({
                "success": False,
                "status": "error",
                "message": "Unauthorized access. Admin authentication required."
            }), 401
        return function(*args, **kwargs)
    return wrapper


# Backward-compatible alias
admin_required = admin_api_required


# ============================================================
# ADMIN REGISTRATION VALIDATION
# ============================================================

def validate_admin_registration(
    full_name,
    email,
    employee_id,
    username,
    password,
    organization_code
):
    if not full_name:
        return "Full Name is required."

    if not email:
        return "Email is required."

    if not EMAIL_REGEX.match(email):
        return "Invalid email address."

    if not employee_id:
        return "Employee ID is required."

    if not username:
        return "Username is required."

    if len(password) < 8:
        return "Password must contain at least 8 characters."

    correct_code = os.getenv("ADMIN_ORG_CODE", "ADMIN2026")

    if organization_code != correct_code:
        return "Invalid Organization Code."

    return None


# ============================================================
# ADMIN LOGIN PAGE
# ============================================================
@admin_bp.route("/admin/login")
def admin_login_page():

    session.clear()

    return render_template("admin_login.html")


# ============================================================
# ADMIN SIGNUP PAGE
# ============================================================

@admin_bp.route("/admin/signup")
def admin_signup_page():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard.dashboard"))
    return render_template("admin_signup.html")


# ============================================================
# ADMIN REGISTRATION API
# ============================================================

@admin_bp.route("/api/admin/register", methods=["POST"])
@admin_bp.route("/admin/api/register", methods=["POST"])
def register_admin():
    data: Dict[str, Any] = request.get_json() or {}

    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    employee_id = data.get("employee_id", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    organization_code = data.get("organization_code", "").strip()

    error = validate_admin_registration(
        full_name,
        email,
        employee_id,
        username,
        password,
        organization_code
    )

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    conn = get_db_connection()

    try:
        invite = conn.execute(
            """
            SELECT *
            FROM AdminInviteIDs
            WHERE employee_id = ?
            """,
            (employee_id,)
        ).fetchone()

        if invite is None:
            return jsonify({
                "status": "error",
                "message": "Employee ID is not authorized."
            }), 403

        if invite["used"] == 1:
            return jsonify({
                "status": "error",
                "message": "Employee ID already used."
            }), 400

        exists = conn.execute(
            """
            SELECT id
            FROM Admins
            WHERE email = ?
               OR username = ?
               OR employee_id = ?
            """,
            (email, username, employee_id)
        ).fetchone()

        if exists:
            return jsonify({
                "status": "error",
                "message": "Email, Username or Employee ID already exists."
            }), 409

        password_hash = generate_password_hash(password)

        conn.execute(
            """
            INSERT INTO Admins (
                full_name,
                email,
                employee_id,
                username,
                password_hash
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (full_name, email, employee_id, username, password_hash)
        )

        conn.execute(
            """
            UPDATE AdminInviteIDs
            SET used = 1, used_at = CURRENT_TIMESTAMP
            WHERE employee_id = ?
            """,
            (employee_id,)
        )

        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Admin registered successfully.",
            "redirect": "/admin/login"
        }), 201

    except sqlite3.IntegrityError as e:
        conn.rollback()
        return jsonify({
            "status": "error",
            "message": f"Database error: {str(e)}"
        }), 400

    except Exception as e:
        conn.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to register admin.",
            "error": str(e)
        }), 500

    finally:
        conn.close()


# ============================================================
# ADMIN LOGIN API
# ============================================================

@admin_bp.route("/api/admin/login", methods=["POST"])
@admin_bp.route("/admin/api/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "status": "error",
            "message": "Username and Password are required."
        }), 400

    conn = get_db_connection()

    try:
        admin = conn.execute(
            """
            SELECT *
            FROM Admins
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if admin is None or not check_password_hash(admin["password_hash"], password):
            return jsonify({
                "status": "error",
                "message": "Invalid username or password."
            }), 401

        session.clear()
        session["admin_id"] = admin["id"]
        session["admin_name"] = admin["full_name"]
        session["admin_username"] = admin["username"]
        session["is_admin"] = True
        session.permanent = True

        return jsonify({
            "status": "success",
            "message": "Login successful.",
            "redirect": "/admin/dashboard",
            "admin": {
                "id": admin["id"],
                "name": admin["full_name"],
                "username": admin["username"],
                "email": admin["email"]
            }
        }), 200

    finally:
        conn.close()


# ============================================================
# CURRENT ADMIN
# ============================================================

@admin_bp.route("/api/admin/me")
@admin_bp.route("/admin/api/me")
def current_admin():
    if "admin_id" not in session:
        return jsonify({
            "logged_in": False
        }), 401

    conn = get_db_connection()

    try:
        admin = conn.execute(
            """
            SELECT
                id,
                full_name,
                email,
                employee_id,
                username,
                created_at
            FROM Admins
            WHERE id = ?
            """,
            (session["admin_id"],)
        ).fetchone()

        if admin is None:
            session.clear()
            return jsonify({
                "logged_in": False
            }), 401

        return jsonify({
            "logged_in": True,
            "admin": dict(admin)
        })

    finally:
        conn.close()


# ============================================================
# LOGOUT API
# ============================================================

@admin_bp.route("/api/admin/logout")
@admin_bp.route("/admin/api/logout")
def admin_logout():
    session.clear()
    return jsonify({
        "status": "success",
        "message": "Logged out successfully."
    })
