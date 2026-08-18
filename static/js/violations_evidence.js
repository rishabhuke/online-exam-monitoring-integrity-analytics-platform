const API_URL =
    "/admin/api/violations-evidence";

let currentPage = 1;
let selectedEvent = null;

function getEvidenceUrl(path) {
    if (!path) return "";
    if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("/admin/api/evidence")) {
        return path;
    }
    return `/admin/api/evidence?path=${encodeURIComponent(path)}`;
}


/* =====================================================
   CATEGORY CONFIGURATION
===================================================== */

const categoryConfig = [

    {
        key: "TAB_SWITCH",
        title: "Tab Switches",
        description: "Browser activity",
        icon: "↗"
    },

    {
        key: "FOCUS_LOSS",
        title: "Focus Loss",
        description: "Window focus events",
        icon: "◎"
    },

    {
        key: "FACE_ABSENCE",
        title: "Face Absence",
        description: "Face presence events",
        icon: "◉"
    },

    {
        key: "FULLSCREEN_EXIT",
        title: "Fullscreen Exit",
        description: "Fullscreen violations",
        icon: "↙"
    },

    {
        key: "COPY_PASTE",
        title: "Copy / Paste",
        description: "Clipboard activity",
        icon: "▣"
    },

    {
        key: "SCREENSHOT",
        title: "Screenshots",
        description: "Screenshot attempts",
        icon: "▧"
    },

    {
        key: "RIGHT_CLICK",
        title: "Right Click",
        description: "Context menu activity",
        icon: "◉"
    },

    {
        key: "IDENTITY_MISMATCH",
        title: "Identity Mismatch",
        description: "Verification failures",
        icon: "◎"
    },

    {
        key: "MULTIPLE_FACES",
        title: "Multiple Faces",
        description: "Multiple person detection",
        icon: "♧"
    },

    {
        key: "OTHER",
        title: "Other Violations",
        description: "Other suspicious events",
        icon: "•••"
    }

];


/* =====================================================
   LOAD DATA
===================================================== */

async function loadViolations() {

    const params =
        new URLSearchParams();

    const search =
        document
            .getElementById("candidateSearch")
            .value
            .trim();

    const exam =
        document
            .getElementById("examFilter")
            .value;

    const category =
        document
            .getElementById("categoryFilter")
            .value;

    const severity =
        document
            .getElementById("severityFilter")
            .value;


    if (search) {

        params.set(
            "search",
            search
        );

    }


    if (
        exam &&
        exam !== "ALL"
    ) {

        params.set(
            "exam_id",
            exam
        );

    }


    if (
        category &&
        category !== "ALL"
    ) {

        params.set(
            "category",
            category
        );

    }


    if (
        severity &&
        severity !== "ALL"
    ) {

        params.set(
            "severity",
            severity
        );

    }


    params.set(
        "page",
        currentPage
    );

    params.set(
        "per_page",
        10
    );


    try {

        const response =
            await fetch(
                `${API_URL}?${params.toString()}`
            );


        const data =
            await response.json();


        if (!data.success) {

            console.error(
                data.message
            );

            return;

        }


        renderStatistics(
            data.statistics
        );

        renderViolationCards(
            data.statistics
        );

        renderEvents(
            data.events
        );

        renderRecentEvidence(
            data.recent_evidence
        );

        renderTimeline(
            data.timeline
        );

        renderExams(
            data.exams
        );

        renderPagination(
            data.pagination
        );

        updateLastUpdated();


    } catch (error) {

        console.error(
            "Unable to load violations:",
            error
        );

    }

}


/* =====================================================
   STATISTICS
===================================================== */

function renderStatistics(stats) {

    document.getElementById(
        "highCount"
    ).textContent = stats.high;


    document.getElementById(
        "mediumCount"
    ).textContent = stats.medium;


    document.getElementById(
        "lowCount"
    ).textContent = stats.low;


    document.getElementById(
        "totalSeverity"
    ).textContent = stats.total;


    document.getElementById(
        "totalEvidence"
    ).textContent =
        stats.total_evidence;


    /*
       These can later be replaced with
       actual verified/pending columns
       if your database has them.
    */

    document.getElementById(
        "verifiedEvidence"
    ).textContent = 0;


    document.getElementById(
        "pendingEvidence"
    ).textContent = 0;

}


