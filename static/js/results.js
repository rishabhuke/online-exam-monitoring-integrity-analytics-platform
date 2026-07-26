"use strict";

/* ==========================================================
   RESULTS
========================================================== */

let results = [];

const tableBody =
    document.getElementById("resultsTableBody");

const totalExams =
    document.getElementById("totalExamsCount");

const passedCount =
    document.getElementById("passedCount");

const failedCount =
    document.getElementById("failedCount");

const averageScore =
    document.getElementById("avgScore");

const noResults =
    document.getElementById("noResultsMessage");


/* ==========================================================
   LOAD RESULTS
========================================================== */

async function loadResults() {

    try {

        const response =
            await fetch("/api/results");

        if (!response.ok) {

            throw new Error("Unable to fetch results.");

        }

        results =
            await response.json();

        renderTable(results);

        updateSummary(results);

    }

    catch (error) {

        console.error(error);

        tableBody.innerHTML = "";

        noResults.style.display = "block";

    }

}


/* ==========================================================
   UPDATE SUMMARY
========================================================== */

function updateSummary(data) {

    totalExams.textContent =
        data.length;

    const passed =
        data.filter(result => result.result === "PASS").length;

    const failed =
        data.filter(result => result.result === "FAIL").length;

    passedCount.textContent =
        passed;

    failedCount.textContent =
        failed;

    if (data.length === 0) {

        averageScore.textContent = "0%";

        return;

    }

    const average =

        data.reduce(

            (sum, result) =>

                sum + Number(result.percentage),

            0

        ) / data.length;

    averageScore.textContent =
        average.toFixed(1) + "%";

}


/* ==========================================================
   RENDER TABLE
========================================================== */

function renderTable(data) {

    tableBody.innerHTML = "";

    if (data.length === 0) {

        noResults.style.display = "block";

        return;

    }

    noResults.style.display = "none";

    data.forEach((result, index) => {

        tableBody.innerHTML += `

        <tr>

            <td>${index + 1}</td>

            <td>${result.title}</td>

            <td>${result.topic}</td>

            <td>${result.difficulty}</td>

            <td>

                ${result.score}

                /

                ${result.total_questions}

            </td>

            <td>

                ${result.percentage}%

            </td>

            <td>

                <span class="status-badge

                ${result.result === "PASS"

                    ? "passed-badge"

                    : "failed-badge"}

                ">

                    ${result.result}

                </span>

            </td>

            <td>

                <button

                    class="table-action-btn"

                    onclick="openResult(${result.exam_id})"

                >

                    View Report

                </button>

            </td>

        </tr>

        `;

    });

}


/* ==========================================================
   INITIAL LOAD
========================================================== */

loadResults();
/* ==========================================================
   SEARCH & FILTER
========================================================== */

const searchInput =
    document.getElementById("resultSearch");

const statusFilter =
    document.getElementById("statusFilter");

searchInput.addEventListener("input", filterResults);

statusFilter.addEventListener("change", filterResults);

function filterResults() {

    const keyword =
        searchInput.value.toLowerCase().trim();

    const status =
        statusFilter.value;

    const filtered = results.filter(result => {

        const matchTitle =
            result.title.toLowerCase().includes(keyword);

        const matchStatus =
            status === "all" ||
            result.result === status;

        return matchTitle && matchStatus;

    });

    renderTable(filtered);

}



/* ==========================================================
   RESULT MODAL
========================================================== */

const resultModal =
    document.getElementById("resultModal");

const closeModal =
    document.getElementById("closeModal");

const resultDetails =
    document.getElementById("resultDetails");

const viewAnswersBtn =
    document.getElementById("viewAnswersBtn");

let selectedExamId = null;



/* ==========================================================
   OPEN RESULT
========================================================== */

function openResult(examId) {

    selectedExamId = examId;

    const result = results.find(

        r => r.exam_id === examId

    );

    if (!result)
        return;

    resultDetails.innerHTML = `

        <div class="detail-row">

            <span class="detail-label">

                Exam

            </span>

            <span class="detail-value">

                ${result.title}

            </span>

        </div>

        <div class="detail-row">

            <span class="detail-label">

                Topic

            </span>

            <span class="detail-value">

                ${result.topic}

            </span>

        </div>

        <div class="detail-row">

            <span class="detail-label">

                Difficulty

            </span>

            <span class="detail-value">

                ${result.difficulty}

            </span>

        </div>

        <div class="detail-row">

            <span class="detail-label">

                Score

            </span>

            <span class="detail-value">

                ${result.score} / ${result.total_questions}

            </span>

        </div>

        <div class="detail-row">

            <span class="detail-label">

                Percentage

            </span>

            <span class="detail-value">

                ${result.percentage}%

            </span>

        </div>

        <div class="detail-row">

            <span class="detail-label">

                Result

            </span>

            <span class="detail-value">

                ${result.result}

            </span>

        </div>

    `;

    resultModal.style.display = "flex";

}



/* ==========================================================
   CLOSE MODAL
========================================================== */

closeModal.addEventListener(

    "click",

    function(){

        resultModal.style.display = "none";

    }

);

window.addEventListener(

    "click",

    function(event){

        if(event.target === resultModal){

            resultModal.style.display = "none";

        }

    }

);



/* ==========================================================
   VIEW ANSWERS
========================================================== */

viewAnswersBtn.addEventListener(

    "click",

    function(){

        if(selectedExamId===null)
            return;

        window.location.href =
            `/view_answers/${selectedExamId}`;

    }

);