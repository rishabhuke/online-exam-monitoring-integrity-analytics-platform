import os
import json

from groq import Groq

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_quiz(subject, topic, difficulty, count):

    prompt = f"""
Generate exactly {count} multiple choice questions.

Subject: {subject}

Topic: {topic}

Difficulty: {difficulty}

Return ONLY valid JSON.

Example format:

[
    {{
        "question":"Which keyword is used for inheritance?",

        "option_a":"implements",

        "option_b":"extends",

        "option_c":"super",

        "option_d":"import",

        "correct_option":"B"
    }}
]

Rules:

1. Return ONLY JSON.

2. Do not write explanations.

3. Do not use markdown.

4. correct_option must be A/B/C/D.

"""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        temperature=0.5,

        messages=[

            {

                "role": "user",

                "content": prompt

            }

        ]

    )

    output = response.choices[0].message.content

    return json.loads(output)