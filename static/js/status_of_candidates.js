"use strict";


/* ============================================================
   STATE
============================================================ */

let allCandidates = [];

let filteredCandidates = [];

let currentPage = 1;

let rowsPerPage = 10;

let refreshTimer = null;


/* ============================================================
   DOM
============================================================ */

const tableBody =
    document.getElementById(
        "candidateTableBody"
    );

const examFilter =
    document.getElementById(
        "examFilter"
    );

const statusFilter =
    document.getElementById(
        "statusFilter"
    );

const riskFilter =
    document.getElementById(
        "riskFilter"
    );

const searchInput =
    document.getElementById(
        "candidateSearch"
    );

const refreshButton =
    document.getElementById(
        "refreshButton"
    );

const resetFilters =
    document.getElementById(
        "resetFilters"
    );

const rowsSelect =
    document.getElementById(
        "rowsPerPage"
    );

const prevPage =
    document.getElementById(
        "prevPage"
    );

const nextPage =
    document.getElementById(
        "nextPage"
    );

const pageNumbers =
    document.getElementById(
        "pageNumbers"
    );


/* ============================================================
   LOAD DATA
============================================================ */

async function loadCandidateStatus() {

    try {

        showLoading();

        let url =
            "/admin/api/candidate-status";

        const selectedExam =
            examFilter
                ? examFilter.value
                : "";

        if (selectedExam) {

            url +=
                "?exam_id=" +
                encodeURIComponent(
                    selectedExam
                );

        }

        const response =
            await fetch(url, {
                cache: "no-store"
            });

        if (!response.ok) {

            throw new Error(
                "HTTP " +
                response.status
            );

        }

        const data =
            await response.json();

        if (!data.success) {

            throw new Error(
                data.message ||
                "Unable to load candidate data."
            );

        }

        allCandidates =
            Array.isArray(data.candidates)
                ? data.candidates
                : [];

        populateExams(
            data.exams || []
        );

        renderStatistics(
            data.statistics
        );

        applyFilters();

    }

    catch (error) {

        console.error(
            "Candidate status:",
            error
        );

        showError(
            "Unable to load candidate data."
        );

    }

}


/* ============================================================
   EXAMS
============================================================ */

function populateExams(exams) {

    if (!examFilter)
        return;

    const currentValue =
        examFilter.value;

    examFilter.innerHTML = `
        <option value="">
            All Active Exams
        </option>
    `;

    exams.forEach(
        exam => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                exam.id;

            option.textContent =
                exam.title +
                (
                    exam.topic
                        ? " • " +
                          exam.topic
                        : ""
                );

            examFilter.appendChild(
                option
            );

        }
    );

    /*
     * Preserve selected exam
     */

    if (
        currentValue &&
        exams.some(
            exam =>
                String(exam.id)
                ===
                String(currentValue)
        )
    ) {

        examFilter.value =
            currentValue;

    }

}


/* ============================================================
   STATISTICS
============================================================ */

function renderStatistics(stats) {

    stats = stats || {};

    const total =
        Number(stats.total || 0);

    const online =
        Number(stats.online || 0);

    const warning =
        Number(stats.warning || 0);

    const violations =
        Number(stats.violations || 0);

    const offline =
        Number(stats.offline || 0);


    setText(
        "totalCandidates",
        total
    );

    setText(
        "onlineCandidates",
        online
    );

    setText(
        "warningCandidates",
        warning
    );

    setText(
        "violationCandidates",
        violations
    );

    setText(
        "offlineCandidates",
        offline
    );


    setText(
        "totalPercentage",
        percentage(
            total,
            total
        )
    );

    setText(
        "onlinePercentage",
        percentage(
            online,
            total
        )
    );

    setText(
        "warningPercentage",
        percentage(
            warning,
            total
        )
    );

    setText(
        "violationPercentage",
        percentage(
            violations,
            total
        )
    );

    setText(
        "offlinePercentage",
        percentage(
            offline,
            total
        )
    );

}


/* ============================================================
   FILTERS
============================================================ */

