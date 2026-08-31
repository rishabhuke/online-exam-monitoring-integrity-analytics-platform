"""
Tests for the AI Integrity Report Agent (Milestone 3). Owner: Rishabh

Run with:
    python -m pytest tests/test_report_agent.py -v

No Ollama server is available in CI, so these tests exercise the template
fallback path (source == "template") for get_default_llm()/generate_summary(),
plus a stub-LLM test to confirm the LangChain chain wiring itself works
without needing a real provider. The low/medium/high risk-scenario tests
below validate generate_summary() end-to-end across the three risk bands
called for in the brief, using the template path (deterministic, so no
Ollama dependency), and a stub-LLM equivalent to confirm the LLM path
produces the same risk_label/context regardless of wording source.
"""

import os
import sys
import sqlite3

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import modules.report_agent as report_agent
import modules.flags_storage as flags_storage
import modules.monitoring_storage as monitoring_storage
import modules.scoring as scoring
import modules.analytics as analytics


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(flags_storage, "DATABASE", test_db)
    monkeypatch.setattr(monitoring_storage, "DATABASE", test_db)
    monkeypatch.setattr(scoring, "DATABASE", test_db)
    monkeypatch.setattr(analytics, "DATABASE", test_db)
    report_agent._exam_summary_cache.clear()

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (1, 'Alice', 'alice@test.com', 'hash')"
    )
    conn.execute("INSERT INTO Exams (id, title, duration) VALUES (1, 'Test Exam', 60)")
    conn.commit()
    conn.close()

    return test_db


def test_build_session_context_with_no_events(isolated_db):
    context = report_agent.build_session_context(1, 1)

    assert context["face_absence_count"] == 0
    assert context["browser_event_counts"] == {}
    assert context["flag_counts"] == {}
    assert context["risk_label"] == "Low"


def test_build_session_context_aggregates_events_and_flags(isolated_db):
    monitoring_storage.create_face_event(1, 1, "2026-01-01T00:00:00", "2026-01-01T00:01:00", 60)
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    flags_storage.create_flag(1, 1, "excessive_tab_switching", "medium", "2 tab switches", "max_tab_switches=2")

    context = report_agent.build_session_context(1, 1)

    assert context["face_absence_count"] == 1
    assert context["face_absence_total_seconds"] == 60
    assert context["browser_event_counts"] == {"tab_switch": 2}
    assert context["flag_counts"] == {"excessive_tab_switching": 1}
    assert context["risk_label"] == "Medium"


def test_generate_summary_falls_back_to_template_without_llm(isolated_db, monkeypatch):
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    result = report_agent.generate_summary(1, 1)

    assert result["source"] == "template"
    assert "Candidate 1, exam 1" in result["summary"]
    assert "Overall integrity risk: Low." in result["summary"]


def test_generate_summary_reflects_flagged_session(isolated_db, monkeypatch):
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    monitoring_storage.create_face_event(1, 1, "2026-01-01T00:00:00", "2026-01-01T00:04:00", 240)
    flags_storage.create_flag(1, 1, "face_absent_single_interval", "high", "absent 240s", "max_face_absent_seconds=120")

    result = report_agent.generate_summary(1, 1)

    assert result["risk_label"] == "Medium"
    assert "240s" in result["summary"]
    assert "1 integrity flag(s)" in result["summary"]


from langchain_core.runnables import RunnableLambda


class _StubResult:
    def __init__(self, content):
        self.content = content


def _StubLLM():
    """Minimal LangChain Runnable stub so the LLM code path can be tested
    without a real provider/API key - wraps a plain function as a Runnable,
    same as any LangChain-compatible chat model would present."""
    return RunnableLambda(lambda prompt_value: _StubResult(f"stub summary for: {prompt_value.text[:20]}..."))


def test_generate_summary_uses_llm_when_provided(isolated_db):
    result = report_agent.generate_summary(1, 1, llm=_StubLLM())

    assert result["source"] == "llm"
    assert result["summary"].startswith("stub summary for:")


