import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


# ==========================================================
# LOCAL LLM
# ==========================================================

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

llm = ChatOllama(
    model=OLLAMA_MODEL,
    temperature=0.2,
    timeout=180
)


# ==========================================================
# EXAMINATION ANALYSIS PROMPT
# ==========================================================

exam_prompt = ChatPromptTemplate.from_messages([

    (
        "system",
        """
You are an Examination Integrity Intelligence Analyst.

Analyze the supplied examination-level integrity data.

IMPORTANT RULES:

1. Use ONLY the supplied data.
2. Never invent statistics, candidates, violations, or events.
3. Do not claim cheating is proven.
4. Risk labels indicate candidates requiring review.
5. Keep the analysis professional and objective.
6. Identify important behavioural patterns.
7. Mention technical explanations where supported by the data.
8. Give practical recommendations.

OUTPUT FORMAT:

Return ONLY the following sections.

EXAMINATION SUMMARY
Write one concise paragraph describing the examination,
difficulty, number of questions, duration, and overall
integrity situation.

COHORT PERFORMANCE
Write one concise paragraph describing the number of
candidates, average examination score, average integrity
score, average face presence, total violations, and
evidence count.

BEHAVIOURAL OBSERVATIONS
Write 3 to 5 concise bullet points describing the most
important violation patterns.

RISK PROFILE
Write one concise paragraph describing the Low, Medium,
and High risk distribution and what it means.

INTEGRITY CONCLUSION
Write one concise paragraph summarizing the overall
integrity condition of the examination.

RECOMMENDED REVIEW
Write 3 to 5 concise bullet points describing what should
be reviewed or investigated.

STRICT FORMATTING RULES:

- Do NOT use Markdown.
- Do NOT use **.
- Do NOT use ##.
- Do NOT use #.
- Do NOT use Markdown tables.
- Do NOT use ``` blocks.
- Do NOT add extra sections.
- Use the exact section names above.
- For bullet points, start each item with "- ".
- Keep the language professional and concise.
"""
    ),

    (
        "human",
        """
EXAMINATION:

{exam}

COHORT STATISTICS:

{statistics}

VIOLATION BREAKDOWN:

{violations}

RISK DISTRIBUTION:

{risk_distribution}

CANDIDATE SUMMARY:

{candidates}

Generate the examination-level integrity report.
"""
    )

])

# ==========================================================
# GENERATE REPORT
# ==========================================================

def generate_exam_behavioural_assessment(
    exam,
    statistics,
    violations,
    risk_distribution,
    candidates
):

    print("=" * 70)
    print("EXAMINATION AI ANALYSIS STARTED")
    print("=" * 70)

    print("Exam:", exam)
    print("Statistics:", statistics)
    print("Violations:", violations)
    print("Risk distribution:", risk_distribution)

    try:

        chain = exam_prompt | llm

        response = chain.invoke({

            "exam": exam,

            "statistics": statistics,

            "violations": violations,

            "risk_distribution":
                risk_distribution,

            "candidates":
                candidates

        })

        report = response.content

        print(
            "EXAMINATION AI REPORT GENERATED"
        )

        print(report)

        return report

    except Exception as error:

        print(
            "EXAMINATION AI ERROR:",
            repr(error)
        )

        raise