"use strict";

/* ============================================================
   AI ONLINE EXAMINATION SYSTEM
   exam_window.js
   PART 1
   Variables • DOM • Camera • Fullscreen • Initialization
============================================================ */

/* ============================================================
   GLOBAL VARIABLES
============================================================ */

let questions = [];
let questionState = [];

let currentQuestionIndex = 0;

let examStarted = false;
let submitting = false;

let cameraVerified = false;
let cameraStream = null;

let totalSeconds = 0;
let timerInterval = null;
let submittedExamId = EXAM_ID;
let warningCount = 0;
const MAX_WARNINGS = 3;


/* ============================================================
   DOM ELEMENTS
============================================================ */

/* ---------- Start Screen ---------- */

const startOverlay =
    document.getElementById("startOverlay");

const examContent =
    document.getElementById("examContent");

const checkCameraBtn =
    document.getElementById("checkCameraBtn");

const startExamBtn =
    document.getElementById("startExamBtn");

const cameraStatus =
    document.getElementById("cameraStatus");
const viewAnswersBtn =
    document.getElementById("viewAnswersBtn");


/* ---------- Header ---------- */

const examTitle =
    document.getElementById("examTitle");

const examTimer =
    document.getElementById("examTimer");

const warningCountElement =
    document.getElementById("warningCount");


/* ---------- Status ---------- */

const answeredCount =
    document.getElementById("answeredCount");

const notAnsweredCount =
    document.getElementById("notAnsweredCount");

const reviewCount =
    document.getElementById("reviewCount");


/* ---------- Question ---------- */

const paletteGrid =
    document.getElementById("paletteGrid");

const questionNumber =
    document.getElementById("questionNumber");

const questionText =
    document.getElementById("questionText");

const optionsList =
    document.getElementById("optionsList");


/* ---------- Navigation ---------- */

const prevBtn =
    document.getElementById("prevBtn");

const nextBtn =
    document.getElementById("nextBtn");

const markReviewBtn =
    document.getElementById("markReviewBtn");

const clearResponseBtn =
    document.getElementById("clearResponseBtn");

const submitExamBtn =
    document.getElementById("submitExamBtn");


/* ---------- Submit Modal ---------- */

const submitModal =
    document.getElementById("submitModal");

const modalAnswered =
    document.getElementById("modalAnswered");

const modalNotAnswered =
    document.getElementById("modalNotAnswered");

const modalReview =
    document.getElementById("modalReview");

const cancelSubmitBtn =
    document.getElementById("cancelSubmitBtn");

const confirmSubmitBtn =
    document.getElementById("confirmSubmitBtn");


/* ---------- Result Modal ---------- */

const successModal =
    document.getElementById("successModal");

const correctCount =
    document.getElementById("correctCount");

const wrongCount =
    document.getElementById("wrongCount");

const totalCount =
    document.getElementById("totalCount");

const scoreCount =
    document.getElementById("scoreCount");

const percentageCount =
    document.getElementById("percentageCount");

const resultStatus =
    document.getElementById("resultStatus");

const closeSuccessBtn =
    document.getElementById("closeSuccessBtn");


/* ============================================================
   CAMERA VERIFICATION
============================================================ */

async function verifyCamera() {

    if (cameraVerified) return;

    cameraStatus.textContent = "Checking camera...";

    try {

        cameraStream =
            await navigator.mediaDevices.getUserMedia({

                video: true,
                audio: false

            });

        cameraVerified = true;

        cameraStatus.textContent =
            "✅ Camera Verified Successfully";

        cameraStatus.classList.remove("error");
        cameraStatus.classList.add("success");

        checkCameraBtn.style.display = "none";

        startExamBtn.style.display = "inline-block";

    }

    catch (error) {

        console.error(error);

        cameraVerified = false;

        cameraStatus.textContent =
            "❌ Camera Permission Denied";

        cameraStatus.classList.remove("success");
        cameraStatus.classList.add("error");

    }

}


/* ============================================================
   START EXAM
============================================================ */

async function startExam() {

    if (!cameraVerified) {

        alert("Please verify your camera first.");

        return;

    }

    try {

        await enterFullscreen();

    }

    catch (error) {

        alert("Fullscreen permission is required.");

        return;

    }

    examStarted = true;

    startOverlay.style.display = "none";

    examContent.style.display = "block";

    /*
       Camera continues running in the background.
       No preview is displayed.
    */

    loadExam();

}


