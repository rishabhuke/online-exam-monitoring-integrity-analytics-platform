// ============================================================
// EXAMGUARD AI
// ADMIN DASHBOARD JAVASCRIPT
// ============================================================

let currentSupportTicket = null;
document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializeDashboard();

        initializeSidebar();

        initializeLogout();

        initializeSearch();

        initializeRiskFilter();
         loadSupportTickets();

        initializeRefreshButton();

        updateCurrentDate();

        updateCurrentTime();

        loadAllDashboardData();
        
document.getElementById("closeSupportModal")
    .addEventListener("click",closeSupportModal);

document.getElementById("cancelSupportModal")
    .addEventListener("click",closeSupportModal);
     document
        .getElementById("saveSupportResponse")
        ?.addEventListener("click", updateSupportTicket);


        setInterval(
            loadAllDashboardData,
            30000
        );

        setInterval(
            updateCurrentTime,
            1000
        );

    }
);


// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

function initializeDashboard() {

    const pageTitle =
        document.getElementById(
            "pageTitle"
        );

    if (pageTitle) {

        pageTitle.innerHTML =
            "Dashboard";

    }
    
}
function createProfileRow(
    label,
    value
) {

    return `
        <div
            style="
                display:flex;
                justify-content:space-between;
                gap:15px;
                padding:10px 0;
                border-bottom:1px solid rgba(148,163,184,.1);
            "
        >

            <span
                style="
                    color:#94a3b8;
                    font-size:13px;
                "
            >
                ${escapeHtml(label)}
            </span>

            <strong
                style="
                    text-align:right;
                    font-size:13px;
                    word-break:break-word;
                "
            >
                ${escapeHtml(
                    String(value ?? "-")
                )}
            </strong>


        </div>
    `;

}


// ============================================================
// LOAD ALL DATA
// ============================================================

function loadAllDashboardData() {

    loadDashboardStatistics();


    loadIntegritySummary();

    loadRiskDistribution();

    loadIntegrityTrend();

    loadLiveExams();

    loadRecentActivity();

    loadUpcomingExams();

    loadCandidates();

    loadLiveMonitoring();

    loadLiveAlerts();

    loadViolations();

    loadReports();



}

async function loadSupportTickets() {
    try {
        const response = await fetch("/admin/api/support", {
            credentials: "same-origin"
        });

        if (!response.ok) {
            throw new Error("HTTP " + response.status);
        }

        const data = await response.json();

        console.log("SUPPORT API RESPONSE:", data);
        console.log("SUPPORT TICKETS:", data.tickets);

        if (!data.success) {
            console.error("Support API failed:", data.message);
            return;
        }

        renderSupportTickets(data.tickets || []);

    } catch (error) {
        console.error("Support tickets error:", error);
    }
}

function openSupportModal(ticket){

    currentSupportTicket=ticket;

    document.getElementById("modalCandidateName").textContent=ticket.candidate_name;
    document.getElementById("modalCandidateEmail").textContent=ticket.candidate_email;
    document.getElementById("modalIssueType").textContent=ticket.issue_type;
    document.getElementById("modalPriority").textContent=ticket.priority;
    document.getElementById("modalSubject").textContent=ticket.subject;
    document.getElementById("modalCandidateMessage").value=ticket.message;
    document.getElementById("modalAdminResponse").value=ticket.admin_response || "";
    document.getElementById("modalTicketStatus").value=ticket.status;

    document.getElementById("supportModal").classList.add("show");

}


function renderSupportTickets(tickets){

    const container =
        document.getElementById("supportTicketsList");

    const badge =
        document.getElementById("openSupportCount");

    if(!container) return;

    container.innerHTML = "";

  const openTickets = tickets.filter(ticket =>
    String(ticket.status || "").trim().toLowerCase() === "open"
).length;

    badge.textContent =
        `${openTickets} Open`;

    if(tickets.length===0){

        container.innerHTML =
        `<div class="empty-state">
            No support requests found.
        </div>`;

        return;
    }

    tickets.slice(0,5).forEach(ticket=>{

        const statusClass =
            ticket.status.toLowerCase().replace(/\s+/g,"-");

        const priorityClass =
            ticket.priority.toLowerCase();

        const card =
            document.createElement("div");

        card.className="support-ticket";

        card.innerHTML=`
            <div class="support-ticket-top">

                <div>
                    <h4>${ticket.candidate_name}</h4>
                    <small>${ticket.candidate_email}</small>
                </div>

                <span class="ticket-status ${statusClass}">
                    ${ticket.status}
                </span>

            </div>

            <strong>${ticket.subject}</strong>

            <p class="support-ticket-message">
                ${ticket.message}
            </p>

            <div class="support-meta">

                <span class="priority ${priorityClass}">
                    ${ticket.priority}
                </span>

                <span>${ticket.issue_type}</span>

            </div>

            <div class="support-actions">

                <button class="respond-btn">
                    Respond
                </button>

            </div>
        `;

        card.querySelector(".respond-btn")
            .addEventListener("click",function(){

                openSupportModal(ticket);

            });

        container.appendChild(card);

    });

}

