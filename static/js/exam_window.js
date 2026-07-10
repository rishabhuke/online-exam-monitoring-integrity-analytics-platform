document.addEventListener("DOMContentLoaded", function () {
    const questions = [
        {
            id: 1,
            text: "Which of the following is not a primitive data type in Java?",
            options: ["int", "String", "boolean", "double"]
        },
        {
            id: 2,
            text: "Which keyword is used to inherit a class in Java?",
            options: ["implements", "extends", "inherits", "super"]
        },
        {
            id: 3,
            text: "Which method is the entry point of a Java program?",
            options: ["start()", "run()", "main()", "init()"]
        },
        {
            id: 4,
            text: "Which of the following is used to handle exceptions in Java?",
            options: ["catch", "throws", "throw", "All of the above"]
        },
        {
            id: 5,
            text: "Which collection does not allow duplicate elements?",
            options: ["List", "Set", "ArrayList", "Vector"]
        },
        {
            id: 6,
            text: "Which operator is used for object creation in Java?",
            options: ["new", "create", "make", "init"]
        },
        {
            id: 7,
            text: "Which access modifier makes members visible only within the same class?",
            options: ["public", "private", "protected", "default"]
        },
        {
            id: 8,
            text: "Which of these is not an OOP concept in Java?",
            options: ["Encapsulation", "Polymorphism", "Compilation", "Inheritance"]
        },
        {
            id: 9,
            text: "Which package is imported by default in every Java program?",
            options: ["java.io", "java.util", "java.lang", "java.net"]
        },
        {
            id: 10,
            text: "Which loop is guaranteed to execute at least once?",
            options: ["for", "while", "do-while", "foreach"]
        }
    ];

    let currentQuestionIndex = 0;

    // state per question
    // selectedAnswer: null or option text
    // status: "not-answered" | "answered" | "review"
    const questionState = questions.map(() => ({
        selectedAnswer: null,
        status: "not-answered"
    }));

    // DOM
    const questionNumber = document.getElementById("questionNumber");
    const questionText = document.getElementById("questionText");
    const optionsList = document.getElementById("optionsList");
    const paletteGrid = document.getElementById("paletteGrid");

    const answeredCount = document.getElementById("answeredCount");
    const notAnsweredCount = document.getElementById("notAnsweredCount");
    const reviewCount = document.getElementById("reviewCount");

    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const markReviewBtn = document.getElementById("markReviewBtn");
    const clearResponseBtn = document.getElementById("clearResponseBtn");
    const submitExamBtn = document.getElementById("submitExamBtn");

    const submitModal = document.getElementById("submitModal");
    const successModal = document.getElementById("successModal");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const cancelSubmitBtn = document.getElementById("cancelSubmitBtn");
    const confirmSubmitBtn = document.getElementById("confirmSubmitBtn");
    const closeSuccessBtn = document.getElementById("closeSuccessBtn");

    const modalAnswered = document.getElementById("modalAnswered");
    const modalNotAnswered = document.getElementById("modalNotAnswered");
    const modalReview = document.getElementById("modalReview");
    const modalPaletteGrid = document.getElementById("modalPaletteGrid");

    // ================= PALETTE =================
    function buildPalette() {
        paletteGrid.innerHTML = "";

        questions.forEach((q, index) => {
            const btn = document.createElement("button");
            btn.className = "palette-btn";
            btn.textContent = q.id;
            btn.dataset.index = index;

            btn.addEventListener("click", () => {
                currentQuestionIndex = index;
                renderQuestion();
            });

            paletteGrid.appendChild(btn);
        });
    }

    function updatePalette() {
        const buttons = paletteGrid.querySelectorAll(".palette-btn");

        buttons.forEach((btn, index) => {
            btn.className = "palette-btn";

            const state = questionState[index];

            btn.classList.add(state.status);

            if (index === currentQuestionIndex) {
                btn.classList.add("current");
            }
        });
    }

    // ================= COUNTS =================
    function updateCounts() {
        let answered = 0;
        let review = 0;
        let notAnswered = 0;

        questionState.forEach(item => {
            if (item.status === "answered") answered++;
            else if (item.status === "review") review++;
            else notAnswered++;
        });

        answeredCount.textContent = answered;
        reviewCount.textContent = review;
        notAnsweredCount.textContent = notAnswered;
    }

    // ================= RENDER QUESTION =================
    function renderQuestion() {
        const question = questions[currentQuestionIndex];
        const state = questionState[currentQuestionIndex];

        questionNumber.textContent = `Question ${question.id}`;
        questionText.textContent = question.text;

        optionsList.innerHTML = "";

        question.options.forEach(option => {
            const label = document.createElement("label");
            label.className = "option-item";

            const input = document.createElement("input");
            input.type = "radio";
            input.name = `question_${question.id}`;
            input.value = option;

            if (state.selectedAnswer === option) {
                input.checked = true;
                label.classList.add("selected");
            }

            input.addEventListener("change", function () {
                questionState[currentQuestionIndex].selectedAnswer = option;
                questionState[currentQuestionIndex].status = "answered";
                renderQuestion();
                updatePalette();
                updateCounts();
            });

            const span = document.createElement("span");
            span.textContent = option;

            label.appendChild(input);
            label.appendChild(span);

            label.addEventListener("click", function () {
                setTimeout(() => {
                    questionState[currentQuestionIndex].selectedAnswer = option;
                    questionState[currentQuestionIndex].status = "answered";
                    renderQuestion();
                    updatePalette();
                    updateCounts();
                }, 0);
            });

            optionsList.appendChild(label);
        });

        prevBtn.disabled = currentQuestionIndex === 0;
        nextBtn.disabled = currentQuestionIndex === questions.length - 1;

        prevBtn.style.opacity = currentQuestionIndex === 0 ? "0.6" : "1";
        nextBtn.style.opacity = currentQuestionIndex === questions.length - 1 ? "0.6" : "1";

        updatePalette();
        updateCounts();
    }

    // ================= NAVIGATION =================
    prevBtn.addEventListener("click", function () {
        if (currentQuestionIndex > 0) {
            currentQuestionIndex--;
            renderQuestion();
        }
    });

    nextBtn.addEventListener("click", function () {
        if (currentQuestionIndex < questions.length - 1) {
            currentQuestionIndex++;
            renderQuestion();
        }
    });

    // ================= MARK REVIEW =================
    markReviewBtn.addEventListener("click", function () {
        const state = questionState[currentQuestionIndex];

        // if answer exists or not, just mark this question as review
        state.status = "review";
        updatePalette();
        updateCounts();

        if (currentQuestionIndex < questions.length - 1) {
            currentQuestionIndex++;
        }
        renderQuestion();
    });

    // ================= CLEAR RESPONSE =================
    clearResponseBtn.addEventListener("click", function () {
        questionState[currentQuestionIndex].selectedAnswer = null;
        questionState[currentQuestionIndex].status = "not-answered";
        renderQuestion();
        updatePalette();
        updateCounts();
    });

    // ================= SUBMIT PREVIEW =================
    function openSubmitPreview() {
        let answered = 0;
        let review = 0;
        let notAnswered = 0;

        questionState.forEach(item => {
            if (item.status === "answered") answered++;
            else if (item.status === "review") review++;
            else notAnswered++;
        });

        modalAnswered.textContent = answered;
        modalReview.textContent = review;
        modalNotAnswered.textContent = notAnswered;

        modalPaletteGrid.innerHTML = "";

        questionState.forEach((item, index) => {
            const div = document.createElement("div");
            div.className = `modal-palette-item ${item.status}`;
            div.textContent = `Q${index + 1}`;
            modalPaletteGrid.appendChild(div);
        });

        submitModal.classList.add("show");
    }

    submitExamBtn.addEventListener("click", openSubmitPreview);

    closeModalBtn.addEventListener("click", function () {
        submitModal.classList.remove("show");
    });

    cancelSubmitBtn.addEventListener("click", function () {
        submitModal.classList.remove("show");
    });

    confirmSubmitBtn.addEventListener("click", function () {
        submitModal.classList.remove("show");
        successModal.classList.add("show");
    });

   closeSuccessBtn.addEventListener("click", function () {
    window.location.href = "/dashboard";
});

    // close modal on overlay click
    submitModal.addEventListener("click", function (e) {
        if (e.target === submitModal) {
            submitModal.classList.remove("show");
        }
    });

    successModal.addEventListener("click", function (e) {
        if (e.target === successModal) {
            successModal.classList.remove("show");
        }
    });

    // ================= TIMER =================
    let totalSeconds = 60 * 60; // 60 mins
    const examTimer = document.getElementById("examTimer");

    function updateTimer() {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        examTimer.textContent =
            `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

        if (totalSeconds > 0) {
            totalSeconds--;
        } else {
            clearInterval(timerInterval);
            openSubmitPreview();
        }
    }

    const timerInterval = setInterval(updateTimer, 1000);
    updateTimer();

    // ================= INIT =================
    buildPalette();
    renderQuestion();
});