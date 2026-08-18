document.addEventListener(
    "DOMContentLoaded",
    () => {
        initializeAnalytics();
        initializeExamAIReport();
    }
);


// ==========================================================
// GLOBAL STATE
// ==========================================================

let exams = [];

let selectedExam = null;

let candidates = [];


// ==========================================================
// INITIALIZE
// ==========================================================

async function initializeAnalytics() {

    console.log(
        "Integrity Analytics initialized"
    );

    const refreshBtn =
        document.getElementById("refreshBtn");

    refreshBtn?.addEventListener(
        "click",
        () => {

            if (selectedExam) {

                loadAnalytics(
                    selectedExam.id
                );

            } else {

                loadExams();

            }

        }
    );


    const examSelect =
        document.getElementById("examSelect");


    examSelect.addEventListener(
        "change",
        handleExamChange
    );


    const search =
        document.getElementById(
            "candidateSearch"
        );


    search?.addEventListener(
        "input",
        filterCandidates
    );


    await loadExams();
}


// ==========================================================
// LOAD EXAMS
// ==========================================================

async function loadExams() {

    const select =
        document.getElementById(
            "examSelect"
        );


    select.innerHTML = `
        <option value="">
            Loading examinations...
        </option>
    `;


    try {

        const response =
            await fetch(
                "/api/integrity/exams",
                {
                    cache: "no-store"
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Unable to load examinations"
            );

        }


        exams = data.exams || [];


        select.innerHTML = `
            <option value="">
                Select an examination
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
                    `${exam.title} • ${exam.difficulty} • ${exam.total_questions} Questions`;


                select.appendChild(
                    option
                );

            }
        );


    } catch(error) {

        console.error(
            "Exam loading error:",
            error
        );


        select.innerHTML = `
            <option value="">
                Unable to load examinations
            </option>
        `;

    }

}


// ==========================================================
// EXAM CHANGE
// ==========================================================

async function handleExamChange(
    event
) {

    const examId =
        event.target.value;


    if (!examId) {

        selectedExam = null;

        document
            .getElementById(
                "examHero"
            )
            .classList.add(
                "hidden"
            );

        document
            .getElementById(
                "analyticsContent"
            )
            .classList.add(
                "hidden"
            );

        document
            .getElementById(
                "emptyState"
            )
            .classList.remove(
                "hidden"
            );

        return;
    }


    selectedExam =
        exams.find(
            exam =>
                String(exam.id) ===
                String(examId)
        );


    if (!selectedExam) {

        return;

    }


    renderExamHero(
        selectedExam
    );


    await loadAnalytics(
        selectedExam.id
    );
    await loadDataScienceAnalytics(
    selectedExam.id
);

}


// ==========================================================
// EXAM HERO
// ==========================================================

function renderExamHero(
    exam
) {

    document
        .getElementById(
            "emptyState"
        )
        .classList.add(
            "hidden"
        );


    document
        .getElementById(
            "examHero"
        )
        .classList.remove(
            "hidden"
        );


    document
        .getElementById(
            "analyticsContent"
        )
        .classList.remove(
            "hidden"
        );


    setText(
        "heroExamTitle",
        exam.title
    );


    setText(
        "heroExamDescription",
        exam.description ||
        "Examination integrity monitoring"
    );


    setText(
        "heroDifficulty",
        exam.difficulty ||
        "—"
    );


    setText(
        "heroQuestions",
        exam.total_questions ??
        "—"
    );


    setText(
        "heroMarks",
        exam.total_marks ??
        "—"
    );


    setText(
        "heroDuration",
        exam.duration
            ? `${exam.duration} min`
            : "—"
    );

}


// ==========================================================
// LOAD ANALYTICS
// ==========================================================

async function loadAnalytics(
    examId
) {

    try {

        const response =
            await fetch(
                `/api/integrity/overview?exam_id=${encodeURIComponent(examId)}`,
                {
                    cache: "no-store"
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Analytics unavailable"
            );

        }


        console.log(
            "Analytics:",
            data
        );


        renderAnalytics(
            data
        );


    } catch(error) {

        console.error(
            "Analytics error:",
            error
        );

    }

}


// ==========================================================
// RENDER ANALYTICS
// ==========================================================

function renderAnalytics(data) {

    const summary =
        data.summary || {};


    // ======================================================
    // KPI CARDS
    // ======================================================

    setText(
        "totalCandidates",
        summary.candidates ?? 0
    );


    setText(
        "averageScore",
        summary.average_score ?? 0
    );


    setText(
        "highRisk",
        summary.high_risk ?? 0
    );


    setText(
        "totalViolations",
        summary.violations ?? 0
    );


    setText(
        "totalEvidence",
        summary.evidence ?? 0
    );


    // ======================================================
    // BEHAVIOURAL EVENTS
    // ======================================================

    renderEventStatistics(data);


    // ======================================================
    // RISK
    // ======================================================

    renderRisk(
        data.risk_distribution || {}
    );


    // ======================================================
    // SCORE DISTRIBUTION
    // ======================================================

    renderScoreDistribution(
        data.score_distribution || []
    );


    // ======================================================
    // CANDIDATES
    // ======================================================

    candidates =
        data.candidates || [];


    renderCandidates(
        candidates
    );


    // ======================================================
    // AI
    // ======================================================

    renderAIInsight(
        data
    );

}
// ==========================================================
// EVENT STATISTICS
// ==========================================================

// ==========================================================
// BEHAVIOURAL EVENT STATISTICS
// ==========================================================

function renderEventStatistics(data) {

    console.log(
        "Integrity Analytics API:",
        data
    );

const events =
    data.events ||
    data.breakdown ||
    {};


    // ======================================================
    // READ COUNTS FROM BACKEND
    // ======================================================

    const tabSwitches =
        Number(
            events.tab_switches
        ) || 0;


    const focusLoss =
        Number(
            events.focus_loss
        ) || 0;


    const faceAbsence =
        Number(
            events.face_absence
        ) || 0;


    const fullscreenExit =
        Number(
            events.fullscreen_exit
        ) || 0;


    const copyPaste =
        Number(
            events.copy_paste
        ) || 0;


    const screenshots =
        Number(
            events.screenshots
        ) || 0;


    const rightClick =
        Number(
            events.right_click
        ) || 0;


    const identityMismatch =
        Number(
            events.identity_mismatch
        ) || 0;


    const multipleFaces =
        Number(
            events.multiple_faces
        ) || 0;


    const otherViolations =
        Number(
            events.other
        ) || 0;


    // ======================================================
    // DISPLAY
    // ======================================================

    setText(
        "tabSwitches",
        tabSwitches
    );


    setText(
        "focusLoss",
        focusLoss
    );


    setText(
        "faceAbsence",
        faceAbsence
    );


    setText(
        "fullscreenExit",
        fullscreenExit
    );


    setText(
        "copyPaste",
        copyPaste
    );


    setText(
        "screenshots",
        screenshots
    );


    setText(
        "rightClick",
        rightClick
    );


    setText(
        "identityMismatch",
        identityMismatch
    );


    setText(
        "multipleFaces",
        multipleFaces
    );


    setText(
        "otherViolations",
        otherViolations
    );


    // ======================================================
    // TOTAL
    // ======================================================

    const calculatedTotal =
        tabSwitches +
        focusLoss +
        faceAbsence +
        fullscreenExit +
        copyPaste +
        screenshots +
        rightClick +
        identityMismatch +
        multipleFaces +
        otherViolations;


    const total =
        Number(
            data.total_violations
        ) || calculatedTotal;


    setText(
        "eventTotal",
        total
    );


    // ======================================================
    // DEBUG
    // ======================================================

    console.table({

        "Tab Switches":
            tabSwitches,

        "Focus Loss":
            focusLoss,

        "Face Absence":
            faceAbsence,

        "Fullscreen Exit":
            fullscreenExit,

        "Copy / Paste":
            copyPaste,

        "Screenshots":
            screenshots,

        "Right Click":
            rightClick,

        "Identity Mismatch":
            identityMismatch,

        "Multiple Faces":
            multipleFaces,

        "Other Violations":
            otherViolations,

        "TOTAL":
            total

    });

}


// ==========================================================
// RISK
// ==========================================================

function renderRisk(
    risk
) {

    const low =
        risk.low ??
        risk.Low ??
        0;

    const medium =
        risk.medium ??
        risk.Medium ??
        0;

    const high =
        risk.high ??
        risk.High ??
        0;


    setText(
        "lowRisk",
        low
    );


    setText(
        "mediumRisk",
        medium
    );


    setText(
        "highRiskPercent",
        high
    );


    setText(
        "riskTotal",
        low + medium + high
    );

}


// ==========================================================
// SCORE DISTRIBUTION
// ==========================================================

function renderScoreDistribution(
    distribution
) {

    const chart =
        document.getElementById(
            "scoreChart"
        );


    chart.innerHTML = "";


    let values = [];


    if (Array.isArray(distribution)) {

        values = distribution;

    } else {

        values =
            Object.values(
                distribution
            );

    }


    if (!values.length) {

        chart.innerHTML = `
            <div style="
                color:#8d9aab;
                margin:auto;
            ">
                No score distribution available
            </div>
        `;

        return;
    }


    const max =
        Math.max(
            ...values.map(
                value =>
                    Number(value) || 0
            ),
            1
        );


    values
        .slice(0, 12)
        .forEach(
            (value, index) => {

                const bar =
                    document.createElement(
                        "div"
                    );


                bar.className =
                    "score-bar";


                const height =
                    Math.max(
                        8,
                        (
                            Number(value) /
                            max
                        ) * 180
                    );


                bar.style.height =
                    `${height}px`;


                bar.innerHTML = `
                    <span>
                        ${value}
                    </span>
                `;


                chart.appendChild(
                    bar
                );

            }
        );

}


// ==========================================================
// CANDIDATES
// ==========================================================

function renderCandidates(
    list
) {

    const tbody =
        document.getElementById(
            "candidateTable"
        );


    tbody.innerHTML = "";


    if (!list.length) {

        tbody.innerHTML = `
            <tr>
                <td colspan="7"
                    style="
                        text-align:center;
                        color:#8d9aab;
                        padding:40px;
                    ">
                    No candidate analytics available
                </td>
            </tr>
        `;

        return;
    }


    list.forEach(
        candidate => {

            const row =
                document.createElement(
                    "tr"
                );


            const risk =
                normalizeRisk(
                    candidate.risk_label ||
                    candidate.risk
                );


            row.innerHTML = `

                <td>

                    <div class="candidate-name">
                        ${escapeHtml(
                            candidate.name ||
                            "Unknown Candidate"
                        )}
                    </div>

                    <div class="candidate-email">
                        ${escapeHtml(
                            candidate.email ||
                            ""
                        )}
                    </div>

                </td>


                <td>
                    <strong>
                        ${candidate.exam_score ?? "—"}
                    </strong>
                </td>


                <td>
                    ${candidate.integrity_score ??
                      candidate.integrity ??
                      "—"}
                </td>


                <td>

                    <span class="
                        risk-pill ${risk}
                    ">
                        ${risk.toUpperCase()}
                    </span>

                </td>


                <td>
                    ${candidate.violations ?? 0}
                </td>


                <td>
                    ${candidate.face_presence_ratio != null
                        ? `${(
                            Number(
                                candidate.face_presence_ratio
                            ) * 100
                        ).toFixed(1)}%`
                        : "—"}
                </td>


                <td>

                    <button
                        class="view-btn"
                        onclick="openCandidate(
                            ${candidate.candidate_id ??
                              candidate.id}
                        )"
                    >
                        View Intelligence
                    </button>

                </td>

            `;


            tbody.appendChild(
                row
            );

        }
    );

}


// ==========================================================
// OPEN CANDIDATE
// ==========================================================

function openCandidate(
    candidateId
) {

    if (!selectedExam) {

        return;

    }


    window.location.href =
        `/candidate-integrity?candidate_id=${encodeURIComponent(candidateId)}&exam_id=${encodeURIComponent(selectedExam.id)}`;

}


// ==========================================================
// SEARCH
// ==========================================================

function filterCandidates(
    event
) {

    const term =
        event.target.value
            .toLowerCase()
            .trim();


    const filtered =
        candidates.filter(
            candidate => {

                const name =
                    (
                        candidate.name ||
                        ""
                    ).toLowerCase();


                const email =
                    (
                        candidate.email ||
                        ""
                    ).toLowerCase();


                return (
                    name.includes(term) ||
                    email.includes(term)
                );

            }
        );


    renderCandidates(
        filtered
    );

}


// ==========================================================
// AI INSIGHT
// ==========================================================

function renderAIInsight(
    data
) {

    const insight =
        data.ai_summary ||
        data.ai_report ||
        data.summary_text;


    if (insight) {

        setText(
            "aiInsight",
            insight
        );

    } else {

        setText(
            "aiInsight",
            "AI integrity summary will appear here after the selected examination has been analysed."
        );

    }

}


// ==========================================================
// HELPERS
// ==========================================================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (element) {

        element.textContent =
            value ?? "—";

    }

}


function normalizeRisk(
    risk
) {

    const value =
        String(
            risk || "low"
        ).toLowerCase();


    if (
        value === "high"
    ) {

        return "high";

    }


    if (
        value === "medium" ||
        value === "med"
    ) {

        return "medium";

    }


    return "low";

}


function escapeHtml(
    value
) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}
function initializeExamAIReport() {

    const button =
        document.getElementById(
            "generateExamAIReport"
        );


    if (!button) {

        console.warn(
            "generateExamAIReport button not found"
        );

        return;

    }


    button.addEventListener(
        "click",
        generateExamAIReport
    );

}
async function generateExamAIReport() {

    const examSelect =
        document.getElementById(
            "examSelect"
        );


    const examId =
        examSelect?.value;


    const reportContainer =
        document.getElementById(
            "examAIReport"
        );


    const button =
        document.getElementById(
            "generateExamAIReport"
        );


    if (!examId) {

        alert(
            "Please select an examination first."
        );

        return;

    }


    button.disabled = true;

    button.textContent =
        "✦ Generating...";


    reportContainer.innerHTML = `

        <div class="ai-report-loading">

            ✦

            <span>
                Analysing the complete
                examination cohort...
            </span>

        </div>

    `;


    try {

        const response =
            await fetch(
                "/api/integrity/exam-ai-report",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({
                            exam_id:
                                Number(examId)
                        })

                }
            );


        const contentType =
            response.headers.get(
                "content-type"
            ) || "";


        if (
            !contentType.includes(
                "application/json"
            )
        ) {

            throw new Error(
                `Server returned non-JSON response (${response.status})`
            );

        }


        const data =
            await response.json();


        console.log(
            "Examination AI response:",
            data
        );


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Unable to generate examination report."
            );

        }


        renderExamAIReport(
            data.report
        );


    }

    catch (error) {

        console.error(
            "Examination AI error:",
            error
        );


        reportContainer.innerHTML = `

            <div class="ai-report-error">

                <strong>
                    Examination AI report unavailable
                </strong>

                <p>
                    ${escapeHtml(
                        error.message
                    )}
                </p>

            </div>

        `;

    }

    finally {

        button.disabled = false;

        button.textContent =
            "✦ Generate Examination Report";

    }

}
function renderExamAIReport(
    report
) {

    const container =
        document.getElementById(
            "examAIReport"
        );


    if (!container) {
        return;
    }


    container.innerHTML = `

        <div class="exam-ai-result">

            <div class="exam-ai-label">
                ✦ LANGCHAIN EXAMINATION ANALYSIS
            </div>

            <div class="exam-ai-text">

                ${formatExamAIReport(
                    report
                )}

            </div>

        </div>

    `;

}
function formatExamAIReport(text) {

    if (!text) {
        return `
            <p class="ai-empty">
                No examination assessment was generated.
            </p>
        `;
    }


    /*
    --------------------------------------------------------
    CLEAN MARKDOWN
    --------------------------------------------------------
    */

    let cleaned = String(text)

        // Remove bold markdown
        .replace(/\*\*/g, "")

        // Remove heading markdown
        .replace(/^#{1,6}\s*/gm, "")

        // Remove code fences
        .replace(/```/g, "")

        // Normalize Windows line endings
        .replace(/\r\n/g, "\n")

        .trim();


    /*
    --------------------------------------------------------
    SECTION NAMES
    --------------------------------------------------------
    */

    const sections = [

        "EXAMINATION SUMMARY",

        "COHORT PERFORMANCE",

        "BEHAVIOURAL OBSERVATIONS",

        "RISK PROFILE",

        "INTEGRITY CONCLUSION",

        "RECOMMENDED REVIEW"

    ];


    /*
    --------------------------------------------------------
    CREATE SECTION OBJECTS
    --------------------------------------------------------
    */

    const sectionData = {};


    sections.forEach(
        (section, index) => {

            const start =
                cleaned.indexOf(section);


            if (start === -1) {
                return;
            }


            const nextSection =
                sections
                    .slice(index + 1)
                    .map(
                        name =>
                            cleaned.indexOf(
                                name,
                                start + section.length
                            )
                    )
                    .filter(
                        position =>
                            position !== -1
                    )
                    .sort(
                        (a, b) =>
                            a - b
                    )[0];


            const end =
                nextSection !== undefined
                    ? nextSection
                    : cleaned.length;


            sectionData[section] =
                cleaned
                    .substring(
                        start + section.length,
                        end
                    )
                    .trim();

        }
    );


    /*
    --------------------------------------------------------
    BUILD HTML
    --------------------------------------------------------
    */

    let html = "";


    if (
        sectionData[
            "EXAMINATION SUMMARY"
        ]
    ) {

        html += createAISection(
            "EXAMINATION SUMMARY",
            "◎",
            sectionData[
                "EXAMINATION SUMMARY"
            ]
        );

    }


    if (
        sectionData[
            "COHORT PERFORMANCE"
        ]
    ) {

        html += createAISection(
            "COHORT PERFORMANCE",
            "◈",
            sectionData[
                "COHORT PERFORMANCE"
            ]
        );

    }


    if (
        sectionData[
            "BEHAVIOURAL OBSERVATIONS"
        ]
    ) {

        html += createAISection(
            "BEHAVIOURAL OBSERVATIONS",
            "◌",
            sectionData[
                "BEHAVIOURAL OBSERVATIONS"
            ]
        );

    }


    if (
        sectionData[
            "RISK PROFILE"
        ]
    ) {

        html += createAISection(
            "RISK PROFILE",
            "⚠",
            sectionData[
                "RISK PROFILE"
            ]
        );

    }


    if (
        sectionData[
            "INTEGRITY CONCLUSION"
        ]
    ) {

        html += createAISection(
            "INTEGRITY CONCLUSION",
            "✓",
            sectionData[
                "INTEGRITY CONCLUSION"
            ]
        );

    }


    if (
        sectionData[
            "RECOMMENDED REVIEW"
        ]
    ) {

        html += createAISection(
            "RECOMMENDED REVIEW",
            "→",
            sectionData[
                "RECOMMENDED REVIEW"
            ]
        );

    }


    /*
    --------------------------------------------------------
    FALLBACK
    --------------------------------------------------------
    */

    if (!html) {

        html = `
            <div class="ai-section-card">
                <div class="ai-section-content">
                    ${formatPlainAIText(cleaned)}
                </div>
            </div>
        `;

    }


    return html;
}
function createAISection(
    title,
    icon,
    content
) {

    const isList =
        content.includes("- ");


    let formattedContent;


    if (isList) {

        const items =
            content
                .split("\n")
                .map(
                    line =>
                        line
                            .trim()
                )
                .filter(
                    line =>
                        line.startsWith("- ")
                )
                .map(
                    line => `
                        <li>
                            ${escapeHtml(
                                line.substring(2)
                            )}
                        </li>
                    `
                )
                .join("");


        formattedContent = `
            <ul class="ai-report-list">
                ${items}
            </ul>
        `;

    }

    else {

        formattedContent = `
            <p>
                ${escapeHtml(
                    content
                )}
            </p>
        `;

    }


    return `

        <article class="ai-section-card">

            <div class="ai-section-icon">
                ${icon}
            </div>

            <div class="ai-section-content">

                <div class="ai-section-title">
                    ${title}
                </div>

                ${formattedContent}

            </div>

        </article>

    `;

}
function formatPlainAIText(
    text
) {

    return escapeHtml(
        text
    )
        .replace(
            /\n/g,
            "<br>"
        );

}
function escapeHtml(value) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        String(
            value ?? ""
        );

    return div.innerHTML;

}
// ==========================================================
// DATA SCIENCE ANALYTICS
// ==========================================================

