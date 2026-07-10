document.addEventListener("DOMContentLoaded", function () {
    const checks = ["camera", "microphone", "internet", "browser", "fullscreen", "face"];
    const completedChecks = new Set();

    function updateOverallReadiness() {
        const readinessScore = document.getElementById("readinessScore");
        const overallBadge = document.getElementById("overallBadge");

        readinessScore.textContent = `${completedChecks.size} / ${checks.length} Ready`;

        if (completedChecks.size === checks.length) {
            overallBadge.textContent = "All Checks Completed";
            overallBadge.classList.remove("pending-badge");
            overallBadge.classList.add("ready-badge");
        } else {
            overallBadge.textContent = "Pending Checks";
            overallBadge.classList.remove("ready-badge");
            overallBadge.classList.add("pending-badge");
        }
    }

    window.runCheck = function (checkName) {
        const statusEl = document.getElementById(`${checkName}Status`);
        if (!statusEl) return;

        statusEl.textContent = "Checking...";
        statusEl.classList.remove("ready", "pending");
        statusEl.classList.add("checking");

        setTimeout(() => {
            statusEl.textContent = "Ready";
            statusEl.classList.remove("checking", "pending");
            statusEl.classList.add("ready");

            completedChecks.add(checkName);
            updateOverallReadiness();
        }, 1200);
    };

    const runAllBtn = document.getElementById("runAllChecksBtn");
    if (runAllBtn) {
        runAllBtn.addEventListener("click", function () {
            checks.forEach((check, index) => {
                setTimeout(() => {
                    window.runCheck(check);
                }, index * 350);
            });
        });
    }

    updateOverallReadiness();
});