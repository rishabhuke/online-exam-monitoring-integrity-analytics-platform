"use strict";

/*
============================================================
 CANDIDATE INTEGRITY INTELLIGENCE
============================================================

Expected URL:

/candidate-integrity?candidate_id=1&exam_id=27

Candidate API:

GET /api/integrity/candidate/1?exam_id=27

AI API:

POST /api/integrity/ai-report
============================================================
*/


/* =========================================================
   GLOBAL STATE
========================================================= */

const CandidateIntegrity = {

    candidateId: null,

    examId: null,

    data: null

};


/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializeCandidateIntegrity
);


async function initializeCandidateIntegrity() {

    console.log(
        "Candidate Integrity initialized"
    );


    /*
    ---------------------------------------------------------
    Read URL parameters
    ---------------------------------------------------------
    */

    const params =
        new URLSearchParams(
            window.location.search
        );


    CandidateIntegrity.candidateId =
        params.get("candidate_id");


    CandidateIntegrity.examId =
        params.get("exam_id");


    console.log(
        "Candidate ID:",
        CandidateIntegrity.candidateId
    );


    console.log(
        "Exam ID:",
        CandidateIntegrity.examId
    );


    /*
    ---------------------------------------------------------
    Validate parameters
    ---------------------------------------------------------
    */

    if (
        !CandidateIntegrity.candidateId ||
        !CandidateIntegrity.examId
    ) {

        showPageError(
            "Candidate ID or Exam ID is missing."
        );

        return;

    }


    /*
    ---------------------------------------------------------
    Load candidate data
    ---------------------------------------------------------
    */

    await loadCandidateIntegrity();


    /*
    ---------------------------------------------------------
    Initialize AI button
    ---------------------------------------------------------
    */

    initializeAIReportButton();

}


/* =========================================================
   LOAD CANDIDATE INTEGRITY
========================================================= */

async function loadCandidateIntegrity() {

    const candidateId =
        CandidateIntegrity.candidateId;


    const examId =
        CandidateIntegrity.examId;


    const apiUrl =
        `/api/integrity/candidate/${encodeURIComponent(candidateId)}` +
        `?exam_id=${encodeURIComponent(examId)}`;


    console.log(
        "Loading candidate intelligence:",
        apiUrl
    );


    setLoadingState(true);


    try {

        const response =
            await fetch(
                apiUrl,
                {
                    method: "GET",

                    headers: {
                        "Accept":
                            "application/json"
                    },

                    credentials:
                        "same-origin"
                }
            );


        const contentType =
            response.headers.get(
                "content-type"
            ) || "";


        let data;


        if (
            contentType.includes(
                "application/json"
            )
        ) {

            data =
                await response.json();

        } else {

            throw new Error(
                `Server returned non-JSON response (${response.status}).`
            );

        }


        console.log(
            "Candidate integrity response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.message ||
                data.error ||
                `Request failed with status ${response.status}`
            );

        }


        if (
            data.success === false
        ) {

            throw new Error(
                data.message ||
                data.error ||
                "Candidate integrity data unavailable."
            );

        }


        CandidateIntegrity.data =
            data;


        /*
        -----------------------------------------------------
        Render page
        -----------------------------------------------------
        */

        renderCandidateHeader(data);

        renderExamInformation(data);

        renderIntegritySummary(data);

        renderBehaviouralSignals(data);

        renderViolationBreakdown(data);

        renderViolationTimeline(data);

        renderEvidence(data);

        renderAIContext(data);


        setLoadingState(false);


        console.log(
            "Candidate intelligence rendered successfully."
        );

    }

    catch (error) {

        console.error(
            "Candidate integrity error:",
            error
        );


        setLoadingState(false);


        showPageError(
            error.message ||
            "Unable to load candidate integrity data."
        );

    }

}


/* =========================================================
   CANDIDATE HEADER
========================================================= */