/* =====================================================
   VIOLATION CARDS
===================================================== */

function renderViolationCards(stats) {

    const container =
        document.getElementById(
            "violationCards"
        );


    container.innerHTML = "";


    categoryConfig.forEach(
        (category, index) => {

            const count =
                getCategoryCount(
                    category.key,
                    stats
                );


            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "violation-card";


            card.innerHTML = `

                <div class="card-top">

                    <div class="violation-icon">
                        ${category.icon}
                    </div>

                    <div>

                        <div class="card-number">
                            ${index + 1}. ${category.title}
                        </div>

                        <div class="card-description">
                            ${category.description}
                        </div>

                    </div>

                </div>

                <div class="card-count">
                    ${count}
                </div>

                

            `;


            container.appendChild(
                card
            );

        }
    );

}


/* =====================================================
   CATEGORY COUNT
===================================================== */

function getCategoryCount(
    key,
    stats
) {

    const map = {

        TAB_SWITCH:
            stats.tab_switches,

        FOCUS_LOSS:
            stats.focus_loss,

        FACE_ABSENCE:
            stats.face_absence,

        FULLSCREEN_EXIT:
            stats.fullscreen_exit,

        COPY_PASTE:
            stats.copy_paste,

        SCREENSHOT:
            stats.screenshots,

        RIGHT_CLICK:
            stats.right_click,

        IDENTITY_MISMATCH:
            stats.identity_mismatch,

        MULTIPLE_FACES:
            stats.multiple_faces,

        OTHER:
            stats.other

    };


    return map[key] || 0;
}


/* =====================================================
   EVENTS TABLE
===================================================== */

function renderEvents(events) {

    const tbody =
        document.getElementById(
            "eventsTable"
        );


    tbody.innerHTML = "";


    if (!events.length) {

        tbody.innerHTML = `

            <tr>

                <td
                    colspan="9"
                    style="
                        text-align:center;
                        padding:30px;
                        color:#73809b;
                    "
                >
                    No integrity events found
                </td>

            </tr>

        `;

        return;

    }


    events.forEach(
        event => {

            const row =
                document.createElement(
                    "tr"
                );


            const severityClass =
                event.severity
                    .toLowerCase();


            row.innerHTML = `

                <td>

                    <div class="candidate-cell">

                        <div class="candidate-avatar">
                            ${getInitials(
                                event.candidate_name
                            )}
                        </div>

                        <div>

                            <div class="candidate-name">
                                ${escapeHtml(
                                    event.candidate_name
                                )}
                            </div>

                            <div class="candidate-email">
                                ${escapeHtml(
                                    event.candidate_email
                                )}
                            </div>

                        </div>

                    </div>

                </td>


                <td>
                    ${event.candidate_id ?? "--"}
                </td>


                <td>
                    ${escapeHtml(
                        event.exam_title
                    )}
                </td>


                <td>
                    ${escapeHtml(
                        event.violation_type
                    )}
                </td>


                <td>

                    <span
                        class="badge ${severityClass}"
                    >
                        ${event.severity}
                    </span>

                </td>


                <td>
                    ${formatDate(
                        event.detected_at
                    )}
                </td>


                <td>

                    ${
                        event.evidence
                        ?
                        `
                            <button
                                class="evidence-btn"
                                onclick='openEvidence(
                                    ${JSON.stringify(event)}
                                )'
                            >
                                ▣
                            </button>
                        `
                        :
                        "—"
                    }

                </td>


                <td>
                    ${escapeHtml(
                        event.status
                    )}
                </td>


                <td>

                    <button
                        class="details-btn"
                        onclick='openEvidence(
                            ${JSON.stringify(event)}
                        )'
                    >
                        View Details
                    </button>

                </td>

            `;


            tbody.appendChild(
                row
            );

        }
    );

}


/* =====================================================
   RECENT EVIDENCE
===================================================== */

