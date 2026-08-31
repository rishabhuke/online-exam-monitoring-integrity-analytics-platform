"""
Tests for routes/quiz.py (Milestone 5 - P1, AI quiz generator).
Owner: Rishabh

Mirrors the fixture/setup pattern in tests/test_export_route.py.

Run with:
    python -m pytest tests/test_quiz_route.py -v
"""

import os
import sys
import json
import sqlite3

import pytest
from werkzeug.security import generate_password_hash
from langchain_core.runnables import RunnableLambda

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.quiz_generator as quiz_generator
import modules.report_agent as report_agent

VALID_QUESTION = {
    "question": "What is 2+2?",
    "option_a": "3",
    "option_b": "4",
    "option_c": "5",
    "option_d": "6",
    "correct_option": "b",
}


class _StubResult:
    def __init__(self, content):
        self.content = content


def _stub_llm_returning(text):
    return RunnableLambda(lambda prompt_value: _StubResult(text))


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    test_db = tmp_path / "test_quiz_route.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(quiz_generator, "DATABASE", test_db)

    import routes.auth as auth_module
    monkeypatch.setattr(auth_module, "DATABASE", test_db)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute("INSERT INTO Exams (id, title, duration) VALUES (101, 'Python Fundamentals Exam', 60)")
    conn.execute(
        "INSERT INTO Invigilators (id, name, email, password_hash) VALUES (1, 'Invig', 'invig@test.com', ?)",
        (generate_password_hash("SecurePass123"),)
    )
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (1, 'Alice', 'alice@test.com', 'hash')"
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client, test_db


# --- /api/quiz/generate: auth gating -----------------------------------

def test_generate_requires_invigilator_auth_no_session(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.post("/api/quiz/generate", json={"topic": "Python", "count": 3})
    assert resp.status_code == 401


def test_generate_rejects_candidate_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/quiz/generate", json={"topic": "Python", "count": 3})
    assert resp.status_code == 401


# --- /api/quiz/generate: input validation -------------------------------

def test_generate_rejects_missing_topic(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/generate", json={"count": 3})
    assert resp.status_code == 400
    assert "topic" in resp.get_json()["message"]


def test_generate_rejects_empty_topic(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/generate", json={"topic": "   ", "count": 3})
    assert resp.status_code == 400


def test_generate_rejects_missing_count(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/generate", json={"topic": "Python"})
    assert resp.status_code == 400
    assert "count" in resp.get_json()["message"]


def test_generate_rejects_count_out_of_range(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/generate", json={"topic": "Python", "count": 50})
    assert resp.status_code == 400


def test_generate_rejects_non_integer_count(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/generate", json={"topic": "Python", "count": "three"})
    assert resp.status_code == 400


def test_generate_rejects_boolean_count(test_db_and_client):
    """bool is a subclass of int in Python - must be explicitly rejected,
    not silently accepted as count=1/0."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/generate", json={"topic": "Python", "count": True})
    assert resp.status_code == 400


# --- /api/quiz/generate: success path (never touches DB) ---------------

def test_generate_success_returns_preview_and_writes_nothing(test_db_and_client, monkeypatch):
    client, test_db = test_db_and_client
    stub = _stub_llm_returning(json.dumps([VALID_QUESTION, VALID_QUESTION]))
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: stub)

    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/generate", json={"topic": "Python basics", "count": 2})

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert len(body["questions"]) == 2

    conn = sqlite3.connect(test_db)
    count = conn.execute("SELECT COUNT(*) FROM Questions").fetchone()[0]
    conn.close()
    assert count == 0  # preview only - no DB write


def test_generate_llm_failure_returns_502(test_db_and_client, monkeypatch):
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)

    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/generate", json={"topic": "Python", "count": 3})

    assert resp.status_code == 502
    assert resp.get_json()["status"] == "error"


# --- /api/quiz/<exam_id>/confirm: auth gating ---------------------------

def test_confirm_requires_invigilator_auth_no_session(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.post("/api/quiz/101/confirm", json={"questions": [VALID_QUESTION]})
    assert resp.status_code == 401


def test_confirm_rejects_candidate_session(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/quiz/101/confirm", json={"questions": [VALID_QUESTION]})
    assert resp.status_code == 401


# --- /api/quiz/<exam_id>/confirm: validation + no-partial-insert --------

def test_confirm_success_inserts_all_questions(test_db_and_client):
    client, test_db = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/101/confirm", json={
        "questions": [VALID_QUESTION, dict(VALID_QUESTION, question="What is 3+3?")]
    })

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "success"
    assert body["inserted_count"] == 2

    conn = sqlite3.connect(test_db)
    rows = conn.execute("SELECT * FROM Questions WHERE exam_id = 101").fetchall()
    conn.close()
    assert len(rows) == 2


def test_confirm_missing_questions_key_returns_400_no_insert(test_db_and_client):
    client, test_db = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/101/confirm", json={})

    assert resp.status_code == 400
    conn = sqlite3.connect(test_db)
    count = conn.execute("SELECT COUNT(*) FROM Questions").fetchone()[0]
    conn.close()
    assert count == 0


def test_confirm_empty_questions_list_returns_400_no_insert(test_db_and_client):
    client, test_db = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/101/confirm", json={"questions": []})

    assert resp.status_code == 400
    conn = sqlite3.connect(test_db)
    count = conn.execute("SELECT COUNT(*) FROM Questions").fetchone()[0]
    conn.close()
    assert count == 0


def test_confirm_one_bad_question_rejects_entire_batch_no_partial_insert(test_db_and_client):
    """The core requirement: if ANY question in the payload is invalid,
    NOTHING gets inserted - not even the valid ones in the same batch."""
    client, test_db = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    bad = dict(VALID_QUESTION, correct_option="z")
    resp = client.post("/api/quiz/101/confirm", json={
        "questions": [VALID_QUESTION, bad, VALID_QUESTION]
    })

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["status"] == "error"
    assert "errors" in body

    conn = sqlite3.connect(test_db)
    count = conn.execute("SELECT COUNT(*) FROM Questions").fetchone()[0]
    conn.close()
    assert count == 0  # no partial insert - all-or-nothing


def test_confirm_missing_field_rejects_batch(test_db_and_client):
    client, test_db = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    bad = dict(VALID_QUESTION)
    del bad["option_d"]

    resp = client.post("/api/quiz/101/confirm", json={"questions": [bad]})

    assert resp.status_code == 400
    conn = sqlite3.connect(test_db)
    count = conn.execute("SELECT COUNT(*) FROM Questions").fetchone()[0]
    conn.close()
    assert count == 0


def test_confirm_invalid_exam_id_type_returns_404(test_db_and_client):
    """exam_id is an <int:...> route converter - a non-integer path
    segment should 404 (Flask routing), not reach the handler at all."""
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.post("/api/quiz/not-a-number/confirm", json={"questions": [VALID_QUESTION]})
    assert resp.status_code == 404