function renderCandidateHeader(data) {

    const candidate =
        data.candidate || {};


    setText(
        "candidateName",
        candidate.name ||
        "Unknown Candidate"
    );


    setText(
        "candidateEmail",
        candidate.email ||
        "Email unavailable"
    );


    const avatar =
        document.getElementById(
            "candidateAvatar"
        );


    if (avatar) {

        const name =
            candidate.name ||
            "C";


        avatar.textContent =
            name
                .trim()
                .charAt(0)
                .toUpperCase();

    }

}


/* =========================================================
   EXAM INFORMATION
========================================================= */

function renderExamInformation(data) {

    const exam =
        data.exam || {};


    setText(
        "examTitle",
        exam.title ||
        "Unknown Examination"
    );


    const difficulty =
        exam.difficulty ||
        "Unknown";


    const questions =
        exam.total_questions ??
        0;


    const marks =
        exam.total_marks ??
        0;


    const duration =
        exam.duration ??
        0;


    setText(
        "examMeta",
        `${difficulty} • ${questions} Questions • ${marks} Marks`
    );


    setText(
        "examDifficulty",
        difficulty
    );


    setText(
        "examQuestions",
        questions
    );


    setText(
        "examMarks",
        marks
    );


    setText(
        "examDuration",
        `${duration} min`
    );

}


/* =========================================================
   INTEGRITY SUMMARY
========================================================= */

function renderIntegritySummary(data) {

    const integrity =
        data.integrity || {};


    const attempt =
        data.attempt || null;


    /*
    ---------------------------------------------------------
    Integrity score
    ---------------------------------------------------------
    */

    const score =
        toNumberOrNull(
            integrity.score
        );


    setText(
        "integrityScore",
        score === null
            ? "—"
            : formatNumber(score, 0)
    );


    updateScoreCircle(score);


    /*
    ---------------------------------------------------------
    Risk
    ---------------------------------------------------------
    */

    const risk =
        integrity.risk_label ||
        "Unknown";


    setText(
        "riskLabel",
        risk.toUpperCase()
    );


    updateRiskClass(risk);


    /*
    ---------------------------------------------------------
    Face presence
    ---------------------------------------------------------
    */

    const faceRatio =
        toNumberOrNull(
            integrity.face_presence_ratio
        );


    let facePercentage = null;


    if (faceRatio !== null) {

        facePercentage =
            faceRatio <= 1
                ? faceRatio * 100
                : faceRatio;

    }


    setText(
        "facePresence",
        facePercentage === null
            ? "—"
            : `${facePercentage.toFixed(1)}%`
    );


    /*
    ---------------------------------------------------------
    Warnings
    ---------------------------------------------------------
    */

    const totalWarnings =
        data.total_warnings ??
        integrity.warning_count ??
        0;


    setText(
        "warningCount",
        totalWarnings
    );


    setText(
        "summaryWarningCount",
        totalWarnings
    );


    setText(
        "aiWarningCount",
        totalWarnings
    );


    setText(
        "resultEvidenceCount",
        data.evidence_count ?? 0
    );


    /*
    ---------------------------------------------------------
    Exam result
    ---------------------------------------------------------
    */

    if (attempt) {

        const percentage =
            toNumberOrNull(
                attempt.percentage
            );


        setText(
            "examScore",
            percentage === null
                ? "—"
                : `${percentage}%`
        );


        setText(
            "examRawScore",
            `${attempt.score ?? 0}/${attempt.total_questions ?? 0}`
        );


        setText(
            "examResult",
            attempt.result ||
            "—"
        );

    }

    else {

        setText(
            "examScore",
            "—"
        );


        setText(
            "examRawScore",
            "—"
        );


        setText(
            "examResult",
            "—"
        );

    }

}


/* =========================================================
   SCORE CIRCLE
========================================================= */

