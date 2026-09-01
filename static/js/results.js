document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("resultSearch");
    const statusFilter = document.getElementById("statusFilter");
    const tableBody = document.getElementById("resultsTableBody");
    const noResultsMessage = document.getElementById("noResultsMessage");
    const totalExamsCount = document.getElementById("totalExamsCount");
    const passedCount = document.getElementById("passedCount");
    const avgScore = document.getElementById("avgScore");

    let rows = [];

    async function fetchJSON(url) {
        const resp = await fetch(url, {
            headers: { "Accept": "application/json" }
        });
        if (!resp.ok) {
            throw new Error(`Request to ${url} failed with status ${resp.status}`);
        }
        return resp.json();
    }

    function formatDate(isoString) {
        const date = new Date(isoString.replace(" ", "T"));
        if (isNaN(date)) return isoString;
        return date.toLocaleDateString("en-US", {
            day: "numeric", month: "long", year: "numeric"
        });
    }

    function renderSummary(attempts) {
        const total = attempts.length;
        const passed = attempts.filter(a => a.status === "Passed").length;
        const avg = total > 0
            ? Math.round(attempts.reduce((sum, a) => sum + a.percentage, 0) / total)
            : 0;

        totalExamsCount.textContent = total;
        passedCount.textContent = passed;
        avgScore.textContent = `${avg}%`;
    }

    function renderTable(attempts) {
        tableBody.innerHTML = "";

        attempts.forEach(a => {
            const statusLower = a.status.toLowerCase();

            const tr = document.createElement("tr");
            tr.setAttribute("data-status", statusLower);

            tr.innerHTML = `
                <td>${a.title}</td>
                <td>${formatDate(a.created_at)}</td>
                <td>${a.score} / ${a.total_questions}</td>
                <td>${a.percentage}%</td>
                <td><span class="status-badge ${statusLower}-badge">${a.status}</span></td>
                <td class="results-action-cell">
                    <a href="/report/${a.exam_id}" class="table-action-btn">View Report</a>
                    <a href="/results/${a.exam_id}/answers" class="table-action-btn table-action-btn-secondary">Review Answers</a>
                </td>
            `;

            tableBody.appendChild(tr);
        });

        rows = Array.from(tableBody.querySelectorAll("tr"));
    }

    function filterResults() {
        const searchValue = searchInput.value.trim().toLowerCase();
        const selectedStatus = statusFilter.value.toLowerCase();

        let visibleCount = 0;

        rows.forEach(row => {
            const examName = row.cells[0].textContent.trim().toLowerCase();
            const rowStatus = row.getAttribute("data-status");

            const matchesSearch = examName.includes(searchValue);
            const matchesStatus =
                selectedStatus === "all" || rowStatus === selectedStatus;

            if (matchesSearch && matchesStatus) {
                row.style.display = "";
                visibleCount++;
            } else {
                row.style.display = "none";
            }
        });

        noResultsMessage.style.display = visibleCount === 0 ? "block" : "none";
    }



    async function loadResults() {
        try {
            const attempts = await fetchJSON("/api/results");
            renderSummary(attempts);
            renderTable(attempts);
            filterResults();
        } catch (err) {
            console.error(err);
            tableBody.innerHTML = "";
            noResultsMessage.style.display = "block";
        }
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterResults);
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", filterResults);
    }

    loadResults();
});
