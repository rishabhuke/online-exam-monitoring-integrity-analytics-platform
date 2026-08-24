/* =========================================================
   AI GENERATED REPORTS
========================================================= */

document.addEventListener("DOMContentLoaded", () => {
    initializeAIReports();
});





/* =========================================================
   ELEMENTS
========================================================= */

const examSelect =
    document.getElementById("examSelect");

const candidateSelect =
    document.getElementById("candidateSelect");

const generateButton =
    document.getElementById("generateReportBtn");

const reportContainer =
    document.getElementById("reportContent");

const historyContainer =
    document.getElementById("reportHistory");

const loadingElement =
    document.getElementById("reportLoading");

const previewSection =
    document.getElementById("reportPreviewSection");

const generatedMetrics =
    document.getElementById("generatedMetrics");

const downloadPdfButton =
    document.getElementById("downloadPdfBtn");

const downloadWordButton =
    document.getElementById("downloadWordBtn");

const downloadCsvButton =
    document.getElementById("downloadCsvBtn");


/* =========================================================
   MODAL
========================================================= */

const reportModal =
    document.getElementById("reportViewModal");

const modalReportTitle =
    document.getElementById("modalReportTitle");

const modalReportContent =
    document.getElementById("modalReportContent");

const closeReportModal =
    document.getElementById("closeReportModal");

const modalCloseButton =
    document.getElementById("modalCloseButton");

const reportModalOverlay =
    document.getElementById("reportModalOverlay");


/* =========================================================
   STATE
========================================================= */

let currentReportId = null;

let currentReportType = "candidate";

let currentReport = null;


/* =========================================================
   INITIALIZE
========================================================= */

async function initializeAIReports() {

    initializeReportType();

    initializeExamChange();

    initializeGenerateButton();

    initializeModal();

    initializeDownloadButtons();

    initializeHistoryFilter();

    initializeSearch();

    initializeRefresh();

    await loadExams();

    await loadReportHistory();
}


/* =========================================================
   REPORT TYPE
========================================================= */

function initializeReportType() {

    const buttons =
        document.querySelectorAll(".type-option");

    buttons.forEach(button => {

        button.addEventListener("click", () => {

            buttons.forEach(btn =>
                btn.classList.remove("active")
            );

            button.classList.add("active");

            currentReportType =
                button.dataset.type;

            updateReportTypeUI();

        });

    });

    updateReportTypeUI();
}


/* =========================================================
   REPORT TYPE UI
========================================================= */

function updateReportTypeUI() {

    const candidateField =
        document.querySelector(".candidate-field");

    if (!candidateField) {
        return;
    }

    if (currentReportType === "candidate") {

        candidateField.style.display = "";

    } else {

        candidateField.style.display = "none";

        if (candidateSelect) {
            candidateSelect.value = "";
        }

    }
}


/* =========================================================
   EXAM CHANGE
========================================================= */

function initializeExamChange() {

    if (!examSelect) {
        return;
    }

    examSelect.addEventListener("change", async () => {

        await loadCandidates(
            examSelect.value
        );

    });
}


/* =========================================================
   GENERATE
========================================================= */

function initializeGenerateButton() {

    if (!generateButton) {
        return;
    }

    generateButton.addEventListener(
        "click",
        generateReport
    );
}


/* =========================================================
   DOWNLOAD
========================================================= */

function initializeDownloadButtons() {

    if (downloadPdfButton) {

        downloadPdfButton.addEventListener(
            "click",
            downloadPDF
        );

    }

    if (downloadWordButton) {

        downloadWordButton.addEventListener(
            "click",
            downloadWord
        );

    }

    if (downloadCsvButton) {

        downloadCsvButton.addEventListener(
            "click",
            downloadCSV
        );

    }
}


/* =========================================================
   MODAL
========================================================= */

function initializeModal() {

    if (closeReportModal) {

        closeReportModal.addEventListener(
            "click",
            closeReportView
        );

    }

    if (modalCloseButton) {

        modalCloseButton.addEventListener(
            "click",
            closeReportView
        );

    }

    if (reportModalOverlay) {

        reportModalOverlay.addEventListener(
            "click",
            closeReportView
        );

    }

    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Escape" &&
                reportModal &&
                !reportModal.classList.contains("hidden")
            ) {

                closeReportView();

            }

        }
    );
}


/* =========================================================
   HISTORY FILTER
========================================================= */

