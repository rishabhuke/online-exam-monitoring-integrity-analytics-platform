"use strict";

/* =========================================================
   GLOBAL STATE
   ========================================================= */

let currentData = null;

let distributionChart = null;
let riskChart = null;
let clusterChart = null;

let sessionsMiniChart = null;
let scoreMiniChart = null;
let faceMiniChart = null;

let refreshTimer = null;

let isLoading = false;


/* =========================================================
   API
   ========================================================= */

const API_URL = "/admin/api/integrity-analysis";


/* =========================================================
   DOM READY
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializePage();

    }
);


/* =========================================================
   INITIALIZE
   ========================================================= */

function initializePage() {

    const examFilter =
        document.getElementById("examFilter");

    const refreshBtn =
        document.getElementById("refreshBtn");

    const search =
        document.getElementById("globalSearch");

    const themeBtn =
        document.getElementById("themeBtn");


    const notificationBtn =
        document.querySelector(
            ".icon-btn:not(#themeBtn)"
        );


    /* =====================================================
       EXAM FILTER
       ===================================================== */

    if (examFilter) {

        examFilter.addEventListener(
            "change",
            function () {

                loadIntegrityAnalysis();

            }
        );

    }


    /* =====================================================
       REFRESH BUTTON
       ===================================================== */

    if (refreshBtn) {

        refreshBtn.addEventListener(
            "click",
            function () {

                loadIntegrityAnalysis();

            }
        );

    }


    /* =====================================================
       GLOBAL SEARCH
       ===================================================== */

    if (search) {

        search.addEventListener(
            "input",
            function () {

                filterSessions(
                    search.value
                );

            }
        );

    }


    /* =====================================================
       THEME BUTTON
       ===================================================== */

    if (themeBtn) {

        themeBtn.addEventListener(
            "click",
            function () {

                toggleTheme();

            }
        );

    }



    /* =====================================================
       NOTIFICATION BUTTON
       ===================================================== */

    if (notificationBtn) {

        notificationBtn.addEventListener(
            "click",
            function (event) {

                event.stopPropagation();

                toggleNotifications();

            }
        );

    }





    /* =====================================================
       KEYBOARD SHORTCUT
       ===================================================== */

    initializeKeyboardShortcut();


    /* =====================================================
       CREATE UI ELEMENTS
       ===================================================== */

    createSessionModal();

    createExportButton();


    /* =====================================================
       INITIAL LOAD
       ===================================================== */

    loadIntegrityAnalysis();




    /* =====================================================
       LIVE REFRESH
       ===================================================== */

    refreshTimer =
        setInterval(
            function () {

                loadIntegrityAnalysis(
                    true
                );


            },
            10000
        );

}


/* =========================================================
   LOAD INTEGRITY API DATA
   ========================================================= */

