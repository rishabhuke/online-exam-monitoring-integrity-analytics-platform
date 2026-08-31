"""
Tests for modules/quiz_generator.py (Milestone 5 - P1, AI quiz generator).
Owner: Rishabh

Run with:
    python -m pytest tests/test_quiz_generator.py -v

No real LLM call in any test - uses langchain_core.runnables.RunnableLambda
stubs, same pattern as tests/test_report_agent.py's _StubLLM(), so these
are fully deterministic and offline.
"""

import os
import sys
import sqlite3

import pytest
from langchain_core.runnables import RunnableLambda

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import modules.quiz_generator as quiz_generator
import modules.report_agent as report_agent


# ---------------------------------------------------------------------------
# validate_question_dict / validate_quiz_payload
# ---------------------------------------------------------------------------

VALID_QUESTION = {
    "question": "What is 2+2?",
    "option_a": "3",
    "option_b": "4",
    "option_c": "5",
    "option_d": "6",
    "correct_option": "b",
}


def test_validate_question_dict_valid_question_has_no_errors():
    errors = quiz_generator.validate_question_dict(VALID_QUESTION, 0)
    assert errors == []


def test_validate_question_dict_not_a_dict():
    errors = quiz_generator.validate_question_dict("not a dict", 0)
    assert len(errors) == 1
    assert "not an object" in errors[0]


def test_validate_question_dict_missing_field():
    q = dict(VALID_QUESTION)
    del q["option_c"]
    errors = quiz_generator.validate_question_dict(q, 2)
    assert any("option_c" in e and "question[2]" in e for e in errors)


def test_validate_question_dict_empty_string_field():
    q = dict(VALID_QUESTION)
    q["question"] = "   "
    errors = quiz_generator.validate_question_dict(q, 0)
    assert any("'question'" in e for e in errors)


def test_validate_question_dict_invalid_correct_option():
    q = dict(VALID_QUESTION)
    q["correct_option"] = "e"
    errors = quiz_generator.validate_question_dict(q, 0)
    assert any("correct_option" in e for e in errors)


def test_validate_question_dict_correct_option_case_insensitive():
    q = dict(VALID_QUESTION)
    q["correct_option"] = "B"
    errors = quiz_generator.validate_question_dict(q, 0)
    assert errors == []


def test_validate_quiz_payload_valid_list():
    is_valid, errors = quiz_generator.validate_quiz_payload([VALID_QUESTION, VALID_QUESTION])
    assert is_valid is True
    assert errors == []


def test_validate_quiz_payload_empty_list_is_invalid():
    is_valid, errors = quiz_generator.validate_quiz_payload([])
    assert is_valid is False
    assert len(errors) == 1


def test_validate_quiz_payload_not_a_list_is_invalid():
    is_valid, errors = quiz_generator.validate_quiz_payload({"not": "a list"})
    assert is_valid is False


def test_validate_quiz_payload_one_bad_question_fails_whole_batch():
    """This is the 'no partial inserts' guarantee at the validation layer -
    one invalid question in an otherwise-valid batch must fail the whole
    payload, not just be silently dropped."""
    bad = dict(VALID_QUESTION)
    bad["correct_option"] = "z"
    is_valid, errors = quiz_generator.validate_quiz_payload([VALID_QUESTION, bad, VALID_QUESTION])

    assert is_valid is False
    assert any("question[1]" in e for e in errors)


# ---------------------------------------------------------------------------
# generate_quiz_questions
# ---------------------------------------------------------------------------

class _StubResult:
    def __init__(self, content):
        self.content = content


def _stub_llm_returning(text):
    return RunnableLambda(lambda prompt_value: _StubResult(text))


def test_generate_quiz_questions_no_llm_available_returns_error(monkeypatch):
    monkeypatch.setattr(report_agent, "get_default_llm", lambda: None)

    result = quiz_generator.generate_quiz_questions("Python basics", 3)

    assert result["status"] == "error"
    assert "No AI provider" in result["message"]


def test_generate_quiz_questions_success_with_valid_json():
    import json
    questions = [VALID_QUESTION, VALID_QUESTION, VALID_QUESTION]
    stub = _stub_llm_returning(json.dumps(questions))

    result = quiz_generator.generate_quiz_questions("Python basics", 3, llm=stub)

    assert result["status"] == "success"
    assert result["source"] == "llm"
    assert len(result["questions"]) == 3


def test_generate_quiz_questions_strips_markdown_fences():
    import json
    fenced = "```json\n" + json.dumps([VALID_QUESTION]) + "\n```"
    stub = _stub_llm_returning(fenced)

    result = quiz_generator.generate_quiz_questions("Python basics", 1, llm=stub)

    assert result["status"] == "success"
    assert len(result["questions"]) == 1


def test_generate_quiz_questions_malformed_json_returns_error():
    stub = _stub_llm_returning("this is not JSON at all")

    result = quiz_generator.generate_quiz_questions("Python basics", 1, llm=stub)

    assert result["status"] == "error"
    assert "not valid JSON" in result["message"]


def test_generate_quiz_questions_non_array_json_returns_error():
    stub = _stub_llm_returning('{"not": "an array"}')

    result = quiz_generator.generate_quiz_questions("Python basics", 1, llm=stub)

    assert result["status"] == "error"


def test_generate_quiz_questions_llm_returns_invalid_question_fails_validation():
    """Even if the LLM returns syntactically valid JSON, a semantically
    invalid question (bad correct_option, missing field) must still fail -
    generate_quiz_questions() validates before ever calling it 'success'."""
    import json
    bad = dict(VALID_QUESTION)
    bad["correct_option"] = "z"
    stub = _stub_llm_returning(json.dumps([bad]))

    result = quiz_generator.generate_quiz_questions("Python basics", 1, llm=stub)

    assert result["status"] == "error"
    assert "failed validation" in result["message"]


def test_generate_quiz_questions_llm_exception_returns_error():
    def _raise(prompt_value):
        raise RuntimeError("provider unreachable")

    stub = RunnableLambda(_raise)

    result = quiz_generator.generate_quiz_questions("Python basics", 1, llm=stub)

    assert result["status"] == "error"
    assert "AI generation failed" in result["message"]


# ---------------------------------------------------------------------------
# insert_questions (needs an isolated DB - only insert_questions touches SQL)
# ---------------------------------------------------------------------------

@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(quiz_generator, "DATABASE", test_db)

    conn = sqlite3.connect(test_db)
    conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    with open(schema_path) as f:
        conn.executescript(f.read())

    conn.execute("INSERT INTO Exams (id, title, duration) VALUES (1, 'Test Exam', 60)")
    conn.commit()
    conn.close()

    return test_db


def test_insert_questions_writes_all_rows_and_commits(isolated_db):
    questions = [VALID_QUESTION, dict(VALID_QUESTION, question="What is 3+3?")]

    inserted_count = quiz_generator.insert_questions(1, questions)

    assert inserted_count == 2

    conn = sqlite3.connect(isolated_db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM Questions WHERE exam_id = 1").fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0]["correct_option"] == "b"
    assert rows[0]["question"] == "What is 2+2?"


def test_insert_questions_lowercases_and_strips_correct_option(isolated_db):
    q = dict(VALID_QUESTION, correct_option="  B  ")

    quiz_generator.insert_questions(1, [q])

    conn = sqlite3.connect(isolated_db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM Questions WHERE exam_id = 1").fetchone()
    conn.close()

    assert row["correct_option"] == "b"