function applyFilters() {

    const status =
        statusFilter
            ? statusFilter.value
            : "";

    const risk =
        riskFilter
            ? riskFilter.value
            : "";

    const keyword =
        searchInput
            ? searchInput.value
                .trim()
                .toLowerCase()
            : "";


    filteredCandidates =
        allCandidates.filter(
            candidate => {

                /*
                 * Status
                 */

                if (
                    status &&
                    candidate.status !== status
                ) {

                    return false;

                }


                /*
                 * Risk
                 */

                if (
                    risk &&
                    candidate.risk !== risk
                ) {

                    return false;

                }


                /*
                 * Search
                 */

                if (keyword) {

                    const searchable = [

                        candidate.name,

                        candidate.email,

                        candidate.candidate_id,

                        candidate.exam_title,

                        candidate.exam_topic

                    ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase();

                    if (
                        !searchable.includes(
                            keyword
                        )
                    ) {

                        return false;

                    }

                }


                return true;

            }
        );


    currentPage = 1;

    renderTable();

}


/* ============================================================
   TABLE
============================================================ */

function renderTable() {

    if (!tableBody)
        return;


    const total =
        filteredCandidates.length;


    const totalPages =
        Math.max(
            1,
            Math.ceil(
                total /
                rowsPerPage
            )
        );


    if (
        currentPage >
        totalPages
    ) {

        currentPage =
            totalPages;

    }


    const start =
        (
            currentPage - 1
        ) *
        rowsPerPage;


    const end =
        start +
        rowsPerPage;


    const pageData =
        filteredCandidates.slice(
            start,
            end
        );


    if (pageData.length === 0) {

        tableBody.innerHTML = `

            <tr>

                <td
                    colspan="10"
                    class="empty-row"
                >

                    <i class="fa-solid fa-users-slash"></i>

                    <br><br>

                    No candidates found.

                </td>

            </tr>

        `;

    }

    else {

        tableBody.innerHTML =
            pageData
                .map(
                    createCandidateRow
                )
                .join("");

    }


    renderPagination(
        totalPages
    );


    if (total === 0) {

        setText(
            "resultCount",
            "Showing 0 candidates"
        );

    }

    else {

        const first =
            start + 1;

        const last =
            Math.min(
                end,
                total
            );

        setText(
            "resultCount",
            `Showing ${first}-${last} of ${total} candidates`
        );

    }


    bindDetailButtons();

}


/* ============================================================
   CANDIDATE ROW
============================================================ */
function getCandidatePhotoUrl(photo) {

    if (!photo) {
        return "";
    }

    let value = String(photo).trim();

    if (!value) {
        return "";
    }

    console.log("Original candidate photo:", value);

    /*
     * Convert Windows backslashes to URL slashes.
     *
     * static\uploads\photos\image.png
     * becomes
     * static/uploads/photos/image.png
     */
    value = value.replace(/\\/g, "/");

    /*
     * Remove leading slash.
     */
    value = value.replace(/^\/+/, "");

    /*
     * Absolute URL
     */
    if (
        value.startsWith("http://") ||
        value.startsWith("https://") ||
        value.startsWith("data:")
    ) {
        return value;
    }

    /*
     * If database contains:
     *
     * static/uploads/photos/image.png
     *
     * return:
     *
     * /static/uploads/photos/image.png
     */
    if (value.startsWith("static/")) {
        return "/" + value;
    }

    /*
     * If database contains:
     *
     * uploads/photos/image.png
     *
     * return:
     *
     * /static/uploads/photos/image.png
     */
    if (value.startsWith("uploads/")) {
        return "/static/" + value;
    }

    /*
     * If database contains only:
     *
     * image.png
     *
     * return:
     *
     * /static/uploads/photos/image.png
     */
    return "/static/uploads/photos/" + value;
}

function createCandidateRow(candidate) {

    const initials =
        getInitials(candidate.name);


    /* ========================================================
       CANDIDATE PHOTO
    ======================================================== */

    const photoUrl =
        getCandidatePhotoUrl(candidate.photo);


    const photo =
        photoUrl
            ? `
                <img
                    src="${escapeAttribute(photoUrl)}"
                    alt="${escapeAttribute(
                        candidate.name || "Candidate"
                    )}"
                    class="candidate-photo"
                    onerror="
                        this.style.display='none';
                        this.nextElementSibling.style.display='flex';
                    "
                >
            `
            : "";


    const avatarFallback =
        `
            <span
                style="${
                    photoUrl
                        ? "display:none"
                        : ""
                }"
            >
                ${escapeHTML(initials)}
            </span>
        `;


    /* ========================================================
       STATUS
    ======================================================== */

    const statusClass =
        getStatusClass(
            candidate.status
        );


    /* ========================================================
       RISK
    ======================================================== */

    const riskClass =
        getRiskClass(
            candidate.risk
        );


    /* ========================================================
       SCORE
    ======================================================== */

 


    /* ========================================================
       VIOLATIONS
    ======================================================== */
const violationCount = Number(candidate.violation_count ?? 0);

// Calculate integrity score
let score = 100 - (violationCount * 10);

// Keep score between 0 and 100
score = Math.max(0, Math.min(100, score));

// Make sure it is an integer
score = Math.round(score);




    const violationClass =
        violationCount > 0
            ? "has-violations"
            : "";


    /* ========================================================
       EXAM
    ======================================================== */

    const examName =
        candidate.exam_title ||
        "No examination";


    const topic =
        candidate.exam_topic ||
        "";


    /* ========================================================
       ROW
    ======================================================== */

    return `

        <tr>

            <!-- Candidate -->

            <td>

                <div class="candidate-cell">

                    <div class="candidate-avatar">

                        ${photo}

                        ${avatarFallback}

                    </div>


                    <div>

                        <span class="candidate-name">

                            ${escapeHTML(
                                candidate.name ||
                                "Unknown"
                            )}

                        </span>


                        <span class="candidate-email">

                            ${escapeHTML(
                                candidate.email ||
                                ""
                            )}

                        </span>

                    </div>

                </div>

            </td>


            <!-- Candidate ID -->

            <td>

                <span class="candidate-id">

                    ${escapeHTML(
                        String(
                            candidate.candidate_id ?? ""
                        )
                    )}

                </span>

            </td>


            <!-- Examination -->

            <td>

                <span class="exam-name">

                    ${escapeHTML(
                        examName
                    )}

                </span>

                ${
                    topic
                        ? `
                            <span class="exam-topic">
                                ${escapeHTML(topic)}
                            </span>
                        `
                        : ""
                }

            </td>


            <!-- Login Time -->



            <!-- Status -->

            <td>

                <span
                    class="status-badge ${statusClass}"
                >

                    ${escapeHTML(
                        candidate.status ||
                        "Offline"
                    )}

                </span>

            </td>


            <!-- Risk -->

            <td>

                <span
                    class="risk-badge ${riskClass}"
                >

                    ${escapeHTML(
                        candidate.risk ||
                        "Low"
                    )}

                </span>

            </td>


            <!-- Violations -->

            <td>

                <span
                    class="
                        violation-number
                        ${violationClass}
                    "
                >

                    ${violationCount}

                </span>

            </td>


            <!-- Integrity Score -->

     


            <!-- Last Activity -->

            <td>

                ${formatDateTime(
                    candidate.last_activity
                )}

            </td>


            <!-- Actions -->


        </tr>

    `;
}


/* ============================================================
   VIEW DETAILS
============================================================ */

function bindDetailButtons() {

    document
        .querySelectorAll(
            ".view-details"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    function () {

                        const examId =
                            this.dataset.examId;

                        if (examId) {

                            window.location.href =
                                "/admin/live-monitoring" +
                                "?exam_id=" +
                                encodeURIComponent(
                                    examId
                                );

                        }
                        else {

                            window.location.href =
                                "/admin/live-monitoring";

                        }

                    }
                );

            }
        );

}