async function loadIntegrityAnalysis() {

    if (isLoading) {
        return;
    }

    isLoading = true;

    setLoadingState(true);

    try {

        const examId =
            document.getElementById(
                "examFilter"
            )?.value || "";


        let url =
            API_URL;


        if (examId) {

            url +=
                "?exam_id=" +
                encodeURIComponent(
                    examId
                );

        }


        console.log(
            "Loading integrity API:",
            url
        );


        const response =
            await fetch(
                url,
                {
                    method: "GET",

                    credentials: "same-origin",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        console.log(
            "Integrity API status:",
            response.status
        );


        let data = null;

        try {

            data =
                await response.json();

        }
        catch (jsonError) {

            throw new Error(
                "Server returned an invalid response."
            );

        }


        if (!response.ok) {

            throw new Error(
                data?.message ||
                data?.error ||
                "Integrity analysis API request failed."
            );

        }


        if (
            data.status &&
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Unable to load integrity analysis."
            );

        }


        currentData =
            data;


        console.log(
            "Integrity API data:",
            data
        );


        /* =================================================
           RENDER
           ================================================= */

        populateExamFilter(
            data.exams || []
        );


        renderSummary(
            data.summary || {}
        );


        renderIntegrityTable(
            data.sessions || []
        );


        renderMiniCharts(
            data.summary?.totalSessions || 0,

            (data.sessions || []).map(
                function (s) {
                    return Number(
                        s.integrityScore || 0
                    );
                }
            ),

            (data.sessions || []).map(
                function (s) {
                    return Number(
                        s.facePresence || 0
                    );
                }
            )
        );


        renderDistribution(
            data.distribution || {}
        );


        renderRiskDistribution(
            data.riskDistribution || {}
        );


        renderHeatmap(
            data.heatmap || {}
        );


        renderClusters(
            data.clusters || []
        );


        renderCohorts(
            data.cohorts || []
        );


        renderRecentActivity(
            data.recentActivity || []
        );


        updateLastUpdated();


        /*
         * Reapply search after every live refresh.
         */

        const search =
            document.getElementById(
                "globalSearch"
            );

        if (search && search.value) {

            filterSessions(
                search.value
            );

        }


        console.log(
            "Integrity analysis rendered successfully."
        );

    }
    catch (error) {

        console.error(
            "Integrity analysis error:",
            error
        );


        showGlobalError(
            error.message ||
            "Unable to load integrity analysis."
        );

    }
    finally {

        isLoading = false;

        setLoadingState(false);

    }

}


/* =========================================================
   EXAMINATION DROPDOWN
   ========================================================= */

function populateExamFilter(
    exams
) {

    const select =
        document.getElementById(
            "examFilter"
        );


    if (!select) {
        return;
    }


    const currentValue =
        select.value;


    select.innerHTML =
        "";


    const defaultOption =
        document.createElement(
            "option"
        );


    defaultOption.value =
        "";


    defaultOption.textContent =
        "All Examinations";


    select.appendChild(
        defaultOption
    );


    if (!Array.isArray(exams)) {
        return;
    }


    exams.forEach(
        function (exam) {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                exam.id;


            option.textContent =
                exam.title ||
                "Untitled Examination";


            select.appendChild(
                option
            );

        }
    );


    if (
        currentValue &&
        exams.some(
            function (exam) {

                return String(
                    exam.id
                ) ===
                String(
                    currentValue
                );

            }
        )
    ) {

        select.value =
            currentValue;

    }

}


/* =========================================================
   SUMMARY
   ========================================================= */

function renderSummary(
    summary
) {

    setText(
        "totalSessions",
        summary.totalSessions ?? 0
    );


    setText(
        "averageScore",
        summary.averageScore ?? 0
    );


    setText(
        "lowRisk",
        summary.lowRisk ?? 0
    );


    setText(
        "mediumRisk",
        summary.mediumRisk ?? 0
    );


    setText(
        "highRisk",
        summary.highRisk ?? 0
    );


    setText(
        "facePresence",
        (summary.facePresence ?? 0) +
        "%"
    );

}


/* =========================================================
   MINI CHARTS
   ========================================================= */

function renderMiniCharts(
    sessionCount,
    scores,
    faceValues
) {

    destroyChart(
        sessionsMiniChart
    );

    destroyChart(
        scoreMiniChart
    );

    destroyChart(
        faceMiniChart
    );


    sessionsMiniChart =
        null;

    scoreMiniChart =
        null;

    faceMiniChart =
        null;


    const sessionCanvas =
        document.getElementById(
            "sessionsMiniChart"
        );


    const scoreCanvas =
        document.getElementById(
            "scoreMiniChart"
        );


    const faceCanvas =
        document.getElementById(
            "faceMiniChart"
        );


    if (sessionCanvas) {

        const values =
            scores.length
                ? scores.map(
                    function () {
                        return sessionCount;
                    }
                )
                : [0];


        sessionsMiniChart =
            createMiniChart(
                sessionCanvas,
                values,
                "#3b82f6"
            );

    }


    if (scoreCanvas) {

        scoreMiniChart =
            createMiniChart(
                scoreCanvas,
                scores.length
                    ? scores
                    : [0],
                "#a855f7"
            );

    }


    if (faceCanvas) {

        faceMiniChart =
            createMiniChart(
                faceCanvas,
                faceValues.length
                    ? faceValues
                    : [0],
                "#22d3ee"
            );

    }

}


function createMiniChart(
    canvas,
    values,
    color
) {

    return new Chart(
        canvas,
        {
            type: "line",

            data: {

                labels:
                    values.map(
                        function (_, i) {
                            return i + 1;
                        }
                    ),

                datasets: [
                    {
                        data: values,

                        borderColor:
                            color,

                        borderWidth: 1.2,

                        pointRadius: 0,

                        tension: 0.4,

                        fill: false
                    }
                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    x: {
                        display: false
                    },

                    y: {
                        display: false
                    }

                },

                elements: {

                    line: {
                        tension: 0.4
                    }

                }

            }

        }
    );

}


/* =========================================================
   SESSION TABLE
   ========================================================= */

function renderIntegrityTable(
    sessions
) {

    const tbody =
        document.getElementById(
            "sessionsTable"
        );


    if (!tbody) {
        return;
    }


    tbody.innerHTML =
        "";


    if (
        !Array.isArray(sessions) ||
        !sessions.length
    ) {

        tbody.innerHTML =
            createEmptyRow(
                9,
                "No session data available for this examination."
            );

        return;

    }


    sessions.forEach(
        function (session) {

            const row =
                document.createElement(
                    "tr"
                );


            const score =
                Number(
                    session.integrityScore || 0
                );


            const severity =
                Number(
                    session.severityScore || 0
                );


            const events =
                Number(
                    session.totalEvents || 0
                );


            const face =
                Number(
                    session.facePresence || 0
                );


            const risk =
                getRiskLabel(
                    session,
                    score
                );


            const photo =
                session.photo ||
                "/static/images/default-avatar.png";


            row.innerHTML = `

                <td>

                    <div class="candidate-cell">

                        <img
                            class="candidate-avatar"
                            src="${escapeHtml(photo)}"
                            alt="Candidate"
                            onerror="
                                this.onerror=null;
                                this.src='/static/images/default-avatar.png';
                            "
                        >

                        <div class="candidate-info">

                            <span class="candidate-name">
                                ${escapeHtml(
                                    session.candidateName ||
                                    "Unknown Candidate"
                                )}
                            </span>

                            <span class="candidate-email">
                                ${escapeHtml(
                                    session.candidateEmail ||
                                    ""
                                )}
                            </span>

                        </div>

                    </div>

                </td>


                <td>
                    ${escapeHtml(
                        String(
                            session.candidateId ?? "-"
                        )
                    )}
                </td>


                <td>
                    ${escapeHtml(
                        session.examTitle ||
                        "-"
                    )}
                </td>


                <td>
                    ${events}
                </td>


                <td>
                    ${severity.toFixed(1)}
                </td>


                <td>

                    <div class="face-progress">

                        <span
                            style="
                                width:${Math.min(
                                    Math.max(
                                        face,
                                        0
                                    ),
                                    100
                                )}%;
                            "
                        ></span>

                    </div>

                    ${face.toFixed(1)}%

                </td>


                <td>

                    <div
                        class="score-ring"
                        style="
                            border-color:${getScoreColor(
                                score
                            )};
                        "
                    >
                        ${score.toFixed(0)}
                    </div>

                </td>


                <td>

                    <span
                        class="risk ${risk.toLowerCase()}"
                    >
                        ${escapeHtml(risk)}
                    </span>

                </td>


                <td>

                    <button
                        class="view-btn"
                        type="button"
                        data-session-id="${escapeHtml(
                            String(
                                session.id ?? ""
                            )
                        )}"
                    >
                        View Analysis
                    </button>

                </td>

            `;


            const viewButton =
                row.querySelector(
                    ".view-btn"
                );


            if (viewButton) {

                viewButton.addEventListener(
                    "click",
                    function () {

                        viewSession(
                            session.id
                        );

                    }
                );

            }


            tbody.appendChild(
                row
            );

        }
    );

}


/* =========================================================
   RISK LABEL
   ========================================================= */

function getRiskLabel(
    session,
    score
) {

    if (session.riskLevel) {

        const risk =
            String(
                session.riskLevel
            )
            .trim()
            .toLowerCase();


        if (
            risk === "low" ||
            risk === "medium" ||
            risk === "high"
        ) {

            return (
                risk.charAt(0).toUpperCase() +
                risk.slice(1)
            );

        }

    }


    if (score >= 80) {
        return "Low";
    }


    if (score >= 60) {
        return "Medium";
    }


    return "High";

}


/* =========================================================
   SCORE COLOR
   ========================================================= */

function getScoreColor(
    score
) {

    if (score >= 80) {
        return "#22d3a3";
    }


    if (score >= 60) {
        return "#f59e0b";
    }


    return "#ef4444";

}


/* =========================================================
   SCORE DISTRIBUTION
   ========================================================= */

function renderDistribution(
    data
) {

    const canvas =
        document.getElementById(
            "distributionChart"
        );


    if (!canvas) {
        return;
    }


    destroyChart(
        distributionChart
    );


    distributionChart =
        null;


    const labels =
        Array.isArray(
            data.labels
        )
            ? data.labels
            : [];


    const values =
        Array.isArray(
            data.values
        )
            ? data.values.map(
                Number
            )
            : [];


    distributionChart =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {

                    labels: labels,

                    datasets: [
                        {
                            label:
                                "Sessions",

                            data:
                                values,

                            backgroundColor:
                                "rgba(139,92,246,0.78)",

                            borderColor:
                                "#8b5cf6",

                            borderWidth: 1,

                            borderRadius: 4
                        }
                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {
                            display: false
                        }

                    },

                    scales: {

                        x: {

                            ticks: {
                                color: "#718099",
                                font: {
                                    size: 8
                                }
                            },

                            grid: {
                                color:
                                    "rgba(148,163,184,0.06)"
                            }

                        },

                        y: {

                            beginAtZero: true,

                            ticks: {

                                color: "#718099",

                                font: {
                                    size: 8
                                },

                                precision: 0

                            },

                            grid: {

                                color:
                                    "rgba(148,163,184,0.06)"

                            }

                        }

                    }

                }

            }
        );

}