function initializeHistoryFilter() {

    const filter =
        document.getElementById("historyType");

    if (!filter) {
        return;
    }

    filter.addEventListener(
        "change",
        loadReportHistory
    );
}


/* =========================================================
   SEARCH
========================================================= */

function initializeSearch() {

    const search =
        document.getElementById("globalSearch");

    if (!search) {
        return;
    }

    search.addEventListener(
        "input",
        () => {

            const query =
                search.value
                    .trim()
                    .toLowerCase();

            document
                .querySelectorAll(
                    "#reportHistory tr"
                )
                .forEach(row => {

                    const text =
                        row.textContent
                            .toLowerCase();

                    row.style.display =
                        !query ||
                        text.includes(query)
                            ? ""
                            : "none";

                });

        }
    );
}


/* =========================================================
   REFRESH
========================================================= */

function initializeRefresh() {

    const refresh =
        document.getElementById("refreshBtn");

    if (!refresh) {
        return;
    }

    refresh.addEventListener(
        "click",
        async () => {

            await loadExams();

            await loadReportHistory();

        }
    );
}


/* =========================================================
   LOAD EXAMS
========================================================= */

async function loadExams() {

    if (!examSelect) {
        return;
    }

    try {

        const response =
            await fetch(
                "/admin/api/ai-reports/exams"
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "Unable to load examinations."
            );

        }

        examSelect.innerHTML =
            `<option value="">
                Select examination
            </option>`;

        (data.exams || []).forEach(exam => {

            const option =
                document.createElement("option");

            option.value = exam.id;

            option.textContent =
                exam.topic
                    ? `${exam.title} - ${exam.topic}`
                    : exam.title;

            examSelect.appendChild(option);

        });

    } catch (error) {

        console.error(
            "Exam loading error:",
            error
        );

        examSelect.innerHTML =
            `<option value="">
                Unable to load examinations
            </option>`;

    }
}


/* =========================================================
   LOAD CANDIDATES
========================================================= */

async function loadCandidates(examId) {

    if (!candidateSelect) {
        return;
    }

    if (currentReportType === "exam") {

        candidateSelect.innerHTML =
            `<option value="">
                Not required for examination report
            </option>`;

        return;
    }

    if (!examId) {

        candidateSelect.innerHTML =
            `<option value="">
                Select examination first
            </option>`;

        return;
    }

    candidateSelect.innerHTML =
        `<option value="">
            Loading candidates...
        </option>`;

    try {

        const response =
            await fetch(
                `/admin/api/ai-reports/candidates?exam_id=${encodeURIComponent(examId)}`
            );

        const data =
            await response.json();

        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "Unable to load candidates."
            );

        }

        candidateSelect.innerHTML =
            `<option value="">
                Select candidate
            </option>`;

        (data.candidates || []).forEach(candidate => {

            const option =
                document.createElement("option");

            option.value =
                candidate.id;

            option.textContent =
                `${candidate.name} (${candidate.email || "No email"})`;

            candidateSelect.appendChild(option);

        });

    } catch (error) {

        console.error(
            "Candidate loading error:",
            error
        );

        candidateSelect.innerHTML =
            `<option value="">
                Unable to load candidates
            </option>`;

    }
}


/* =========================================================
   GENERATE REPORT
========================================================= */

async function generateReport() {

    if (!examSelect) {
        return;
    }

    const examId =
        examSelect.value;

    if (!examId) {

        showError(
            "Please select an examination."
        );

        return;
    }


    let url;

    let body;


    if (currentReportType === "candidate") {

        if (!candidateSelect) {
            return;
        }

        const candidateId =
            candidateSelect.value;

        if (!candidateId) {

            showError(
                "Please select a candidate."
            );

            return;
        }

        url =
            "/admin/api/ai-reports/generate";

        body = {

            exam_id:
                Number(examId),

            candidate_id:
                Number(candidateId),

            include_violations:
                document.getElementById(
                    "includeViolations"
                )?.checked ?? true,

            include_integrity:
                document.getElementById(
                    "includeIntegrity"
                )?.checked ?? true,

            include_recommendations:
                document.getElementById(
                    "includeRecommendations"
                )?.checked ?? true
        };

    } else {

        url =
            "/admin/api/ai-reports/generate-exam";

        body = {

            exam_id:
                Number(examId),

            include_violations:
                document.getElementById(
                    "includeViolations"
                )?.checked ?? true,

            include_integrity:
                document.getElementById(
                    "includeIntegrity"
                )?.checked ?? true,

            include_recommendations:
                document.getElementById(
                    "includeRecommendations"
                )?.checked ?? true
        };

    }


    setLoading(true);

    try {

        const response =
            await fetch(
                url,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(body)
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "Report generation failed."
            );

        }


        currentReportId =
            data.report_id ||
            data.report?.id;


        currentReport =
            normalizeReport(data);


        updateMetrics(currentReport);

        renderGeneratedReport(
            currentReport
        );


        await loadReportHistory();


        showSuccess(
            "AI report generated successfully."
        );


    } catch (error) {

        console.error(
            "AI report error:",
            error
        );

        showError(
            error.message
        );

    } finally {

        setLoading(false);

    }
}


