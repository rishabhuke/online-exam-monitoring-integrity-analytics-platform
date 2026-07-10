import unittest
import json
import sqlite3
from pathlib import Path
from flask import session
from app import app, get_db_connection

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()

        # Clear/setup database for testing
        self.conn = get_db_connection()
        self.conn.execute("DELETE FROM Candidates")
        self.conn.commit()

    def tearDown(self):
        # Clean up candidates
        self.conn.execute("DELETE FROM Candidates")
        self.conn.commit()
        self.conn.close()

    def test_login_page_renders(self):
        """Test GET /login renders the candidate login page."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Candidate Login', response.data)

    def test_register_page_renders(self):
        """Test GET /register renders the candidate registration page."""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Candidate Registration', response.data)

    def test_login_test_endpoint(self):
        """Test GET /login/test endpoint."""
        response = self.client.get('/login/test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'Session Created Successfully')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('candidate_id'), 1)

    def test_logout(self):
        """Test GET /logout endpoint clears the session."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['candidate_id'] = 123
            response = c.get('/logout')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b'Logged Out Successfully')
            self.assertNotIn('candidate_id', session)

    def test_register_validation_missing_fields(self):
        """Test POST /register handles missing fields correctly."""
        # Missing fields
        payload = {
            "name": "John Doe",
            "email": "",
            "password": "password123",
            "photo_data": ""
        }
        response = self.client.post('/register', 
                                    data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "error")

    def test_login_validation_missing_fields(self):
        """Test POST /login handles missing email/password."""
        payload = {
            "email": "",
            "password": "password123"
        }
        response = self.client.post('/login',
                                    data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")

if __name__ == '__main__':
    unittest.main()