function renderRecentEvidence(
    evidence
) {

    const container =
        document.getElementById(
            "recentEvidence"
        );


    container.innerHTML = "";


    if (!evidence.length) {

        container.innerHTML = `

            <div
                style="
                    grid-column:1/-1;
                    padding:30px;
                    text-align:center;
                    color:#71809b;
                    font-size:10px;
                "
            >
                No evidence captured
            </div>

        `;

        return;

    }


    evidence.forEach(
        event => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "evidence-card";


            card.onclick = () =>
                openEvidence(event);


            card.innerHTML = `

                <div class="evidence-image">

                    <img
                        src="${escapeAttribute(
                            getEvidenceUrl(event.evidence)
                        )}"
                        alt="Evidence"
                        onerror="
                            this.style.display='none'
                        "
                    >

                    <span
                        class="
                            severity-label
                            ${event.severity.toLowerCase()}
                        "
                    >
                        ${event.severity}
                    </span>

                </div>


                <div class="evidence-info">

                    <strong>
                        ${escapeHtml(
                            event.violation_type
                        )}
                    </strong>

                    <span>
                        ${escapeHtml(
                            event.candidate_name
                        )}
                    </span>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}


/* =====================================================
   TIMELINE
===================================================== */

function renderTimeline(
    timeline
) {

    const container =
        document.getElementById(
            "timeline"
        );


    container.innerHTML = "";


    if (!timeline.length) {

        container.innerHTML = `

            <div
                style="
                    color:#73809b;
                    text-align:center;
                    padding:20px;
                    font-size:10px;
                "
            >
                No activity recorded
            </div>

        `;

        return;

    }


    timeline.forEach(
        event => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "timeline-item";


            item.innerHTML = `

                <div class="timeline-dot"></div>

                <div>

                    <strong>
                        ${escapeHtml(
                            event.violation_type
                        )}
                    </strong>

                    <span>
                        ${escapeHtml(
                            event.candidate_name
                        )}
                    </span>

                </div>

                <div class="timeline-time">
                    ${formatTime(
                        event.detected_at
                    )}
                </div>

            `;


            container.appendChild(
                item
            );

        }
    );

}


/* =====================================================
   EXAMS
===================================================== */

function renderExams(
    exams
) {

    const select =
        document.getElementById(
            "examFilter"
        );


    const currentValue =
        select.value;


    select.innerHTML = `

        <option value="ALL">
            All Examinations
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
                exam.title;


            select.appendChild(
                option
            );

        }
    );


    if (
        currentValue &&
        [...select.options].some(
            option =>
                option.value ===
                currentValue
        )
    ) {

        select.value =
            currentValue;

    }

}


/* =====================================================
   PAGINATION
===================================================== */

function renderPagination(
    pagination
) {

    const info =
        document.getElementById(
            "paginationInfo"
        );


    const buttons =
        document.getElementById(
            "paginationButtons"
        );


    if (!pagination.total) {

        info.textContent =
            "Showing 0 events";

        buttons.innerHTML = "";

        return;

    }


    const start =
        (
            (pagination.page - 1)
            * pagination.per_page
        ) + 1;


    const end =
        Math.min(
            pagination.page
                * pagination.per_page,

            pagination.total
        );


    info.textContent =
        `Showing ${start}-${end} of ${pagination.total} events`;


    buttons.innerHTML = "";


    if (pagination.page > 1) {

        createPageButton(
            "‹",
            pagination.page - 1,
            buttons
        );

    }


    for (
        let i = 1;
        i <= pagination.total_pages;
        i++
    ) {

        if (
            i <= 3 ||
            i === pagination.total_pages
        ) {

            createPageButton(
                i,
                i,
                buttons,
                i === pagination.page
            );

        }

    }


    if (
        pagination.page <
        pagination.total_pages
    ) {

        createPageButton(
            "›",
            pagination.page + 1,
            buttons
        );

    }

}


function createPageButton(
    label,
    page,
    container,
    active = false
) {

    const button =
        document.createElement(
            "button"
        );


    button.textContent =
        label;


    if (active) {

        button.classList.add(
            "active"
        );

    }


    button.onclick = () => {

        currentPage =
            page;

        loadViolations();

    };


    container.appendChild(
        button
    );

}


/* =====================================================
   EVIDENCE DRAWER
===================================================== */