function updateScoreCircle(score) {

    const progress =
        document.getElementById(
            "integrityProgress"
        );


    if (
        progress &&
        score !== null
    ) {

        const safeScore =
            Math.max(
                0,
                Math.min(
                    100,
                    Number(score)
                )
            );


        const radius =
            Number(
                progress.getAttribute("r")
            );


        if (
            Number.isFinite(radius)
        ) {

            const circumference =
                2 *
                Math.PI *
                radius;


            progress.style.strokeDasharray =
                circumference;


            progress.style.strokeDashoffset =
                circumference -
                (
                    safeScore / 100
                ) *
                circumference;

        }

    }


    const scoreCircle =
        document.getElementById(
            "scoreCircle"
        );


    if (
        scoreCircle &&
        score !== null
    ) {

        scoreCircle.style.setProperty(
            "--score",
            `${score}%`
        );

    }

}


/* =========================================================
   RISK CLASS
========================================================= */

function updateRiskClass(risk) {

    const element =
        document.getElementById(
            "riskLabel"
        );


    if (!element) {
        return;
    }


    element.classList.remove(
        "low",
        "medium",
        "high",
        "unknown"
    );


    const normalized =
        String(
            risk || "unknown"
        )
            .trim()
            .toLowerCase();


    if (
        normalized === "low"
    ) {

        element.classList.add(
            "low"
        );

    }

    else if (
        normalized === "medium"
    ) {

        element.classList.add(
            "medium"
        );

    }

    else if (
        normalized === "high"
    ) {

        element.classList.add(
            "high"
        );

    }

    else {

        element.classList.add(
            "unknown"
        );

    }

}


/* =========================================================
   BEHAVIOURAL SIGNALS
========================================================= */

function renderBehaviouralSignals(data) {

    const breakdown =
        data.breakdown || {};


    setText(
        "tabSwitchCount",
        breakdown.tab_switches ?? 0
    );


    setText(
        "focusLossCount",
        breakdown.focus_loss ?? 0
    );


    setText(
        "faceAbsenceCount",
        breakdown.face_absence ?? 0
    );


    setText(
        "fullscreenExitCount",
        breakdown.fullscreen_exit ?? 0
    );


    setText(
        "copyPasteCount",
        breakdown.copy_paste ?? 0
    );


    setText(
        "screenshotCount",
        breakdown.screenshots ?? 0
    );


    setText(
        "rightClickCount",
        breakdown.right_click ?? 0
    );


    setText(
        "identityMismatchCount",
        breakdown.identity_mismatch ?? 0
    );


    setText(
        "multipleFacesCount",
        breakdown.multiple_faces ?? 0
    );


    setText(
        "otherViolationCount",
        breakdown.other ?? 0
    );

}


/* =========================================================
   VIOLATION BREAKDOWN
========================================================= */

function renderViolationBreakdown(data) {

    const breakdown =
        data.breakdown || {};


    const definitions = [

        {
            key: "tab_switches",
            id: "tabSwitchCount"
        },

        {
            key: "focus_loss",
            id: "focusLossCount"
        },

        {
            key: "face_absence",
            id: "faceAbsenceCount"
        },

        {
            key: "fullscreen_exit",
            id: "fullscreenExitCount"
        },

        {
            key: "copy_paste",
            id: "copyPasteCount"
        },

        {
            key: "screenshots",
            id: "screenshotCount"
        },

        {
            key: "right_click",
            id: "rightClickCount"
        },

        {
            key: "identity_mismatch",
            id: "identityMismatchCount"
        },

        {
            key: "multiple_faces",
            id: "multipleFacesCount"
        },

        {
            key: "other",
            id: "otherViolationCount"
        }

    ];


    definitions.forEach(
        item => {

            setText(
                item.id,
                breakdown[item.key] ?? 0
            );

        }
    );


    const total =
        Object.values(
            breakdown
        )
        .reduce(
            (
                sum,
                value
            ) =>
                sum +
                Number(value || 0),
            0
        );


    const apiTotal =
        data.total_warnings;


    setText(
        "warningCount",
        apiTotal !== undefined
            ? apiTotal
            : total
    );

}