/* ============================================================
   PAGINATION
============================================================ */

function renderPagination(
    totalPages
) {

    if (!pageNumbers)
        return;


    pageNumbers.innerHTML = "";


    for (
        let i = 1;
        i <= totalPages;
        i++
    ) {

        const button =
            document.createElement(
                "button"
            );

        button.type = "button";

        button.className =
            "page-number" +
            (
                i === currentPage
                    ? " active"
                    : ""
            );

        button.textContent =
            i;

        button.addEventListener(
            "click",
            () => {

                currentPage = i;

                renderTable();

            }
        );

        pageNumbers.appendChild(
            button
        );

    }


    if (prevPage) {

        prevPage.disabled =
            currentPage <= 1;

    }


    if (nextPage) {

        nextPage.disabled =
            currentPage >= totalPages;

    }

}


/* ============================================================
   ACTIVITY FEED
============================================================ */

function renderActivityFeed() {

    const feed =
        document.getElementById(
            "activityFeed"
        );

    if (!feed)
        return;


    const recent =
        [...allCandidates]
            .filter(
                candidate =>
                    candidate.last_activity
            )
            .sort(
                (a, b) =>
                    String(
                        b.last_activity
                    ).localeCompare(
                        String(
                            a.last_activity
                        )
                    )
            )
            .slice(0, 6);


    if (recent.length === 0) {

        feed.innerHTML = `

            <div class="empty-activity">

                No recent activity

            </div>

        `;

        return;

    }


    feed.innerHTML =
        recent
            .map(
                candidate => `

                    <div class="activity-item">

                        <strong>

                            ${escapeHTML(
                                candidate.name
                            )}

                        </strong>

                        <span>

                            ${
                                candidate.violation_count > 0
                                    ? "Integrity activity detected"
                                    : "Candidate activity recorded"
                            }

                        </span>

                    </div>

                `
            )
            .join("");

}


