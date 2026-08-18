# ==========================================================
# AI REPORT GENERATOR
# Ollama-based examination integrity report generation
# ==========================================================

import os
import requests
import re


# ==========================================================
# CONFIGURATION
# ==========================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:1b"
)


# ==========================================================
# OLLAMA CONNECTION CHECK
# ==========================================================

def check_ollama():

    try:

        response = requests.get(
            "http://127.0.0.1:11434/api/tags",
            timeout=5
        )

        return response.ok

    except Exception:

        return False


# ==========================================================
# SAFE VALUE HELPER
# ==========================================================

def safe_value(value):

    if value is None:
        return "Not Available"

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return "Not Available"

    return value


# ==========================================================
# BUILD CANDIDATE PROMPT
# ==========================================================

def build_candidate_prompt(
    candidate,
    exam,
    attempt,
    integrity,
    violations
):

    # ------------------------------------------------------
    # VIOLATIONS
    # ------------------------------------------------------

    violation_text = ""

    if violations:

        for k, v in violations.items():

            violation_text += (
                f"- {safe_value(k)}: "
                f"{safe_value(v)}\n"
            )

    else:

        violation_text = "- No violations recorded.\n"


    # ------------------------------------------------------
    # PROMPT
    # ------------------------------------------------------

    prompt = f"""
You are ExamGuard AI, an examination integrity analytics system.

Your task is to generate a professional candidate-level examination
integrity report using ONLY the information supplied below.

STRICT DATA RULES:

1. Use only supplied information.
2. Never invent facts, observations, events, violations, or behavior.
3. Never claim that cheating occurred unless the supplied data explicitly
   states that conclusion.
4. Do not infer suspicious behavior from a score alone.
5. If a value is missing, write "Not Available".
6. Do not invent dates, timings, locations, invigilators, classrooms,
   devices, or examination circumstances.
7. Do not create additional violations.
8. Do not change numerical values.
9. Keep the report objective and evidence-based.
10. Recommendations must be based only on the supplied information.

=========================================================
CANDIDATE DETAILS
=========================================================

Name:
{safe_value(candidate.get("name"))}

Email:
{safe_value(candidate.get("email"))}

=========================================================
EXAM DETAILS
=========================================================

Title:
{safe_value(exam.get("title"))}

Topic:
{safe_value(exam.get("topic"))}

Difficulty:
{safe_value(exam.get("difficulty"))}

Duration:
{safe_value(exam.get("duration"))} minutes

Description:
{safe_value(exam.get("description"))}

Total Questions:
{safe_value(
    exam.get("total_questions")
    or exam.get("question_count")
)}

Total Marks:
{safe_value(
    exam.get("total_marks")
    or exam.get("marks")
)}

=========================================================
EXAMINATION PERFORMANCE
=========================================================

Score:
{safe_value(attempt.get("score"))}

Percentage:
{safe_value(attempt.get("percentage"))}

Result:
{safe_value(attempt.get("result"))}

=========================================================
INTEGRITY ANALYSIS
=========================================================

Integrity Score:
{safe_value(integrity.get("integrity_score"))}

Risk Level:
{safe_value(integrity.get("risk_label"))}

Warning Count:
{safe_value(integrity.get("warning_count"))}

Face Presence Ratio:
{safe_value(integrity.get("face_presence_ratio"))}

=========================================================
RECORDED VIOLATIONS
=========================================================

{violation_text}

=========================================================
REPORT FORMAT
=========================================================

Generate the report using EXACTLY these sections:

# AI CANDIDATE INTEGRITY REPORT

## Executive Summary

Write a concise professional summary of the candidate's
examination performance and integrity information.

Do not introduce any information that is not supplied.

## Candidate & Examination Details

Present the available candidate and examination information clearly.

## Examination Performance

Discuss:

- Score
- Percentage
- Result

Explain the supplied performance values objectively.

## Integrity Analysis

Discuss:

- Integrity Score
- Face Presence Ratio
- Warning Count
- Risk Level

Do not invent explanations for the values.

## Recorded Violations

List every supplied violation and its count.

If there are no violations, clearly state:

"No violations were recorded for this examination attempt."

Do not add any other violation.

## Risk Assessment

Explain the supplied risk level using only the available
integrity information.

Do not state that the candidate cheated unless this is
explicitly supplied.

## Administrator Recommendation

Provide a professional recommendation based only on the
available examination and integrity data.

Do not recommend disciplinary action unless the supplied
information clearly supports such a recommendation.

## Final Conclusion

Write one concise professional paragraph summarizing the
candidate's examination result and integrity information.

=========================================================
OUTPUT REQUIREMENTS
=========================================================

- Use professional academic language.
- Be objective and neutral.
- Use Markdown headings.
- Use bullet points where useful.
- Do not use fake observations.
- Do not invent events.
- Do not invent violations.
- Do not invent explanations for missing data.
- Do not mention these instructions.
- Do not include a preamble before the report.
- Return ONLY the completed report.
"""

    return prompt