/* =========================================================
   NORMALIZE REPORT
========================================================= */

function normalizeReport(data) {

    const report =
        data.report
            ? {
                ...data.report,
                ...data
            }
            : {
                ...data
            };


    let score =
        firstValidNumber(
            report.integrity_score,
            report.integrityScore,
            report.score
        );


    let risk =
        firstText(
            report.risk_label,
            report.risk,
            report.riskLevel
        );


    let face =
        firstValidNumber(
            report.face_presence_ratio,
            report.facePresenceRatio,
            report.face_presence
        );


    let warnings =
        firstValidNumber(
            report.warning_count,
            report.warningCount,
            report.warnings
        );


    if (score === null) {
        score = null;
    }


    if (!risk && score !== null) {

        risk =
            calculateRisk(score);

    }


    if (face === null) {
        face = null;
    }


    if (warnings === null) {

        warnings =
            countViolations(
                report.violations
            );

    }


    return {

        ...report,

        integrity_score:
            score,

        risk_label:
            risk,

        face_presence_ratio:
            face,

        warning_count:
            warnings,

        report_content:
            report.report_content ||
            report.assessment ||
            "No report content available."

    };
}


/* =========================================================
   NUMBER HELPERS
========================================================= */

function firstValidNumber(...values) {

    for (const value of values) {

        if (
            value !== null &&
            value !== undefined &&
            value !== "" &&
            !Number.isNaN(Number(value))
        ) {

            return Number(value);

        }

    }

    return null;
}


function firstText(...values) {

    for (const value of values) {

        if (
            value !== null &&
            value !== undefined &&
            String(value).trim() !== ""
        ) {

            return String(value).trim();

        }

    }

    return null;
}


/* =========================================================
   RISK
========================================================= */

function calculateRisk(score) {

    const value =
        Number(score);

    if (Number.isNaN(value)) {
        return "Unknown";
    }

    if (value >= 80) {
        return "Low";
    }

    if (value >= 60) {
        return "Medium";
    }

    return "High";
}


/* =========================================================
   VIOLATION COUNT
========================================================= */

function countViolations(violations) {

    if (
        !violations ||
        typeof violations !== "object"
    ) {

        return 0;
    }

    return Object.values(violations)
        .reduce(
            (total, value) =>
                total + (Number(value) || 0),
            0
        );
}


/* =========================================================
   UPDATE METRICS
========================================================= */

function updateMetrics(report) {

    if (!generatedMetrics) {
        return;
    }


    generatedMetrics.classList.remove(
        "hidden"
    );


    const scoreElement =
        document.getElementById(
            "reportScore"
        );

    const riskElement =
        document.getElementById(
            "reportRisk"
        );

    const faceElement =
        document.getElementById(
            "reportFace"
        );

    const warningsElement =
        document.getElementById(
            "reportWarnings"
        );


    /*
       IMPORTANT:
       Do NOT use 0 or N/A as fallback.
    */


    if (scoreElement) {

        scoreElement.textContent =
            report.integrity_score !== null
                ? Number(
                    report.integrity_score
                ).toFixed(0)
                : "--";

    }


    if (riskElement) {

        const risk =
            report.risk_label ||
            (
                report.integrity_score !== null
                    ? calculateRisk(
                        report.integrity_score
                    )
                    : "Unknown"
            );

        riskElement.textContent =
            risk;

        riskElement.className =
            "risk-badge";

        const riskClass =
            String(risk)
                .toLowerCase();

        if (riskClass === "low") {

            riskElement.classList.add(
                "risk-low"
            );

        } else if (
            riskClass === "medium"
        ) {

            riskElement.classList.add(
                "risk-medium"
            );

        } else if (
            riskClass === "high"
        ) {

            riskElement.classList.add(
                "risk-high"
            );

        }

    }


    if (faceElement) {

        faceElement.textContent =
            formatFaceRatio(
                report.face_presence_ratio
            );

    }


    if (warningsElement) {

        warningsElement.textContent =
            report.warning_count !== null
                ? report.warning_count
                : "--";

    }

}


