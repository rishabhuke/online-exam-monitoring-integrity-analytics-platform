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

from modules import flags_storage, monitoring_storage

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

    return {
        "candidate_id": candidate_id,
        "exam_id": exam_id,
        "face_absence_count": len(face_events),
        "face_absence_total_seconds": face_absence_total_seconds,
        "browser_event_counts": browser_event_counts,
        "flags": flags,
        "flag_counts": flag_counts,
        "risk_label": _fallback_risk_label(flags),
    }


def _fallback_risk_label(flags: List[Dict[str, Any]]) -> str:
    """Severity-weighted risk label. Placeholder until Priyanshu's Integrity
    Scoring Module (Milestone 3) lands - see module docstring."""
    weights = {"high": 3, "medium": 2, "low": 1}
    score = sum(weights.get(f.get("severity", "low"), 1) for f in flags)

    if score >= 5:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"


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