/* =========================================================
   RISK DISTRIBUTION
   ========================================================= */

function renderRiskDistribution(
    data
) {

    const canvas =
        document.getElementById(
            "riskChart"
        );


    if (!canvas) {
        return;
    }


    destroyChart(
        riskChart
    );


    riskChart =
        null;


    const values =
        Array.isArray(
            data.values
        )
            ? data.values
            : [];


    const low =
        Number(
            values[0] || 0
        );


    const medium =
        Number(
            values[1] || 0
        );


    const high =
        Number(
            values[2] || 0
        );


    const total =
        low +
        medium +
        high;


    setText(
        "lowRiskPercent",
        total
            ? ((low / total) * 100).toFixed(1) + "%"
            : "0%"
    );


    setText(
        "mediumRiskPercent",
        total
            ? ((medium / total) * 100).toFixed(1) + "%"
            : "0%"
    );


    setText(
        "highRiskPercent",
        total
            ? ((high / total) * 100).toFixed(1) + "%"
            : "0%"
    );


    riskChart =
        new Chart(
            canvas,
            {
                type: "doughnut",

                data: {

                    labels: [
                        "Low Risk",
                        "Medium Risk",
                        "High Risk"
                    ],

                    datasets: [
                        {
                            data: [
                                low,
                                medium,
                                high
                            ],

                            backgroundColor: [
                                "#22d3a3",
                                "#f59e0b",
                                "#ef4444"
                            ],

                            borderWidth: 0
                        }
                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    cutout: "68%",

                    plugins: {

                        legend: {
                            display: false
                        }

                    }

                }

            }
        );

}


/* =========================================================
   HEATMAP
   ========================================================= */

function renderHeatmap(
    data
) {

    const container =
        document.getElementById(
            "heatmap"
        );


    const labels =
        document.getElementById(
            "heatmapLabels"
        );


    const hours =
        document.getElementById(
            "heatmapHours"
        );


    if (
        !container ||
        !labels ||
        !hours
    ) {
        return;
    }


    container.innerHTML =
        "";


    labels.innerHTML =
        "";


    hours.innerHTML =
        "";


    const events =
        Array.isArray(
            data.events
        )
            ? data.events
            : [];


    if (!events.length) {

        labels.innerHTML =
            "<div>No events</div>";


        container.innerHTML =
            `
            <div
                class="empty-state"
                style="
                    grid-column:1 / -1;
                "
            >
                <i class="fa-solid fa-chart-area"></i>

                No violation activity recorded.

            </div>
            `;


        return;

    }


    events.forEach(
        function (event) {

            const label =
                document.createElement(
                    "div"
                );


            label.textContent =
                formatEventName(
                    event.event
                );


            labels.appendChild(
                label
            );

        }
    );


    events.forEach(
        function (event) {

            const values =
                Array.isArray(
                    event.values
                )
                    ? event.values
                    : [];


            for (
                let hour = 0;
                hour < 24;
                hour++
            ) {

                const value =
                    Number(
                        values[hour] || 0
                    );


                const cell =
                    document.createElement(
                        "div"
                    );


                cell.className =
                    "heat-cell";


                if (value >= 1) {

                    cell.classList.add(
                        "level-1"
                    );

                }


                if (value >= 3) {

                    cell.classList.add(
                        "level-2"
                    );

                }


                if (value >= 6) {

                    cell.classList.add(
                        "level-3"
                    );

                }


                if (value >= 10) {

                    cell.classList.add(
                        "level-4"
                    );

                }


                cell.title =
                    formatEventName(
                        event.event
                    ) +
                    " at " +
                    hour +
                    ":00 — " +
                    value +
                    " event(s)";


                container.appendChild(
                    cell
                );

            }

        }
    );


    for (
        let hour = 0;
        hour < 24;
        hour++
    ) {

        const hourLabel =
            document.createElement(
                "div"
            );


        hourLabel.textContent =
            hour;


        hours.appendChild(
            hourLabel
        );

    }

}


/* =========================================================
   CLUSTERING
   ========================================================= */

function renderClusters(
    clusters
) {

    const container =
        document.getElementById(
            "clusters"
        );


    const canvas =
        document.getElementById(
            "clusterChart"
        );


    if (!container) {
        return;
    }


    container.innerHTML =
        "";


    destroyChart(
        clusterChart
    );


    clusterChart =
        null;


    if (
        !Array.isArray(
            clusters
        ) ||
        clusters.length === 0
    ) {

        container.innerHTML =
            `
            <div class="empty-state">

                <i class="fa-solid fa-diagram-project"></i>

                <span>
                    At least 3 sessions are required
                    for K-Means clustering.
                </span>

            </div>
            `;

        return;

    }


    clusters.forEach(
        function (cluster) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "cluster-item";


            const score =
                Number(
                    cluster.average_score || 0
                );


            const color =
                getScoreColor(
                    score
                );


            item.innerHTML =
                `

                <div class="cluster-title">

                    <strong>

                        <span
                            class="cluster-risk-dot"
                            style="
                                background:${color};
                            "
                        ></span>

                        Cluster ${escapeHtml(
                            String(
                                cluster.cluster ?? "-"
                            )
                        )}

                    </strong>

                    <span>
                        ${Number(
                            cluster.count || 0
                        )}
                        sessions
                    </span>

                </div>


                <div class="cluster-info">

                    ${escapeHtml(
                        cluster.behavior ||
                        "Behaviour pattern"
                    )}

                    · Average score:
                    ${Number(
                        cluster.average_score || 0
                    ).toFixed(2)}

                    · Average events:
                    ${Number(
                        cluster.average_events || 0
                    ).toFixed(2)}

                </div>

                `;


            container.appendChild(
                item
            );

        }
    );


    if (!canvas) {
        return;
    }


    const datasets =
        clusters.map(
            function (cluster) {

                const score =
                    Number(
                        cluster.average_score || 0
                    );


                const events =
                    Number(
                        cluster.average_events || 0
                    );


                const count =
                    Number(
                        cluster.count || 0
                    );


                const color =
                    getScoreColor(
                        score
                    );


                return {

                    label:
                        "Cluster " +
                        cluster.cluster,

                    data: [
                        {
                            x: events,

                            y: score,

                            r:
                                Math.max(
                                    6,
                                    Math.min(
                                        20,
                                        5 + count
                                    )
                                )
                        }
                    ],

                    backgroundColor:
                        color,

                    borderColor:
                        color,

                    borderWidth: 1

                };

            }
        );


    clusterChart =
        new Chart(
            canvas,
            {
                type: "bubble",

                data: {

                    datasets:
                        datasets

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {

                            labels: {

                                color:
                                    "#8b98ad",

                                font: {
                                    size: 8
                                }

                            }

                        }

                    },

                    scales: {

                        x: {

                            title: {

                                display: true,

                                text:
                                    "Average Events",

                                color:
                                    "#6f7e96",

                                font: {
                                    size: 8
                                }

                            },

                            ticks: {

                                color:
                                    "#65748b",

                                font: {
                                    size: 7
                                }

                            },

                            grid: {

                                color:
                                    "rgba(148,163,184,0.06)"

                            }

                        },

                        y: {

                            beginAtZero: true,

                            max: 100,

                            title: {

                                display: true,

                                text:
                                    "Average Integrity Score",

                                color:
                                    "#6f7e96",

                                font: {
                                    size: 8
                                }

                            },

                            ticks: {

                                color:
                                    "#65748b",

                                font: {
                                    size: 7
                                }

                            },

                            grid: {

                                color:
                                    "rgba(148,163,184,0.06)"

                            }

                        }

                    }

                }

            }
        );

}


