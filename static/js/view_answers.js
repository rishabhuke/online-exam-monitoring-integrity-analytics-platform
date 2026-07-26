"use strict";

/* ==========================================================
   VIEW ANSWERS
========================================================== */

const examName =
    document.getElementById("examName");

const questionsContainer =
    document.getElementById("questionsContainer");

const dashboardBtn =
    document.getElementById("dashboardBtn");


/* ==========================================================
   LOAD ANSWERS
========================================================== */

async function loadAnswers() {

    try {

        const response =
            await fetch(`/api/view_answers/${EXAM_ID}`);

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            alert(data.message || "Unable to load answers.");

            return;

        }

        examName.textContent =
            data.exam_name;

        renderQuestions(data.questions);

    }

    catch (error) {

        console.error(error);

        alert("Unable to connect to server.");

    }

}


/* ==========================================================
   RENDER QUESTIONS
========================================================== */

function renderQuestions(questions) {

    questionsContainer.innerHTML = "";

    questions.forEach((question, index) => {

        const card =
            document.createElement("div");

        card.className = "question-card";

        card.innerHTML = `

            <div class="question-title">

                Q${index + 1}. ${question.question}

            </div>

            ${createOption("A", question.option_a, question)}

            ${createOption("B", question.option_b, question)}

            ${createOption("C", question.option_c, question)}

            ${createOption("D", question.option_d, question)}

            <div class="legend">

                <div>

                    <div class="green-box"></div>

                    Correct Answer

                </div>

                <div>

                    <div class="red-box"></div>

                    Your Wrong Answer

                </div>

                <div>

                    <div class="gray-box"></div>

                    Other Options

                </div>

            </div>

        `;

        questionsContainer.appendChild(card);

    });

}


/* ==========================================================
   CREATE OPTION
========================================================== */

function createOption(letter, text, question) {

    let css = "option normal";

    let symbol = "○";

    /* Correct Answer */

    if (letter === question.correct_option) {

        css = "option correct";

        symbol = "✅";

    }

    /* Wrong Selected Answer */

    if (

        letter === question.selected_option &&

        question.selected_option !== question.correct_option

    ) {

        css = "option wrong";

        symbol = "❌";

    }

    /* Correctly Selected */

    if (

        letter === question.selected_option &&

        question.selected_option === question.correct_option

    ) {

        css = "option correct";

        symbol = "✅";

    }

    return `

        <div class="${css}">

            ${symbol}

            <strong>${letter}.</strong>

            ${text}

        </div>

    `;

}


/* ==========================================================
   DASHBOARD
========================================================== */

dashboardBtn.addEventListener(

    "click",

    function () {

        window.location.href = "/dashboard";

    }

);


/* ==========================================================
   START
========================================================== */

loadAnswers();