// ============================================================
// DASHBOARD STATISTICS
// ============================================================

async function loadDashboardStatistics() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/stats",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const stats =
            result.statistics;


        setCardValue(
            "totalCandidates",
            stats.total_candidates ?? 0
        );


        setCardValue(
            "totalExams",
            stats.total_exams ?? 0
        );


        setCardValue(
            "runningExams",
            stats.running_exams ?? 0
        );


        setCardValue(
            "completedToday",
            stats.completed_today ?? 0
        );


        setCardValue(
            "violationCount",
            stats.violation_count ?? 0
        );


        setCardValue(
            "highRiskCandidates",
            stats.high_risk ?? 0
        );


        setCardValue(
            "reportCount",
            stats.report_count ?? 0
        );


        setCardValue(
            "averageIntegrity",
            (stats.average_integrity ?? 0) + "%"
        );

    }

    catch (error) {

        console.error(
            "Dashboard statistics error:",
            error
        );

    }
}


// ============================================================
// INTEGRITY SUMMARY
// ============================================================

async function loadIntegritySummary() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/integrity",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        setCardValue(
            "overallIntegrity",
            (result.overallIntegrity ?? 0) + "%"
        );


        const summary =
            document.getElementById(
                "integritySummary"
            );


        if (summary) {

            const items =
                result.integritySummary || [];


            summary.innerHTML = "";


            items.forEach(
                function (item) {

                    const li =
                        document.createElement(
                            "li"
                        );

                    li.textContent =
                        item;

                    summary.appendChild(
                        li
                    );

                }
            );

        }

    }

    catch (error) {

        console.error(
            "Integrity summary error:",
            error
        );

    }
}


// ============================================================
// RISK DISTRIBUTION
// ============================================================

async function loadRiskDistribution() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/risk-distribution",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const labels = [];

        const values = [];


        result.distribution.forEach(
            function (item) {

                labels.push(
                    item.risk
                );

                values.push(
                    item.count
                );

            }
        );


        const canvas =
            document.getElementById(
                "riskChart"
            );


        if (!canvas) {

            return;

        }


        if (
            window.riskChartInstance
        ) {

            window.riskChartInstance.destroy();

        }


        window.riskChartInstance =
            new Chart(
                canvas,
                {

                    type: "doughnut",

                    data: {

                        labels: labels,

                        datasets: [

                            {

                                data: values

                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false

                    }

                }
            );

    }

    catch (error) {

        console.error(
            "Risk distribution error:",
            error
        );

    }
}


// ============================================================
// INTEGRITY TREND
// ============================================================

async function loadIntegrityTrend() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/integrity-trend",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const canvas =
            document.getElementById(
                "trendChart"
            );


        if (!canvas) {

            return;

        }


        if (
            window.trendChartInstance
        ) {

            window.trendChartInstance.destroy();

        }


        window.trendChartInstance =
            new Chart(
                canvas,
                {

                    type: "line",

                    data: {

                        labels:
                            result.labels,

                        datasets: [

                            {

                                label:
                                    "Integrity Score",

                                data:
                                    result.values,

                                tension:
                                    0.3,

                                fill:
                                    false

                            }

                        ]

                    },

                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        scales: {

                            y: {

                                beginAtZero: true,

                                max: 100

                            }

                        }

                    }

                }
            );

    }

    catch (error) {

        console.error(
            "Integrity trend error:",
            error
        );

    }
}


// ============================================================
// LIVE EXAMS
// ============================================================

