from integrity_ai import (
    generate_behavioural_assessment
)


candidate = {

    "name":
        "Rahul Kumar",

    "email":
        "rahul@example.com"

}


exam = {

    "title":
        "Operating Systems",

    "topic":
        "Operating Systems",

    "difficulty":
        "Medium",

    "total_questions":
        30,

    "total_marks":
        30

}


exam_result = {

    "score":
        24,

    "total_questions":
        30,

    "percentage":
        80,

    "result":
        "PASS"

}


integrity = {

    "integrity_score":
        79,

    "face_presence_ratio":
        0.80,

    "warning_count":
        4,

    "risk_label":
        "Medium"

}


violations = {

    "NO_FACE":
        1,

    "TAB_SWITCH":
        1,

    "FOCUS_LOSS":
        1,

    "FULLSCREEN_EXIT":
        1,

    "COPY_PASTE":
        0,

    "SCREENSHOT":
        0,

    "RIGHT_CLICK":
        0,

    "IDENTITY_MISMATCH":
        0,

    "MULTIPLE_FACES":
        0

}


print("=" * 70)
print("GENERATING LOCAL AI REPORT")
print("=" * 70)


result = generate_behavioural_assessment(

    candidate=
        candidate,

    exam=
        exam,

    exam_result=
        exam_result,

    integrity=
        integrity,

    violations=
        violations

)


print("\n")
print(result)


print("\n")
print("=" * 70)
print("REPORT GENERATION COMPLETE")
print("=" * 70)