function openEvidence(event) {

    selectedEvent =
        event;


    document
        .getElementById(
            "evidenceDrawer"
        )
        .classList.add(
            "open"
        );


    document.getElementById(
        "detailCandidate"
    ).textContent =
        event.candidate_name || "--";


    document.getElementById(
        "detailCandidateId"
    ).textContent =
        event.candidate_id || "--";


    document.getElementById(
        "detailExam"
    ).textContent =
        event.exam_title || "--";


    document.getElementById(
        "detailType"
    ).textContent =
        event.violation_type || "--";


    document.getElementById(
        "detailSeverity"
    ).textContent =
        event.severity || "--";


    document.getElementById(
        "detailTime"
    ).textContent =
        formatDate(
            event.detected_at
        );


    document.getElementById(
        "detailFaces"
    ).textContent =
        event.face_count ?? 0;


    document.getElementById(
        "detailEvidence"
    ).textContent =
        event.id || "--";


    document.getElementById(
        "detailStatus"
    ).textContent =
        event.status || "--";


    const image =
        document.getElementById(
            "drawerImage"
        );


    if (event.evidence) {

        image.innerHTML = `

            <img
                src="${escapeAttribute(
                    getEvidenceUrl(event.evidence)
                )}"
                alt="Evidence"
            >

        `;

    } else {

        image.innerHTML = `
            <span>No Evidence Captured</span>
        `;

    }


    renderRelatedEvents(
        event
    );

}


function renderRelatedEvents(
    event
) {

    const container =
        document.getElementById(
            "relatedEvents"
        );


    container.innerHTML = `

        <div class="related-event">

            <strong>
                ${escapeHtml(
                    event.violation_type
                )}
            </strong>

            <span>
                ${formatDate(
                    event.detected_at
                )}
            </span>

        </div>

    `;

}


/* =====================================================
   CLOSE DRAWER
===================================================== */

function closeDrawer() {

    document
        .getElementById(
            "evidenceDrawer"
        )
        .classList.remove(
            "open"
        );

}


document
    .getElementById(
        "closeDrawer"
    )
    .addEventListener(
        "click",
        closeDrawer
    );


document
    .getElementById(
        "drawerCloseBtn"
    )
    .addEventListener(
        "click",
        closeDrawer
    );


/* =====================================================
   FILTER EVENTS
===================================================== */

document
    .getElementById(
        "filterBtn"
    )
    .addEventListener(
        "click",
        () => {

            currentPage = 1;

            loadViolations();

        }
    );


document
    .getElementById(
        "resetBtn"
    )
    .addEventListener(
        "click",
        () => {

            document
                .getElementById(
                    "candidateSearch"
                )
                .value = "";


            document
                .getElementById(
                    "examFilter"
                )
                .value = "ALL";


            document
                .getElementById(
                    "categoryFilter"
                )
                .value = "ALL";


            document
                .getElementById(
                    "severityFilter"
                )
                .value = "ALL";


            currentPage = 1;

            loadViolations();

        }
    );


document
    .getElementById(
        "refreshBtn"
    )
    .addEventListener(
        "click",
        () => {

            loadViolations();

        }
    );


/* =====================================================
   SEARCH ENTER
===================================================== */

document
    .getElementById(
        "candidateSearch"
    )
    .addEventListener(
        "keydown",
        event => {

            if (
                event.key ===
                "Enter"
            ) {

                currentPage = 1;

                loadViolations();

            }

        }
    );


/* =====================================================
   AUTO REFRESH
===================================================== */

setInterval(
    loadViolations,
    10000
);


/* =====================================================
   HELPERS
===================================================== */

function updateLastUpdated() {

    const now =
        new Date();


    document.getElementById(
        "lastUpdated"
    ).textContent =
        now.toLocaleTimeString();

}


function formatDate(
    value
) {

    if (!value) {
        return "--";
    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;

    }


    return date.toLocaleString();

}


function formatTime(
    value
) {

    if (!value) {
        return "--";
    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;

    }


    return date.toLocaleTimeString();

}


function getInitials(
    name
) {

    if (!name) {
        return "?";
    }


    return name
        .split(" ")
        .slice(0, 2)
        .map(
            word =>
                word[0]
        )
        .join("")
        .toUpperCase();

}


function escapeHtml(
    value
) {

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


function escapeAttribute(
    value
) {

    return escapeHtml(
        value
    );

}


/* =====================================================
   INITIAL LOAD
===================================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadViolations();

    }
);