/* ============================================================
   FULLSCREEN HELPERS
============================================================ */

async function enterFullscreen() {

    if (!document.fullscreenElement) {

        await document.documentElement.requestFullscreen();

    }

}

async function exitFullscreen() {

    if (document.fullscreenElement) {

        await document.exitFullscreen();

    }

}


/* ============================================================
   WARNING DISPLAY
============================================================ */

function updateWarningDisplay() {

    warningCountElement.textContent =
        `${warningCount} / ${MAX_WARNINGS}`;

}


/* ============================================================
   CLEANUP
============================================================ */

function stopCamera() {

    if (!cameraStream) return;

    cameraStream.getTracks().forEach(track => {

        track.stop();

    });

    cameraStream = null;

}


/* ============================================================
   INITIALIZATION
============================================================ */

function initialize() {

    startExamBtn.style.display = "none";

    examContent.style.display = "none";

    updateWarningDisplay();

}


/* ============================================================
   EVENTS
============================================================ */

checkCameraBtn.addEventListener(
    "click",
    verifyCamera
);

startExamBtn.addEventListener(
    "click",
    startExam
);


/* ============================================================
   START
============================================================ */

initialize();
/* ============================================================
   PART 2
   LOAD EXAM • QUESTION PALETTE • TIMER
============================================================ */

/* ============================================================
   LOAD EXAM FROM SERVER
============================================================ */

async function loadExam() {

    try {

        const response = await fetch(`/api/exam/${EXAM_ID}`);

        const data = await response.json();
        console.log(data);

        if (!response.ok || !data.success) {

            alert(data.message || "Unable to load exam.");

            return;

        }

        questions = data.questions || [];

        examTitle.textContent =
            data.exam_name || "AI Online Examination";

        totalSeconds =
            (data.duration || 60) * 60;

        questionState = questions.map(() => ({

            selected: null,
            answered: false,
            markedReview: false

        }));

        createQuestionPalette();

updateStatusSummary();

startTimer();

renderQuestion();

updateNavigationButtons();

updateReviewButton();

initializeMonitoring();

    }
    catch (error) {

        console.error(error);

        alert("Unable to connect to server.");

    }

}


/* ============================================================
   CREATE QUESTION PALETTE
============================================================ */

function createQuestionPalette() {

    paletteGrid.innerHTML = "";

    questions.forEach((question, index) => {

        const button =
            document.createElement("button");

        button.className = "palette-btn";

        button.textContent = index + 1;

        button.addEventListener("click", () => {

    gotoQuestion(index);

});

        paletteGrid.appendChild(button);

    });

    updatePalette();

}


/* ============================================================
   UPDATE PALETTE
============================================================ */

function updatePalette() {

    const buttons =
        paletteGrid.querySelectorAll(".palette-btn");

    buttons.forEach((button, index) => {

        button.className = "palette-btn";

        if (index === currentQuestionIndex) {

            button.classList.add("current");

        }

        if (questionState[index].answered) {

            button.classList.add("answered");

        }

        if (questionState[index].markedReview) {

            button.classList.add("review");

        }

    });

}


/* ============================================================
   STATUS SUMMARY
============================================================ */

function updateStatusSummary() {

    let answered = 0;

    let review = 0;

    questionState.forEach(state => {

        if (state.answered) {

            answered++;

        }

        if (state.markedReview) {

            review++;

        }

    });

    answeredCount.textContent = answered;

    reviewCount.textContent = review;

    notAnsweredCount.textContent =
        questions.length - answered;

    updatePalette();

}


/* ============================================================
   START TIMER
============================================================ */

function startTimer() {

    clearInterval(timerInterval);

    updateTimerDisplay();

    timerInterval = setInterval(() => {

        totalSeconds--;

        updateTimerDisplay();

        if (totalSeconds <= 0) {

            clearInterval(timerInterval);

            totalSeconds = 0;

            autoSubmitExam("Time Expired");

        }

    }, 1000);

}


/* ============================================================
   UPDATE TIMER DISPLAY
============================================================ */

