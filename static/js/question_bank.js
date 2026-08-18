/* ============================================================
   EXAMGUARD AI - QUESTION BANK
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    // =========================================================
    // DOM ELEMENTS
    // =========================================================

    const examCards = document.getElementById("examCards");
    const examSearch = document.getElementById("examSearch");
    const subjectFilter = document.getElementById("subjectFilter");
    const sortFilter = document.getElementById("sortFilter");
    const refreshButton = document.getElementById("refreshQuestionBank");

    const totalExams = document.getElementById("totalExams");
    const totalQuestions = document.getElementById("totalQuestions");
    const aiGeneratedCount = document.getElementById("aiGeneratedCount");
    const examCountText = document.getElementById("examCountText");

    const answerModal = document.getElementById("answerModal");
    const answerModalBody = document.getElementById("answerModalBody");

    const answerExamTitle = document.getElementById("answerExamTitle");
    const answerExamMeta = document.getElementById("answerExamMeta");
    const answerQuestionCount = document.getElementById("answerQuestionCount");

    const closeAnswerModal = document.getElementById("closeAnswerModal");
    const closeAnswerModalBottom =
        document.getElementById("closeAnswerModalBottom");

    const modalOverlay =
        document.querySelector(".answer-modal-overlay");

    const adminName = document.getElementById("adminName");
    const adminRole = document.getElementById("adminRole");

    const notificationCount =
        document.getElementById("notificationCount");

    const toggleSidebar =
        document.getElementById("toggleSidebar");


    // =========================================================
    // STATE
    // =========================================================

    let allExams = [];
    let filteredExams = [];


    // =========================================================
    // INITIAL LOAD
    // =========================================================

    loadQuestionBank();
    loadAdminProfile();
    loadNotificationCount();


    // =========================================================
    // LOAD QUESTION BANK
    // =========================================================

    async function loadQuestionBank() {

        showLoading();

        try {

            const response = await fetch(
                "/admin/api/question-bank",
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );

            if (response.status === 401) {

                window.location.href = "/admin/login";
                return;
            }

            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            const data = await response.json();

            if (!data.success) {

                throw new Error(
                    data.message ||
                    "Unable to load question bank."
                );
            }

            allExams =
                Array.isArray(data.exams)
                    ? data.exams
                    : [];

            filteredExams = [...allExams];

            updateStatistics();

            populateSubjectFilter();

            applyFilters();

        }
        catch (error) {

            console.error(
                "Question bank loading error:",
                error
            );

            showError(
                "Unable to load examinations."
            );
        }
    }


    // =========================================================
    // SHOW LOADING
    // =========================================================

    function showLoading() {

        examCards.innerHTML = `

            <div class="qb-loading">

                <div class="spinner"></div>

                <p>
                    Loading AI-generated examinations...
                </p>

            </div>

        `;

        examCountText.textContent =
            "Loading examinations...";
    }


    // =========================================================
    // SHOW ERROR
    // =========================================================

    function showError(message) {

        examCards.innerHTML = `

            <div class="qb-empty-state">

                <div class="empty-icon">

                    <i class="fa-solid fa-triangle-exclamation"></i>

                </div>

                <h3>
                    ${escapeHtml(message)}
                </h3>

                <p>
                    Please refresh the page and try again.
                </p>

                <button
                    class="retry-btn"
                    id="retryQuestionBank"
                >
                    <i class="fa-solid fa-rotate"></i>
                    Retry
                </button>

            </div>

        `;

        examCountText.textContent =
            "Unable to load examinations.";

        const retryButton =
            document.getElementById(
                "retryQuestionBank"
            );

        if (retryButton) {

            retryButton.addEventListener(
                "click",
                loadQuestionBank
            );
        }
    }


    // =========================================================
    // UPDATE STATISTICS
    // =========================================================

    function updateStatistics() {

        const examCount =
            allExams.length;

        let questionCount = 0;

        allExams.forEach(exam => {

            questionCount +=
                Number(
                    exam.total_questions ??
                    exam.totalQuestions ??
                    exam.question_count ??
                    exam.questionCount ??
                    0
                );

        });

        totalExams.textContent =
            examCount;

        totalQuestions.textContent =
            questionCount;

        // These examinations are generated by the AI quiz generator.
        aiGeneratedCount.textContent =
            examCount;
    }


    // =========================================================
    // SUBJECT FILTER
    // =========================================================

    function populateSubjectFilter() {

        if (!subjectFilter) {
            return;
        }

        const currentValue =
            subjectFilter.value;

        const subjects =
            new Set();

        allExams.forEach(exam => {

            const subject =
                exam.subject ||
                exam.title ||
                "";

            if (subject.trim()) {

                subjects.add(
                    subject.trim()
                );
            }

        });

        subjectFilter.innerHTML = `

            <option value="all">
                All Subjects
            </option>

        `;

        Array.from(subjects)
            .sort((a, b) =>
                a.localeCompare(b)
            )
            .forEach(subject => {

                const option =
                    document.createElement("option");

                option.value =
                    subject;

                option.textContent =
                    subject;

                subjectFilter.appendChild(
                    option
                );
            });

        if (
            Array.from(
                subjectFilter.options
            ).some(
                option =>
                    option.value === currentValue
            )
        ) {

            subjectFilter.value =
                currentValue;
        }
    }


    // =========================================================
    // APPLY SEARCH / FILTER / SORT
    // =========================================================

    function applyFilters() {

        const searchTerm =
            (examSearch?.value || "")
                .trim()
                .toLowerCase();

        const selectedSubject =
            subjectFilter?.value || "all";

        const selectedSort =
            sortFilter?.value || "newest";

        filteredExams =
            allExams.filter(exam => {

                const title =
                    String(
                        exam.title ||
                        exam.examName ||
                        ""
                    ).toLowerCase();

                const topic =
                    String(
                        exam.topic ||
                        ""
                    ).toLowerCase();

                const description =
                    String(
                        exam.description ||
                        ""
                    ).toLowerCase();

                const subject =
                    String(
                        exam.subject ||
                        exam.title ||
                        ""
                    );

                const matchesSearch =
                    !searchTerm ||
                    title.includes(searchTerm) ||
                    topic.includes(searchTerm) ||
                    description.includes(searchTerm);

                const matchesSubject =
                    selectedSubject === "all" ||
                    subject === selectedSubject;

                return (
                    matchesSearch &&
                    matchesSubject
                );
            });


        // -----------------------------------------------------
        // SORT
        // -----------------------------------------------------

        filteredExams.sort(
            (a, b) => {

                if (
                    selectedSort === "title"
                ) {

                    return String(
                        a.title || ""
                    ).localeCompare(
                        String(
                            b.title || ""
                        )
                    );
                }


                if (
                    selectedSort === "questions"
                ) {

                    return (
                        getQuestionCount(b) -
                        getQuestionCount(a)
                    );
                }


                const dateA =
                    getExamDate(a);

                const dateB =
                    getExamDate(b);


                if (
                    selectedSort === "oldest"
                ) {

                    return dateA - dateB;
                }


                // newest
                return dateB - dateA;
            }
        );


        renderExamCards();
    }


    // =========================================================
    // GET QUESTION COUNT
    // =========================================================

    function getQuestionCount(exam) {

        return Number(
            exam.total_questions ??
            exam.totalQuestions ??
            exam.question_count ??
            exam.questionCount ??
            0
        );
    }


    // =========================================================
    // GET EXAM DATE
    // =========================================================

    function getExamDate(exam) {

        const value =
            exam.created_at ||
            exam.createdAt ||
            exam.start_time ||
            exam.startTime ||
            exam.id ||
            0;

        const timestamp =
            new Date(value).getTime();

        return Number.isNaN(timestamp)
            ? 0
            : timestamp;
    }


    // =========================================================
    // RENDER EXAM CARDS
    // =========================================================

    function renderExamCards() {

        examCards.innerHTML = "";

        if (
            filteredExams.length === 0
        ) {

            examCards.innerHTML = `

                <div class="qb-empty-state">

                    <div class="empty-icon">

                        <i class="fa-regular fa-folder-open"></i>

                    </div>

                    <h3>
                        No examinations found
                    </h3>

                    <p>
                        No AI-generated examinations
                        match your search.
                    </p>

                </div>

            `;

            examCountText.textContent =
                "0 examinations";

            return;
        }


        examCountText.textContent =
            filteredExams.length === 1
                ? "1 examination available"
                : `${filteredExams.length} examinations available`;


        filteredExams.forEach(
            exam => {

                const card =
                    createExamCard(exam);

                examCards.appendChild(
                    card
                );
            }
        );
    }


    // =========================================================
    // CREATE EXAM CARD
    // =========================================================

    function createExamCard(exam) {

        const card =
            document.createElement("article");

        card.className =
            "qb-exam-card";


        const examId =
            exam.id ||
            exam.exam_id ||
            exam.examId;


        const title =
            exam.title ||
            exam.examName ||
            exam.name ||
            "Untitled Examination";


        const topic =
            exam.topic ||
            "General";


        const difficulty =
            exam.difficulty ||
            "Not specified";


        const description =
            exam.description ||
            "AI-generated examination";


        const questions =
            getQuestionCount(exam);


        const duration =
            exam.duration ||
            0;


        const marks =
            exam.total_marks ??
            exam.totalMarks ??
            questions;


        const difficultyClass =
            String(
                difficulty
            ).toLowerCase();


        card.innerHTML = `

            <div class="qb-card-top">

                <div class="qb-exam-icon">

                    <i class="fa-solid fa-file-circle-check"></i>

                </div>

                <span class="ai-badge">

                    <i class="fa-solid fa-robot"></i>

                    AI Generated

                </span>

            </div>


            <div class="qb-card-body">

                <h3 class="qb-exam-title">

                    ${escapeHtml(title)}

                </h3>


                <p class="qb-exam-description">

                    ${escapeHtml(description)}

                </p>


                <div class="qb-exam-topic">

                    <i class="fa-solid fa-book-open"></i>

                    <span>
                        ${escapeHtml(topic)}
                    </span>

                </div>


                <div class="qb-exam-details">

                    <div class="qb-detail">

                        <i class="fa-solid fa-circle-question"></i>

                        <div>

                            <span>
                                Questions
                            </span>

                            <strong>
                                ${questions}
                            </strong>

                        </div>

                    </div>


                    <div class="qb-detail">

                        <i class="fa-regular fa-clock"></i>

                        <div>

                            <span>
                                Duration
                            </span>

                            <strong>
                                ${duration} min
                            </strong>

                        </div>

                    </div>


                    <div class="qb-detail">

                        <i class="fa-solid fa-star"></i>

                        <div>

                            <span>
                                Marks
                            </span>

                            <strong>
                                ${marks}
                            </strong>

                        </div>

                    </div>

                </div>


                <div class="qb-card-footer">

                    <span
                        class="difficulty-badge ${escapeHtml(difficultyClass)}"
                    >

                        ${escapeHtml(difficulty)}

                    </span>


                    <button
    class="view-answers-btn"
    onclick="openAnswerModal(${exam.id})"
>
    <i class="fa-solid fa-list-check"></i>
    View Answers
</button>

                </div>

            </div>

        `;


        const viewButton =
            card.querySelector(
                ".view-answers-btn"
            );


        if (viewButton) {

            viewButton.addEventListener(
                "click",
                () => {

                    openAnswerModal(
                        exam
                    );

                }
            );
        }


        return card;
    }


    // =========================================================
    // OPEN ANSWER MODAL
    // =========================================================

   async function openAnswerModal(examId) {

    const modal = document.getElementById("answerModal");
    const body = document.getElementById("answerModalBody");

    const title = document.getElementById("answerExamTitle");
    const meta = document.getElementById("answerExamMeta");
    const count = document.getElementById("answerQuestionCount");

    if (!modal || !body) {
        console.error("Answer modal elements not found");
        return;
    }

    // --------------------------------------------------
    // OPEN MODAL
    // --------------------------------------------------

    modal.classList.add("show");

    document.body.classList.add("modal-open");

    // --------------------------------------------------
    // LOADING
    // --------------------------------------------------

    body.innerHTML = `
        <div class="answer-loading">
            <div class="spinner"></div>
            <p>Loading questions...</p>
        </div>
    `;

    title.textContent = "Loading...";
    meta.textContent = "Answer Key";
    count.textContent = "Loading...";


    try {

        console.log(
            "Loading questions for exam:",
            examId
        );

        const response = await fetch(`/admin/api/question-bank/exam/${examId}`,
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                }
            }
        );


        // --------------------------------------------------
        // HTTP ERROR
        // --------------------------------------------------

        if (!response.ok) {

            let errorMessage =
                `HTTP ${response.status}`;

            try {

                const errorData =
                    await response.json();

                errorMessage =
                    errorData.message ||
                    errorData.error ||
                    errorMessage;

            } catch (_) {
                // Response was not JSON
            }

            throw new Error(errorMessage);
        }


        // --------------------------------------------------
        // JSON
        // --------------------------------------------------

        const result =
            await response.json();


        console.log(
            "Question bank response:",
            result
        );


        if (!result.success) {

            throw new Error(
                result.message ||
                "Unable to load answers"
            );
        }


        // --------------------------------------------------
        // EXAM DATA
        // --------------------------------------------------

        const exam =
            result.exam || {};

        const questions =
            result.questions || [];


        title.textContent =
            exam.title || "Examination";


        meta.textContent = `
            ${exam.topic || "General"}
            •
            ${exam.difficulty || "Standard"}
            •
            ${questions.length} Questions
        `;


        count.textContent =
            `${questions.length} questions`;


        // --------------------------------------------------
        // NO QUESTIONS
        // --------------------------------------------------

        if (questions.length === 0) {

            body.innerHTML = `
                <div class="no-questions">
                    <i class="fa-solid fa-circle-info"></i>

                    <h3>No Questions Found</h3>

                    <p>
                        This examination does not contain
                        any questions yet.
                    </p>
                </div>
            `;

            return;
        }


        // --------------------------------------------------
        // RENDER QUESTIONS
        // --------------------------------------------------

        body.innerHTML = "";


        questions.forEach(
            (question, index) => {

                const questionText =
                    question.question ||
                    question.question_text ||
                    question.text ||
                    `Question ${index + 1}`;


                const correctAnswer =
                    question.correct_answer ||
                    question.answer ||
                    question.correct_option ||
                    question.answer_key ||
                    "Not available";


                const optionA =
                    question.option_a ||
                    question.optionA ||
                    question.a ||
                    "";

                const optionB =
                    question.option_b ||
                    question.optionB ||
                    question.b ||
                    "";

                const optionC =
                    question.option_c ||
                    question.optionC ||
                    question.c ||
                    "";

                const optionD =
                    question.option_d ||
                    question.optionD ||
                    question.d ||
                    "";


                const options = [];

                if (optionA)
                    options.push({
                        key: "A",
                        value: optionA
                    });

                if (optionB)
                    options.push({
                        key: "B",
                        value: optionB
                    });

                if (optionC)
                    options.push({
                        key: "C",
                        value: optionC
                    });

                if (optionD)
                    options.push({
                        key: "D",
                        value: optionD
                    });


                const questionCard =
                    document.createElement("div");

                questionCard.className =
                    "answer-question-card";


                let optionsHTML = "";


                if (options.length > 0) {

                    optionsHTML = `
                        <div class="answer-options">

                            ${options.map(option => `

                                <div class="
                                    answer-option
                                    ${
                                        String(correctAnswer)
                                            .trim()
                                            .toUpperCase()
                                            === option.key
                                            ? "correct"
                                            : ""
                                    }
                                ">

                                    <span class="option-letter">
                                        ${option.key}
                                    </span>

                                    <span class="option-text">
                                        ${escapeHTML(option.value)}
                                    </span>

                                    ${
                                        String(correctAnswer)
                                            .trim()
                                            .toUpperCase()
                                            === option.key
                                            ? `
                                                <i class="
                                                    fa-solid
                                                    fa-circle-check
                                                "></i>
                                            `
                                            : ""
                                    }

                                </div>

                            `).join("")}

                        </div>
                    `;

                } else {

                    optionsHTML = `
                        <div class="answer-direct">
                            <strong>Correct Answer:</strong>
                            ${escapeHTML(correctAnswer)}
                        </div>
                    `;
                }


                questionCard.innerHTML = `

                    <div class="question-number">
                        Question ${index + 1}
                    </div>

                    <div class="question-text">
                        ${escapeHTML(questionText)}
                    </div>

                    ${optionsHTML}

                    <div class="correct-answer">

                        <i class="
                            fa-solid
                            fa-circle-check
                        "></i>

                        <span>
                            Correct Answer:
                            <strong>
                                ${escapeHTML(correctAnswer)}
                            </strong>
                        </span>

                    </div>
                `;


                body.appendChild(questionCard);
            }
        );


    } catch (error) {

        console.error(
            "Answer loading error:",
            error
        );


        body.innerHTML = `

            <div class="answer-error">

                <i class="
                    fa-solid
                    fa-triangle-exclamation
                "></i>

                <h3>
                    Unable to load answers
                </h3>

                <p>
                    ${escapeHTML(error.message)}
                </p>

                <button
                    class="retry-answer-btn"
                    onclick="openAnswerModal(${examId})"
                >
                    <i class="fa-solid fa-rotate"></i>
                    Try Again
                </button>

            </div>

        `;

        count.textContent =
            "Unable to load";

    }
}


    // =========================================================
    // RENDER ANSWERS
    // =========================================================

    function renderAnswers(questions) {

        if (
            questions.length === 0
        ) {

            answerModalBody.innerHTML = `

                <div class="answer-empty">

                    <i class="fa-regular fa-circle-question"></i>

                    <h3>
                        No questions available
                    </h3>

                    <p>
                        This examination does not contain
                        any saved questions.
                    </p>

                </div>

            `;


            answerQuestionCount.textContent =
                "0 questions";

            return;
        }


        answerQuestionCount.textContent =
            questions.length === 1
                ? "1 question"
                : `${questions.length} questions`;


        answerModalBody.innerHTML = "";


        questions.forEach(
            (question, index) => {

                const questionElement =
                    createQuestionElement(
                        question,
                        index
                    );

                answerModalBody.appendChild(
                    questionElement
                );
            }
        );
    }


    // =========================================================
    // CREATE QUESTION
    // =========================================================

    function createQuestionElement(
        question,
        index
    ) {

        const wrapper =
            document.createElement("div");

        wrapper.className =
            "answer-question";


        const correctOption =
            normalizeCorrectOption(
                question.correct_option ??
                question.correctOption ??
                question.answer
            );


        const options = [

            {
                key: "A",
                value:
                    question.option_a ??
                    question.optionA ??
                    ""
            },

            {
                key: "B",
                value:
                    question.option_b ??
                    question.optionB ??
                    ""
            },

            {
                key: "C",
                value:
                    question.option_c ??
                    question.optionC ??
                    ""
            },

            {
                key: "D",
                value:
                    question.option_d ??
                    question.optionD ??
                    ""
            }

        ];


        let optionsHtml = "";


        options.forEach(
            option => {

                const isCorrect =
                    option.key ===
                    correctOption;


                optionsHtml += `

                    <div
                        class="
                            answer-option
                            ${isCorrect
                                ? "correct-answer"
                                : ""}
                        "
                    >

                        <span class="option-letter">

                            ${option.key}

                        </span>


                        <span class="option-text">

                            ${escapeHtml(
                                option.value
                            )}

                        </span>


                        ${
                            isCorrect
                                ? `
                                    <span class="correct-label">

                                        <i class="fa-solid fa-check"></i>

                                        Correct Answer

                                    </span>
                                  `
                                : ""
                        }

                    </div>

                `;
            }
        );


        wrapper.innerHTML = `

            <div class="question-number">

                Question ${index + 1}

            </div>


            <div class="question-text">

                ${escapeHtml(
                    question.question ||
                    "Question text unavailable."
                )}

            </div>


            <div class="answer-options">

                ${optionsHtml}

            </div>


            <div class="correct-answer-summary">

                <i class="fa-solid fa-circle-check"></i>

                <span>

                    Correct Option:

                    <strong>
                        ${correctOption || "Not available"}
                    </strong>

                </span>

            </div>

        `;


        return wrapper;
    }


    // =========================================================
    // NORMALIZE CORRECT OPTION
    // =========================================================

    function normalizeCorrectOption(value) {

        if (
            value === null ||
            value === undefined
        ) {

            return "";
        }


        let option =
            String(value)
                .trim()
                .toUpperCase();


        // A / B / C / D
        if (
            ["A", "B", "C", "D"]
                .includes(option)
        ) {

            return option;
        }


        // Option A / Option B etc.
        const match =
            option.match(
                /OPTION\s*([ABCD])/
            );


        if (match) {

            return match[1];
        }


        // If database stores:
        // option_a / option_b etc.
        if (
            option.endsWith("_A") ||
            option.endsWith("-A")
        ) {

            return "A";
        }


        if (
            option.endsWith("_B") ||
            option.endsWith("-B")
        ) {

            return "B";
        }


        if (
            option.endsWith("_C") ||
            option.endsWith("-C")
        ) {

            return "C";
        }


        if (
            option.endsWith("_D") ||
            option.endsWith("-D")
        ) {

            return "D";
        }


        return option;
    }


    // =========================================================
    // CLOSE MODAL
    // =========================================================

    function closeModal() {

        answerModal.classList.remove(
            "show"
        );

        document.body.classList.remove(
            "modal-open"
        );
    }


    if (closeAnswerModal) {

        closeAnswerModal.addEventListener(
            "click",
            closeModal
        );
    }


    if (closeAnswerModalBottom) {

        closeAnswerModalBottom.addEventListener(
            "click",
            closeModal
        );
    }


    if (modalOverlay) {

        modalOverlay.addEventListener(
            "click",
            closeModal
        );
    }


    // ESC key
    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Escape" &&
                answerModal.classList.contains(
                    "show"
                )
            ) {

                closeModal();
            }
        }
    );


    // =========================================================
    // SEARCH
    // =========================================================

    if (examSearch) {

        examSearch.addEventListener(
            "input",
            applyFilters
        );
    }


    // =========================================================
    // SUBJECT FILTER
    // =========================================================

    if (subjectFilter) {

        subjectFilter.addEventListener(
            "change",
            applyFilters
        );
    }


    // =========================================================
    // SORT
    // =========================================================

    if (sortFilter) {

        sortFilter.addEventListener(
            "change",
            applyFilters
        );
    }


    // =========================================================
    // REFRESH
    // =========================================================

    if (refreshButton) {

        refreshButton.addEventListener(
            "click",
            async () => {

                refreshButton.classList.add(
                    "rotating"
                );

                await loadQuestionBank();

                setTimeout(
                    () => {

                        refreshButton.classList.remove(
                            "rotating"
                        );

                    },
                    300
                );
            }
        );
    }


    // =========================================================
    // SIDEBAR TOGGLE
    // =========================================================

    if (toggleSidebar) {

        toggleSidebar.addEventListener(
            "click",
            () => {

                document.body.classList.toggle(
                    "sidebar-collapsed"
                );

            }
        );
    }


    // =========================================================
    // LOAD ADMIN PROFILE
    // =========================================================

    async function loadAdminProfile() {

        try {

            const response =
                await fetch(
                    "/admin/api/dashboard/admin-profile",
                    {
                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {

                return;
            }


            const data =
                await response.json();


            if (
                data.success &&
                data.admin
            ) {

                adminName.textContent =
                    data.admin.full_name ||
                    data.admin.name ||
                    "Administrator";


                adminRole.textContent =
                    data.admin.username
                        ? data.admin.username
                        : "Administrator";
            }

        }
        catch (error) {

            console.error(
                "Admin profile error:",
                error
            );
        }
    }


    // =========================================================
    // LOAD NOTIFICATION COUNT
    // =========================================================

    async function loadNotificationCount() {

        try {

            const response =
                await fetch(
                    "/admin/api/notifications/count",
                    {
                        credentials:
                            "same-origin"
                    }
                );


            if (!response.ok) {

                return;
            }


            const data =
                await response.json();


            if (
                data.success &&
                notificationCount
            ) {

                notificationCount.textContent =
                    data.count || 0;
            }

        }
        catch (error) {

            console.error(
                "Notification count error:",
                error
            );
        }
    }


    // =========================================================
    // HTML ESCAPE
    // =========================================================

    function escapeHtml(value) {

        if (
            value === null ||
            value === undefined
        ) {

            return "";
        }


        return String(value)
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );
    }

});