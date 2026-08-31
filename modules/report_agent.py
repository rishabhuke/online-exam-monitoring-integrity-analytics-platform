"""
AI Integrity Report Agent (Milestone 3). Owner: Rishabh

Reads a candidate/exam session's structured event log (face-absence
intervals, browser events, integrity flags) and generates a concise natural
language summary for the invigilator, per the brief's example:

    "Candidate showed 3 tab switches in the first 20 minutes and face was
    absent for 4 intervals totalling 6 minutes. Overall integrity risk:
    Medium."

Design notes:
- Built with LangChain (PromptTemplate + a pluggable chat-model chain) so an
  actual LLM can be dropped in once the team decides which one to use.
- Provider: Groq (langchain-groq), chosen for speed - free tier, no card
  required, and their inference hardware is built for low latency (roughly
  1-2s for a short summary vs. 60-75s measured locally on Ollama/llama3.2 on
  a MacBook Air). Requires GROQ_API_KEY set as an env var and an internet
  connection - unlike Ollama, which is fully offline but was too slow for
  this use case (an invigilator clicking through many candidate reports).
  get_default_llm() tries Groq first, then falls back to Ollama (still
  useful for offline dev/demo), then to the template if neither is
  configured/reachable.
- generate_summary() falls back to a deterministic, template-based summary
  (_fallback_summary) built from the same structured context the LLM prompt
  would receive, whenever no LLM is passed in or the LLM call fails. This
  keeps the module fully testable offline and keeps app behaviour identical
  either way - only the wording source changes.
- build_session_context() now delegates overall risk calculation to
  modules.scoring.calculate_session_score(candidate_id, exam_id) and
  reads the returned "risk_label" for both LLM and template summaries.
  Summary wording remains local to this module, but risk-level logic is
  centralized in the scoring module.
"""

import os
import time
from typing import Any, Dict, List, Optional

from langchain_core.prompts import PromptTemplate

from modules import flags_storage, monitoring_storage, scoring, analytics

# Groq model name, overridable via env var. openai/gpt-oss-20b is fast and
# free-tier-friendly (llama-3.1-8b-instant was the original choice but Groq
# deprecated it); swap for a larger model if quality matters more than
# latency for your use case.
GROQ_MODEL = os.environ.get("REPORT_AGENT_GROQ_MODEL", "openai/gpt-oss-20b")

# Ollama model name, kept as an offline fallback. Overridable via env var so
# different machines can use whatever model they've pulled.
OLLAMA_MODEL = os.environ.get("REPORT_AGENT_OLLAMA_MODEL", "llama3.2")


REPORT_PROMPT = PromptTemplate.from_template(
    "You are an exam-integrity assistant helping an invigilator review a "
    "candidate's session. Write a concise, neutral, 2-4 sentence summary of "
    "the session below. State facts only (counts, durations, risk level) - "
    "do not accuse the candidate or recommend disciplinary action; the "
    "invigilator decides that.\n\n"
    "Candidate: {candidate_id}\n"
    "Exam: {exam_id}\n"
    "Face-absence intervals: {face_absence_count} (total {face_absence_total_seconds:.0f}s)\n"
    "Browser events: {browser_event_summary}\n"
    "Integrity flags raised: {flag_summary}\n"
    "Overall risk label: {risk_label}\n"
)


def build_session_context(candidate_id: int, exam_id: int) -> Dict[str, Any]:
    """Gathers everything known about a session into one structured dict.

    This is the single place that reaches into the other Milestone 2/3
    modules, so both generate_summary() (LLM path) and _fallback_summary()
    (template path) read from exactly the same data.
    """
    face_events = monitoring_storage.get_face_events(candidate_id=candidate_id, exam_id=exam_id)
    browser_events = monitoring_storage.get_browser_events(candidate_id=candidate_id, exam_id=exam_id)
    flags = flags_storage.get_flags_filtered(candidate_id=candidate_id, exam_id=exam_id)

    face_absence_total_seconds = sum(e.get("duration_seconds", 0) for e in face_events)

    browser_event_counts: Dict[str, int] = {}
    for e in browser_events:
        et = e.get("event_type", "unknown")
        browser_event_counts[et] = browser_event_counts.get(et, 0) + 1

    flag_counts: Dict[str, int] = {}
    for f in flags:
        flag_counts[f.get("flag_type", "unknown")] = flag_counts.get(f.get("flag_type", "unknown"), 0) + 1

    scoring_result = scoring.calculate_session_score(candidate_id, exam_id)

    return {
        "candidate_id": candidate_id,
        "exam_id": exam_id,
        "face_absence_count": len(face_events),
        "face_absence_total_seconds": face_absence_total_seconds,
        "browser_event_counts": browser_event_counts,
        "flags": flags,
        "flag_counts": flag_counts,
        "risk_label": scoring_result["risk_label"],
    }


def _format_counts(counts: Dict[str, int]) -> str:
    if not counts:
        return "none recorded"
    return ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))