/* =========================================================
   VIOLATION TIMELINE
========================================================= */

function renderViolationTimeline(data) {

    const container =
        document.getElementById(
            "violationTimeline"
        );


    if (!container) {

        console.warn(
            "#violationTimeline not found"
        );

        return;

    }


    const violations =
        Array.isArray(
            data.violations
        )
            ? data.violations
            : [];


    container.replaceChildren();


    if (
        violations.length === 0
    ) {

        const empty =
            createElement(
                "div",
                "empty-state"
            );


        empty.textContent =
            "No integrity violations recorded for this examination.";


        container.appendChild(
            empty
        );


        return;

    }


    violations.forEach(
        violation => {

            const item =
                createElement(
                    "article",
                    "violation-item"
                );


            const icon =
                createElement(
                    "div",
                    "violation-icon"
                );


            icon.textContent =
                getViolationIcon(
                    violation.category ||
                    violation.type
                );


            const content =
                createElement(
                    "div",
                    "violation-content"
                );


            const title =
                createElement(
                    "div",
                    "violation-title"
                );


            title.textContent =
                formatViolationCategory(
                    violation.category ||
                    violation.type
                );


            if (
                violation.has_evidence ||
                violation.evidence_image
            ) {

                const badge =
                    createElement(
                        "span",
                        "evidence-tag"
                    );


                badge.textContent =
                    "Evidence";


                title.appendChild(
                    document.createTextNode(" ")
                );


                title.appendChild(
                    badge
                );

            }


            const description =
                createElement(
                    "div",
                    "violation-description"
                );


            description.textContent =
                violation.type ||
                "Integrity event";


            const time =
                createElement(
                    "div",
                    "violation-time"
                );


            time.textContent =
                formatDate(
                    violation.time ||
                    violation.violation_time
                );


            content.appendChild(
                title
            );


            content.appendChild(
                description
            );


            content.appendChild(
                time
            );


            item.appendChild(
                icon
            );


            item.appendChild(
                content
            );


            if (
                violation.evidence_image
            ) {

                const viewButton =
                    createElement(
                        "button",
                        "view-evidence-btn"
                    );


                viewButton.type =
                    "button";


                viewButton.textContent =
                    "View Evidence";


                viewButton.addEventListener(
                    "click",
                    () => {

                        openEvidence(
                            violation
                        );

                    }
                );


                item.appendChild(
                    viewButton
                );

            }


            container.appendChild(
                item
            );

        }
    );

}


/* =========================================================
   EVIDENCE
========================================================= */

function renderEvidence(data) {

    const container =
        document.getElementById(
            "evidenceGrid"
        );


    if (!container) {

        console.warn(
            "#evidenceGrid not found"
        );

        return;

    }


    container.replaceChildren();


    const violations =
        Array.isArray(
            data.violations
        )
            ? data.violations
            : [];


    const evidence =
        violations.filter(
            violation =>
                Boolean(
                    violation.evidence_image
                )
        );


    setText(
        "evidenceCount",
        data.evidence_count ??
        evidence.length
    );


    if (
        evidence.length === 0
    ) {

        const empty =
            createElement(
                "div",
                "empty-state"
            );


        empty.textContent =
            "No evidence images recorded for this candidate.";


        container.appendChild(
            empty
        );


        return;

    }


    evidence.forEach(
        violation => {

            const card =
                createElement(
                    "article",
                    "evidence-card"
                );


            const imageWrapper =
                createElement(
                    "div",
                    "evidence-image-wrapper"
                );


            const image =
                document.createElement(
                    "img"
                );


            image.alt =
                `Evidence: ${formatViolationCategory(
                    violation.category ||
                    violation.type
                )}`;


            image.loading =
                "lazy";


            image.src =
                buildEvidenceUrl(
                    violation.evidence_image
                );


            image.addEventListener(
                "error",
                () => {

                    imageWrapper.classList.add(
                        "image-error"
                    );


                    image.alt =
                        "Evidence image unavailable";

                }
            );


            image.addEventListener(
                "click",
                () => {

                    openEvidence(
                        violation
                    );

                }
            );


            imageWrapper.appendChild(
                image
            );


            const info =
                createElement(
                    "div",
                    "evidence-info"
                );


            const title =
                createElement(
                    "strong"
                );


            title.textContent =
                formatViolationCategory(
                    violation.category ||
                    violation.type
                );


            const time =
                createElement(
                    "span"
                );


            time.textContent =
                formatDate(
                    violation.time ||
                    violation.violation_time
                );


            info.appendChild(
                title
            );


            info.appendChild(
                time
            );


            card.appendChild(
                imageWrapper
            );


            card.appendChild(
                info
            );


            container.appendChild(
                card
            );

        }
    );

}