/* =========================================================
   RENDER REPORT
========================================================= */

function renderGeneratedReport(report) {

    if (!reportContainer) {
        return;
    }


    if (previewSection) {

        previewSection.classList.remove(
            "hidden"
        );

    }


    const isExam =
        report.report_type === "exam";


    const title =
        isExam
            ? (
                report.exam_title ||
                report.exam?.title ||
                "Examination Report"
            )
            : (
                report.candidate_name ||
                report.candidate?.name ||
                "Candidate Report"
            );


    const previewTitle =
        document.getElementById(
            "previewTitle"
        );


    const previewSubtitle =
        document.getElementById(
            "previewSubtitle"
        );


    if (previewTitle) {

        previewTitle.textContent =
            isExam
                ? "AI Examination Integrity Report"
                : "AI Candidate Integrity Report";

    }


    if (previewSubtitle) {

        previewSubtitle.textContent =
            isExam
                ? "Examination-wide analysis generated by ExamGuard AI"
                : "Candidate-level integrity assessment generated by ExamGuard AI";

    }


    const generatedTime =
        document.getElementById(
            "reportGeneratedTime"
        );


    if (generatedTime) {

        generatedTime.textContent =
            formatDate(
                report.generated_at
            );

    }


    const content =
        cleanReportText(
            report.report_content ||
            report.assessment ||
            "No report content available."
        );


    if (!isExam) {

        const violations =
            report.violations || {};


        reportContainer.innerHTML = `

            <div class="generated-report">

                <h3>
                    ${escapeHtml(title)}
                </h3>

                <p>
                    ${escapeHtml(
                        report.exam_title ||
                        report.exam?.title ||
                        "Examination"
                    )}
                </p>

                <div class="violation-list">

                    ${buildViolationsHtml(
                        violations
                    )}

                </div>

                <h4>
                    AI Integrity Assessment
                </h4>

                <div class="report-text">

                    ${formatReportText(content)}

                </div>

            </div>

        `;

    } else {

        reportContainer.innerHTML = `

            <div class="generated-report">

                <h3>
                    ${escapeHtml(title)}
                </h3>

                <p>
                    Examination-wide Integrity Analysis
                </p>

                <h4>
                    AI Examination Assessment
                </h4>

                <div class="report-text">

                    ${formatReportText(content)}

                </div>

            </div>

        `;

    }


    enableDownloadButtons(
        report.id ||
        currentReportId
    );
}


/* =========================================================
   VIOLATIONS
========================================================= */

function buildViolationsHtml(violations) {

    if (
        !violations ||
        Object.keys(violations).length === 0
    ) {

        return `

            <div class="report-violation">

                <span>
                    No Recorded Violations
                </span>

                <strong>
                    0
                </strong>

            </div>

        `;

    }


    return Object.entries(
        violations
    )
    .map(([type, count]) => `

        <div class="report-violation">

            <span>
                ${escapeHtml(type)}
            </span>

            <strong>
                ${escapeHtml(count)}
            </strong>

        </div>

    `)
    .join("");
}


/* =========================================================
   HISTORY
========================================================= */