/* ============================================================
   REFRESH
============================================================ */

function startAutoRefresh() {

    if (refreshTimer) {

        clearInterval(
            refreshTimer
        );

    }


    refreshTimer =
        setInterval(
            () => {

                loadCandidateStatus();

            },
            10000
        );

}


/* ============================================================
   EVENTS
============================================================ */

if (examFilter) {

    examFilter.addEventListener(
        "change",
        () => {

            loadCandidateStatus();

        }
    );

}


if (statusFilter) {

    statusFilter.addEventListener(
        "change",
        applyFilters
    );

}


if (riskFilter) {

    riskFilter.addEventListener(
        "change",
        applyFilters
    );

}


if (searchInput) {

    searchInput.addEventListener(
        "input",
        applyFilters
    );

}


if (refreshButton) {

    refreshButton.addEventListener(
        "click",
        () => {

            loadCandidateStatus();

        }
    );

}


if (resetFilters) {

    resetFilters.addEventListener(
        "click",
        () => {

            if (examFilter)
                examFilter.value = "";

            if (statusFilter)
                statusFilter.value = "";

            if (riskFilter)
                riskFilter.value = "";

            if (searchInput)
                searchInput.value = "";

            loadCandidateStatus();

        }
    );

}


if (rowsSelect) {

    rowsSelect.addEventListener(
        "change",
        function () {

            rowsPerPage =
                Number(
                    this.value
                );

            currentPage = 1;

            renderTable();

        }
    );

}


if (prevPage) {

    prevPage.addEventListener(
        "click",
        () => {

            if (currentPage > 1) {

                currentPage--;

                renderTable();

            }

        }
    );

}


if (nextPage) {

    nextPage.addEventListener(
        "click",
        () => {

            const totalPages =
                Math.ceil(
                    filteredCandidates.length /
                    rowsPerPage
                );

            if (
                currentPage <
                totalPages
            ) {

                currentPage++;

                renderTable();

            }

        }
    );

}


/* ============================================================
   EXPORT CSV
============================================================ */

const exportButton =
    document.getElementById(
        "exportReport"
    );

if (exportButton) {

    exportButton.addEventListener(
        "click",
        exportCSV
    );

}


