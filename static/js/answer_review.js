document.addEventListener("DOMContentLoaded", function () {
    const page = document.getElementById("answerReviewPage");
    const examId = page ? page.dataset.examId : null;

    const statScore = document.getElementById("statScore");
    const statPercentage = document.getElementById("statPercentage");
    const statResult = document.getElementById("statResult");

    const answerReviewList = document.getElementById("answerReviewList");
    const loadingState = document.getElementById("loadingState");
    const notSubmittedState = document.getElementById("notSubmittedState");
    const errorState = document.getElementById("errorState");

    async function fetchJSON(url) {
        const resp = await fetch(url, { headers: { "Accept": "application/json" } });
        if (!resp.ok) {
            throw new Error(`Request to ${url} failed with status ${resp.status}`);
        }
        return resp.json();
    }

    function renderSummary(data) {
        statScore.textContent = `${data.score} / ${data.total_questions}`;
        statPercentage.textContent = `${data.percentage}%`;
        statResult.textContent = data.result;
    }

    function questionStatus(question) {
        if (!question.answered) {
            return { icon: "fa-circle-minus", text: "Unanswered", cls: "answer-status-unanswered" };
        }
        if (question.is_correct) {
            return { icon: "fa-circle-check", text: "Correct", cls: "answer-status-correct" };
        }
        return { icon: "fa-circle-xmark", text: "Incorrect", cls: "answer-status-incorrect" };
    }

    function renderQuestions(questions) {
        answerReviewList.innerHTML = "";

        questions.forEach((q, index) => {
            const status = questionStatus(q);

            const item = document.createElement("div");
            item.className = "answer-review-item";
            item.innerHTML = `
                <div class="answer-review-item-top">
                    <span class="answer-review-number">Question ${index + 1}</span>
                    <span class="answer-status-badge ${status.cls}">
                        <i class="fa-solid ${status.icon}"></i> ${status.text}
                    </span>
                </div>
                <p class="answer-review-question">${q.question}</p>
                <div class="answer-review-detail">
                    <span class="answer-review-label">Your answer:</span>
                    <span class="answer-review-value">${q.answered ? q.selected_text : "Not answered"}</span>
                </div>
                <div class="answer-review-detail">
                    <span class="answer-review-label">Correct answer:</span>
                    <span class="answer-review-value">${q.correct_text}</span>
                </div>
            `;
            answerReviewList.appendChild(item);
        });
    }

    async function loadAnswerReview() {
        if (!examId) {
            loadingState.hidden = true;
            errorState.hidden = false;
            return;
        }

        loadingState.hidden = false;
        notSubmittedState.hidden = true;
        errorState.hidden = true;

        try {
            const data = await fetchJSON(`/api/attempt/${examId}/answers`);
            loadingState.hidden = true;

            if (!data.submitted) {
                notSubmittedState.hidden = false;
                return;
            }

            renderSummary(data);
            renderQuestions(data.questions);
        } catch (err) {
            loadingState.hidden = true;
            errorState.hidden = false;
            console.error(err);
        }
    }

    loadAnswerReview();
});