def test_get_default_llm_returns_none_without_any_provider_configured(isolated_db, monkeypatch):
    """No GROQ_API_KEY and no Ollama server reachable -> get_default_llm()
    should fail closed and return None (never raise), regardless of what's
    actually set in the shell running the tests."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert report_agent.get_default_llm() is None


def test_get_groq_llm_returns_none_without_api_key(isolated_db, monkeypatch):
    """No GROQ_API_KEY set -> _get_groq_llm() should return None without
    even trying to import/call langchain_groq."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert report_agent._get_groq_llm() is None


def test_generate_summary_falls_back_when_llm_none_and_no_ollama(isolated_db, monkeypatch):
    """With llm=None and no provider reachable, generate_summary() should
    silently use the template path rather than erroring."""
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    result = report_agent.generate_summary(1, 1)

    assert result["source"] == "template"


# --- Risk-scenario tests (low / medium / high) ---------------------------
# Exercises generate_summary() end-to-end across the three risk bands the
# brief calls out. Uses the template path (deterministic, forced via
# monkeypatch so these pass regardless of what's configured in the shell)
# for risk_label/content correctness, and a stub LLM for the "low" case to
# confirm the LLM code path doesn't alter risk_label regardless of wording
# source.

def test_risk_scenario_low(isolated_db, monkeypatch):
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    # No events, no flags -> Low.
    result = report_agent.generate_summary(1, 1)

    assert result["risk_label"] == "Low"
    assert result["source"] == "template"
    assert "no integrity flags were raised" in result["summary"]
    assert "face presence was maintained throughout" in result["summary"]


def test_risk_scenario_low_with_llm_stub(isolated_db):
    # Same low-risk data, routed through a stub LLM - risk_label must match
    # the template path even though the wording source differs.
    result = report_agent.generate_summary(1, 1, llm=_StubLLM())

    assert result["risk_label"] == "Low"
    assert result["source"] == "llm"


def test_risk_scenario_medium(isolated_db, monkeypatch):
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    # A handful of tab switches plus one medium-severity flag -> Medium.
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    flags_storage.create_flag(1, 1, "excessive_tab_switching", "medium", "3 tab switches", "max_tab_switches=2")

    result = report_agent.generate_summary(1, 1)

    assert result["risk_label"] == "Medium"
    assert result["source"] == "template"
    assert "3 tab_switch" in result["summary"]
    assert "1 integrity flag(s)" in result["summary"]


def test_risk_scenario_high(isolated_db, monkeypatch):
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    # Extended face absence plus a high-severity flag and a medium one
    # (weights: high=3, medium=2 -> score 5) -> High.
    monitoring_storage.create_face_event(1, 1, "2026-01-01T00:00:00", "2026-01-01T00:06:00", 360)
    flags_storage.create_flag(1, 1, "face_absent_single_interval", "high", "absent 360s", "max_face_absent_seconds=120")
    flags_storage.create_flag(1, 1, "excessive_tab_switching", "medium", "4 tab switches", "max_tab_switches=2")

    result = report_agent.generate_summary(1, 1)

    assert result["risk_label"] == "High"
    assert result["source"] == "template"
    assert "360s" in result["summary"]
    assert "2 integrity flag(s)" in result["summary"]
    assert "Overall integrity risk: High." in result["summary"]


# ---------------------------------------------------------------------------
# Exam-level (cohort) summary tests (Milestone 5 - integrity analysis port)
# ---------------------------------------------------------------------------

def test_build_exam_cohort_context_with_no_candidates(isolated_db):
    """No candidate has any monitoring data for this exam yet."""
    context = report_agent.build_exam_cohort_context(1)

    assert context["cohort_size"] == 0
    assert context["candidate_ids"] == []
    assert context["risk_breakdown"] == {}
    assert context["flag_counts"] == {}
    assert context["clean_count"] == 0