async function loadLiveExams() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/live-exams",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const table =
            document.getElementById(
                "liveExamTable"
            );


        if (!table) {

            return;

        }


        table.innerHTML = "";


        const exams =
            result.exams || [];


        if (exams.length === 0) {

            table.innerHTML = `
                <tr>
                    <td colspan="5">
                        No examinations are running.
                    </td>
                </tr>
            `;

            return;

        }


        exams.forEach(
            function (exam) {

                table.innerHTML += `

                    <tr>

                        <td>
                            ${escapeHtml(
                                exam.title ||
                                exam.examName ||
                                "Examination"
                            )}
                        </td>

                        <td>
                            <span class="badge success">
                                Running
                            </span>
                        </td>

                        <td>
                            ${exam.candidates ?? 0}
                        </td>

                        <td>
                            ${exam.violations ?? 0}
                        </td>

                        <td>
                            ${exam.progress ?? 0}%
                        </td>

                    </tr>

                `;

            }
        );

    }

    catch (error) {

        console.error(
            "Live exams error:",
            error
        );

    }
}


// ============================================================
// RECENT ACTIVITY
// ============================================================

async function loadRecentActivity() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/activity",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const container =
            document.getElementById(
                "recentActivity"
            );


        if (!container) {

            return;

        }


        container.innerHTML = "";


        const activities =
            result.activities || [];


        if (activities.length === 0) {

            container.innerHTML =
                "<p>No recent activity.</p>";

            return;

        }


        activities.forEach(
            function (activity) {

                container.innerHTML += `

                    <div class="activity-item">

                        <div class="activity-icon">

                            <i class="fas fa-circle"></i>

                        </div>

                        <div class="activity-details">

                            <h4>
                                ${escapeHtml(
                                    activity.title ||
                                    activity.type ||
                                    "Activity"
                                )}
                            </h4>

                            <p>
                                ${escapeHtml(
                                    activity.description ||
                                    activity.message ||
                                    ""
                                )}
                            </p>

                            <span>
                                ${escapeHtml(
                                    activity.time || ""
                                )}
                            </span>

                        </div>

                    </div>

                `;

            }
        );

    }

    catch (error) {

        console.error(
            "Recent activity error:",
            error
        );

    }
}
function closeSupportModal(){

    document.getElementById("supportModal")
        .classList.remove("show");

    currentSupportTicket=null;

}


// ============================================================
// UPCOMING EXAMS
// ============================================================



async function loadUpcomingExams() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/upcoming-exams",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const container =
            document.getElementById(
                "upcomingExamContainer"
            );


        if (!container) {

            return;

        }


        container.innerHTML = "";


        const exams =
            result.exams || [];


        if (exams.length === 0) {

            container.innerHTML =
                "<p>No upcoming examinations.</p>";

            return;

        }


        exams.forEach(
            function (exam) {

                container.innerHTML += `

                    <div class="exam-card">

                        <h4>
                            ${escapeHtml(
                                exam.title
                            )}
                        </h4>

                        <p>
                            ${escapeHtml(
                                exam.topic || ""
                            )}
                        </p>

                        <div class="exam-footer">

                            <span>
                                ${escapeHtml(
                                    exam.start_time || ""
                                )}
                            </span>

                            <span>
                                ${exam.total_questions ?? 0}
                                Questions
                            </span>

                        </div>

                    </div>

                `;

            }
        );

    }

    catch (error) {

        console.error(
            "Upcoming exams error:",
            error
        );

    }
}


// ============================================================
// CANDIDATES
// ============================================================

async function loadCandidates() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/candidates",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const tbody =
            document.getElementById(
                "candidateTableBody"
            );


        if (!tbody) {

            return;

        }


        tbody.innerHTML = "";


        const candidates =
            result.candidates || [];


        if (candidates.length === 0) {

            tbody.innerHTML = `

                <tr>

                    <td colspan="5">
                        No candidates found.
                    </td>

                </tr>

            `;

            return;

        }


        candidates.forEach(
            function (candidate) {

                tbody.innerHTML += `

                    <tr>

                        <td>
                            ${candidate.id}
                        </td>

                        <td>
                            ${escapeHtml(
                                candidate.name
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                candidate.email || ""
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                candidate.createdAt || ""
                            )}
                        </td>

                        <td>
                            Registered
                        </td>

                    </tr>

                `;

            }
        );

    }

    catch (error) {

        console.error(
            "Candidates error:",
            error
        );

    }
}


// ============================================================
// LIVE MONITORING
// ============================================================

