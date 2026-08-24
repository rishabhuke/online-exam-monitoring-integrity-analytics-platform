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
   CANDIDATE DETAILS MODAL
============================================================ */

const candidateDetailsModal =
    document.getElementById(
        "candidateDetailsModal"
    );

const candidateModalClose =
    document.getElementById(
        "candidateModalClose"
    );

const candidateModalCloseBottom =
    document.getElementById(
        "candidateModalCloseBottom"
    );

const candidateModalBackdrop =
    document.querySelector(
        ".candidate-modal-backdrop"
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
            data.statistics || {}
        );

        renderActivityFeed(
            data.activity_feed ||
            data.activity ||
            []
        );

        renderRealtimeActivity(
            data.realtime_activity ||
            []
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

    if (
        currentValue &&
        exams.some(
            exam =>
                String(exam.id) ===
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
        percentage(total, total)
    );

    setText(
        "onlinePercentage",
        percentage(online, total)
    );

    setText(
        "warningPercentage",
        percentage(warning, total)
    );

    setText(
        "violationPercentage",
        percentage(violations, total)
    );

    setText(
        "offlinePercentage",
        percentage(offline, total)
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

                if (
                    status &&
                    candidate.status !== status
                ) {

                    return false;

                }


                if (
                    risk &&
                    candidate.risk !== risk
                ) {

                    return false;

                }


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
                    colspan="8"
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
   CANDIDATE PHOTO
============================================================ */

function getCandidatePhotoUrl(photo) {

    if (!photo) {
        return "";
    }

    let value =
        String(photo).trim();

    if (!value) {
        return "";
    }

    value =
        value.replace(/\\/g, "/");

    value =
        value.replace(/^\/+/, "");


    if (
        value.startsWith("http://") ||
        value.startsWith("https://") ||
        value.startsWith("data:")
    ) {

        return value;

    }


    if (
        value.startsWith("static/")
    ) {

        return "/" + value;

    }


    if (
        value.startsWith("uploads/")
    ) {

        return "/static/" + value;

    }


    return "/static/uploads/photos/" + value;

}


/* ============================================================
   CANDIDATE ROW
============================================================ */

function createCandidateRow(candidate) {

    const initials =
        getInitials(
            candidate.name
        );


    const photoUrl =
        getCandidatePhotoUrl(
            candidate.photo
        );


    const photo =
        photoUrl
            ? `
                <img
                    src="${escapeAttribute(photoUrl)}"
                    alt="${escapeAttribute(
                        candidate.name ||
                        "Candidate"
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


    const statusClass =
        getStatusClass(
            candidate.status
        );


    const riskClass =
        getRiskClass(
            candidate.risk
        );


    const violationCount =
        Number(
            candidate.violation_count ?? 0
        );


    const violationClass =
        violationCount > 0
            ? "has-violations"
            : "";


    const examName =
        candidate.exam_title ||
        "No examination";


    const topic =
        candidate.exam_topic ||
        "";


    /* ========================================================
       ACTION BUTTON
    ======================================================== */

    const actionButton = `
        <button
            type="button"
            class="view-details"
            data-candidate-id="${escapeAttribute(
                String(candidate.candidate_id ?? "")
            )}"
            title="View candidate details"
        >
            <i class="fa-solid fa-eye"></i>
            <span>View Details</span>
        </button>
    `;


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


            <!-- Last Activity -->

            <td>

                ${formatDateTime(
                    candidate.last_activity
                )}

            </td>


            <!-- Actions -->

            <td>

                ${actionButton}

            </td>


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

                        const candidateId =
                            this.dataset.candidateId;

                        openCandidateDetails(
                            candidateId
                        );

                    }
                );

            }
        );

}


/* ============================================================
   OPEN CANDIDATE DETAILS
============================================================ */

function openCandidateDetails(candidateId) {

    const candidate =
        allCandidates.find(
            item =>
                String(
                    item.candidate_id
                ) ===
                String(candidateId)
        );


    if (!candidate) {

        console.error(
            "Candidate not found:",
            candidateId
        );

        return;

    }


    populateCandidateModal(
        candidate
    );


    if (!candidateDetailsModal) {
        return;
    }


    candidateDetailsModal.classList.add(
        "show"
    );

    candidateDetailsModal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.classList.add(
        "modal-open"
    );

}


/* ============================================================
   POPULATE CANDIDATE MODAL
============================================================ */

function populateCandidateModal(candidate) {
       console.log("FULL CANDIDATE DATA:", candidate);
    console.log("INTEGRITY SCORE:", candidate.integrity_score);

    const name =
        candidate.name ||
        "Unknown Candidate";


    const email =
        candidate.email ||
        "--";


    const candidateId =
        candidate.candidate_id ??
        "--";


    const status =
        candidate.status ||
        "Offline";


    const risk =
        candidate.risk ||
        "Low";


    const violations =
        Number(
            candidate.violation_count ?? 0
        );


    let integrity =
        Number(
            candidate.integrity_score ?? 0
        );


    integrity =
        Math.max(
            0,
            Math.min(
                100,
                Math.round(integrity)
            )
        );


    const exams =
        Array.isArray(
            candidate.completed_exams
        )
            ? candidate.completed_exams
            : [];


    const averageScore =
        Number(
            candidate.average_exam_score ?? 0
        );


    setText(
        "candidateModalName",
        name
    );


    setText(
        "candidateModalEmail",
        email
    );


    setText(
        "candidateModalId",
        `Candidate ID: ${candidateId}`
    );


    setText(
        "candidateModalIntegrity",
        `${integrity}%`
    );


    setText(
        "candidateIntegrityRingValue",
        integrity
    );


    setText(
        "candidateModalViolations",
        violations
    );


    setText(
        "candidateModalExamCount",
        exams.length
    );


    setText(
        "candidateModalAverageScore",
        `${averageScore.toFixed(1)}%`
    );


    setText(
        "candidateModalLastActivity",
        formatDateTime(
            candidate.last_activity
        )
    );


    /* ========================================================
       STATUS
    ======================================================== */

    const statusElement =
        document.getElementById(
            "candidateModalStatus"
        );

    if (statusElement) {

        statusElement.textContent =
            status;

        statusElement.className =
            "status-badge " +
            getStatusClass(status);

    }


    /* ========================================================
       RISK
    ======================================================== */

    const riskElement =
        document.getElementById(
            "candidateModalRisk"
        );

    if (riskElement) {

        riskElement.textContent =
            risk;

        riskElement.className =
            "risk-badge " +
            getRiskClass(risk);

    }


    /* ========================================================
       PROFILE AVATAR
    ======================================================== */

    const modalAvatar =
        document.getElementById(
            "candidateModalAvatar"
        );

    const modalInitials =
        document.getElementById(
            "candidateModalInitials"
        );


    const photoUrl =
        getCandidatePhotoUrl(
            candidate.photo
        );


    if (
        modalAvatar &&
        modalInitials
    ) {

        modalAvatar.innerHTML = `
            <span>
                ${escapeHTML(
                    getInitials(name)
                )}
            </span>
        `;


        if (photoUrl) {

            const image =
                document.createElement(
                    "img"
                );

            image.src =
                photoUrl;

            image.alt =
                name;

            image.className =
                "modal-candidate-photo";


            image.onerror =
                function () {

                    this.remove();

                };


            modalAvatar.prepend(
                image
            );

        }

    }


    /* ========================================================
       INTEGRITY RING
    ======================================================== */

    const ring =
        document.getElementById(
            "candidateIntegrityRing"
        );

    if (ring) {

        ring.style.setProperty(
            "--score",
            integrity
        );

        ring.classList.remove(
            "score-low",
            "score-medium",
            "score-high"
        );


        if (integrity >= 80) {

            ring.classList.add(
                "score-high"
            );

        }

        else if (integrity >= 50) {

            ring.classList.add(
                "score-medium"
            );

        }

        else {

            ring.classList.add(
                "score-low"
            );

        }

    }


    renderCandidateExamHistory(
        exams
    );

}


/* ============================================================
   EXAM HISTORY
============================================================ */

function renderCandidateExamHistory(
    exams
) {

    const container =
        document.getElementById(
            "candidateExamHistory"
        );


    if (!container) {
        return;
    }


    if (
        !Array.isArray(exams) ||
        exams.length === 0
    ) {

        container.innerHTML = `

            <div class="no-exam-history">

                <div class="no-exam-icon">

                    <i class="fa-solid fa-file-circle-xmark"></i>

                </div>

                <div>

                    <strong>
                        No examination history
                    </strong>

                    <span>
                        This candidate has not completed an examination yet.
                    </span>

                </div>

            </div>

        `;

        return;

    }


    container.innerHTML =
        exams
            .map(
                (exam, index) => {

                    const score =
                        Number(
                            exam.score ?? 0
                        );


                    const scoreClass =
                        score >= 80
                            ? "excellent"
                            : score >= 50
                                ? "average"
                                : "poor";


                    return `

                        <div
                            class="exam-history-item"
                        >

                            <div class="exam-history-number">

                                ${index + 1}

                            </div>


                            <div class="exam-history-main">

                                <div class="exam-history-name">

                                    <strong>
                                        ${escapeHTML(
                                            exam.exam_name ||
                                            "Unknown Exam"
                                        )}
                                    </strong>

                                    ${
                                        exam.topic
                                            ? `
                                                <span>
                                                    ${escapeHTML(
                                                        exam.topic
                                                    )}
                                                </span>
                                            `
                                            : ""
                                    }

                                </div>


                                <div class="exam-history-meta">

                                    <span>

                                        <i class="fa-solid fa-hashtag"></i>

                                        Exam ID:
                                        ${escapeHTML(
                                            String(
                                                exam.exam_id ??
                                                "--"
                                            )
                                        )}

                                    </span>


                                    <span>

                                        <i class="fa-solid fa-file-circle-check"></i>

                                        Completed

                                    </span>

                                </div>

                            </div>


                            <div class="exam-history-score ${scoreClass}">

                                <span>
                                    SCORE
                                </span>

                                <strong>
                                    ${score.toFixed(1)}%
                                </strong>

                            </div>

                        </div>

                    `;

                }
            )
            .join("");

}


/* ============================================================
   CLOSE CANDIDATE MODAL
============================================================ */

function closeCandidateDetails() {

    if (!candidateDetailsModal) {
        return;
    }


    candidateDetailsModal.classList.remove(
        "show"
    );


    candidateDetailsModal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.classList.remove(
        "modal-open"
    );

}


if (candidateModalClose) {

    candidateModalClose.addEventListener(
        "click",
        closeCandidateDetails
    );

}


if (candidateModalCloseBottom) {

    candidateModalCloseBottom.addEventListener(
        "click",
        closeCandidateDetails
    );

}


if (candidateModalBackdrop) {

    candidateModalBackdrop.addEventListener(
        "click",
        closeCandidateDetails
    );

}


document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape" &&
            candidateDetailsModal &&
            candidateDetailsModal.classList.contains(
                "show"
            )
        ) {

            closeCandidateDetails();

        }

    }
);


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

        button.type =
            "button";

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

                currentPage =
                    i;

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

function renderActivityFeed(activity) {

    const feed =
        document.getElementById(
            "activityFeed"
        );


    if (!feed) {
        return;
    }


    if (
        !Array.isArray(activity) ||
        activity.length === 0
    ) {

        feed.innerHTML = `

            <div class="empty-activity">

                <i class="fa-solid fa-clock"></i>

                <span>
                    No recent activity
                </span>

            </div>

        `;

        return;

    }


    feed.innerHTML =
        activity
            .slice(0, 8)
            .map(event => {

                const severity =
                    String(
                        event.severity ||
                        "Medium"
                    ).toLowerCase();


                const candidate =
                    escapeHTML(
                        event.candidate_name ||
                        "Unknown Candidate"
                    );


                const type =
                    escapeHTML(
                        event.violation_type ||
                        event.type ||
                        "Integrity Event"
                    );


                const exam =
                    escapeHTML(
                        event.exam_title ||
                        "Unknown Examination"
                    );


                const time =
                    formatDateTime(
                        event.time
                    );


                return `

                    <div
                        class="activity-item severity-${severity}"
                    >

                        <div class="activity-icon">

                            <i class="fa-solid fa-triangle-exclamation"></i>

                        </div>


                        <div class="activity-content">

                            <strong>
                                ${candidate}
                            </strong>

                            <span>
                                ${type}
                            </span>

                            <small>
                                ${exam}
                            </small>

                            <time>
                                ${time}
                            </time>

                        </div>

                    </div>

                `;

            })
            .join("");

}


/* ============================================================
   REALTIME ACTIVITY
============================================================ */

function renderRealtimeActivity(activity) {

    const chart =
        document.getElementById(
            "activityChart"
        );


    if (!chart) {
        return;
    }


    if (
        !Array.isArray(activity) ||
        activity.length === 0
    ) {

        chart.innerHTML = `

            <div class="activity-empty">
                No integrity events yet
            </div>

        `;

        return;

    }


    const maxCount =
        Math.max(
            ...activity.map(
                item =>
                    Number(
                        item.count || 0
                    )
            ),
            1
        );


    chart.innerHTML = `

        <div class="realtime-bars">

            ${
                activity
                    .map(item => {

                        const count =
                            Number(
                                item.count || 0
                            );


                        const height =
                            Math.max(
                                8,
                                (
                                    count /
                                    maxCount
                                ) * 100
                            );


                        return `

                            <div
                                class="realtime-bar-wrapper"
                                title="${escapeAttribute(
                                    item.time
                                )}: ${count} events"
                            >

                                <div
                                    class="realtime-bar"
                                    style="
                                        height:${height}%;
                                    "
                                ></div>

                                <span>
                                    ${escapeHTML(
                                        item.time
                                    )}
                                </span>

                            </div>

                        `;

                    })
                    .join("")
            }

        </div>

    `;

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

                /*
                 * Do not close the modal while refreshing.
                 * The candidate data itself will be refreshed.
                 */

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
        "Status",
        "Risk",
        "Violations",
        "Last Activity"

    ];


    const rows =
        filteredCandidates.map(
            candidate => [

                candidate.name,

                candidate.candidate_id,

                candidate.email,

                candidate.status,

                candidate.risk,

                candidate.violation_count,

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


    link.href =
        url;


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
                colspan="8"
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
                colspan="8"
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
        document.getElementById(
            id
        );


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