async function loadDataScienceAnalytics(
    examId
) {

    try {

        const response =
            await fetch(
                `/api/integrity/data-science?exam_id=${encodeURIComponent(examId)}`,
                {
                    cache: "no-store"
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Data Science analytics unavailable"
            );

        }


        renderDSScoreDistribution(
            data.score_distribution
        );


        renderDSEventFrequency(
            data.event_frequency
        );


        renderDSHeatmap(
            data.event_heatmap
        );


        renderDSClusters(
            data.kmeans
        );


        renderDSRiskProfile(
            data.risk_profile
        );


    }
    catch (error) {

        console.error(
            "Data Science analytics:",
            error
        );

    }

}
function renderDSScoreDistribution(
    distribution
) {

    const container =
        document.getElementById(
            "dsScoreChart"
        );


    if (!container) return;


    container.innerHTML = "";


    const labels =
        distribution?.labels || [];


    const values =
        distribution?.values || [];


    if (!values.length) {

        container.innerHTML =
            `<span class="ds-empty">
                No score data available
            </span>`;

        return;

    }


    const max =
        Math.max(
            ...values,
            1
        );


    values.forEach(
        (value, index) => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "ds-score-item";


            const height =
                Math.max(
                    10,
                    (
                        value /
                        max
                    ) * 150
                );


            item.innerHTML = `

                <div
                    class="ds-score-value"
                    style="height:${height}px"
                >
                    ${value}
                </div>

                <span>
                    ${labels[index]}
                </span>

            `;


            container.appendChild(
                item
            );

        }
    );

}
function renderDSEventFrequency(
    frequency
) {

    const container =
        document.getElementById(
            "dsEventFrequency"
        );


    if (!container) return;


    container.innerHTML = "";


    const entries =
        Object.entries(
            frequency || {}
        );


    if (!entries.length) {

        container.innerHTML =
            `<span class="ds-empty">
                No events recorded
            </span>`;

        return;

    }


    entries.sort(
        (a, b) =>
            b[1] - a[1]
    );


    entries.forEach(
        ([name, count]) => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "ds-event-row";


            row.innerHTML = `

                <span>
                    ${name}
                </span>

                <strong>
                    ${count}
                </strong>

            `;


            container.appendChild(
                row
            );

        }
    );

}
function renderDSHeatmap(
    path
) {

    const image =
        document.getElementById(
            "dsHeatmap"
        );


    if (!image) return;


    if (!path) {

        image.style.display =
            "none";

        return;

    }


    image.src =
        `${path}?t=${Date.now()}`;

    image.style.display =
        "block";

}
function renderDSClusters(
    result
) {

    const container =
        document.getElementById(
            "dsClusters"
        );


    if (!container) return;


    container.innerHTML = "";


    if (
        !result ||
        !result.available
    ) {

        container.innerHTML = `
            <div class="ds-empty">
                ${
                    result?.message ||
                    "Clustering unavailable"
                }
            </div>
        `;

        return;

    }


    result.clusters.forEach(
        cluster => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "cluster-card";


            card.innerHTML = `

                <strong>
                    Cluster ${cluster.cluster + 1}
                </strong>

                <span>
                    ${cluster.candidates}
                    candidate(s)
                </span>

                <small>
                    Avg Integrity:
                    ${cluster.avg_integrity}
                </small>

                <small>
                    Avg Face Presence:
                    ${(
                        cluster.avg_face_presence *
                        100
                    ).toFixed(1)}%
                </small>

                <small>
                    Avg Warnings:
                    ${cluster.avg_warnings}
                </small>

            `;


            container.appendChild(
                card
            );

        }
    );

}
function renderDSRiskProfile(
    profile
) {

    const container =
        document.getElementById(
            "dsRiskProfile"
        );


    if (!container) return;


    container.innerHTML = "";


    const risks = [
        ["Low", "low"],
        ["Medium", "medium"],
        ["High", "high"]
    ];


    risks.forEach(
        ([label, css]) => {

            const count =
                Number(
                    profile?.[label] || 0
                );


            const item =
                document.createElement(
                    "div"
                );


            item.className =
                `ds-risk-item ${css}`;


            item.innerHTML = `

                <span>
                    ${label}
                </span>

                <strong>
                    ${count}
                </strong>

            `;


            container.appendChild(
                item
            );

        }
    );

}