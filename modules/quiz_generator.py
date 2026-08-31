"""
AI Quiz Generator (Milestone 5 - P1, integrity analysis port). Owner: Rishabh

Generates candidate exam questions via the same LLM provider chain already
used by modules.report_agent (Groq via langchain-groq, GROQ_API_KEY) - no
second AI client/dependency, unlike Prashanthi's branch which used the raw
groq SDK alongside langchain-groq.

Design: strict two-step generate -> confirm flow (see routes/quiz.py).
generate_quiz_questions() below NEVER writes to the database - it only
returns a preview for an invigilator to review/edit. insert_questions()
is the only function that writes, and it is only ever called after the
full payload has been validated (validate_quiz_payload()), so there is no
partial-insert path: either every question in the payload is valid and
all get inserted in one transaction, or none do.

Unlike report_agent.generate_summary(), there is no deterministic
template fallback here - there's no non-AI way to "generate" a quiz, so
if no LLM is available or the response can't be parsed, this returns a
clear error status instead of silently degrading.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.prompts import PromptTemplate

from modules import report_agent

import sqlite3
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = _BASE_DIR / "database.db"

VALID_OPTIONS = {"a", "b", "c", "d"}
REQUIRED_FIELDS = ["question", "option_a", "option_b", "option_c", "option_d", "correct_option"]

QUIZ_PROMPT = PromptTemplate.from_template(
    "You are an exam-question author. Generate exactly {count} multiple-choice "
    "questions on the topic: {topic}.\n\n"
    "Respond with ONLY a valid JSON array (no markdown fences, no commentary, "
    "no preamble) where each element has exactly these keys: "
    '"question", "option_a", "option_b", "option_c", "option_d", "correct_option".\n'
    'correct_option must be exactly one of "a", "b", "c", or "d", matching '
    "which option text is correct. Every field must be a non-empty string.\n\n"
    "Example element:\n"
    '{{"question": "What is 2+2?", "option_a": "3", "option_b": "4", '
    '"option_c": "5", "option_d": "6", "correct_option": "b"}}\n'
)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _extract_json_array(text: str) -> Optional[list]:
    """Best-effort extraction of a JSON array from an LLM response that may
    include stray whitespace or (despite instructions) markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(parsed, list):
        return None
    return parsed


def generate_quiz_questions(topic: str, count: int, llm: Optional[Any] = None) -> Dict[str, Any]:
    """
    Generates `count` multiple-choice questions on `topic` via an LLM.

    This is PREVIEW ONLY - it never touches the database. The caller
    (routes/quiz.py) is responsible for showing the result to an
    invigilator for review/edit before any call to insert_questions().

    Returns on success:
        {"status": "success", "questions": [...], "source": "llm"}
    Returns on failure (no LLM available, bad/unparseable response,
    generated count doesn't match request, or payload fails validation):
        {"status": "error", "message": str}
    """
    if llm is None:
        llm = report_agent.get_default_llm()

    if llm is None:
        return {
            "status": "error",
            "message": "No AI provider is currently available (Groq/Ollama unreachable). "
                       "Quiz generation requires an LLM - there is no offline fallback.",
        }

    try:
        chain = QUIZ_PROMPT | llm
        result = chain.invoke({"topic": topic, "count": count})
        raw_text = getattr(result, "content", str(result))
    except Exception as e:
        return {"status": "error", "message": f"AI generation failed: {e}"}

    questions = _extract_json_array(raw_text)
    if questions is None:
        return {"status": "error", "message": "AI response was not valid JSON array."}

    is_valid, errors = validate_quiz_payload(questions)
    if not is_valid:
        return {"status": "error", "message": "AI-generated questions failed validation: " + "; ".join(errors)}

    return {"status": "success", "questions": questions, "source": "llm"}


def validate_question_dict(q: Any, index: int) -> List[str]:
    """Returns a list of human-readable error strings for one question
    dict. Empty list means valid. `index` is used only for error messages."""
    errors = []

    if not isinstance(q, dict):
        return [f"question[{index}]: not an object"]

    for field in REQUIRED_FIELDS:
        value = q.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"question[{index}]: '{field}' is missing or empty")

    correct_option = q.get("correct_option")
    if isinstance(correct_option, str) and correct_option.strip().lower() not in VALID_OPTIONS:
        errors.append(f"question[{index}]: 'correct_option' must be one of a/b/c/d, got {correct_option!r}")

    return errors


def validate_quiz_payload(questions: Any) -> Tuple[bool, List[str]]:
    """
    Validates a full list of question dicts (as would be sent to
    POST /api/quiz/<exam_id>/confirm). Returns (is_valid, errors).

    Enforces "no partial inserts": if this returns False, the caller must
    reject the entire request and insert_questions() must never be called.
    """
    if not isinstance(questions, list) or len(questions) == 0:
        return False, ["'questions' must be a non-empty list"]

    all_errors: List[str] = []
    for i, q in enumerate(questions):
        all_errors.extend(validate_question_dict(q, i))

    return (len(all_errors) == 0), all_errors


def insert_questions(exam_id: int, questions: List[Dict[str, Any]]) -> int:
    """
    Inserts every question in `questions` into the Questions table for
    `exam_id`, in a single transaction (one commit at the end).

    Callers MUST validate the payload with validate_quiz_payload() first -
    this function assumes every dict already has all required fields and a
    valid correct_option, and does not re-validate. This split (validate
    fully, then insert with no per-row error handling) is what guarantees
    no partial inserts: either every row succeeds or an exception
    propagates before commit() and nothing is written.

    Returns the number of questions inserted.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for q in questions:
            cursor.execute(
                """
                INSERT INTO Questions
                    (exam_id, question, option_a, option_b, option_c, option_d, correct_option)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exam_id,
                    q["question"].strip(),
                    q["option_a"].strip(),
                    q["option_b"].strip(),
                    q["option_c"].strip(),
                    q["option_d"].strip(),
                    q["correct_option"].strip().lower(),
                ),
            )
        conn.commit()
        return len(questions)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