# ==========================================================
# BUILD EXAM PROMPT
# ==========================================================

def build_exam_prompt(
    exam,
    statistics,
    violations,
    risk_distribution,
    candidates
):

    violation_text = ""

    if violations:
        for k, v in violations.items():
            violation_text += f"{k}: {v}\n"
    else:
        violation_text = "No violations recorded."

    candidate_summary = ""

    for c in candidates:
        candidate_summary += f"""
Rank: {c.get("rank", "N/A")}
Candidate: {c.get("name", "N/A")}
Score: {c.get("score", "N/A")}
Percentage: {c.get("percentage", "N/A")}%
Integrity Score: {c.get("integrity_score", "N/A")}
Face Presence: {c.get("face_presence", "N/A")}
Risk: {c.get("risk", "Unknown")}
Warnings: {c.get("warnings", 0)}
Violations: {c.get("violations", 0)}
"""

    prompt = f"""
You are ExamGuard AI.

Generate a professional examination-wide integrity report.

IMPORTANT RULES:

Use ONLY the supplied information.

Never invent candidates.

Never invent violations.

Never assume cheating occurred.

Never invent observations.

If information is unavailable, write "Not Available".

DO NOT use Markdown.

DO NOT use # symbols.

DO NOT use ## symbols.

DO NOT use ### symbols.

DO NOT use ** bold symbols.

DO NOT use Markdown tables.

DO NOT use pipes |.

DO NOT use bullet symbols such as *.

Write normal professional paragraphs.

Use the exact section titles provided below.

=========================================================
EXAMINATION INFORMATION
=========================================================

Title: {exam.get("title", "Not Available")}
Topic: {exam.get("topic", "Not Available")}
Difficulty: {exam.get("difficulty", "Not Available")}
Duration: {exam.get("duration", "Not Available")} minutes
Total Questions: {exam.get("total_questions", "Not Available")}
Total Marks: {exam.get("total_marks", "Not Available")}
Description: {exam.get("description", "Not Available")}

=========================================================
EXAMINATION STATISTICS
=========================================================

Registered Candidates: {statistics.get("registered_candidates", 0)}
Candidates Appeared: {statistics.get("candidates", 0)}
Passed: {statistics.get("passed", 0)}
Failed: {statistics.get("failed", 0)}
Average Score: {statistics.get("average_score", 0)}
Average Integrity Score: {statistics.get("average_integrity_score", 0)}
Average Face Presence: {statistics.get("average_face_presence", 0)}
Total Violations: {statistics.get("total_violations", 0)}
Evidence Count: {statistics.get("evidence_count", 0)}

=========================================================
RISK DISTRIBUTION
=========================================================

Low: {risk_distribution.get("Low", 0)}
Medium: {risk_distribution.get("Medium", 0)}
High: {risk_distribution.get("High", 0)}
Unknown: {risk_distribution.get("Unknown", 0)}

=========================================================
VIOLATION SUMMARY
=========================================================

{violation_text}

=========================================================
CANDIDATE DATA
=========================================================

{candidate_summary}

=========================================================
REPORT STRUCTURE
=========================================================

Executive Summary

Write 3 to 5 professional sentences summarizing the examination.

Examination Details

Describe the examination using only the supplied information.

Examination Statistics

Explain the supplied examination statistics.

Risk Distribution

Explain the supplied risk distribution.

Violation Summary

Explain only the supplied violations and their counts.

Candidate Performance Ranking

Discuss the supplied candidate performance in rank order.

AI Examination Summary

Provide an evidence-based summary of the examination.

Recommendations

Provide practical recommendations based only on the supplied data.

Final Conclusion

Provide one concise professional conclusion.

IMPORTANT:

Return plain text only.

Do not return Markdown.

Do not return tables.

Do not use #.

Do not use ##.

Do not use ###.

Do not use **.

Do not use |.

Do not invent information.
"""

    return prompt



