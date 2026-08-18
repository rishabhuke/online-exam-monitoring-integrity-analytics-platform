/* =========================================================
   INTEGRITY ANALYSIS CENTER
   ========================================================= */

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


    if (examFilter) {

        examFilter.addEventListener(
            "change",
            function () {

                loadIntegrityAnalysis();

            }
        );

    }


    if (refreshBtn) {

        refreshBtn.addEventListener(
            "click",
            function () {

                loadIntegrityAnalysis();

            }
        );

    }


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


    initializeKeyboardShortcut();

    loadIntegrityAnalysis();


    /*
       Refresh every 10 seconds.
       This keeps LIVE analysis updated.
    */

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
   LOAD API DATA
   ========================================================= */
async function loadIntegrityAnalysis() {

    try {

        const examId =
            document.getElementById("examFilter")?.value || "";

        let url =
            "/admin/api/integrity-analysis";

        if (examId) {
            url += "?exam_id=" +
                encodeURIComponent(examId);
        }

        console.log(
            "Loading integrity API:",
            url
        );

        const response =
            await fetch(url, {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                }
            });

        console.log(
            "Integrity API status:",
            response.status
        );

        const data =
            await response.json();

currentData = data; 

        console.log(
            "Integrity API data:",
            data
        );

        // =====================================================
        // ONLY CHECK HTTP STATUS
        // =====================================================

        if (!response.ok) {

            throw new Error(
                data.message ||
                data.error ||
                "Integrity analysis API request failed"
            );

        }
function populateExamFilter(exams) {

    const select =
        document.getElementById("examFilter");

    if (!select) return;

    const currentValue =
        select.value;

    select.innerHTML = `
        <option value="">
            All Examinations
        </option>
    `;

    exams.forEach(exam => {

        const option =
            document.createElement("option");

        option.value = exam.id;

        option.textContent =
            exam.title;

        select.appendChild(option);

    });

    if (
        currentValue &&
        exams.some(
            exam =>
                String(exam.id) ===
                String(currentValue)
        )
    ) {
        select.value =
            currentValue;
    }
}

        // =====================================================
        // RENDER DATA
        // =====================================================

        populateExamFilter(data.exams || []);

        renderSummary(data.summary || {});
        renderIntegrityTable(data.sessions || []);

renderMiniCharts(
    (data.summary?.totalSessions || 0),
    (data.sessions || []).map(s => Number(s.integrityScore || 0)),
    (data.sessions || []).map(s => Number(s.facePresence || 0))
);

      

        renderDistribution(
            data.distribution || {}
        );

        renderRiskDistribution(
            data.riskDistribution || {}
        );

        renderHeatmap(
            data.heatmap || []
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
}


/* =========================================================
   EXAMINATION DROPDOWN
   ========================================================= */




/* =========================================================
   SUMMARY
   ========================================================= */

function renderSummary(summary) {

    document.getElementById("totalSessions").textContent =
        summary.totalSessions ?? 0;

    document.getElementById("averageScore").textContent =
        summary.averageScore ?? 0;

    document.getElementById("lowRisk").textContent =
        summary.lowRisk ?? 0;

    document.getElementById("mediumRisk").textContent =
        summary.mediumRisk ?? 0;

    document.getElementById("highRisk").textContent =
        summary.highRisk ?? 0;

    document.getElementById("facePresence").textContent =
        (summary.facePresence ?? 0) + "%";
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


    /*
     * Session chart.
     * Uses session ordering as returned
     * by backend.
     */

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


    /*
     * Score chart.
     */

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


    /*
     * Face presence chart.
     */

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

                        borderColor: color,

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


    tbody.innerHTML = "";


    if (!sessions.length) {

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
                                this.src='/static/images/default-avatar.png'
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
                            session.candidateId ??
                            "-"
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
                                    Math.max(face, 0),
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
            ).toLowerCase();


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

const values = data.values || [];

const low = Number(values[0] || 0);

const medium = Number(values[1] || 0);

const high = Number(values[2] || 0);


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


    container.innerHTML = "";
    labels.innerHTML = "";
    hours.innerHTML = "";


    const events =
        Array.isArray(
            data.events
        )
            ? data.events
            : [];


    /*
     * Backend sends event rows.
     */

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


    /*
     * Event labels.
     */

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


    /*
     * Every event has 24 values.
     */

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


    /*
     * Hour labels.
     */

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


    container.innerHTML = "";


    destroyChart(
        clusterChart
    );


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


    /*
     * Create cluster cards.
     */

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


            item.innerHTML = `

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
                                cluster.cluster ??
                                "-"
                            )
                        )}

                    </strong>

                    <span>
                        ${Number(
                            cluster.count || 0
                        )} sessions
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


    /*
     * Visual cluster chart.
     *
     * Your current backend cluster response
     * contains aggregate cluster information,
     * not individual coordinates.
     *
     * Therefore the chart uses:
     *
     * X = average events
     * Y = average integrity score
     *
     * Bubble size = session count
     */

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
                        getScoreColor(score),

                    borderColor:
                        getScoreColor(score),

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
                                color: "#8b98ad",
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
                                color: "#6f7e96",
                                font: {
                                    size: 8
                                }
                            },

                            ticks: {
                                color: "#65748b",
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
                                color: "#6f7e96",
                                font: {
                                    size: 8
                                }
                            },

                            ticks: {
                                color: "#65748b",
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


    tbody.innerHTML = "";


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


            row.innerHTML = `

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

function renderRecentActivity(
    activities
) {

    const container =
        document.getElementById(
            "recentActivity"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(
            activities
        ) ||
        activities.length === 0
    ) {

        container.innerHTML =
            `
            <div class="empty-state">

                <i class="fa-solid fa-shield"></i>

                No recent integrity activity.

            </div>
            `;

        return;

    }


    activities.forEach(
        function (activity) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "activity-item";


            item.innerHTML = `

                <div class="activity-icon">

                    <i class="fa-solid fa-shield-halved"></i>

                </div>


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
                        activity.time ||
                        ""
                    )}

                </div>

            `;


            container.appendChild(
                item
            );

        }
    );

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


    const message =

        "Candidate: " +
        (session.candidateName || "-") +

        "\nCandidate ID: " +
        (session.candidateId || "-") +

        "\nExamination: " +
        (session.examTitle || "-") +

        "\nTotal Events: " +
        (session.totalEvents || 0) +

        "\nSeverity Score: " +
        Number(
            session.severityScore || 0
        ).toFixed(1) +

        "\nFace Presence: " +
        Number(
            session.facePresence || 0
        ).toFixed(1) +
        "%" +

        "\nIntegrity Score: " +
        Number(
            session.integrityScore || 0
        ).toFixed(0) +

        "\nRisk Level: " +
        getRiskLabel(
            session,
            Number(
                session.integrityScore || 0
            )
        );


    alert(
        message
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
                text.includes(value)
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

                ${escapeHtml(message)}

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

    const element = document.getElementById("lastUpdated");

    if (!element) return;

    const now = new Date();

    element.textContent =
        "Last updated: " +
        now.toLocaleString();
}
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

    }
);