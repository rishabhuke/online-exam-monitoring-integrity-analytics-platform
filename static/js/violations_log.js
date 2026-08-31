// ==========================================
// Violations Log
// Online Exam Monitoring Platform
// (Milestone 5 - P1, admin dashboard additions, page 3 of 3)
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    const tableBody = document.querySelector("#violations-table tbody");

    async function fetchJSON(url) {
        const resp = await fetch(url);
        if (!resp.ok) {
            throw new Error(`Request to ${url} failed with status ${resp.status}`);
        }
        return resp.json();
    }

    function severityClass(sev) {
        const s = (sev || "").toLowerCase();
        if (s === "high") return "risk-high";
        if (s === "medium") return "risk-medium";
        if (s === "low") return "risk-low";
        return "risk-unknown";
    }

    function formatEventType(type) {
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
        tableBody.innerHTML = `<tr><td colspan="6" class="invig-empty-row">${message}</td></tr>`;
    }

    function renderViolations(flags) {
        tableBody.innerHTML = "";

        if (!flags || flags.length === 0) {
            renderEmpty("No violations have been recorded for this exam.");
            return;
        }

        flags.forEach(flag => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${flag.candidate_name ? flag.candidate_name : "#" + flag.candidate_id}</td>
                <td>${formatEventType(flag.flag_type)}</td>
                <td><span class="risk-badge ${severityClass(flag.severity)}">${flag.severity || "unknown"}</span></td>
                <td>${flag.detail ? flag.detail : "—"}</td>
                <td>${flag.threshold_breached ? flag.threshold_breached : "—"}</td>
                <td>${formatTime(flag.created_at)}</td>
            `;
            tableBody.appendChild(tr);
        });
    }

    async function loadViolations() {
        renderEmpty("Loading violations...");
        try {
            const data = await fetchJSON(`/api/flags/exam/${VIOLATIONS_EXAM_ID}`);
            renderViolations(data.flags);
        } catch (err) {
            renderEmpty("Could not load violations for this exam. Please try again.");
        }
    }

    loadViolations();
});
