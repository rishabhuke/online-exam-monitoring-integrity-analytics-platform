"""
Tests for candidate registration, login, session management, and logout.
Owner: shared (built by Rishabh to satisfy Milestone 1 testing requirement)

Run with:
    python -m pytest tests/test_auth.py -v

Uses a temporary, isolated SQLite database so these tests never touch your
real development database.
"""

import os
import sys
import tempfile
import base64
import io
import pytest
import cv2
import numpy as np

# Make sure the project root is on the path when running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module


def make_fake_photo_data_url():
    """
    Generates a synthetic 'photo' with a detectable face-like pattern is hard
    without a real face; instead we monkeypatch contains_face for these tests
    so registration logic can be tested independently of face detection.
    """
    img = np.ones((300, 300, 3), dtype=np.uint8) * 255
    _, buf = cv2.imencode(".png", img)
    b64 = base64.b64encode(buf).decode("utf-8")
    return f"data:image/png;base64,{b64}"


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Creates a Flask test client backed by a temporary SQLite database,
    with face detection stubbed out so tests don't depend on a real face
    being present in the synthetic test image.
    """
    test_db = tmp_path / "test.db"

    # Point the app's DATABASE path to our temp file
    monkeypatch.setattr(app_module, "DATABASE", test_db)

    # Initialize schema on the temp DB
    import sqlite3
    conn = sqlite3.connect(test_db)
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

    # Stub out face detection so registration doesn't require a real face photo
    monkeypatch.setattr("modules.photo_capture.contains_face", lambda image: True)

    app_module.app.config["TESTING"] = True
    app_module.app.secret_key = "test-secret"

    with app_module.app.test_client() as test_client:
        yield test_client


def test_register_success(client):
    photo = make_fake_photo_data_url()
    response = client.post("/register", json={
        "name": "Test Candidate",
        "email": "testcandidate@example.com",
        "password": "SecurePass123",
        "photo_data": photo,
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert "candidate_id" in data


def test_register_duplicate_email_rejected(client):
    photo = make_fake_photo_data_url()
    payload = {
        "name": "Test Candidate",
        "email": "duplicate@example.com",
        "password": "SecurePass123",
        "photo_data": photo,
    }
    first = client.post("/register", json=payload)
    assert first.status_code == 201

    second = client.post("/register", json=payload)
    assert second.status_code == 409


def test_register_missing_fields_rejected(client):
    response = client.post("/register", json={
        "name": "",
        "email": "",
        "password": "",
        "photo_data": "",
    })
    assert response.status_code == 400


def test_login_success_creates_session(client):
    photo = make_fake_photo_data_url()
    client.post("/register", json={
        "name": "Login Test",
        "email": "logintest@example.com",
        "password": "SecurePass123",
        "photo_data": photo,
    })

    response = client.post("/login", json={
        "email": "logintest@example.com",
        "password": "SecurePass123",
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"

    # Session should now allow access to a protected route
    with client.session_transaction() as sess:
        assert "candidate_id" in sess


def test_login_wrong_password_rejected(client):
    photo = make_fake_photo_data_url()
    client.post("/register", json={
        "name": "Wrong Pass Test",
        "email": "wrongpass@example.com",
        "password": "CorrectPass123",
        "photo_data": photo,
    })

    response = client.post("/login", json={
        "email": "wrongpass@example.com",
        "password": "IncorrectPassword",
    })
    assert response.status_code == 401


def test_login_nonexistent_user_rejected(client):
    response = client.post("/login", json={
        "email": "doesnotexist@example.com",
        "password": "whatever123",
    })
    assert response.status_code == 404


def test_protected_route_redirects_when_not_logged_in(client):
    response = client.get("/dashboard", follow_redirects=False)
    # Should redirect (302) to login, not show the dashboard directly
    assert response.status_code == 302
    assert "/login" in response.location


def test_logout_clears_session(client):
    photo = make_fake_photo_data_url()
    client.post("/register", json={
        "name": "Logout Test",
        "email": "logouttest@example.com",
        "password": "SecurePass123",
        "photo_data": photo,
    })
    client.post("/login", json={
        "email": "logouttest@example.com",
        "password": "SecurePass123",
    })

    with client.session_transaction() as sess:
        assert "candidate_id" in sess

    client.get("/logout")

    with client.session_transaction() as sess:
        assert "candidate_id" not in sess


def test_session_expiration_config_is_set():
    """
    Verifies the app has a session lifetime configured (inactivity expiry),
    rather than sessions lasting forever by default.
    """
    assert app_module.app.config.get("PERMANENT_SESSION_LIFETIME") is not None
