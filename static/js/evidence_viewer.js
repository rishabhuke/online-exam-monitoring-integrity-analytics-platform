// ==========================================
// Evidence Viewer
// Online Exam Monitoring Platform
// (Milestone 5 - P1, admin dashboard additions, page 1 of 3)
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    const tableBody = document.querySelector("#evidence-table tbody");

    async function fetchJSON(url) {
        const resp = await fetch(url);
        if (!resp.ok) {
            throw new Error(`Request to ${url} failed with status ${resp.status}`);
        }
        return resp.json();
    }

    function flagSeverityClass(flagType) {
        // Mirrors the severities already assigned in
        // modules/detection_engine.py's evaluate_identity_check() -
        // kept here as display-only classification, not a source of truth.
        if (flagType === "identity_mismatch" || flagType === "identity_check_multiple_faces") {
            return "risk-high";
        }
        if (flagType === "identity_check_no_face") {
            return "risk-medium";
        }
        return "risk-unknown";
    }

    function formatFlagType(type) {
        if (!type) return "Unknown";
        return type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    }

    function formatTime(iso) {
        if (!iso) return "—";
        const d = new Date(iso);
        if (isNaN(d.getTime())) return iso;
        return d.toLocaleString();
    }

    function renderEmpty(message) {
        tableBody.innerHTML = `<tr><td colspan="5" class="invig-empty-row">${message}</td></tr>`;
    }

    function renderEvidence(items) {
        tableBody.innerHTML = "";

        if (!items || items.length === 0) {
            renderEmpty("No evidence has been captured for this exam yet.");
            return;
        }

        items.forEach(item => {
            const tr = document.createElement("tr");
            const imageUrl = `/${item.filepath}`;
            tr.innerHTML = `
                <td>
                    <a href="${imageUrl}" target="_blank" rel="noopener">
                        <img src="${imageUrl}" alt="Evidence photo for ${formatFlagType(item.flag_type)}, candidate #${item.candidate_id}" class="evidence-thumb">
                    </a>
                </td>
                <td>${item.candidate_name ? item.candidate_name : "#" + item.candidate_id}</td>
                <td><span class="risk-badge ${flagSeverityClass(item.flag_type)}">${formatFlagType(item.flag_type)}</span></td>
                <td>${formatTime(item.created_at)}</td>
                <td><a class="table-action" href="${imageUrl}" target="_blank" rel="noopener">View Full Image</a></td>
            `;
            tableBody.appendChild(tr);
        });
    }

    async function loadEvidence() {
        renderEmpty("Loading evidence...");
        try {
            const data = await fetchJSON(`/api/alert-evidence/exam/${EVIDENCE_EXAM_ID}`);
            renderEvidence(data.evidence);
        } catch (err) {
            renderEmpty("Could not load evidence for this exam. Please try again.");
        }
    }

    loadEvidence();
});