function updateTimerDisplay() {

    const hours =
        Math.floor(totalSeconds / 3600);

    const minutes =
        Math.floor((totalSeconds % 3600) / 60);

    const seconds =
        totalSeconds % 60;

    examTimer.textContent =
        `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

    if (totalSeconds <= 300) {

        examTimer.classList.add("danger");

    }
}
/* ============================================================
   PART 3
   RENDER QUESTION • RENDER OPTIONS • SAVE ANSWERS
============================================================ */

/* ============================================================
   RENDER CURRENT QUESTION
============================================================ */

function renderQuestion() {

    if (questions.length === 0) return;

    const question = questions[currentQuestionIndex];

    questionNumber.textContent =
        `Question ${currentQuestionIndex + 1} of ${questions.length}`;

    questionText.innerHTML = question.question;

    renderOptions(question);

    prevBtn.disabled = (currentQuestionIndex === 0);

    nextBtn.disabled =
        (currentQuestionIndex === questions.length - 1);

    updateStatusSummary();

    updateNavigationButtons();

    updateReviewButton();

    updatePalette();

}


/* ============================================================
   RENDER OPTIONS
============================================================ */

function renderOptions(question) {

    optionsList.innerHTML = "";

    const options = [

        {
            key: "A",
            value: question.option_a
        },

        {
            key: "B",
            value: question.option_b
        },

        {
            key: "C",
            value: question.option_c
        },

        {
            key: "D",
            value: question.option_d
        }

    ];

    options.forEach(option => {

        const label =
            document.createElement("label");

        label.className = "option-card";

        const radio =
            document.createElement("input");

        radio.type = "radio";

        radio.name = "questionOption";

        radio.value = option.key;

        if (
            questionState[currentQuestionIndex].selected === option.key
        ) {

            radio.checked = true;

            label.classList.add("selected");

        }

        radio.addEventListener("change", () => {

            saveAnswer(option.key);

        });

        const text =
            document.createElement("span");

        text.innerHTML =
            `<strong>${option.key}.</strong> ${option.value}`;

        label.appendChild(radio);

        label.appendChild(text);

        optionsList.appendChild(label);

    });

    updateSelectedStyle();

}


/* ============================================================
   SAVE ANSWER
============================================================ */

function saveAnswer(selectedOption) {

    const state =
        questionState[currentQuestionIndex];

    state.selected = selectedOption;

    state.answered = true;

    updateSelectedStyle();

    updateStatusSummary();

}


/* ============================================================
   UPDATE OPTION HIGHLIGHT
============================================================ */

function updateSelectedStyle() {

    const labels =
        optionsList.querySelectorAll(".option-card");

    labels.forEach(label => {

        label.classList.remove("selected");

        const radio =
            label.querySelector("input");

        if (radio.checked) {

            label.classList.add("selected");

        }

    });

}


/* ============================================================
   GET ANSWERS FOR SUBMISSION
============================================================ */

function getAnswers() {

    return questionState.map((state, index) => ({

        question_id:
            questions[index].question_id,

        selected_option:
            state.selected

    }));

}


/* ============================================================
   HELPER FUNCTIONS
============================================================ */

function answeredQuestionsCount() {

    return questionState.filter(
        state => state.answered
    ).length;

}

function unansweredQuestionsCount() {

    return questions.length -
        answeredQuestionsCount();

}

function reviewQuestionsCount() {

    return questionState.filter(
        state => state.markedReview
    ).length;

}
/* ============================================================
   PART 4
   NAVIGATION • REVIEW • CLEAR RESPONSE
============================================================ */

/* ============================================================
   GO TO QUESTION
============================================================ */

function gotoQuestion(index) {

    if (index < 0 || index >= questions.length) return;

    currentQuestionIndex = index;

    renderQuestion();

    updateReviewButton();

    updatePalette();

}


/* ============================================================
   PREVIOUS QUESTION
============================================================ */

function previousQuestion() {

    if (currentQuestionIndex > 0) {

        currentQuestionIndex--;

        renderQuestion();

        updateReviewButton();

        updatePalette();

    }

}


/* ============================================================
   NEXT QUESTION
============================================================ */

function nextQuestion() {

    if (currentQuestionIndex < questions.length - 1) {

        currentQuestionIndex++;

        renderQuestion();

        updateReviewButton();

        updatePalette();

    }

}


/* ============================================================
   UPDATE REVIEW BUTTON
============================================================ */

function updateReviewButton() {

    if (questionState.length === 0) return;

    const state = questionState[currentQuestionIndex];

    if (!state) return;

    if (state.markedReview) {

        markReviewBtn.textContent = "Remove Review";
        markReviewBtn.classList.add("active");

    } else {

        markReviewBtn.textContent = "Mark For Review";
        markReviewBtn.classList.remove("active");

    }

}


/* ============================================================
   MARK / UNMARK REVIEW
============================================================ */

function toggleReview() {

    const state = questionState[currentQuestionIndex];

    state.markedReview = !state.markedReview;

    updateReviewButton();

    updateStatusSummary();

}


/* ============================================================
   CLEAR RESPONSE
============================================================ */

function clearResponse() {

    const state = questionState[currentQuestionIndex];

    state.selected = null;

    state.answered = false;

    const radios = optionsList.querySelectorAll(
        'input[name="questionOption"]'
    );

    radios.forEach(radio => {

        radio.checked = false;

    });

    updateSelectedStyle();

    updateStatusSummary();

}


/* ============================================================
   UPDATE NAVIGATION BUTTONS
============================================================ */

function updateNavigationButtons() {

    prevBtn.disabled =
        currentQuestionIndex === 0;

    nextBtn.disabled =
        currentQuestionIndex === questions.length - 1;

}


/* ============================================================
   OVERRIDE renderQuestion()
============================================================ */



/* ============================================================
   BUTTON EVENTS
============================================================ */

prevBtn.addEventListener(
    "click",
    previousQuestion
);

nextBtn.addEventListener(
    "click",
    nextQuestion
);

markReviewBtn.addEventListener(
    "click",
    toggleReview
);

clearResponseBtn.addEventListener(
    "click",
    clearResponse
);


/* ============================================================
   KEYBOARD NAVIGATION
============================================================ */

document.addEventListener("keydown", function (event) {

    if (!examStarted) return;

    switch (event.key) {

        case "ArrowLeft":
            previousQuestion();
            break;

        case "ArrowRight":
            nextQuestion();
            break;

    }

});


/* ============================================================
   INITIAL UI STATE
============================================================ */

updateNavigationButtons();

/* ============================================================
   PART 5
   SECURITY • WARNINGS • VIOLATIONS
============================================================ */

/* ============================================================
   INITIALIZE SECURITY MONITORING
============================================================ */

function initializeMonitoring() {

    document.addEventListener(
        "fullscreenchange",
        handleFullscreenChange
    );

    document.addEventListener(
        "visibilitychange",
        handleVisibilityChange
    );

    window.addEventListener(
        "blur",
        handleWindowBlur
    );

}


/* ============================================================
   FULLSCREEN EXIT DETECTION
============================================================ */

function handleFullscreenChange() {

    if (!examStarted) return;

    if (submitting) return;

    if (document.fullscreenElement) return;

    addViolation("Fullscreen exited");

}


/* ============================================================
   TAB SWITCH DETECTION
============================================================ */

function handleVisibilityChange() {

    if (!examStarted) return;

    if (submitting) return;

    if (document.hidden) {

        addViolation("Browser tab changed");

    }

}


/* ============================================================
   WINDOW FOCUS LOST
============================================================ */

function handleWindowBlur() {

    if (!examStarted) return;

    if (submitting) return;

    addViolation("Window lost focus");

}


/* ============================================================
   ADD WARNING
============================================================ */

function addViolation(reason) {

    warningCount++;

    updateWarningDisplay();

    console.warn(
        `Violation ${warningCount}/${MAX_WARNINGS}: ${reason}`
    );

    alert(
        `${reason}\n\nWarning ${warningCount} of ${MAX_WARNINGS}`
    );

    if (warningCount >= MAX_WARNINGS) {

        autoSubmitExam("Maximum warnings exceeded");

        return;

    }

    setTimeout(() => {

        if (
            examStarted &&
            !document.fullscreenElement
        ) {

            enterFullscreen();

        }

    }, 300);

}


/* ============================================================
   AUTO SUBMIT
============================================================ */

function autoSubmitExam(reason) {

    if (submitting) return;

    clearInterval(timerInterval);

    stopCamera();

    submitExam(reason);

}


/* ============================================================
   CLEANUP SECURITY EVENTS
============================================================ */

function removeMonitoring() {

    document.removeEventListener(
        "fullscreenchange",
        handleFullscreenChange
    );

    document.removeEventListener(
        "visibilitychange",
        handleVisibilityChange
    );

    window.removeEventListener(
        "blur",
        handleWindowBlur
    );

}
/* ============================================================
   PART 6
   SUBMIT PREVIEW
============================================================ */

/* ============================================================
   OPEN SUBMIT PREVIEW
============================================================ */

function openSubmitPreview() {

    if (!examStarted) return;

    modalAnswered.textContent =
        answeredQuestionsCount();

    modalNotAnswered.textContent =
        unansweredQuestionsCount();

    modalReview.textContent =
        reviewQuestionsCount();

    submitModal.style.display = "flex";

}


/* ============================================================
   CLOSE SUBMIT PREVIEW
============================================================ */

function closeSubmitPreview() {

    submitModal.style.display = "none";

}


/* ============================================================
   CONFIRM SUBMIT
============================================================ */

function confirmSubmission() {

    closeSubmitPreview();

    submitExam("User Submitted");

}


/* ============================================================
   BUTTON EVENTS
============================================================ */

submitExamBtn.addEventListener(

    "click",

    openSubmitPreview

);

cancelSubmitBtn.addEventListener(

    "click",

    closeSubmitPreview

);

confirmSubmitBtn.addEventListener(

    "click",

    confirmSubmission

);


/* ============================================================
   CLOSE MODAL ON OUTSIDE CLICK
============================================================ */

submitModal.addEventListener("click", function (event) {

    if (event.target === submitModal) {

        closeSubmitPreview();

    }

});


/* ============================================================
   ESC KEY CLOSE
============================================================ */

document.addEventListener("keydown", function (event) {

    if (event.key === "Escape") {

        if (submitModal.style.display === "flex") {

            closeSubmitPreview();

        }

    }

});
/* ============================================================
   PART 7
   SUBMIT EXAM TO FLASK
============================================================ */

/* ============================================================
   SUBMIT EXAM
============================================================ */

async function submitExam(reason = "User Submitted") {

    if (submitting) return;

    submitting = true;

    clearInterval(timerInterval);

    removeMonitoring();

    const payload = {

        exam_id: EXAM_ID,

        answers: getAnswers()

    };

    try {

        const response = await fetch("/submit_exam", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify(payload)

        });

        const data = await response.json();

        if (!response.ok || !data.success) {

            throw new Error(
                data.message || "Unable to submit exam."
            );

        }

        showResult(data);

    }
    catch (error) {

        console.error(error);

        alert(error.message || "Submission failed.");

        submitting = false;

    }

}


/* ============================================================
   DISPLAY RESULT
============================================================ */


/* ============================================================
   CLOSE RESULT
============================================================ */

/* ============================================================
   PART 8
   RESULT MODAL • EXIT FULLSCREEN • REDIRECT
============================================================ */

/* ============================================================
   SHOW RESULT MODAL
============================================================ */

function showResult(result) {

    correctCount.textContent =
        result.score ?? 0;

    wrongCount.textContent =
        result.wrong ?? 0;

    totalCount.textContent =
        result.total ?? questions.length;

    scoreCount.textContent =
        result.score ?? 0;

    percentageCount.textContent =
        `${result.percentage ?? 0}%`;

    resultStatus.textContent =
        result.result ?? "Completed";

    if ((result.percentage ?? 0) >= 50) {

        resultStatus.style.color = "#16a34a";

    } else {

        resultStatus.style.color = "#dc2626";

    }

    successModal.style.display = "flex";
    submittedExamId = EXAM_ID;

}


/* ============================================================
   CLOSE RESULT MODAL
============================================================ */

async function closeResultModal() {

    successModal.style.display = "none";

    clearInterval(timerInterval);

    removeMonitoring();

    stopCamera();

    try {

        await exitFullscreen();

    }
    catch (error) {

        console.error(error);

    }

    window.location.href = "/dashboard";

}


/* ============================================================
   RESULT BUTTON
============================================================ */

closeSuccessBtn.addEventListener(

    "click",

    closeResultModal

);
viewAnswersBtn.addEventListener("click", function(){

    window.location.href =
        `/view_answers/${submittedExamId}`;

});


/* ============================================================
   PREVENT ACCIDENTAL PAGE LEAVE
============================================================ */

window.addEventListener("beforeunload", function (event) {

    if (!examStarted || submitting) {

        return;

    }

    event.preventDefault();

    event.returnValue = "";

});


/* ============================================================
   EXAM CLEANUP
============================================================ */

function cleanupExam() {

    clearInterval(timerInterval);

    removeMonitoring();

    stopCamera();

}


/* ============================================================
   RESET EXAM (OPTIONAL)
============================================================ */

function resetExamState() {

    questions = [];

    questionState = [];

    currentQuestionIndex = 0;

    examStarted = false;

    submitting = false;

    cameraVerified = false;

    warningCount = 0;

    totalSeconds = 0;

}