/* =========================================================
   BUILD EVIDENCE URL
========================================================= */

function buildEvidenceUrl(
    evidencePath
) {

    if (!evidencePath) {
        return "";
    }


    /*
    ---------------------------------------------------------
    Backend already returned a URL
    ---------------------------------------------------------
    */

    if (
        evidencePath.startsWith("http://") ||
        evidencePath.startsWith("https://") ||
        evidencePath.startsWith("/")
    ) {

        return evidencePath;

    }


    /*
    ---------------------------------------------------------
    Normalize Windows path
    ---------------------------------------------------------
    */

    const normalized =
        String(
            evidencePath
        )
        .replace(
            /\\/g,
            "/"
        );


    /*
    ---------------------------------------------------------
    Evidence API
    ---------------------------------------------------------
    */

    return (
        "/api/integrity/evidence?path=" +
        encodeURIComponent(
            normalized
        )
    );

}


/* =========================================================
   OPEN EVIDENCE
========================================================= */

function openEvidence(
    violation
) {

    if (
        !violation ||
        !violation.evidence_image
    ) {

        return;

    }


    const url =
        buildEvidenceUrl(
            violation.evidence_image
        );


    if (!url) {
        return;
    }


    window.open(
        url,
        "_blank",
        "noopener,noreferrer"
    );

}


/* =========================================================
   AI REPORT BUTTON
========================================================= */

function initializeAIReportButton() {

    const button =
        document.getElementById(
            "generateAIReport"
        );


    if (!button) {

        console.warn(
            "#generateAIReport button not found"
        );

        return;

    }


    if (
        button.dataset.initialized ===
        "true"
    ) {

        return;

    }


    button.dataset.initialized =
        "true";


    button.addEventListener(
        "click",
        generateAIReport
    );

}


/* =========================================================
   GENERATE AI REPORT
========================================================= */