def _fallback_summary(context: Dict[str, Any]) -> str:
    """Deterministic, no-LLM-required summary built from the same context
    the prompt would use. This is what generate_summary() returns whenever
    no LLM is configured (see its docstring)."""
    parts = []

    if context["face_absence_count"]:
        parts.append(
            f"face was absent for {context['face_absence_count']} interval"
            f"{'s' if context['face_absence_count'] != 1 else ''} "
            f"totalling {context['face_absence_total_seconds']:.0f}s"
        )
    else:
        parts.append("face presence was maintained throughout")

    browser_summary = _format_counts(context["browser_event_counts"])
    parts.append(f"browser activity: {browser_summary}")

    if context["flag_counts"]:
        flag_summary = _format_counts(context["flag_counts"])
        parts.append(f"{sum(context['flag_counts'].values())} integrity flag(s) raised ({flag_summary})")
    else:
        parts.append("no integrity flags were raised")

    body = "; ".join(parts)
    return (
        f"Candidate {context['candidate_id']}, exam {context['exam_id']}: {body}. "
        f"Overall integrity risk: {context['risk_label']}."
    )


def get_default_llm() -> Optional[Any]:
    """Returns the best available LLM: Groq first (fast, needs GROQ_API_KEY
    + internet), then Ollama (offline, needs a local server), else None
    (caller falls back to the template).

    Kept separate from generate_summary() so callers/tests can still pass
    their own `llm` (or a stub) without touching either provider.
    """
    groq_llm = _get_groq_llm()
    if groq_llm is not None:
        return groq_llm
    return _get_ollama_llm()


def _get_groq_llm() -> Optional[Any]:
    """Returns a ChatGroq instance if langchain-groq is installed and
    GROQ_API_KEY is set and reachable, else None."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        from langchain_groq import ChatGroq
    except ImportError:
        return None

    try:
        llm = ChatGroq(model=GROQ_MODEL, api_key=api_key)
        llm.invoke("ping")  # cheap reachability check, fails fast if key/network is bad
        return llm
    except Exception:
        return None


def _get_ollama_llm() -> Optional[Any]:
    """Returns a ChatOllama instance if langchain-ollama is installed and an
    Ollama server is reachable, else None. Fully offline fallback path -
    no API key, runs on localhost:11434 by default."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        return None

    try:
        llm = ChatOllama(model=OLLAMA_MODEL)
        llm.invoke("ping")  # cheap reachability check, fails fast if server is down
        return llm
    except Exception:
        return None


def generate_summary(candidate_id: int, exam_id: int, llm: Optional[Any] = None) -> Dict[str, Any]:
    """
    Generates the invigilator-facing integrity summary for a session.

    If `llm` is provided (any LangChain-compatible chat model / Runnable),
    it's used with REPORT_PROMPT to generate the summary. If `llm` is None,
    this tries get_default_llm() (Groq, then Ollama) once; if neither is
    call fails, it falls back to a deterministic template summary built from
    the same context - see module docstring for why.

    Returns {"summary": str, "risk_label": str, "context": dict, "source": "llm"|"template"}.
    """
    context = build_session_context(candidate_id, exam_id)

    if llm is None:
        llm = get_default_llm()

    if llm is not None:
        try:
            chain = REPORT_PROMPT | llm
            result = chain.invoke({
                "candidate_id": context["candidate_id"],
                "exam_id": context["exam_id"],
                "face_absence_count": context["face_absence_count"],
                "face_absence_total_seconds": context["face_absence_total_seconds"],
                "browser_event_summary": _format_counts(context["browser_event_counts"]),
                "flag_summary": _format_counts(context["flag_counts"]),
                "risk_label": context["risk_label"],
            })
            summary_text = getattr(result, "content", str(result))
            source = "llm"
        except Exception:
            summary_text = _fallback_summary(context)
            source = "template"
    else:
        summary_text = _fallback_summary(context)
        source = "template"

    return {
        "summary": summary_text,
        "risk_label": context["risk_label"],
        "context": context,
        "source": source,
    }

# ---------------------------------------------------------------------------
# Exam-level (cohort) summary (Milestone 5 - integrity analysis port)
#
# generate_summary() above covers one candidate's session. This covers an
# entire exam's cohort in one call, so an invigilator reviewing many
# candidates gets one aggregate read instead of opening each report
# individually. Reuses build_session_context() per candidate (same context
# generate_summary() already builds) and modules.analytics's cohort
# enumeration (_get_cohort_candidate_ids) rather than re-querying which
# candidates took an exam.
#
# Cached with the same manual TTL-dict pattern as
# modules.analytics._cached_cluster_cohort_risk (see that module's comment
# for the full rationale) - arguably more valuable here, since an LLM call
# costs real time (1-2s Groq, 60-75s Ollama) rather than a cheap recompute.
# Only the no-explicit-llm (real usage) path is cached; tests/callers
# passing their own llm bypass the cache, matching how generate_summary()
# already treats llm as an override.
# ---------------------------------------------------------------------------