async function loadLiveMonitoring() {

    try {

        const response =
            await fetch(
                "/admin/api/live_monitoring",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const container =
            document.getElementById(
                "liveMonitoringContainer"
            );


        if (!container) {

            return;

        }


        container.innerHTML = "";


        const sessions =
            result.sessions || [];


        if (sessions.length === 0) {

            container.innerHTML =
                "<p>No candidates are currently online.</p>";

            return;

        }


        sessions.forEach(
            function (item) {

                let statusClass =
                    "online";


                if (
                    item.status ===
                    "Warning"
                ) {

                    statusClass =
                        "warning";

                }


                if (
                    item.status ===
                    "Violation"
                ) {

                    statusClass =
                        "danger";

                }


                container.innerHTML += `

                    <div class="live-user">

                        <div>

                            <h4>
                                ${escapeHtml(
                                    item.name
                                )}
                            </h4>

                            <p>
                                ${escapeHtml(
                                    item.exam
                                )}
                            </p>

                        </div>

                        <span class="${statusClass}">
                            ${escapeHtml(
                                item.status
                            )}
                        </span>

                    </div>

                `;

            }
        );

    }

    catch (error) {

        console.error(
            "Live monitoring error:",
            error
        );

    }
}


// ============================================================
// LIVE ALERTS
// ============================================================

async function loadLiveAlerts() {

    try {

        const response =
            await fetch(
                "/admin/api/dashboard/alerts",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const container =
            document.getElementById(
                "liveAlerts"
            );


        if (!container) {

            return;

        }


        container.innerHTML = "";


        const alerts =
            result.alerts || [];


        if (alerts.length === 0) {

            container.innerHTML =
                "<p>No live alerts.</p>";

            return;

        }


        alerts.forEach(
            function (alert) {

                container.innerHTML += `

                    <div class="alert-item">

                        <strong>
                            ${escapeHtml(
                                alert.candidate
                            )}
                        </strong>

                        <p>
                            ${escapeHtml(
                                alert.violation
                            )}
                        </p>

                        <small>
                            ${escapeHtml(
                                alert.time || ""
                            )}
                        </small>

                    </div>

                `;

            }
        );

    }

    catch (error) {

        console.error(
            "Live alerts error:",
            error
        );

    }
}


// ============================================================
// VIOLATIONS
// ============================================================

async function loadViolations() {

    try {

        const response =
            await fetch(
                "/admin/api/violations",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const container =
            document.getElementById(
                "violationContainer"
            );


        if (!container) {

            return;

        }


        container.innerHTML = "";


        const violations =
            result.violations || [];


        violations.forEach(
            function (item) {

                container.innerHTML += `

                    <div class="violation-card">

                        <div class="violation-left">

                            <h4>
                                ${escapeHtml(
                                    item.candidate
                                )}
                            </h4>

                            <p>
                                ${escapeHtml(
                                    item.exam
                                )}
                            </p>

                            <small>
                                ${escapeHtml(
                                    item.time || ""
                                )}
                            </small>

                        </div>

                        <div class="violation-right">

                            <span class="badge danger">
                                ${escapeHtml(
                                    item.type
                                )}
                            </span>

                            ${
                                item.image
                                ?
                                `
                                <button
                                    class="viewEvidenceBtn"
                                    data-image="${escapeHtml(
                                        item.image
                                    )}">
                                    View Evidence
                                </button>
                                `
                                :
                                ""
                            }

                        </div>

                    </div>

                `;

            }
        );


        attachEvidenceEvents();

    }

    catch (error) {

        console.error(
            "Violations error:",
            error
        );

    }
}


// ============================================================
// EVIDENCE
// ============================================================

function attachEvidenceEvents() {

    document
        .querySelectorAll(
            ".viewEvidenceBtn"
        )
        .forEach(
            function (button) {

                button.addEventListener(
                    "click",
                    function () {

                        const image =
                            this.dataset.image;


                        if (!image) {

                            alert(
                                "Evidence not available."
                            );

                            return;

                        }


                        window.open(
                            image,
                            "_blank"
                        );

                    }
                );

            }
        );

}


// ============================================================
// AI REPORTS
// ============================================================

async function loadReports() {

    try {

        const response =
            await fetch(
                "/admin/api/reports",
                {
                    credentials: "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const result =
            await response.json();


        if (!result.success) {

            return;

        }


        const container =
            document.getElementById(
                "reportContainer"
            );


        if (!container) {

            return;

        }


        container.innerHTML = "";


        const reports =
            result.reports || [];


        reports.forEach(
            function (report) {

                container.innerHTML += `

                    <div class="report-card">

                        <h4>
                            ${escapeHtml(
                                report.title
                            )}
                        </h4>

                        <p>
                            ${escapeHtml(
                                report.description
                            )}
                        </p>

                    </div>

                `;

            }
        );

    }

    catch (error) {

        console.error(
            "Reports error:",
            error
        );

    }
}





// ============================================================
// LOGOUT
// ============================================================

function initializeLogout() {

    const logoutButton =
        document.getElementById(
            "logoutBtn"
        );


    if (!logoutButton) {

        return;

    }


    logoutButton.addEventListener(
        "click",
        async function (event) {

            event.preventDefault();


            const confirmed =
                confirm(
                    "Do you want to logout?"
                );


            if (!confirmed) {

                return;

            }


            try {

                const response =
                    await fetch(
                        "/api/admin/logout",
                        {
                            credentials:
                                "same-origin"
                        }
                    );


                if (
                    response.ok
                ) {

                    window.location.href =
                        "/admin/login";

                }

                else {

                    alert(
                        "Unable to logout."
                    );

                }

            }

            catch (error) {

                console.error(
                    "Logout error:",
                    error
                );

                alert(
                    "Unable to logout."
                );

            }

        }
    );

}


// ============================================================
// SIDEBAR
// ============================================================

function initializeSidebar() {

    const toggle =
        document.getElementById(
            "toggleSidebar"
        );


    const sidebar =
        document.querySelector(
            ".sidebar"
        );


    if (
        toggle &&
        sidebar
    ) {

        toggle.addEventListener(
            "click",
            function () {

                sidebar.classList.toggle(
                    "collapsed"
                );

            }
        );

    }

}


// ============================================================
// SEARCH
// ============================================================

function initializeSearch() {

    const input =
        document.getElementById(
            "candidateSearch"
        );


    if (!input) {

        return;

    }


    input.addEventListener(
        "input",
        function () {

            const keyword =
                this.value
                    .toLowerCase()
                    .trim();


            const rows =
                document.querySelectorAll(
                    "#candidateTableBody tr"
                );


            rows.forEach(
                function (row) {

                    const text =
                        row.innerText
                            .toLowerCase();


                    row.style.display =
                        text.includes(
                            keyword
                        )
                        ? ""
                        : "none";

                }
            );

        }
    );

}


// ============================================================
// RISK FILTER
// ============================================================

function initializeRiskFilter() {

    const filter =
        document.getElementById(
            "riskFilter"
        );


    if (!filter) {

        return;

    }


    filter.addEventListener(
        "change",
        function () {

            const value =
                this.value
                    .toLowerCase();


            const rows =
                document.querySelectorAll(
                    "#candidateTableBody tr"
                );


            rows.forEach(
                function (row) {

                    if (
                        value ===
                        "all"
                    ) {

                        row.style.display =
                            "";

                        return;

                    }


                    const text =
                        row.innerText
                            .toLowerCase();


                    row.style.display =
                        text.includes(
                            value
                        )
                        ? ""
                        : "none";

                }
            );

        }
    );

}


// ============================================================
// REFRESH BUTTON
// ============================================================

function initializeRefreshButton() {

    const button =
        document.getElementById(
            "refreshDashboard"
        );


    if (!button) {

        return;

    }


    button.addEventListener(
        "click",
        function () {

            loadAllDashboardData();

            rotateRefreshIcon();

        }
    );

}


// ============================================================
// REFRESH ICON
// ============================================================

function rotateRefreshIcon() {

    const icon =
        document.getElementById(
            "refreshIcon"
        );


    if (!icon) {

        return;

    }


    icon.classList.add(
        "rotate"
    );


    setTimeout(
        function () {

            icon.classList.remove(
                "rotate"
            );

        },
        1000
    );

}


// ============================================================
// CURRENT DATE
// ============================================================

function updateCurrentDate() {

    const element =
        document.getElementById(
            "currentDate"
        );


    if (!element) {

        return;

    }


    element.textContent =
        new Date().toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );

}


// ============================================================
// CURRENT TIME
// ============================================================

function updateCurrentTime() {

    const element =
        document.getElementById(
            "currentTime"
        );


    if (!element) {

        return;

    }


    element.textContent =
        new Date().toLocaleTimeString(
            "en-IN"
        );

}


// ============================================================
// CARD VALUE
// ============================================================

function setCardValue(
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


    element.textContent =
        value;

}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(value);


    return div.innerHTML;

}


// ============================================================
// END
// ============================================================