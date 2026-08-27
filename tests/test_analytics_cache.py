"""
Tests for the cluster_cohort_risk() cache added in modules/analytics.py
(Milestone 5 - performance pass). Owner: shared

Context: routes/export.py calls analytics.cluster_cohort_risk(exam_id) to
pull ONE candidate's cluster assignment, but the underlying computation
re-derives the whole cohort (re-queries candidate ids, recalculates every
candidate's integrity score, refits KMeans) from scratch every time.
Exporting N candidates for the same exam back-to-back reran that full
computation N times. This adds a short-TTL cache keyed on
(database path, exam_id, n_clusters).

These tests verify the cache actually caches (same result object reused
within the TTL), respects TTL expiry (recomputes after it elapses), and -
critically - is scoped per-database, so it can never serve a stale result
from a *different* database for the same exam_id, which is exactly the
situation every existing test fixture creates (same exam_id=101, fresh
temp db per test).

Run with:
    python -m pytest tests/test_analytics_cache.py -v
"""

import os
import sys
import sqlite3
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import modules.analytics as analytics
import modules.scoring as scoring


def _seed_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute("INSERT INTO Exams (id, title, duration) VALUES (101, 'Exam', 60)")
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (1, 'A', 'a@test.com', 'h')"
    )
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (2, 'B', 'b@test.com', 'h')"
    )
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (3, 'C', 'c@test.com', 'h')"
    )
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, event_timestamp) "
        "VALUES (2, 101, 'tab_switch', '2026-01-01T10:00:00')"
    )
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, event_timestamp) "
        "VALUES (3, 101, 'tab_switch', '2026-01-01T10:00:00')"
    )
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, event_timestamp) "
        "VALUES (3, 101, 'tab_switch', '2026-01-01T10:00:05')"
    )
    conn.execute(
        "INSERT INTO IntegrityFlags (candidate_id, exam_id, flag_type, severity, created_at) "
        "VALUES (3, 101, 'excessive_tab_switching', 'high', '2026-01-01T10:00:10')"
    )
    conn.execute(
        "INSERT INTO FaceAbsenceEvents (candidate_id, exam_id, start_time, end_time, duration_seconds) "
        "VALUES (3, 101, '2026-01-01T10:01:00', '2026-01-01T10:05:00', 240.0)"
    )
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, event_timestamp) "
        "VALUES (1, 101, 'focus_loss', '2026-01-01T10:00:00')"
    )
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def clear_cache():
    """Every test starts with an empty cache, regardless of what earlier
    tests (in this file or elsewhere) left behind."""
    analytics._cluster_cache.clear()
    yield
    analytics._cluster_cache.clear()


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    test_db = tmp_path / "test_analytics_cache.db"
    monkeypatch.setattr(analytics, "DATABASE", test_db)
    monkeypatch.setattr(scoring, "DATABASE", test_db)
    _seed_db(test_db)
    return test_db


def test_second_call_within_ttl_returns_cached_result(isolated_db, monkeypatch):
    call_count = {"n": 0}
    real_compute = analytics._compute_cluster_cohort_risk

    def counting_compute(exam_id, n_clusters=3):
        call_count["n"] += 1
        return real_compute(exam_id, n_clusters)

    monkeypatch.setattr(analytics, "_compute_cluster_cohort_risk", counting_compute)

    first = analytics.cluster_cohort_risk(101)
    second = analytics.cluster_cohort_risk(101)

    assert call_count["n"] == 1, "Second call within TTL should not recompute"
    assert first == second


def test_cache_expires_after_ttl(isolated_db, monkeypatch):
    monkeypatch.setattr(analytics, "_CLUSTER_CACHE_TTL_SECONDS", 0.05)

    call_count = {"n": 0}
    real_compute = analytics._compute_cluster_cohort_risk

    def counting_compute(exam_id, n_clusters=3):
        call_count["n"] += 1
        return real_compute(exam_id, n_clusters)

    monkeypatch.setattr(analytics, "_compute_cluster_cohort_risk", counting_compute)

    analytics.cluster_cohort_risk(101)
    time.sleep(0.1)
    analytics.cluster_cohort_risk(101)

    assert call_count["n"] == 2, "Call after TTL expiry should recompute"


def test_cache_does_not_leak_across_different_databases(monkeypatch, tmp_path):
    """The exact scenario every other test file's fixtures create: the
    same exam_id (101) in two completely different databases. A cache
    keyed only on exam_id would incorrectly serve db_a's result for
    db_b's query."""
    db_a = tmp_path / "a.db"
    db_b = tmp_path / "b.db"
    _seed_db(db_a)
    _seed_db(db_b)

    conn = sqlite3.connect(db_b)
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (4, 'D', 'd@test.com', 'h')"
    )
    conn.execute(
        "INSERT INTO BrowserEvents (candidate_id, exam_id, event_type, event_timestamp) "
        "VALUES (4, 101, 'tab_switch', '2026-01-01T10:00:00')"
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(analytics, "DATABASE", db_a)
    monkeypatch.setattr(scoring, "DATABASE", db_a)
    result_a = analytics.cluster_cohort_risk(101)

    monkeypatch.setattr(analytics, "DATABASE", db_b)
    monkeypatch.setattr(scoring, "DATABASE", db_b)
    result_b = analytics.cluster_cohort_risk(101)

    assert result_a["cohort_size"] == 3
    assert result_b["cohort_size"] == 4, (
        "Cache leaked db_a's result into db_b's query for the same exam_id"
    )


def test_cluster_cohort_risk_output_unchanged_by_caching(isolated_db):
    """Sanity check: caching must not alter the function's return value
    shape or content vs. calling the uncached implementation directly."""
    cached_result = analytics.cluster_cohort_risk(101)
    direct_result = analytics._compute_cluster_cohort_risk(101)

    assert cached_result == direct_result