/* =========================================================
   COHORTS
   ========================================================= */

function renderCohorts(
    cohorts
) {

    const tbody =
        document.getElementById(
            "cohortTable"
        );


    if (!tbody) {
        return;
    }


    tbody.innerHTML =
        "";


    if (
        !Array.isArray(
            cohorts
        ) ||
        cohorts.length === 0
    ) {

        tbody.innerHTML =
            createEmptyRow(
                4,
                "No cohort data available."
            );

        return;

    }


    cohorts.forEach(
        function (cohort) {

            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML =
                `

                <td>
                    ${escapeHtml(
                        cohort.cohort ||
                        "-"
                    )}
                </td>

                <td>
                    ${Number(
                        cohort.sessions || 0
                    )}
                </td>

                <td>
                    ${Number(
                        cohort.averageScore || 0
                    ).toFixed(2)}
                </td>

                <td>
                    ${Number(
                        cohort.highRisk || 0
                    )}
                </td>

                `;


            tbody.appendChild(
                row
            );

        }
    );

}


/* =========================================================
   RECENT ACTIVITY
   ========================================================= */

function renderRecentActivity(activities) {

    const container =
        document.getElementById("recentActivity");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (
        !Array.isArray(activities) ||
        activities.length === 0
    ) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-shield"></i>
                No recent integrity activity.
            </div>
        `;

        return;
    }

    activities.forEach(function (activity) {

        const item =
            document.createElement("div");

        item.className = "activity-item";

        const candidateImage =
            activity.candidateImage ||
            activity.profileImage ||
            activity.photo ||
            "";

        const imageHTML = candidateImage
            ? `
                <img
                    src="${escapeHtml(candidateImage)}"
                    alt="${escapeHtml(
                        activity.candidateName || "Candidate"
                    )}"
                    class="activity-candidate-image"
                    onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                >

                <div
                    class="activity-icon"
                    style="display:none;"
                >
                    <i class="fa-solid fa-user"></i>
                </div>
              `
            : `
                <div class="activity-icon">
                    <i class="fa-solid fa-user"></i>
                </div>
              `;

        item.innerHTML = `

            ${imageHTML}

            <div class="activity-main">

                <strong>
                    ${escapeHtml(
                        activity.event ||
                        "Integrity Event"
                    )}
                </strong>

                <span>

                    ${escapeHtml(
                        activity.candidateName ||
                        "Unknown"
                    )}

                    ·

                    ${escapeHtml(
                        activity.examTitle ||
                        "Unknown Examination"
                    )}

                </span>

            </div>

            <div class="activity-time">

                ${escapeHtml(
                    activity.time || ""
                )}

            </div>

        `;

        container.appendChild(item);

    });
}


/* =========================================================
   VIEW SESSION
   ========================================================= */

function viewSession(
    sessionId
) {

    if (
        !currentData ||
        !Array.isArray(
            currentData.sessions
        )
    ) {

        return;

    }


    const session =
        currentData.sessions.find(
            function (item) {

                return Number(
                    item.id
                ) === Number(
                    sessionId
                );

            }
        );


    if (!session) {
        return;
    }


    showSessionModal(
        session
    );

}


/* =========================================================
   SESSION DETAILS MODAL
   ========================================================= */

function createSessionModal() {

    if (
        document.getElementById(
            "sessionDetailsModal"
        )
    ) {

        return;

    }


    const modal =
        document.createElement(
            "div"
        );


    modal.id =
        "sessionDetailsModal";


    modal.style.cssText = `
        position:fixed;
        inset:0;
        background:rgba(0,0,0,.65);
        display:none;
        align-items:center;
        justify-content:center;
        z-index:99999;
        padding:20px;
        backdrop-filter:blur(4px);
    `;


    modal.innerHTML =
        `

        <div
            id="sessionDetailsBox"
            style="
                width:min(720px, 95vw);
                max-height:90vh;
                overflow:auto;
                background:#111827;
                color:#e5e7eb;
                border-radius:16px;
                box-shadow:0 25px 80px rgba(0,0,0,.45);
                padding:24px;
            "
        >

            <div
                style="
                    display:flex;
                    align-items:center;
                    justify-content:space-between;
                    gap:20px;
                    margin-bottom:20px;
                "
            >

                <div>

                    <h2
                        id="sessionModalTitle"
                        style="
                            margin:0;
                            font-size:22px;
                        "
                    >
                        Session Analysis
                    </h2>

                    <small
                        style="
                            color:#94a3b8;
                        "
                    >
                        Candidate integrity analysis
                    </small>

                </div>


                <button
                    id="closeSessionModal"
                    type="button"
                    style="
                        border:0;
                        background:#1f2937;
                        color:#fff;
                        width:38px;
                        height:38px;
                        border-radius:10px;
                        cursor:pointer;
                        font-size:18px;
                    "
                    aria-label="Close"
                >
                    ×
                </button>

            </div>


            <div id="sessionModalContent"></div>

        </div>

        `;


    document.body.appendChild(
        modal
    );


    const closeButton =
        document.getElementById(
            "closeSessionModal"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeSessionModal
        );

    }


    modal.addEventListener(
        "click",
        function (event) {

            if (
                event.target === modal
            ) {

                closeSessionModal();

            }

        }
    );


    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
            ) {

                closeSessionModal();

            }

        }
    );

}


function showSessionModal(
    session
) {

    const modal =
        document.getElementById(
            "sessionDetailsModal"
        );


    const title =
        document.getElementById(
            "sessionModalTitle"
        );


    const content =
        document.getElementById(
            "sessionModalContent"
        );


    if (
        !modal ||
        !content
    ) {

        return;

    }


    const score =
        Number(
            session.integrityScore || 0
        );


    const severity =
        Number(
            session.severityScore || 0
        );


    const face =
        Number(
            session.facePresence || 0
        );


    const events =
        Number(
            session.totalEvents || 0
        );


    const risk =
        getRiskLabel(
            session,
            score
        );


    if (title) {

        title.textContent =
            session.candidateName ||
            "Session Analysis";

    }


    content.innerHTML =
        `

        <div
            style="
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
                gap:14px;
            "
        >

            ${createDetailCard(
                "Candidate",
                session.candidateName || "-"
            )}

            ${createDetailCard(
                "Candidate ID",
                session.candidateId ?? "-"
            )}

            ${createDetailCard(
                "Email",
                session.candidateEmail || "-"
            )}

            ${createDetailCard(
                "Examination",
                session.examTitle || "-"
            )}

            ${createDetailCard(
                "Topic",
                session.examTopic || "-"
            )}

            ${createDetailCard(
                "Total Events",
                events
            )}

            ${createDetailCard(
                "Severity Score",
                severity.toFixed(1)
            )}

            ${createDetailCard(
                "Face Presence",
                face.toFixed(1) + "%"
            )}

            ${createDetailCard(
                "Integrity Score",
                score.toFixed(1)
            )}

            ${createDetailCard(
                "Risk Level",
                risk
            )}

            ${createDetailCard(
                "Warning Count",
                Number(
                    session.warningCount || 0
                )
            )}

            ${createDetailCard(
                "Generated At",
                session.generatedAt || "-"
            )}

        </div>

        <div
            style="
                margin-top:20px;
                padding:16px;
                border-radius:12px;
                background:#0f172a;
                border-left:4px solid ${getScoreColor(score)};
            "
        >

            <strong>
                Integrity Assessment
            </strong>

            <p
                style="
                    margin:8px 0 0;
                    color:#94a3b8;
                    line-height:1.6;
                "
            >
                ${getIntegrityDescription(
                    score,
                    risk
                )}
            </p>

        </div>

        `;


    modal.style.display =
        "flex";


    document.body.style.overflow =
        "hidden";

}


function createDetailCard(
    label,
    value
) {

    return `
        <div
            style="
                background:#1e293b;
                padding:14px;
                border-radius:12px;
                border:1px solid rgba(148,163,184,.12);
            "
        >

            <small
                style="
                    display:block;
                    color:#94a3b8;
                    margin-bottom:6px;
                "
            >
                ${escapeHtml(label)}
            </small>

            <strong
                style="
                    color:#f8fafc;
                    word-break:break-word;
                "
            >
                ${escapeHtml(
                    String(value ?? "-")
                )}
            </strong>

        </div>
    `;

}


function getIntegrityDescription(
    score,
    risk
) {

    if (risk === "Low") {

        return (
            "This session has a low integrity risk based on the calculated integrity score."
        );

    }


    if (risk === "Medium") {

        return (
            "This session requires attention because the calculated integrity score indicates a medium level of integrity risk."
        );

    }


    return (
        "This session has a high integrity risk and should be reviewed by the administrator."
    );

}


function closeSessionModal() {

    const modal =
        document.getElementById(
            "sessionDetailsModal"
        );


    if (modal) {

        modal.style.display =
            "none";

    }


    document.body.style.overflow =
        "";

}



function createProfileRow(
    label,
    value
) {

    return `
        <div
            style="
                display:flex;
                justify-content:space-between;
                gap:15px;
                padding:10px 0;
                border-bottom:1px solid rgba(148,163,184,.1);
            "
        >

            <span
                style="
                    color:#94a3b8;
                    font-size:13px;
                "
            >
                ${escapeHtml(label)}
            </span>

            <strong
                style="
                    text-align:right;
                    font-size:13px;
                    word-break:break-word;
                "
            >
                ${escapeHtml(
                    String(value ?? "-")
                )}
            </strong>

        </div>
    `;

}


/* =========================================================
   EXPORT REPORT
   ========================================================= */

function createExportButton() {

    if (
        document.getElementById(
            "exportReportBtn"
        )
    ) {

        return;

    }


    const sessionsPanel =
        document.querySelector(
            ".sessions-panel"
        );


    if (!sessionsPanel) {
        return;
    }


    const panelHeader =
        sessionsPanel.querySelector(
            ".panel-header"
        );


    if (!panelHeader) {
        return;
    }


    const button =
        document.createElement(
            "button"
        );


    button.id =
        "exportReportBtn";


    button.type =
        "button";


    button.className =
        "refresh-btn";


    button.style.cssText = `
        display:flex;
        align-items:center;
        gap:7px;
        margin-left:auto;
    `;


    button.innerHTML =
        `
        <i class="fa-solid fa-file-export"></i>
        Export Report
        `;


    button.addEventListener(
        "click",
        exportReport
    );


    const badge =
        panelHeader.querySelector(
            ".panel-badge"
        );


    if (badge) {

        badge.parentNode.insertBefore(
            button,
            badge
        );

    }
    else {

        panelHeader.appendChild(
            button
        );

    }

}


function exportReport() {

    if (
        !currentData ||
        !Array.isArray(
            currentData.sessions
        )
    ) {

        alert(
            "There is no integrity data available to export."
        );

        return;

    }


    const sessions =
        currentData.sessions;


    if (!sessions.length) {

        alert(
            "There are no sessions available to export."
        );

        return;

    }


    const headers = [

        "Candidate",

        "Candidate ID",

        "Email",

        "Examination",

        "Exam Topic",

        "Total Events",

        "Severity Score",

        "Face Presence (%)",

        "Integrity Score",

        "Risk Level",

        "Warning Count",

        "Generated At"

    ];


    const rows =
        sessions.map(
            function (session) {

                return [

                    session.candidateName || "",

                    session.candidateId ?? "",

                    session.candidateEmail || "",

                    session.examTitle || "",

                    session.examTopic || "",

                    session.totalEvents ?? 0,

                    Number(
                        session.severityScore || 0
                    ).toFixed(1),

                    Number(
                        session.facePresence || 0
                    ).toFixed(1),

                    Number(
                        session.integrityScore || 0
                    ).toFixed(1),

                    getRiskLabel(
                        session,
                        Number(
                            session.integrityScore || 0
                        )
                    ),

                    session.warningCount ?? 0,

                    session.generatedAt || ""

                ];

            }
        );


    const csv =
        [
            headers,
            ...rows
        ]
        .map(
            function (row) {

                return row
                    .map(
                        csvEscape
                    )
                    .join(",");

            }
        )
        .join("\r\n");


    const blob =
        new Blob(
            [
                "\uFEFF" +
                csv
            ],
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


    const examFilter =
        document.getElementById(
            "examFilter"
        );


    const selectedExam =
        examFilter &&
        examFilter.selectedOptions.length
            ? examFilter.selectedOptions[0].textContent.trim()
            : "All-Examinations";


    const safeExamName =
        selectedExam
            .replace(
                /[^a-z0-9]+/gi,
                "_"
            )
            .replace(
                /^_+|_+$/g,
                ""
            );


    const timestamp =
        new Date()
            .toISOString()
            .replace(
                /[:.]/g,
                "-"
            );


    link.download =
        `integrity_report_${safeExamName}_${timestamp}.csv`;


    document.body.appendChild(
        link
    );


    link.click();


    link.remove();


    setTimeout(
        function () {

            URL.revokeObjectURL(
                url
            );

        },
        1000
    );

}


function csvEscape(
    value
) {

    const text =
        String(
            value ?? ""
        );


    return (
        '"' +
        text
            .replace(
                /"/g,
                '""'
            ) +
        '"'
    );

}


/* =========================================================
   SEARCH
   ========================================================= */

function filterSessions(
    query
) {

    if (
        !currentData ||
        !Array.isArray(
            currentData.sessions
        )
    ) {

        return;

    }


    const value =
        String(
            query || ""
        )
        .trim()
        .toLowerCase();


    const rows =
        document.querySelectorAll(
            "#sessionsTable tr"
        );


    rows.forEach(
        function (row) {

            if (!value) {

                row.style.display =
                    "";

                return;

            }


            const text =
                row.textContent
                    .toLowerCase();


            row.style.display =
                text.includes(
                    value
                )
                    ? ""
                    : "none";

        }
    );

}


/* =========================================================
   KEYBOARD SEARCH
   ========================================================= */

function initializeKeyboardShortcut() {

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.ctrlKey &&
                event.key === "/"
            ) {

                event.preventDefault();


                const search =
                    document.getElementById(
                        "globalSearch"
                    );


                if (search) {

                    search.focus();

                }

            }

        }
    );

}


/* =========================================================
   THEME
   ========================================================= */

function toggleTheme() {

    const body =
        document.body;


    const themeBtn =
        document.getElementById(
            "themeBtn"
        );


    body.classList.toggle(
        "light-theme"
    );


    const isLight =
        body.classList.contains(
            "light-theme"
        );


    localStorage.setItem(
        "integrity-theme",
        isLight
            ? "light"
            : "dark"
    );


    if (themeBtn) {

        const icon =
            themeBtn.querySelector(
                "i"
            );


        if (icon) {

            icon.className =
                isLight
                    ? "fa-regular fa-sun"
                    : "fa-regular fa-moon";

        }

    }

}


function initializeTheme() {

    const savedTheme =
        localStorage.getItem(
            "integrity-theme"
        );


    if (
        savedTheme === "light"
    ) {

        document.body.classList.add(
            "light-theme"
        );


        const themeBtn =
            document.getElementById(
                "themeBtn"
            );


        if (themeBtn) {

            const icon =
                themeBtn.querySelector(
                    "i"
                );


            if (icon) {

                icon.className =
                    "fa-regular fa-sun";

            }

        }

    }

}


/* =========================================================
   HELPERS
   ========================================================= */

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


function destroyChart(
    chart
) {

    if (chart) {

        try {

            chart.destroy();

        }
        catch (error) {

            console.warn(
                "Chart destroy error:",
                error
            );

        }

    }

}


function createEmptyRow(
    colspan,
    message
) {

    return `

        <tr>

            <td
                colspan="${colspan}"
                style="
                    text-align:center;
                    padding:30px;
                    color:#66758d;
                "
            >

                <i
                    class="fa-solid fa-database"
                    style="
                        margin-right:6px;
                    "
                ></i>

                ${escapeHtml(
                    message
                )}

            </td>

        </tr>

    `;

}


function formatEventName(
    value
) {

    return String(
        value || "OTHER"
    )
    .replaceAll(
        "_",
        " "
    )
    .toLowerCase()
    .replace(
        /\b\w/g,
        function (letter) {

            return letter.toUpperCase();

        }
    );

}


function escapeHtml(
    value
) {

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


/* =========================================================
   LAST UPDATED
   ========================================================= */

function updateLastUpdated() {

    const element =
        document.getElementById(
            "lastUpdated"
        );


    if (!element) {
        return;
    }


    const now =
        new Date();


    element.textContent =
        "Last updated: " +
        now.toLocaleString();

}


/* =========================================================
   LOADING STATE
   ========================================================= */

function setLoadingState(
    loading
) {

    const refreshBtn =
        document.getElementById(
            "refreshBtn"
        );


    if (!refreshBtn) {
        return;
    }


    if (loading) {

        refreshBtn.disabled =
            true;

        refreshBtn.style.opacity =
            "0.65";

    }
    else {

        refreshBtn.disabled =
            false;

        refreshBtn.style.opacity =
            "";

    }

}


/* =========================================================
   GLOBAL ERROR
   ========================================================= */

function showGlobalError(
    message
) {

    console.error(
        "Integrity Analysis:",
        message
    );


    const tbody =
        document.getElementById(
            "sessionsTable"
        );


    if (tbody) {

        tbody.innerHTML =
            createEmptyRow(
                9,
                "Unable to load integrity analysis data."
            );

    }

}


/* =========================================================
   PAGE CLEANUP
   ========================================================= */

window.addEventListener(
    "beforeunload",
    function () {

        if (refreshTimer) {

            clearInterval(
                refreshTimer
            );

        }


        destroyChart(
            distributionChart
        );

        destroyChart(
            riskChart
        );

        destroyChart(
            clusterChart
        );

        destroyChart(
            sessionsMiniChart
        );

        destroyChart(
            scoreMiniChart
        );

        destroyChart(
            faceMiniChart
        );

    }
);


/* =========================================================
   INITIAL THEME
   ========================================================= */

initializeTheme();