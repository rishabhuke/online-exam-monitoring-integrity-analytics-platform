import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


# ==========================================================
# LOCAL OLLAMA MODEL
# ==========================================================

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

llm = ChatOllama(
    model=OLLAMA_MODEL,
    temperature=0.2
)


# ==========================================================
# BEHAVIOURAL ASSESSMENT PROMPT
# ==========================================================

behavioural_prompt = ChatPromptTemplate.from_messages([

    (
        "system",
        """
You are an AI examination integrity analyst.

You analyze examination behaviour for an
online examination monitoring platform.

Your analysis must be based ONLY on the
data provided.

IMPORTANT RULES:

- Do not invent violations.
- Do not invent evidence.
- Do not claim cheating is confirmed.
- Do not create events that are not present.
- Treat violation records as observed system events.
- Explain suspicious behaviour objectively.
- Use professional language suitable for an
  examination administrator.

Analyze:

1. Integrity score
2. Face presence ratio
3. Warning count
4. Individual violation types
5. Examination performance
6. Risk level

Generate a concise professional behavioural
assessment.

Use exactly these sections:

BEHAVIOURAL SUMMARY

KEY OBSERVATIONS

RISK INTERPRETATION

RECOMMENDED REVIEW

The report should explain why the candidate
received the given risk level.

Do not change the calculated integrity score.
Do not calculate a different score.
The integrity score provided by the system
is authoritative.
"""
    ),

    (
        "human",
        """
CANDIDATE INFORMATION:

{candidate}


EXAMINATION INFORMATION:

{exam}


EXAM RESULT:

{exam_result}


INTEGRITY METRICS:

{integrity}


VIOLATION BREAKDOWN:

{violations}
"""
    )

])


# ==========================================================
# GENERATE BEHAVIOURAL ASSESSMENT
# ==========================================================

def generate_behavioural_assessment(
    candidate,
    exam,
    exam_result,
    integrity,
    violations
):

    chain = (
        behavioural_prompt
        | llm
    )

    response = chain.invoke({

        "candidate":
            candidate,

        "exam":
            exam,

        "exam_result":
            exam_result,

        "integrity":
            integrity,

        "violations":
            violations

    })

    return response.content