import os
import json

from dotenv import load_dotenv
from groq import Groq


# =========================================================
# LOAD ROOT .ENV
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(ENV_PATH)


# =========================================================
# GROQ API
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not configured"
    )


client = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# GENERATE QUIZ
# =========================================================

def generate_quiz(
    subject,
    topic,
    difficulty,
    count
):

    prompt = f"""
Generate exactly {count} multiple choice questions.

Subject: {subject}

Topic: {topic}

Difficulty: {difficulty}

Return ONLY valid JSON.

The JSON must be an array in exactly this format:

[
    {{
        "question": "Question text",
        "option_a": "Option A",
        "option_b": "Option B",
        "option_c": "Option C",
        "option_d": "Option D",
        "correct_option": "A"
    }}
]

Rules:

1. Generate exactly {count} questions.
2. Return ONLY JSON.
3. Do not use markdown.
4. Do not include explanations.
5. Do not include text before or after the JSON.
6. Every question must have exactly four options.
7. correct_option must be exactly one of:
   A
   B
   C
   D
8. Questions must match the requested subject, topic and difficulty.
"""


    # =====================================================
    # CALL GROQ
    # =====================================================

    response = client.chat.completions.create(

        model="openai/gpt-oss-120b",

        temperature=0.5,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )


    # =====================================================
    # GET RESPONSE
    # =====================================================

    output = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )


    print(
        "GROQ RAW RESPONSE:"
    )

    print(output)


    # =====================================================
    # REMOVE MARKDOWN CODE FENCES
    # =====================================================

    if output.startswith("```json"):

        output = output[
            len("```json"):
        ]

    elif output.startswith("```"):

        output = output[
            len("```"):
        ]


    if output.endswith("```"):

        output = output[
            :-len("```")
        ]


    output = output.strip()


    # =====================================================
    # PARSE JSON
    # =====================================================

    try:

        questions = json.loads(
            output
        )

    except json.JSONDecodeError as error:

        print(
            "JSON PARSE ERROR:"
        )

        print(
            repr(error)
        )

        print(
            "INVALID GROQ OUTPUT:"
        )

        print(output)

        raise ValueError(
            "Groq returned invalid JSON."
        )


    # =====================================================
    # VALIDATE RESPONSE
    # =====================================================

    if not isinstance(
        questions,
        list
    ):

        raise ValueError(
            "Groq response is not a list."
        )


    if len(questions) == 0:

        raise ValueError(
            "Groq returned zero questions."
        )


    # =====================================================
    # VALIDATE EACH QUESTION
    # =====================================================

    required_fields = [
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_option"
    ]


    validated_questions = []


    for index, question in enumerate(
        questions,
        start=1
    ):

        if not isinstance(
            question,
            dict
        ):

            raise ValueError(
                f"Question {index} is not an object."
            )


        # -------------------------------------------------
        # CHECK REQUIRED FIELDS
        # -------------------------------------------------

        for field in required_fields:

            value = str(
                question.get(
                    field,
                    ""
                )
            ).strip()


            if not value:

                raise ValueError(
                    f"Missing {field} "
                    f"in question {index}."
                )


        # -------------------------------------------------
        # CORRECT OPTION
        # -------------------------------------------------

        correct_option = str(
            question[
                "correct_option"
            ]
        ).strip().upper()


        if correct_option not in [
            "A",
            "B",
            "C",
            "D"
        ]:

            raise ValueError(
                f"Invalid correct option "
                f"in question {index}: "
                f"{correct_option}"
            )


        # -------------------------------------------------
        # STORE CLEAN QUESTION
        # -------------------------------------------------

        validated_questions.append({

            "question":
                str(
                    question["question"]
                ).strip(),

            "option_a":
                str(
                    question["option_a"]
                ).strip(),

            "option_b":
                str(
                    question["option_b"]
                ).strip(),

            "option_c":
                str(
                    question["option_c"]
                ).strip(),

            "option_d":
                str(
                    question["option_d"]
                ).strip(),

            "correct_option":
                correct_option

        })


    # =====================================================
    # CHECK COUNT
    # =====================================================

    if len(validated_questions) != int(count):

        raise ValueError(
            f"Expected {count} questions, "
            f"but Groq returned "
            f"{len(validated_questions)}."
        )


    # =====================================================
    # RETURN
    # =====================================================

    return validated_questions