async function generateAIReport() {

    const button =
        document.getElementById(
            "generateAIReport"
        );


    /*
    ---------------------------------------------------------
    IMPORTANT:
    This ID should be the div in your HTML where the
    AI report must appear.
    ---------------------------------------------------------
    */

    const reportContainer =
        document.getElementById(
            "behaviouralAssessment"
        );


    /*
    ---------------------------------------------------------
    Fallback for older HTML
    ---------------------------------------------------------
    */

    const fallbackContainer =
        document.getElementById(
            "aiReport"
        );


    const container =
        reportContainer ||
        fallbackContainer;


    if (
        !CandidateIntegrity.candidateId ||
        !CandidateIntegrity.examId
    ) {

        showPageError(
            "Candidate ID or Exam ID is missing."
        );

        return;

    }


    /*
    ---------------------------------------------------------
    Button loading state
    ---------------------------------------------------------
    */

    if (button) {

        button.disabled =
            true;

        button.textContent =
            "Generating AI Report...";

    }


    if (container) {

        container.style.display =
            "block";

        container.innerHTML = `

            <div class="ai-report-loading">

                <div class="ai-loading-icon">
                    ✦
                </div>

                <div>
                    Generating behavioural
                    assessment...
                </div>

            </div>

        `;

    }


    try {

        console.log(
            "Generating AI report for:",
            {
                candidate_id:
                    CandidateIntegrity.candidateId,

                exam_id:
                    CandidateIntegrity.examId
            }
        );


        /*
        -----------------------------------------------------
        POST AI REPORT
        -----------------------------------------------------
        */

        const response =
            await fetch(
                "/api/integrity/ai-report",
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

                            candidate_id:
                                Number(
                                    CandidateIntegrity.candidateId
                                ),

                            exam_id:
                                Number(
                                    CandidateIntegrity.examId
                                )

                        })

                }
            );


        /*
        -----------------------------------------------------
        Parse JSON safely
        -----------------------------------------------------
        */

        const contentType =
            response.headers.get(
                "content-type"
            ) || "";


        let data;


        if (
            contentType.includes(
                "application/json"
            )
        ) {

            data =
                await response.json();

        }

        else {

            const text =
                await response.text();


            throw new Error(
                `AI report endpoint returned non-JSON response (${response.status}).`
            );

        }


        console.log(
            "AI report response:",
            data
        );


        /*
        -----------------------------------------------------
        HTTP ERROR
        -----------------------------------------------------
        */

        if (!response.ok) {

            throw new Error(
                data.error ||
                data.message ||
                `AI report failed (${response.status}).`
            );

        }


        /*
        -----------------------------------------------------
        API ERROR
        -----------------------------------------------------
        */

        if (
            data.success === false
        ) {

            throw new Error(
                data.error ||
                data.message ||
                "AI report could not be generated."
            );

        }


        /*
        -----------------------------------------------------
        IMPORTANT:
        Your Flask backend returns:

        {
            success: true,
            assessment: "...",
            risk: "...",
            integrity_score: ...,
            face_presence_ratio: ...,
            warning_count: ...,
            violations: {...}
        }

        Therefore we MUST use:

        data.assessment

        -----------------------------------------------------
        */

        renderAIReport(data);


        console.log(
            "AI report generated successfully."
        );

    }

    catch (error) {

        console.error(
            "AI report error:",
            error
        );


        if (container) {

            container.innerHTML = `

                <div class="ai-report-error">

                    <strong>
                        AI report unavailable
                    </strong>

                    <p>
                        ${escapeHtml(
                            error.message ||
                            "Unable to generate AI report."
                        )}
                    </p>

                </div>

            `;

        }

    }

    finally {

        if (button) {

            button.disabled =
                false;

            button.textContent =
                "Generate AI Report";

        }

    }

}


/* =========================================================
   RENDER AI REPORT
========================================================= */

function renderAIReport(data) {

    const reportContainer =
        document.getElementById(
            "behaviouralAssessment"
        );


    const fallbackContainer =
        document.getElementById(
            "aiReport"
        );


    const container =
        reportContainer ||
        fallbackContainer;


    if (!container) {

        console.error(
            "Neither #behaviouralAssessment nor #aiReport exists."
        );

        return;

    }


    /*
    ---------------------------------------------------------
    Get assessment returned by LangChain
    ---------------------------------------------------------
    */

    const report =
        data.assessment ||
        data.report ||
        data.ai_report ||
        data.content ||
        "No AI assessment was returned.";


    /*
    ---------------------------------------------------------
    Render actual AI report
    ---------------------------------------------------------
    */

    container.innerHTML = `

        <div class="ai-report-result">

            <div class="ai-report-label">
                ✦ LANGCHAIN GENERATED ASSESSMENT
            </div>

            <div class="ai-report-text">
                ${formatAIReport(report)}
            </div>

        </div>

    `;


    /*
    ---------------------------------------------------------
    Update AI metrics
    ---------------------------------------------------------
    */

    setText(
        "assessmentScore",
        data.integrity_score ??
        data.integrity?.integrity_score ??
        0
    );


    setText(
        "assessmentFace",
        formatPercentage(
            data.face_presence_ratio ??
            data.integrity?.face_presence_ratio
        )
    );


    setText(
        "assessmentEvents",
        data.warning_count ??
        data.integrity?.warning_count ??
        0
    );


    const risk =
        data.risk ||
        data.risk_label ||
        data.integrity?.risk_label ||
        "Unknown";


    setText(
        "assessmentRisk",
        risk
    );


    /*
    ---------------------------------------------------------
    Risk badge
    ---------------------------------------------------------
    */

    const riskBadge =
        document.getElementById(
            "assessmentRiskBadge"
        );


    if (riskBadge) {

        riskBadge.textContent =
            String(risk).toUpperCase();


        riskBadge.className =
            "assessment-risk-badge " +
            String(risk)
                .toLowerCase();

    }

}