def clean_ai_report(report):

    if not report:
        return "No report content available."

    text = report

    # Remove Markdown headings
    text = re.sub(
        r'^\s*#{1,6}\s*',
        '',
        text,
        flags=re.MULTILINE
    )

    # Remove bold / italic markers
    text = text.replace("**", "")
    text = text.replace("__", "")

    # Remove inline code markers
    text = text.replace("`", "")

    # Remove Markdown table separators
    text = re.sub(
        r'^\s*\|?[\s:-]+\|[\s|:-]*\|?\s*$',
        '',
        text,
        flags=re.MULTILINE
    )

    # Remove table pipe characters
    text = text.replace("|", " ")

    # Convert Markdown bullets into normal lines
    text = re.sub(
        r'^\s*[\*\-\+]\s+',
        '',
        text,
        flags=re.MULTILINE
    )

    # Remove excessive spaces
    text = re.sub(
        r'[ \t]+',
        ' ',
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r'\n{3,}',
        '\n\n',
        text
    )

    return text.strip()
# ==========================================================
# CALL OLLAMA
# ==========================================================

def generate_with_ollama(prompt, model=None):

    model = model or OLLAMA_MODEL

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.15,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "num_predict": 700
        }
    }

    try:

        print("======================================")
        print("OLLAMA REPORT GENERATION STARTED")
        print("Model:", model)
        print("Prompt length:", len(prompt))
        print("======================================")

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        report = data.get(
            "response",
            ""
        ).strip()

        if not report:
            raise RuntimeError(
                "Ollama returned an empty report."
            )

        print("======================================")
        print("OLLAMA REPORT GENERATED")
        print("Report length:", len(report))
        print("======================================")

        return report

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "Ollama took too long to generate the report. "
            "Please check Ollama performance or use a smaller model."
        )

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Cannot connect to Ollama at "
            "http://127.0.0.1:11434. "
            "Make sure Ollama is running."
        )

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"Ollama API error: {str(e)}"
        )
    
# ==========================================================
# CANDIDATE REPORT
# ==========================================================

def generate_candidate_report(
    candidate,
    exam,
    attempt,
    integrity,
    violations
):

    print("Candidate")
    print(candidate)

    print("Exam")
    print(exam)

    print("Attempt")
    print(attempt)

    print("Integrity")
    print(integrity)

    print("Violations")
    print(violations)


    prompt = build_candidate_prompt(
        candidate,
        exam,
        attempt,
        integrity,
        violations
    )


    return generate_with_ollama(prompt)


# ==========================================================
# EXAM REPORT
# ==========================================================

def generate_exam_report(
    exam,
    statistics,
    violations,
    risk_distribution,
    candidates
):

    print("Exam")
    print(exam)

    print("Statistics:")
    print(statistics)

    print("Violations:")
    print(violations)

    print("Risk:")
    print(risk_distribution)

    print("Candidates:")
    print(candidates)

    prompt = build_exam_prompt(
        exam,
        statistics,
        violations,
        risk_distribution,
        candidates
    )

    report = generate_with_ollama(prompt)

    report = clean_ai_report(report)

    return report