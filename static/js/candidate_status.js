// ==========================================
// Candidate Status Viewer
// Online Exam Monitoring Platform
// (Milestone 5 - P1, admin dashboard additions, page 2 of 3)
//
// "Attempted - Not Submitted" means the candidate has monitored
// activity (browser/face-absence/flag events) for this exam but no
// ExamAttempts row - it does NOT mean the candidate abandoned the
// exam. There is no reliable signal for abandonment in this codebase
// (SessionLogs has no real, non-synthetic writer), so that state is
// deliberately not claimed here. See modules/analytics.py::
// get_candidate_status() for the full reasoning.
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    const submittedBody = document.querySelector("#submitted-table tbody");
    const notSubmittedBody = document.querySelector("#not-submitted-table tbody");

    async function fetchJSON(url) {
        const resp = await fetch(url);
        if (!resp.ok) {
            throw new Error(`Request to ${url} failed with status ${resp.status}`);
        }
        return resp.json();
    }

    function formatTime(iso) {
        if (!iso) return "—";
        const d = new Date(iso);
        if (isNaN(d.getTime())) return iso;
        return d.toLocaleString();
    }

    function resultBadge(result) {
        // Text + icon, not color alone.
        if (result === "Passed") {
            return `<span class="risk-badge risk-low"><i class="fa-solid fa-circle-check"></i> Passed</span>`;
        }
        return `<span class="risk-badge risk-high"><i class="fa-solid fa-circle-xmark"></i> Failed</span>`;
    }

    function renderEmpty(tbody, colspan, message) {
        tbody.innerHTML = `<tr><td colspan="${colspan}" class="invig-empty-row">${message}</td></tr>`;
    }

    function renderSubmitted(rows) {
        submittedBody.innerHTML = "";
        if (!rows || rows.length === 0) {
            renderEmpty(submittedBody, 4, "No candidates have submitted this exam yet.");
            return;
        }
        rows.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${row.name ? row.name : "#" + row.candidate_id}</td>
                <td>${row.score}/${row.total_questions} (${row.percentage}%)</td>
                <td>${resultBadge(row.result)}</td>
                <td>${formatTime(row.submitted_at)}</td>
            `;
            submittedBody.appendChild(tr);
        });
    }

    function renderNotSubmitted(rows) {
        notSubmittedBody.innerHTML = "";
        if (!rows || rows.length === 0) {
            renderEmpty(notSubmittedBody, 1, "No candidates have activity without a submission.");
            return;
        }
        rows.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>
                    <span class="status-pill"><i class="fa-solid fa-clock"></i> Attempted &mdash; Not Submitted</span>
                    ${row.name ? row.name : "#" + row.candidate_id}
                </td>
            `;
            notSubmittedBody.appendChild(tr);
        });
    }

    async function loadCandidateStatus() {
        renderEmpty(submittedBody, 4, "Loading candidate status...");
        renderEmpty(notSubmittedBody, 1, "Loading candidate status...");
        try {
            const data = await fetchJSON(`/api/analytics/candidate-status/${CANDIDATE_STATUS_EXAM_ID}`);
            renderSubmitted(data.submitted);
            renderNotSubmitted(data.attempted_not_submitted);
        } catch (err) {
            renderEmpty(submittedBody, 4, "Could not load candidate status for this exam. Please try again.");
            renderEmpty(notSubmittedBody, 1, "Could not load candidate status for this exam. Please try again.");
        }
    }

    loadCandidateStatus();
});
