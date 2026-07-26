let allExams = [];

/* ================================
   Load Exams
================================ */

document.addEventListener("DOMContentLoaded", () => {

    loadExams();

    document
        .getElementById("searchExam")
        .addEventListener("keyup", filterExams);

});

/* ================================
   Fetch Exams
================================ */

async function loadExams() {

    const container = document.getElementById("examContainer");

    const loading = document.getElementById("loading");

    const emptyState = document.getElementById("emptyState");

    try {

        loading.style.display = "block";

        const response = await fetch("/api/exams");

        allExams = await response.json();

        loading.style.display = "none";

        if (allExams.length === 0) {

            emptyState.style.display = "block";

            return;

        }

        document.getElementById("totalExams").innerText =
            allExams.length;

        const available =
    allExams.filter(exam =>
        exam.exam_status === "Available"
    ).length;

document.getElementById("availableExams").innerText =
    available;

        renderExams(allExams);

    }

    catch (err) {

        console.error(err);

        loading.innerHTML =
            "Unable to load examinations.";

    }

}

/* ================================
   Render Exams
================================ */

function renderExams(exams) {

    const container = document.getElementById("examContainer");

    container.innerHTML = "";

    exams.forEach(exam => {
        let statusClass = "";

switch (exam.exam_status) {

    case "Completed":
        statusClass = "completed";
        break;

    case "Unavailable":
        statusClass = "unavailable";
        break;

    default:
        statusClass = "available";
}

       let button = "";

if (exam.exam_status === "Completed") {

    button = `
        <button class="completed-btn" disabled>
            ✓ Completed
        </button>
    `;

}
else if (exam.exam_status === "Unavailable") {

    button = `
        <button class="unavailable-btn" disabled>
            Exam Not Started
        </button>
    `;

}
else {

    button = `
        <button
            class="exam-btn"
            onclick="startExam(${exam.id})">
            Start Exam
        </button>
    `;

}


        let difficultyClass = "";

        switch ((exam.difficulty || "").toLowerCase()) {

            case "easy":

                difficultyClass = "easy";

                break;

            case "medium":

                difficultyClass = "medium";

                break;

            case "hard":

                difficultyClass = "hard";

                break;

            default:

                difficultyClass = "";

        }
        

        container.innerHTML += `

        <div class="exam-card">

            <div class="exam-card-top">

                <div class="exam-title-wrap">

                    <div class="exam-icon">

                        <i class="fa-solid fa-graduation-cap"></i>

                    </div>

                    <div>

                        <h3>${exam.title}</h3>

                        <small>${exam.topic}</small>

                    </div>

                </div>

              <span class="status ${statusClass}">

    ${exam.exam_status}

</span>

            </div>

            <div class="exam-details">

                <div class="detail-item">

                    <span class="label">

                        Difficulty

                    </span>

                    <span class="value ${difficultyClass}">

                        ${exam.difficulty}

                    </span>

                </div>

                <div class="detail-item">

                    <span class="label">

                        Duration

                    </span>

                    <span class="value">

                        ${exam.duration} Minutes

                    </span>

                </div>

                <div class="detail-item">

                    <span class="label">

                        Questions

                    </span>

                    <span class="value">

                        ${exam.total_questions}

                    </span>

                </div>

                <div class="detail-item">

    <span class="label">

        Marks

    </span>

    <span class="value">

        ${exam.total_marks}

    </span>

</div>

<div class="detail-item">

    <span class="label">

        Starts

    </span>

    <span class="value">

        ${formatDateTime(exam.start_time)}

    </span>

</div>

<div class="detail-item">

    <span class="label">

        Ends

    </span>

    <span class="value">

        ${formatDateTime(exam.end_time)}

    </span>

</div>

            </div>

            <p style="margin:15px 0;color:#666;">

                ${exam.description}

            </p>

            <div class="exam-footer">

    ${button}

</div>

        </div>

        `;

    });

}

/* ================================
   Search
================================ */

function filterExams() {

    const keyword = document
        .getElementById("searchExam")
        .value
        .toLowerCase();

    const filtered = allExams.filter(exam =>

        exam.title.toLowerCase().includes(keyword) ||

        exam.topic.toLowerCase().includes(keyword)

    );

    renderExams(filtered);

}
function formatDateTime(dateTime) {

    if (!dateTime) return "-";

    const date = new Date(dateTime);

    return date.toLocaleString("en-IN", {

        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true

    });

}
/* ================================
   Start Exam
================================ */

async function startExam(examId) {
    
    try {

        await document.documentElement.requestFullscreen();

        window.location.href = "/start_exam/" + examId;

    } catch (e) {

        alert("Please allow fullscreen to start the exam.");

    }

}