COHORT_PROMPT = PromptTemplate.from_template(
    "You are an exam-integrity assistant helping an invigilator review an "
    "entire exam cohort at a glance. Write a concise, neutral, 3-5 sentence "
    "summary of the cohort below. State facts only (counts, proportions, "
    "which flag types are most common) - do not accuse any candidate or "
    "recommend disciplinary action; the invigilator reviews individual "
    "reports for that.\n\n"
    "Exam: {exam_id}\n"
    "Cohort size: {cohort_size}\n"
    "Risk breakdown: {risk_breakdown_summary}\n"
    "Most common integrity flags across the cohort: {flag_summary}\n"
    "Candidates with no flags raised: {clean_count}\n"
)


def build_exam_cohort_context(exam_id: int) -> Dict[str, Any]:
    """Gathers per-candidate contexts for every candidate in an exam's
    cohort (via modules.analytics._get_cohort_candidate_ids), then
    aggregates them into cohort-level counts. Returns an empty-cohort
    shape (cohort_size 0) rather than raising if no candidate has any
    monitoring data yet for this exam."""
    candidate_ids = analytics._get_cohort_candidate_ids(exam_id)

    per_candidate = [build_session_context(cid, exam_id) for cid in candidate_ids]

    risk_breakdown: Dict[str, int] = {}
    cohort_flag_counts: Dict[str, int] = {}
    clean_count = 0

    for ctx in per_candidate:
        risk_breakdown[ctx["risk_label"]] = risk_breakdown.get(ctx["risk_label"], 0) + 1
        if ctx["flag_counts"]:
            for flag_type, count in ctx["flag_counts"].items():
                cohort_flag_counts[flag_type] = cohort_flag_counts.get(flag_type, 0) + count
        else:
            clean_count += 1

    return {
        "exam_id": exam_id,
        "cohort_size": len(candidate_ids),
        "candidate_ids": candidate_ids,
        "risk_breakdown": risk_breakdown,
        "flag_counts": cohort_flag_counts,
        "clean_count": clean_count,
        "per_candidate": per_candidate,
    }


def _fallback_exam_summary(context: Dict[str, Any]) -> str:
    """Deterministic, no-LLM-required cohort summary - same role as
    _fallback_summary() but for a whole exam's cohort."""
    if context["cohort_size"] == 0:
        return f"Exam {context['exam_id']}: no candidates have monitoring data for this exam yet."

    risk_summary = _format_counts(context["risk_breakdown"])
    parts = [f"cohort of {context['cohort_size']} candidate(s), risk breakdown: {risk_summary}"]

    if context["flag_counts"]:
        flag_summary = _format_counts(context["flag_counts"])
        parts.append(f"most common integrity flags: {flag_summary}")
    else:
        parts.append("no integrity flags raised across the cohort")

    parts.append(f"{context['clean_count']} candidate(s) with no flags raised")

    body = "; ".join(parts)
    return f"Exam {context['exam_id']}: {body}."


def _compute_exam_summary(exam_id: int, llm: Optional[Any] = None) -> Dict[str, Any]:
    context = build_exam_cohort_context(exam_id)

    if llm is None:
        llm = get_default_llm()

    if llm is not None and context["cohort_size"] > 0:
        try:
            chain = COHORT_PROMPT | llm
            result = chain.invoke({
                "exam_id": context["exam_id"],
                "cohort_size": context["cohort_size"],
                "risk_breakdown_summary": _format_counts(context["risk_breakdown"]),
                "flag_summary": _format_counts(context["flag_counts"]),
                "clean_count": context["clean_count"],
            })
            summary_text = getattr(result, "content", str(result))
            source = "llm"
        except Exception:
            summary_text = _fallback_exam_summary(context)
            source = "template"
    else:
        summary_text = _fallback_exam_summary(context)
        source = "template"

    return {
        "summary": summary_text,
        "cohort_size": context["cohort_size"],
        "risk_breakdown": context["risk_breakdown"],
        "context": context,
        "source": source,
    }


_EXAM_SUMMARY_CACHE_TTL_SECONDS = 30.0
_exam_summary_cache: Dict[Any, Any] = {}


def _cached_exam_summary(exam_id: int) -> Dict[str, Any]:
    from pathlib import Path
    db_marker = str(getattr(scoring, "DATABASE", "unknown"))
    cache_key = (db_marker, exam_id)
    cached = _exam_summary_cache.get(cache_key)
    if cached is not None:
        cached_at, result = cached
        if time.monotonic() - cached_at < _EXAM_SUMMARY_CACHE_TTL_SECONDS:
            return result

    result = _compute_exam_summary(exam_id, llm=None)
    _exam_summary_cache[cache_key] = (time.monotonic(), result)
    return result


def generate_exam_summary(exam_id: int, llm: Optional[Any] = None) -> Dict[str, Any]:
    """
    Generates the invigilator-facing AI cohort summary for an entire exam.

    Mirrors generate_summary()'s llm-override behavior: pass an explicit
    `llm` to bypass both the default-provider lookup AND the cache (useful
    for tests/callers wanting a fresh, uncached call); omit it for normal
    usage, which uses get_default_llm() and the 30s TTL cache described
    above the cache functions.

    Returns {"summary": str, "cohort_size": int, "risk_breakdown": dict,
    "context": dict, "source": "llm"|"template"}.
    """
    if llm is not None:
        return _compute_exam_summary(exam_id, llm=llm)
    return _cached_exam_summary(exam_id)