async function loadReportHistory() {

    if (!historyContainer) {
        return;
    }


    try {

        const response =
            await fetch(
                "/admin/api/ai-reports/history"
            );


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "Unable to load report history."
            );

        }


        const reports =
            data.reports || [];


        updateSummary(
            reports
        );


        const filter =
            document.getElementById(
                "historyType"
            );


        const filterValue =
            filter?.value || "all";


        const filteredReports =
            filterValue === "all"
                ? reports
                : reports.filter(
                    report =>
                        report.report_type ===
                        filterValue
                );


        historyContainer.innerHTML =
            "";


        if (!filteredReports.length) {

            historyContainer.innerHTML = `

                <tr>

                    <td
                        colspan="8"
                        class="empty-state"
                    >

                        <i class="fa-solid fa-file-circle-question"></i>

                        <p>
                            No AI reports found.
                        </p>

                    </td>

                </tr>

            `;

            return;
        }


        filteredReports.forEach(
            report => {

                const row =
                    document.createElement(
                        "tr"
                    );


                const normalized =
                    normalizeReport(
                        report
                    );


                const isExam =
                    report.report_type === "exam";


                const displayName =
                    isExam
                        ? (
                            report.exam_title ||
                            "Examination"
                        )
                        : (
                            report.candidate_name ||
                            "Candidate"
                        );


                const label =
                    isExam
                        ? "Examination Report"
                        : "Candidate Report";


                const score =
                    normalized.integrity_score !== null
                        ? `${normalized.integrity_score.toFixed(0)} / 100`
                        : "--";


                row.innerHTML = `

                    <td>

                        <strong>
                            ${escapeHtml(label)}
                        </strong>

                    </td>


                    <td>
                        ${escapeHtml(displayName)}
                    </td>


                    <td>

                        <span
                            class="history-risk"
                        >
                            ${escapeHtml(
                                normalized.risk_label ||
                                "--"
                            )}
                        </span>

                    </td>


                    <td>

                        <span
                            class="history-score"
                        >
                            ${escapeHtml(score)}
                        </span>

                    </td>


                    <td>
                        ${escapeHtml(
                            formatFaceRatio(
                                normalized.face_presence_ratio
                            )
                        )}
                    </td>


                    <td>
                        ${escapeHtml(
                            formatDate(
                                report.generated_at
                            )
                        )}
                    </td>


                    <!-- DOWNLOADS COLUMN -->

                    <td>

                        <div
                            class="download-icons"
                        >

                            <a
                                href="/admin/api/ai-reports/${report.id}/pdf"
                                title="Download PDF"
                                class="pdf-icon"
                            >
                                <i class="fa-solid fa-file-pdf"></i>
                            </a>


                            <a
                                href="/admin/api/ai-reports/${report.id}/docx"
                                title="Download Word"
                                class="word-icon"
                            >
                                <i class="fa-solid fa-file-word"></i>
                            </a>


                            <a
                                href="/admin/api/ai-reports/${report.id}/csv"
                                title="Download CSV"
                                class="csv-icon"
                            >
                                <i class="fa-solid fa-file-csv"></i>
                            </a>

                        </div>

                    </td>


                    <!-- ACTION COLUMN -->

                    <td>

                        <button
                            type="button"
                            class="history-view-btn"
                            data-report-id="${report.id}"
                        >

                            <i class="fa-solid fa-eye"></i>

                            View

                        </button>

                    </td>

                `;


                historyContainer.appendChild(
                    row
                );

            }
        );


        document
            .querySelectorAll(
                ".history-view-btn"
            )
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        loadSingleReport(
                            button.dataset.reportId
                        );

                    }
                );

            });


    } catch (error) {

        console.error(
            "History error:",
            error
        );

        historyContainer.innerHTML = `

            <tr>

                <td
                    colspan="8"
                    class="empty-state"
                >

                    Unable to load report history.

                </td>

            </tr>

        `;

    }
}


/* =========================================================
   SUMMARY
========================================================= */

function updateSummary(reports) {

    const total =
        document.getElementById(
            "totalReports"
        );

    const candidate =
        document.getElementById(
            "candidateReports"
        );

    const exam =
        document.getElementById(
            "examReports"
        );


    if (total) {

        total.textContent =
            reports.length;

    }


    if (candidate) {

        candidate.textContent =
            reports.filter(
                report =>
                    report.report_type ===
                    "candidate"
            ).length;

    }


    if (exam) {

        exam.textContent =
            reports.filter(
                report =>
                    report.report_type ===
                    "exam"
            ).length;

    }

}


/* =========================================================
   LOAD SINGLE REPORT
========================================================= */

async function loadSingleReport(reportId) {

    try {

        const response =
            await fetch(
                `/admin/api/ai-reports/${reportId}`
            );


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.error ||
                "Unable to load report."
            );

        }


        const report =
            normalizeReport(
                data.report
            );


        currentReport =
            report;

        currentReportId =
            report.id;


        updateMetrics(
            report
        );


        renderGeneratedReport(
            report
        );


        openReportModal(
            report
        );


    } catch (error) {

        console.error(
            "Report loading error:",
            error
        );

        showError(
            error.message
        );

    }
}


/* =========================================================
   OPEN MODAL
========================================================= */

function openReportModal(report) {

    if (!reportModal) {
        return;
    }


    const isExam =
        report.report_type === "exam";


    if (modalReportTitle) {

        modalReportTitle.textContent =
            isExam
                ? (
                    report.exam_title ||
                    "Examination Report"
                )
                : (
                    report.candidate_name ||
                    "Candidate Report"
                );

    }


    if (modalReportContent) {

        modalReportContent.innerHTML =
            formatReportText(
                cleanReportText(
                    report.report_content ||
                    "No report content available."
                )
            );

    }


    reportModal.classList.remove(
        "hidden"
    );


    document.body.classList.add(
        "modal-open"
    );
}