/* =========================================================
   FORMAT AI REPORT
========================================================= */

function formatAIReport(text) {

    const escaped =
        escapeHtml(
            text
        );


    return escaped

        .replace(
            /BEHAVIOURAL SUMMARY/gi,
            '<h3>Behavioural Summary</h3>'
        )

        .replace(
            /KEY OBSERVATIONS/gi,
            '<h3>Key Observations</h3>'
        )

        .replace(
            /RISK INTERPRETATION/gi,
            '<h3>Risk Interpretation</h3>'
        )

        .replace(
            /RECOMMENDED REVIEW/gi,
            '<h3>Recommended Review</h3>'
        )

        .replace(
            /\r?\n/g,
            '<br>'
        );

}


/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHtml(
    value
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(
            value ??
            ""
        );


    return div.innerHTML;

}


/* =========================================================
   FORMAT PERCENTAGE
========================================================= */

function formatPercentage(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "0%";

    }


    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {

        return "0%";

    }


    if (
        number <= 1
    ) {

        return (
            number * 100
        ).toFixed(0) + "%";

    }


    return (
        number
    ).toFixed(0) + "%";

}


/* =========================================================
   AI CONTEXT
========================================================= */

function renderAIContext(
    data
) {

    const integrity =
        data.integrity || {};


    setText(
        "aiRiskLabel",
        integrity.risk_label ||
        "Unknown"
    );


    setText(
        "aiWarningCount",
        data.total_warnings ??
        integrity.warning_count ??
        0
    );


    setText(
        "aiEvidenceCount",
        data.evidence_count ??
        0
    );

}


/* =========================================================
   LOADING STATE
========================================================= */

function setLoadingState(
    loading
) {

    const loader =
        document.getElementById(
            "analyticsLoader"
        );


    if (loader) {

        loader.style.display =
            loading
                ? "flex"
                : "none";

    }


    const page =
        document.getElementById(
            "candidateIntegrityPage"
        );


    if (page) {

        page.classList.toggle(
            "is-loading",
            loading
        );

    }

}


/* =========================================================
   ERROR
========================================================= */