def test_build_exam_cohort_context_aggregates_across_candidates(isolated_db):
    # Second candidate needed for a real cohort - reuse the isolated_db
    # fixture's exam (id=1), add another candidate.
    conn = sqlite3.connect(isolated_db)
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (2, 'Bob', 'bob@test.com', 'hash')"
    )
    conn.commit()
    conn.close()

    # Candidate 1: flagged (medium risk)
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")
    flags_storage.create_flag(1, 1, "excessive_tab_switching", "medium", "2 switches", "max_tab_switches=2")

    # Candidate 2: clean session, no events/flags at all - but needs to
    # appear in the cohort, so give it a browser event with no resulting
    # flag (cohort membership comes from _get_cohort_candidate_ids, which
    # looks at BrowserEvents/FaceAbsenceEvents/IntegrityFlags directly).
    monitoring_storage.create_browser_event(2, 1, event_type="focus_loss")

    context = report_agent.build_exam_cohort_context(1)

    assert context["cohort_size"] == 2
    assert set(context["candidate_ids"]) == {1, 2}
    assert context["risk_breakdown"]["Medium"] == 1
    assert context["risk_breakdown"]["Low"] == 1
    assert context["flag_counts"] == {"excessive_tab_switching": 1}
    assert context["clean_count"] == 1  # candidate 2 has no flags


def test_generate_exam_summary_empty_cohort_uses_template_message(isolated_db):
    """cohort_size == 0 must never attempt an LLM call, even if one would
    otherwise be available - nothing meaningful to summarize."""
    from langchain_core.runnables import RunnableLambda

    calls = {"n": 0}

    def _tracking_llm(prompt_value):
        calls["n"] += 1
        return _StubResult("should not be called")

    result = report_agent.generate_exam_summary(1, llm=RunnableLambda(_tracking_llm))

    assert calls["n"] == 0
    assert result["source"] == "template"
    assert "no candidates have monitoring data" in result["summary"]


def test_generate_exam_summary_with_flagged_cohort_template(isolated_db, monkeypatch):
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)

    conn = sqlite3.connect(isolated_db)
    conn.execute(
        "INSERT INTO Candidates (id, name, email, password_hash) VALUES (2, 'Bob', 'bob@test.com', 'hash')"
    )
    conn.commit()
    conn.close()

    # Matches test_risk_scenario_high's setup exactly - reaching "High"
    # requires both a high- and a medium-severity flag together (combined
    # severity score crosses the threshold), not a single high flag alone.
    monitoring_storage.create_face_event(1, 1, "2026-01-01T00:00:00", "2026-01-01T00:06:00", 360)
    flags_storage.create_flag(1, 1, "face_absent_single_interval", "high", "absent 360s", "max_face_absent_seconds=120")
    flags_storage.create_flag(1, 1, "excessive_tab_switching", "medium", "4 tab switches", "max_tab_switches=2")
    monitoring_storage.create_browser_event(2, 1, event_type="tab_switch")

    result = report_agent.generate_exam_summary(1)

    assert result["cohort_size"] == 2
    assert result["source"] == "template"
    assert result["risk_breakdown"].get("High") == 1
    assert "cohort of 2 candidate(s)" in result["summary"]


def test_generate_exam_summary_uses_llm_when_provided(isolated_db):
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")

    result = report_agent.generate_exam_summary(1, llm=_StubLLM())

    assert result["source"] == "llm"
    assert result["summary"].startswith("stub summary for:")


def test_generate_exam_summary_default_path_is_cached(isolated_db, monkeypatch):
    """No explicit llm -> goes through _cached_exam_summary(). Two calls
    in quick succession should return the identical cached object (same
    id), confirming the second call didn't recompute."""
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")

    result1 = report_agent.generate_exam_summary(1)
    result2 = report_agent.generate_exam_summary(1)

    assert result1 is result2


def test_generate_exam_summary_explicit_llm_bypasses_cache(isolated_db):
    """Passing an explicit llm should never go through the cache - each
    call recomputes, so two calls return different dict objects even for
    the same exam_id."""
    monitoring_storage.create_browser_event(1, 1, event_type="tab_switch")

    result1 = report_agent.generate_exam_summary(1, llm=_StubLLM())
    result2 = report_agent.generate_exam_summary(1, llm=_StubLLM())

    assert result1 is not result2