function exportCSV() {

    if (
        filteredCandidates.length === 0
    ) {

        alert(
            "There are no candidates to export."
        );

        return;

    }


    const header = [

        "Candidate",
        "Candidate ID",
        "Email",
        "Examination",
        "Login Time",
        "Status",
        "Risk",
        "Violations",
        "Integrity Score",
        "Last Activity"

    ];


    const rows =
        filteredCandidates.map(
            candidate => [

                candidate.name,

                candidate.candidate_id,

                candidate.email,

                candidate.exam_title,

                candidate.login_time,

                candidate.status,

                candidate.risk,

                candidate.violation_count,

                candidate.integrity_score,

                candidate.last_activity

            ]
        );


    const csv = [

        header,

        ...rows

    ]
    .map(
        row =>
            row
                .map(
                    value =>
                        `"${String(
                            value ?? ""
                        ).replaceAll(
                            '"',
                            '""'
                        )}"`
                )
                .join(",")
    )
    .join("\n");


    const blob =
        new Blob(
            [csv],
            {
                type:
                    "text/csv;charset=utf-8;"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const link =
        document.createElement(
            "a"
        );

    link.href = url;

    link.download =
        "candidate_status_report.csv";

    link.click();

    URL.revokeObjectURL(
        url
    );

}


/* ============================================================
   CLOCK
============================================================ */

function updateClock() {

    const now =
        new Date();


    const time =
        now.toLocaleTimeString(
            [],
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        );


    const date =
        now.toLocaleDateString(
            [],
            {
                weekday: "short",
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );


    setText(
        "currentTime",
        time
    );

    setText(
        "currentDate",
        date
    );

}


setInterval(
    updateClock,
    1000
);


/* ============================================================
   HELPERS
============================================================ */

function showLoading() {

    if (!tableBody)
        return;

    tableBody.innerHTML = `

        <tr>

            <td
                colspan="10"
                class="loading-row"
            >

                <i class="fa-solid fa-spinner fa-spin"></i>

                Loading candidates...

            </td>

        </tr>

    `;

}


function showError(message) {

    if (!tableBody)
        return;

    tableBody.innerHTML = `

        <tr>

            <td
                colspan="10"
                class="empty-row"
            >

                <i class="fa-solid fa-circle-exclamation"></i>

                <br><br>

                ${escapeHTML(message)}

                <br><br>

                <button
                    class="view-details"
                    onclick="loadCandidateStatus()"
                >
                    Try Again
                </button>

            </td>

        </tr>

    `;

}


function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent =
            value;

    }

}


function percentage(
    value,
    total
) {

    if (!total)
        return "0%";

    return (
        (value / total) *
        100
    ).toFixed(1) + "%";

}


function getInitials(name) {

    if (!name)
        return "?";


    return name
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map(
            part =>
                part.charAt(0)
        )
        .join("")
        .toUpperCase();

}


function getStatusClass(status) {

    if (status === "Online")
        return "status-online";

    if (status === "Warning")
        return "status-warning";

    return "status-offline";

}


function getRiskClass(risk) {

    if (risk === "High")
        return "risk-high";

    if (risk === "Medium")
        return "risk-medium";

    return "risk-low";

}


function formatDateTime(value) {

    if (!value)
        return "--";


    const date =
        new Date(
            String(value).replace(
                " ",
                "T"
            )
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return escapeHTML(
            String(value)
        );

    }


    return date.toLocaleString(
        [],
        {
            month: "short",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        }
    );

}


function escapeHTML(value) {

    return String(
        value ?? ""
    )
    .replaceAll(
        "&",
        "&amp;"
    )
    .replaceAll(
        "<",
        "&lt;"
    )
    .replaceAll(
        ">",
        "&gt;"
    )
    .replaceAll(
        '"',
        "&quot;"
    )
    .replaceAll(
        "'",
        "&#039;"
    );

}


function escapeAttribute(value) {

    return escapeHTML(
        value
    );

}


/* ============================================================
   START
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        updateClock();

        loadCandidateStatus();

        startAutoRefresh();

    }
);