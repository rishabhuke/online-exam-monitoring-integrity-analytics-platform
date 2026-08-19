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
- Provider decision: Ollama (langchain-ollama), chosen because it's free -
  runs locally, no API key, no per-token cost, no vendor rate limit. The
  trade-off is it requires Ollama installed and a model pulled on whatever
  machine runs the app (see get_default_llm() below); there's no cloud
  fallback if that's not set up, which is why the template fallback still
  exists and is still the default when no LLM is configured or reachable.
- generate_summary() falls back to a deterministic, template-based summary
  (_fallback_summary) built from the same structured context the LLM prompt
  would receive, whenever no LLM is passed in or the LLM call fails. This
  keeps the module fully testable offline and keeps app behaviour identical
  either way - only the wording source changes.
- Integrity Scoring Module (Priyanshu, Milestone 3) isn't merged yet, so
  build_session_context() computes a lightweight fallback risk label
  in-house (severity-weighted flag count vs. face-absence ratio isn't
  available without exam duration, so this only uses flag severity/counts).
  Swap _fallback_risk_label() out for a call into his scoring module once
  that PR lands - the interface (candidate_id, exam_id) -> risk label is
  meant to be a drop-in replacement.
"""

import os
from typing import Any, Dict, List, Optional

from langchain_core.prompts import PromptTemplate

from modules import flags_storage, monitoring_storage, scoring

# Ollama model name, overridable via env var so different machines can use
# whatever model they've pulled (e.g. "llama3.2", "mistral", "phi3").
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
    """Returns a ChatOllama instance if langchain-ollama is installed and an
    Ollama server is reachable, else None (caller falls back to template).

    This is the "free provider" path: no API key, runs on localhost:11434
    by default. Kept separate from generate_summary() so callers/tests can
    still pass their own `llm` (or a stub) without touching Ollama at all.
    """
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
    this tries get_default_llm() (Ollama) once; if that's unavailable or the
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