function showPageError(
    message
) {

    console.error(
        "Candidate intelligence:",
        message
    );


    const errorElement =
        document.getElementById(
            "analyticsError"
        );


    if (errorElement) {

        errorElement.textContent =
            message;


        errorElement.style.display =
            "block";


        return;

    }


    const error =
        createElement(
            "div",
            "analytics-error"
        );


    error.textContent =
        message;


    error.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 420px;
        padding: 16px 20px;
        border-radius: 12px;
        background: #3b1015;
        border: 1px solid #ef4444;
        color: #fecaca;
        font-family: inherit;
        box-shadow: 0 12px 40px rgba(0,0,0,.35);
    `;


    document.body.appendChild(
        error
    );

}


/* =========================================================
   TEXT HELPER
========================================================= */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {
        return;
    }


    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        element.textContent =
            "—";

    }

    else {

        element.textContent =
            String(value);

    }

}


/* =========================================================
   CREATE ELEMENT
========================================================= */

function createElement(
    tag,
    className
) {

    const element =
        document.createElement(
            tag
        );


    if (className) {

        element.className =
            className;

    }


    return element;

}


/* =========================================================
   NUMBER HELPER
========================================================= */

function toNumberOrNull(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return null;

    }


    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {

        return null;

    }


    return number;

}


/* =========================================================
   NUMBER FORMAT
========================================================= */

function formatNumber(
    value,
    decimals = 0
) {

    const number =
        Number(value);


    if (
        Number.isNaN(number)
    ) {

        return "—";

    }


    return number.toFixed(
        decimals
    );

}


/* =========================================================
   DATE FORMAT
========================================================= */

function formatDate(
    value
) {

    if (!value) {

        return "Time unavailable";

    }


    let normalized =
        String(value)
            .trim();


    /*
    SQLite:

    2026-08-10 08:36:53

    Convert to:

    2026-08-10T08:36:53
    */

    if (
        normalized.includes(" ") &&
        !normalized.includes("T")
    ) {

        normalized =
            normalized.replace(
                " ",
                "T"
            );

    }


    const date =
        new Date(
            normalized
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(value);

    }


    return date.toLocaleString(
        undefined,
        {
            dateStyle:
                "medium",

            timeStyle:
                "medium"
        }
    );

}


/* =========================================================
   VIOLATION CATEGORY LABEL
========================================================= */

function formatViolationCategory(
    category
) {

    const labels = {

        TAB_SWITCH:
            "Tab Switch",

        FOCUS_LOSS:
            "Focus Loss",

        FACE_ABSENCE:
            "Face Absence",

        FULLSCREEN_EXIT:
            "Fullscreen Exit",

        COPY_PASTE:
            "Copy / Cut / Paste",

        SCREENSHOT:
            "Screenshot Attempt",

        RIGHT_CLICK:
            "Right Click",

        IDENTITY_MISMATCH:
            "Identity Mismatch",

        MULTIPLE_FACES:
            "Multiple Faces",

        OTHER:
            "Other Violation",

        NO_FACE:
            "Face Absence",

        COPY:
            "Copy Attempt",

        PASTE:
            "Paste Attempt",

        CUT:
            "Cut Attempt"

    };


    const normalized =
        String(
            category ||
            "OTHER"
        )
            .trim()
            .toUpperCase();


    return (
        labels[normalized] ||
        humanizeText(
            normalized
        )
    );

}


/* =========================================================
   HUMANIZE TEXT
========================================================= */

function humanizeText(
    value
) {

    return String(
        value || ""
    )
        .toLowerCase()
        .replace(
            /_/g,
            " "
        )
        .replace(
            /\b\w/g,
            char =>
                char.toUpperCase()
        );

}


/* =========================================================
   VIOLATION ICON
========================================================= */

function getViolationIcon(
    category
) {

    const icons = {

        TAB_SWITCH:
            "↔",

        FOCUS_LOSS:
            "◌",

        FACE_ABSENCE:
            "◉",

        FULLSCREEN_EXIT:
            "⛶",

        COPY_PASTE:
            "▣",

        SCREENSHOT:
            "▤",

        RIGHT_CLICK:
            "⊙",

        IDENTITY_MISMATCH:
            "⚠",

        MULTIPLE_FACES:
            "👥",

        NO_FACE:
            "◉",

        COPY:
            "▣",

        PASTE:
            "▣",

        CUT:
            "▣",

        OTHER:
            "!"

    };


    const normalized =
        String(
            category ||
            "OTHER"
        )
            .trim()
            .toUpperCase();


    return (
        icons[normalized] ||
        "!"
    );

}


/* =========================================================
   EXPORT FOR DEBUGGING
========================================================= */

window.CandidateIntegrity =
    CandidateIntegrity;