/* =========================================================
   CLOSE MODAL
========================================================= */

function closeReportView() {

    if (!reportModal) {
        return;
    }


    reportModal.classList.add(
        "hidden"
    );


    document.body.classList.remove(
        "modal-open"
    );
}


/* =========================================================
   ENABLE DOWNLOADS
========================================================= */

function enableDownloadButtons(reportId) {

    const valid =
        Boolean(reportId);


    if (downloadPdfButton) {
        downloadPdfButton.disabled =
            !valid;
    }

    if (downloadWordButton) {
        downloadWordButton.disabled =
            !valid;
    }

    if (downloadCsvButton) {
        downloadCsvButton.disabled =
            !valid;
    }
}


/* =========================================================
   DOWNLOAD PDF
========================================================= */

function downloadPDF() {

    if (!currentReportId) {

        showError(
            "Generate or select a report first."
        );

        return;
    }


    window.location.href =
        `/admin/api/ai-reports/${currentReportId}/pdf`;
}


/* =========================================================
   DOWNLOAD WORD
========================================================= */

function downloadWord() {

    if (!currentReportId) {

        showError(
            "Generate or select a report first."
        );

        return;
    }


    window.location.href =
        `/admin/api/ai-reports/${currentReportId}/docx`;
}


/* =========================================================
   DOWNLOAD CSV
========================================================= */

function downloadCSV() {

    if (!currentReportId) {

        showError(
            "Generate or select a report first."
        );

        return;
    }


    window.location.href =
        `/admin/api/ai-reports/${currentReportId}/csv`;
}


/* =========================================================
   LOADING
========================================================= */

function setLoading(loading) {

    if (loadingElement) {

        loadingElement.classList.toggle(
            "show",
            loading
        );

    }


    if (generateButton) {

        generateButton.disabled =
            loading;


        generateButton.innerHTML =
            loading
                ? `
                    <i class="fa-solid fa-spinner fa-spin"></i>
                    Generating...
                `
                : `
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                    Generate AI Report
                    <span class="generate-arrow">
                        <i class="fa-solid fa-arrow-right"></i>
                    </span>
                `;

    }

}


/* =========================================================
   FACE RATIO
========================================================= */

function formatFaceRatio(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "--";
    }


    const number =
        Number(value);


    if (Number.isNaN(number)) {

        return "--";
    }


    if (number <= 1) {

        return `${(
            number * 100
        ).toFixed(1)}%`;

    }


    return `${number.toFixed(1)}%`;
}


/* =========================================================
   CLEAN REPORT
========================================================= */

function cleanReportText(text) {

    if (!text) {
        return "";
    }


    return String(text)

        .replace(
            /^\s*#{1,6}\s*/gm,
            ""
        )

        .replace(
            /\*\*/g,
            ""
        )

        .replace(
            /(?<!\*)\*(?!\*)/g,
            ""
        )

        .replace(
            /`/g,
            ""
        )

        .replace(
            /\|/g,
            " "
        )

        .replace(
            /[ \t]+/g,
            " "
        )

        .replace(
            /\n{3,}/g,
            "\n\n"
        )

        .trim();
}


/* =========================================================
   FORMAT REPORT
========================================================= */

function formatReportText(text) {

    if (!text) {

        return `
            <p>
                No report content available.
            </p>
        `;
    }


    return String(text)

        .split("\n")

        .map(
            line =>
                line.trim()
        )

        .filter(
            line =>
                line.length > 0
        )

        .map(line => {

            if (
                line.endsWith(":") &&
                line.length < 100
            ) {

                return `
                    <h4>
                        ${escapeHtml(line)}
                    </h4>
                `;

            }


            return `
                <p>
                    ${escapeHtml(line)}
                </p>
            `;

        })

        .join("");
}


/* =========================================================
   DATE
========================================================= */

function formatDate(value) {

    if (!value) {
        return "--";
    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(value);

    }


    return date.toLocaleString();
}


/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHtml(value) {

    return String(
        value ?? ""
    )

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


/* =========================================================
   MESSAGES
========================================================= */

function showError(message) {

    console.error(message);

    alert(message);
}


function showSuccess(message) {

    console.log(message);

}