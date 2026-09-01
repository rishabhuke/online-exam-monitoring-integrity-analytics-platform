"""
Tests for SupportTickets storage layer and API endpoints (Milestone 5 -
support ticket backend port).

Run with:
    python -m pytest tests/test_support.py -v
"""

import os
import sys
import sqlite3
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module
import modules.support_storage as support_storage
import routes.support as support_route_module


@pytest.fixture
def test_db_and_client(monkeypatch, tmp_path):
    """
    Fixture providing an isolated SQLite database and Flask test client.
    Seeds candidates and an invigilator for FK constraints and auth.
    """
    test_db = tmp_path / "test_support.db"

    monkeypatch.setattr(app_module, "DATABASE", test_db)
    monkeypatch.setattr(support_storage, "DATABASE", test_db)

    import routes.auth as auth_module
    monkeypatch.setattr(auth_module, "DATABASE", test_db)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (1, 'Alice', 'alice@test.com', 'hash1')"
    )
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (2, 'Bob', 'bob@test.com', 'hash2')"
    )
    conn.execute(
        "INSERT INTO Invigilators (id, name, email, password_hash) VALUES (1, 'Invig', 'invig@test.com', ?)",
        (generate_password_hash("SecurePass123"),)
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client, test_db


# ---------------------------------------------------------------------------
# Storage Layer Unit Tests (modules/support_storage.py)
# ---------------------------------------------------------------------------

def test_storage_create_and_get_ticket(test_db_and_client):
    _, _ = test_db_and_client

    ticket = support_storage.create_ticket(
        candidate_id=1,
        issue_type="Login Problem",
        priority="High",
        message="Can't log in after registering.",
        contact_name="Alice",
        contact_email="alice@test.com",
    )

    assert ticket is not None
    assert ticket["id"] is not None
    assert ticket["candidate_id"] == 1
    assert ticket["issue_type"] == "Login Problem"
    assert ticket["priority"] == "High"
    assert ticket["status"] == "Open"
    assert ticket["response"] is None

    retrieved = support_storage.get_ticket_by_id(ticket["id"])
    assert retrieved == ticket


def test_storage_get_tickets_for_candidate_scoped(test_db_and_client):
    _, _ = test_db_and_client

    support_storage.create_ticket(1, "Login Problem", "High", "issue 1")
    support_storage.create_ticket(1, "Exam Access Issue", "Medium", "issue 2")
    support_storage.create_ticket(2, "Technical Error", "Low", "issue 3")

    alice_tickets = support_storage.get_tickets_for_candidate(1)
    assert len(alice_tickets) == 2
    assert all(t["candidate_id"] == 1 for t in alice_tickets)

    bob_tickets = support_storage.get_tickets_for_candidate(2)
    assert len(bob_tickets) == 1


def test_storage_get_all_tickets_joins_candidate_name(test_db_and_client):
    _, _ = test_db_and_client

    support_storage.create_ticket(1, "Login Problem", "High", "issue 1")

    all_tickets = support_storage.get_all_tickets()
    assert len(all_tickets) == 1
    assert all_tickets[0]["candidate_name"] == "Alice"


def test_storage_get_all_tickets_status_filter(test_db_and_client):
    _, _ = test_db_and_client

    t1 = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")
    support_storage.create_ticket(1, "Exam Access Issue", "Medium", "issue 2")

    support_storage.update_ticket(t1["id"], status="Resolved")

    open_tickets = support_storage.get_all_tickets(status="Open")
    assert len(open_tickets) == 1

    resolved_tickets = support_storage.get_all_tickets(status="Resolved")
    assert len(resolved_tickets) == 1
    assert resolved_tickets[0]["id"] == t1["id"]


def test_storage_update_ticket_sets_status_and_response(test_db_and_client):
    _, _ = test_db_and_client

    ticket = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")

    updated = support_storage.update_ticket(
        ticket["id"], status="In Progress", response="Looking into this.", responded_by=1
    )

    assert updated["status"] == "In Progress"
    assert updated["response"] == "Looking into this."
    assert updated["responded_by"] == 1


def test_storage_update_ticket_missing_returns_none(test_db_and_client):
    _, _ = test_db_and_client
    assert support_storage.update_ticket(9999, status="Resolved") is None


# ---------------------------------------------------------------------------
# API Route Tests (routes/support.py)
# ---------------------------------------------------------------------------

def test_create_ticket_requires_candidate_auth(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.post("/api/support", json={
        "issue_type": "Login Problem", "priority": "High", "message": "help"
    })
    assert resp.status_code == 401


def test_create_ticket_success(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/support", json={
        "issue_type": "Login Problem",
        "priority": "High",
        "message": "Can't log in.",
        "contact_name": "Alice",
        "contact_email": "alice@test.com",
    })
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "success"
    assert body["ticket"]["candidate_id"] == 1
    assert body["ticket"]["status"] == "Open"


def test_create_ticket_missing_fields_rejected(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.post("/api/support", json={"issue_type": "Login Problem"})
    assert resp.status_code == 400


def test_list_tickets_requires_auth(test_db_and_client):
    client, _ = test_db_and_client
    resp = client.get("/api/support")
    assert resp.status_code == 401


def test_list_tickets_candidate_sees_only_own(test_db_and_client):
    client, _ = test_db_and_client

    support_storage.create_ticket(1, "Login Problem", "High", "issue 1")
    support_storage.create_ticket(2, "Technical Error", "Low", "issue 2")

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get("/api/support")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] == 1
    assert body["tickets"][0]["candidate_id"] == 1


def test_list_tickets_invigilator_sees_all(test_db_and_client):
    client, _ = test_db_and_client

    support_storage.create_ticket(1, "Login Problem", "High", "issue 1")
    support_storage.create_ticket(2, "Technical Error", "Low", "issue 2")

    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/support")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] == 2


def test_list_tickets_invigilator_status_filter(test_db_and_client):
    client, _ = test_db_and_client

    t1 = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")
    support_storage.create_ticket(2, "Technical Error", "Low", "issue 2")
    support_storage.update_ticket(t1["id"], status="Resolved")

    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/support?status=Resolved")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] == 1
    assert body["tickets"][0]["id"] == t1["id"]


def test_get_ticket_requires_auth(test_db_and_client):
    client, _ = test_db_and_client
    ticket = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")
    resp = client.get(f"/api/support/{ticket['id']}")
    assert resp.status_code == 401


def test_get_ticket_candidate_cannot_view_others(test_db_and_client):
    client, _ = test_db_and_client
    ticket = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")

    with client.session_transaction() as sess:
        sess["candidate_id"] = 2

    resp = client.get(f"/api/support/{ticket['id']}")
    assert resp.status_code == 403


def test_get_ticket_owner_can_view(test_db_and_client):
    client, _ = test_db_and_client
    ticket = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.get(f"/api/support/{ticket['id']}")
    assert resp.status_code == 200


def test_get_ticket_not_found(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.get("/api/support/9999")
    assert resp.status_code == 404


def test_respond_to_ticket_requires_invigilator_auth(test_db_and_client):
    client, _ = test_db_and_client
    ticket = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")

    with client.session_transaction() as sess:
        sess["candidate_id"] = 1

    resp = client.patch(f"/api/support/{ticket['id']}", json={"status": "Resolved"})
    assert resp.status_code == 401


def test_respond_to_ticket_updates_status_and_response(test_db_and_client):
    client, _ = test_db_and_client
    ticket = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")

    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.patch(f"/api/support/{ticket['id']}", json={
        "status": "Resolved", "response": "Fixed your account."
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ticket"]["status"] == "Resolved"
    assert body["ticket"]["response"] == "Fixed your account."
    assert body["ticket"]["responded_by"] == 1


def test_respond_to_ticket_rejects_invalid_status(test_db_and_client):
    client, _ = test_db_and_client
    ticket = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")

    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.patch(f"/api/support/{ticket['id']}", json={"status": "Not A Real Status"})
    assert resp.status_code == 400


def test_respond_to_ticket_requires_at_least_one_field(test_db_and_client):
    client, _ = test_db_and_client
    ticket = support_storage.create_ticket(1, "Login Problem", "High", "issue 1")

    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.patch(f"/api/support/{ticket['id']}", json={})
    assert resp.status_code == 400


def test_respond_to_ticket_not_found(test_db_and_client):
    client, _ = test_db_and_client
    with client.session_transaction() as sess:
        sess["invigilator_id"] = 1

    resp = client.patch("/api/support/9999", json={"status": "Resolved"})
    assert resp.status_code == 404
