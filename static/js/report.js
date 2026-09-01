document.addEventListener("DOMContentLoaded", function () {
    const page = document.getElementById("reportPage");
    const examId = page ? page.dataset.examId : null;

    const statIntegrityScore = document.getElementById("statIntegrityScore");
    const statRiskLabel = document.getElementById("statRiskLabel");
    const statFacePresence = document.getElementById("statFacePresence");
    const statTotalFlags = document.getElementById("statTotalFlags");
    const statTotalEventsSub = document.getElementById("statTotalEventsSub");

    const summaryText = document.getElementById("summaryText");
    const summarySourceBadge = document.getElementById("summarySourceBadge");
    const loadingState = document.getElementById("loadingState");
    const emptyState = document.getElementById("emptyState");
    const errorState = document.getElementById("errorState");

    async function fetchJSON(url) {
        const resp = await fetch(url, { headers: { "Accept": "application/json" } });
        if (!resp.ok) {
            throw new Error(`Request to ${url} failed with status ${resp.status}`);
        }
        return resp.json();
    }

    function renderScore(score) {
        statIntegrityScore.textContent = `${score.integrity_score}`;
        statRiskLabel.textContent = score.risk_label;
        statFacePresence.textContent = `${Math.round(score.face_presence_ratio * 100)}%`;
        statTotalFlags.textContent = `${score.total_flags}`;
        statTotalEventsSub.textContent = `${score.total_browser_events} browser events`;
    }

    function renderSummary(report) {
        summaryText.textContent = report.summary;
        summaryText.hidden = false;
        summarySourceBadge.textContent = report.source === "llm" ? "" : "(template-generated)";
    }

    async function loadReport() {
        if (!examId) {
            loadingState.hidden = true;
            errorState.hidden = false;
            return;
        }

        loadingState.hidden = false;
        emptyState.hidden = true;
        errorState.hidden = true;

        try {
            const [scoreResp, reportResp] = await Promise.all([
                fetchJSON(`/api/score/${examId}`),
                fetchJSON(`/api/report/${examId}`),
            ]);

            loadingState.hidden = true;

            if (scoreResp.total_flags === 0 && scoreResp.total_browser_events === 0) {
                emptyState.hidden = false;
            }

            renderScore(scoreResp);
            renderSummary(reportResp);
        } catch (err) {
            loadingState.hidden = true;
            errorState.hidden = false;
            console.error(err);
        }
    }

    loadReport();
});
