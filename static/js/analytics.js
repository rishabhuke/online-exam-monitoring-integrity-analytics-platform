document.addEventListener("DOMContentLoaded", function () {
    const statTotalExams = document.getElementById("statTotalExams");
    const statAverageScore = document.getElementById("statAverageScore");
    const statBestScore = document.getElementById("statBestScore");
    const statPassedExams = document.getElementById("statPassedExams");

    const activityList = document.getElementById("activityList");
    const loadingState = document.getElementById("loadingState");
    const emptyState = document.getElementById("emptyState");
    const errorState = document.getElementById("errorState");

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

    function renderStats(attempts) {
        const total = attempts.length;
        const passed = attempts.filter(a => a.status === "Passed").length;
        const avg = total > 0
            ? Math.round(attempts.reduce((sum, a) => sum + a.percentage, 0) / total)
            : 0;
        const best = total > 0
            ? Math.round(Math.max(...attempts.map(a => a.percentage)))
            : 0;

        statTotalExams.textContent = total;
        statAverageScore.textContent = `${avg}%`;
        statBestScore.textContent = `${best}%`;
        statPassedExams.textContent = `${passed} / ${total}`;
    }

    function renderActivity(attempts) {
        activityList.innerHTML = "";

        attempts.forEach(a => {
            const statusLower = a.status.toLowerCase();
            const iconClass = a.status === "Passed" ? "green-icon" : "orange-icon";
            const icon = a.status === "Passed" ? "fa-circle-check" : "fa-circle-xmark";

            const item = document.createElement("div");
            item.className = "activity-item";
            item.innerHTML = `
                <div class="activity-icon ${iconClass}">
                    <i class="fa-solid ${icon}"></i>
                </div>
                <div class="activity-content">
                    <h4>${a.title}</h4>
                    <p>Completed on ${formatDate(a.created_at)} &middot; Score: ${a.score}/${a.total_questions} &middot; ${a.percentage}%</p>
                </div>
                <span class="status-badge ${statusLower}-badge">${a.status}</span>
            `;
            activityList.appendChild(item);
        });
    }

    async function loadAnalytics() {
        loadingState.hidden = false;
        emptyState.hidden = true;
        errorState.hidden = true;

        try {
            const attempts = await fetchJSON("/api/results");
            loadingState.hidden = true;

            if (attempts.length === 0) {
                emptyState.hidden = false;
                renderStats([]);
                return;
            }

            renderStats(attempts);
            renderActivity(attempts);
        } catch (err) {
            loadingState.hidden = true;
            errorState.hidden = false;
            console.error(err);
        }
    }

    loadAnalytics();
});
