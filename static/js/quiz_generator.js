document.addEventListener("DOMContentLoaded", function () {

    // ==========================================================
    // ELEMENTS
    // ==========================================================

    const quizContainer = document.getElementById("quizContainer");
    const generateBtn = document.getElementById("generateBtn");
    const saveQuizBtn = document.getElementById("saveQuizBtn");

    const quizPreview = document.getElementById("quizPreview");
    const questionsContainer =
        document.getElementById("questionsContainer");


    // ==========================================================
    // VARIABLES
    // ==========================================================

    let generatedQuestions = [];
    let generatedQuiz = null;


    // ==========================================================
    // GENERATE QUIZ
    // ==========================================================

    generateBtn.addEventListener("click", async function () {

        const subject =
            document.getElementById("subject").value.trim();

        const topic =
            document.getElementById("topic").value.trim();

        const difficultyElement =
            document.querySelector(
                'input[name="difficulty"]:checked'
            );

        const difficulty =
            difficultyElement
                ? difficultyElement.value
                : "Medium";

        const count =
            parseInt(
                document.getElementById("count").value
            );

        const duration =
            parseInt(
                document.getElementById("duration").value
            );

        const startTime =
            document.getElementById("startTime").value;

        const endTime =
            document.getElementById("endTime").value;


        // ======================================================
        // VALIDATION
        // ======================================================

        if (!subject) {
            alert("Please enter a subject.");
            return;
        }

        if (!topic) {
            alert("Please enter a topic.");
            return;
        }

        if (!count || count < 1) {
            alert("Please enter a valid number of questions.");
            return;
        }

        if (!duration || duration < 5) {
            alert("Please enter a valid duration.");
            return;
        }

        if (!startTime) {
            alert("Please select start time.");
            return;
        }

        if (!endTime) {
            alert("Please select end time.");
            return;
        }


        // ======================================================
        // BUTTON LOADING
        // ======================================================

        generateBtn.disabled = true;

        generateBtn.innerHTML = `
            <span>⏳</span> Generating...
        `;


        // ======================================================
        // HIDE OLD PREVIEW WHILE GENERATING
        // ======================================================

        quizContainer.classList.remove("quiz-generated");

        questionsContainer.innerHTML = "";

        generatedQuestions = [];
        generatedQuiz = null;


        try {

            // ==================================================
            // API REQUEST
            // ==================================================

            const response = await fetch(
                "/admin/api/generate-quiz",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({

                        subject: subject,
                        topic: topic,
                        difficulty: difficulty,
                        count: count,
                        duration: duration,
                        start_time: startTime,
                        end_time: endTime

                    })
                }
            );


            // ==================================================
            // READ RESPONSE
            // ==================================================

            const result = await response.json();


            console.log(
                "QUIZ GENERATION RESPONSE:",
                result
            );


            // ==================================================
            // CHECK API RESPONSE
            // ==================================================

            if (
                !response.ok ||
                result.status !== "success"
            ) {

                alert(
                    result.message ||
                    result.error ||
                    "Quiz generation failed."
                );

                return;
            }


            // ==================================================
            // SAVE RESPONSE DATA
            // ==================================================

            generatedQuestions =
                Array.isArray(result.questions)
                    ? result.questions
                    : [];

            generatedQuiz =
                result.quiz || {};


            console.log(
                "Generated questions:",
                generatedQuestions
            );

            console.log(
                "Generated quiz:",
                generatedQuiz
            );


            // ==================================================
            // CHECK QUESTIONS
            // ==================================================

            if (generatedQuestions.length === 0) {

                alert(
                    "Quiz generated, but no questions were returned."
                );

                return;
            }


            // ==================================================
            // RENDER QUESTIONS
            // ==================================================

            renderQuestions(generatedQuestions);


            // ==================================================
            // IMPORTANT FIX
            // ==================================================
            // Add the class that activates the CSS layout.
            //
            // Without this class:
            //
            // #quizPreview {
            //     width: 0;
            //     opacity: 0;
            //     padding: 0;
            // }
            //
            // Therefore the preview remains invisible.
            // ==================================================

            quizContainer.classList.add("quiz-generated");


            // ==================================================
            // SHOW PREVIEW
            // ==================================================

            quizPreview.style.display = "flex";


            // ==================================================
            // SHOW SAVE BUTTON
            // ==================================================

            saveQuizBtn.style.display = "inline-block";


            // ==================================================
            // SCROLL PREVIEW TO TOP
            // ==================================================

            questionsContainer.scrollTop = 0;


            console.log(
                "Quiz preview displayed successfully."
            );

        }
        catch (error) {

            console.error(
                "Quiz generation error:",
                error
            );

            alert(
                "Unable to generate quiz. Check the browser console."
            );

        }
        finally {

            generateBtn.disabled = false;

            generateBtn.innerHTML = `
                <span>✦</span> Generate Quiz
            `;

        }

    });


    // ==========================================================
    // RENDER QUESTIONS
    // ==========================================================

    function renderQuestions(questions) {

        questionsContainer.innerHTML = "";


        questions.forEach(function (question, index) {

            const questionCard =
                document.createElement("div");

            questionCard.className =
                "question-card";


            questionCard.innerHTML = `

                <div class="question-number">
                    Question ${index + 1}
                </div>

                <div class="question-text">
                    ${escapeHTML(question.question)}
                </div>

                <div class="options">

                    <div class="option">
                        <strong>A.</strong>
                        ${escapeHTML(question.option_a)}
                    </div>

                    <div class="option">
                        <strong>B.</strong>
                        ${escapeHTML(question.option_b)}
                    </div>

                    <div class="option">
                        <strong>C.</strong>
                        ${escapeHTML(question.option_c)}
                    </div>

                    <div class="option">
                        <strong>D.</strong>
                        ${escapeHTML(question.option_d)}
                    </div>

                </div>

                <div class="correct-answer">
                    Correct Answer:
                    ${escapeHTML(question.correct_option)}
                </div>

            `;


            questionsContainer.appendChild(
                questionCard
            );

        });

    }


    // ==========================================================
    // ESCAPE HTML
    // ==========================================================

    function escapeHTML(value) {

        if (
            value === null ||
            value === undefined
        ) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    // ==========================================================
    // SAVE QUIZ
    // ==========================================================

    saveQuizBtn.addEventListener(
        "click",
        async function () {

            if (!generatedQuestions.length) {

                alert(
                    "Please generate questions before saving."
                );

                return;
            }


            saveQuizBtn.disabled = true;

            saveQuizBtn.innerHTML =
                "Saving...";


            try {

                const response = await fetch(
                    "/admin/api/save-quiz",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type": "application/json"
                        },

                        body: JSON.stringify({

                            ...generatedQuiz,

                            questions:
                                generatedQuestions

                        })
                    }
                );


                const result =
                    await response.json();


                console.log(
                    "SAVE QUIZ RESPONSE:",
                    result
                );


                if (
                    !response.ok ||
                    result.status !== "success"
                ) {

                    alert(
                        result.message ||
                        result.error ||
                        "Unable to save quiz."
                    );

                    return;
                }


                alert(
                    "Quiz saved successfully!"
                );

            }
            catch (error) {

                console.error(
                    "Save quiz error:",
                    error
                );

                alert(
                    "Error while saving quiz."
                );

            }
            finally {

                saveQuizBtn.disabled = false;

                saveQuizBtn.innerHTML =
                    "✓ Save Quiz";

            }

        }
    );

});