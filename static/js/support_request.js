// ============================================================
// EXAMGUARD AI
// ADMIN SUPPORT REQUESTS
// ============================================================

let supportTickets = [];

let currentSupportTicket = null;


// ============================================================
// DOM READY
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    initializeSidebar();

    initializeSupportSearch();

    initializeStatusFilter();

    initializeRefresh();

    initializeSupportModal();

    loadSupportTickets();

});


// ============================================================
// LOAD SUPPORT TICKETS
// ============================================================

async function loadSupportTickets() {

    const container =
        document.getElementById("supportTicketsList");

    if (container) {

        container.innerHTML = `
            <div class="loading-state">

                <div class="loading-spinner"></div>

                <span>
                    Loading support requests...
                </span>

            </div>
        `;

    }

    try {

        const response =
            await fetch(
                "/admin/api/support",
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "Support API:",
            data
        );


        if (!data.success) {

            throw new Error(
                data.message ||
                "Unable to load support requests."
            );

        }


        supportTickets =
            Array.isArray(data.tickets)
                ? data.tickets
                : [];


        updateSupportSummary(
            supportTickets
        );


        renderSupportTickets(
            supportTickets
        );

    }

    catch (error) {

        console.error(
            "Support tickets error:",
            error
        );


        if (container) {

            container.innerHTML = `

                <div class="empty-state">

                    <i
                        class="fa-solid fa-triangle-exclamation"
                        style="
                            font-size:28px;
                            color:#f87171;
                        "
                    ></i>

                    <span>
                        Unable to load support requests.
                    </span>

                </div>

            `;

        }

    }

}


// ============================================================
// UPDATE SUMMARY
// ============================================================

function updateSupportSummary(tickets) {

    tickets =
        Array.isArray(tickets)
            ? tickets
            : [];


    const normalized =
        tickets.map(ticket =>
            String(
                ticket.status || "Open"
            )
            .trim()
            .toLowerCase()
        );


    const openCount =
        normalized.filter(
            status => status === "open"
        ).length;


    const pendingCount =
        normalized.filter(
            status => status === "in progress"
        ).length;


    const resolvedCount =
        normalized.filter(
            status => status === "resolved"
        ).length;


    const totalCount =
        tickets.length;


    setText(
        "openSupportCount",
        openCount
    );


    setText(
        "pendingSupportCount",
        pendingCount
    );


    setText(
        "resolvedSupportCount",
        resolvedCount
    );


    setText(
        "totalSupportCount",
        totalCount
    );

}


// ============================================================
// RENDER TICKETS
// ============================================================

function renderSupportTickets(tickets) {

    const container =
        document.getElementById(
            "supportTicketsList"
        );


    if (!container) {

        console.error(
            "supportTicketsList element not found"
        );

        return;

    }


    tickets =
        Array.isArray(tickets)
            ? tickets
            : [];


    const searchValue =
        document.getElementById(
            "supportSearch"
        )?.value
            ?.toLowerCase()
            .trim() || "";


    const statusFilter =
        document.getElementById(
            "supportStatusFilter"
        )?.value
            ?.toLowerCase()
            .trim() || "all";


    // ------------------------------------------------------------
    // FILTER
    // ------------------------------------------------------------

    let filteredTickets =
        tickets.filter(ticket => {

            const candidateName =
                String(
                    ticket.candidate_name || ""
                ).toLowerCase();


            const candidateEmail =
                String(
                    ticket.candidate_email || ""
                ).toLowerCase();


            const subject =
                String(
                    ticket.subject || ""
                ).toLowerCase();


            const message =
                String(
                    ticket.message || ""
                ).toLowerCase();


            const issueType =
                String(
                    ticket.issue_type || ""
                ).toLowerCase();


            const searchableText =
                `${candidateName} ${candidateEmail} ${subject} ${message} ${issueType}`;


            const matchesSearch =
                !searchValue ||
                searchableText.includes(
                    searchValue
                );


            const ticketStatus =
                String(
                    ticket.status || "Open"
                )
                .trim()
                .toLowerCase();


            const matchesStatus =
                statusFilter === "all" ||
                ticketStatus === statusFilter;


            return (
                matchesSearch &&
                matchesStatus
            );

        });


    container.innerHTML = "";


    // ------------------------------------------------------------
    // EMPTY
    // ------------------------------------------------------------

    if (
        filteredTickets.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">

                <div class="empty-icon">
                    <i class="fa-solid fa-inbox"></i>
                </div>

                <h3>
                    No support requests found
                </h3>

                <p>
                    There are no support requests
                    matching your current search
                    or filter.
                </p>

            </div>
        `;

        return;

    }


    // ------------------------------------------------------------
    // CARDS
    // ------------------------------------------------------------

    filteredTickets.forEach(ticket => {

        const card =
            document.createElement(
                "article"
            );


        card.className =
            "support-ticket";


        const status =
            String(
                ticket.status || "Open"
            ).trim();


        const normalizedStatus =
            status.toLowerCase();


        const statusClass =
            normalizedStatus
                .replace(/\s+/g, "-");


        const priority =
            String(
                ticket.priority || "Normal"
            ).trim();


        const priorityClass =
            priority
                .toLowerCase()
                .replace(/\s+/g, "-");


        const candidateName =
            ticket.candidate_name ||
            "Unknown Candidate";


        const email =
            ticket.candidate_email ||
            "No email available";


        const subject =
            ticket.subject ||
            "Support Request";


        const message =
            ticket.message ||
            "No message provided.";


        const issueType =
            ticket.issue_type ||
            "General";


        card.innerHTML = `

            <div class="support-ticket-header">

                <div class="ticket-user">

                    <div class="ticket-avatar">
                        <i class="fa-solid fa-user"></i>
                    </div>

                    <div class="ticket-user-info">

                        <h3>
                            ${escapeHtml(candidateName)}
                        </h3>

                        <div class="ticket-email">

                            <i class="fa-solid fa-envelope"></i>

                            <span>
                                ${escapeHtml(email)}
                            </span>

                        </div>

                    </div>

                </div>


                <span
                    class="ticket-status ${escapeHtml(statusClass)}">

                    <span class="status-dot"></span>

                    ${escapeHtml(status)}

                </span>

            </div>


            <div class="ticket-content">

                <div class="ticket-subject-row">

                    <span class="ticket-label">
                        Subject
                    </span>

                    <h4>
                        ${escapeHtml(subject)}
                    </h4>

                </div>


                <div class="ticket-message-section">

                    <span class="ticket-label">
                        Candidate Message
                    </span>

                    <p class="ticket-message">
                        ${escapeHtml(message)}
                    </p>

                </div>


                <div class="support-meta">

                    <span class="ticket-meta-item">

                        <i class="fa-solid fa-layer-group"></i>

                        ${escapeHtml(issueType)}

                    </span>


                    <span
                        class="ticket-meta-item ticket-priority ${escapeHtml(priorityClass)}">

                        <i class="fa-solid fa-flag"></i>

                        ${escapeHtml(priority)}

                    </span>

                </div>

            </div>


            <div class="support-actions">

                <button
                    type="button"
                    class="respond-btn">

                    <i class="fa-solid fa-reply"></i>

                    Respond

                </button>

            </div>

        `;


        const respondButton =
            card.querySelector(
                ".respond-btn"
            );


        respondButton?.addEventListener(
            "click",
            function () {

                openSupportModal(ticket);

            }
        );


        container.appendChild(card);

    });

}

// ============================================================
// CREATE TICKET CARD
// ============================================================

function createTicketCard(ticket) {

    const card =
        document.createElement("article");


    card.className =
        "support-ticket";


    const status =
        String(
            ticket.status || "Open"
        )
        .trim();


    const statusClass =
        status
            .toLowerCase()
            .replace(/\s+/g, "-");


    const priority =
        String(
            ticket.priority || "Normal"
        )
        .trim();


    const priorityClass =
        priority
            .toLowerCase();


    const candidateName =
        ticket.candidate_name ||
        "Unknown Candidate";


    const email =
        ticket.candidate_email ||
        "No email available";


    const subject =
        ticket.subject ||
        "Support Request";


    const message =
        ticket.message ||
        "No message provided.";


    const issueType =
        ticket.issue_type ||
        "General";


    card.innerHTML = `

        <div class="support-ticket-top">

            <div class="ticket-candidate">

                <h4>
                    ${escapeHtml(candidateName)}
                </h4>

                <div class="ticket-email">

                    <i class="fa-solid fa-envelope"></i>

                    <span>
                        ${escapeHtml(email)}
                    </span>

                </div>

            </div>


            <span class="ticket-status ${escapeHtml(statusClass)}">

                ${escapeHtml(status)}

            </span>

        </div>


        <h3 class="ticket-subject">

            ${escapeHtml(subject)}

        </h3>


        <p class="ticket-message">

            ${escapeHtml(message)}

        </p>


        <div class="support-meta">

            <span class="ticket-meta-item">

                <i class="fa-solid fa-layer-group"></i>

                ${escapeHtml(issueType)}

            </span>


            <span class="ticket-meta-item ticket-priority ${escapeHtml(priorityClass)}">

                <i class="fa-solid fa-flag"></i>

                ${escapeHtml(priority)}

            </span>

        </div>


        <div class="support-actions">

            <button
                type="button"
                class="respond-btn">

                <i class="fa-solid fa-reply"></i>

                Respond

            </button>

        </div>

    `;


    const respondButton =
        card.querySelector(
            ".respond-btn"
        );


    if (respondButton) {

        respondButton.addEventListener(
            "click",
            function () {

                openSupportModal(ticket);

            }
        );

    }


    return card;

}


// ============================================================
// OPEN MODAL
// ============================================================

function openSupportModal(ticket) {

    currentSupportTicket = ticket;

    setText(
        "modalCandidateName",
        ticket.candidate_name || "--"
    );

    setText(
        "modalCandidateEmail",
        ticket.candidate_email || "--"
    );

    setText(
        "modalIssueType",
        ticket.issue_type || "--"
    );

    setText(
        "modalPriority",
        ticket.priority || "--"
    );

    setText(
        "modalSubject",
        ticket.subject || "--"
    );


    const candidateMessage =
        document.getElementById(
            "modalCandidateMessage"
        );

    if (candidateMessage) {

        candidateMessage.value =
            ticket.message || "";

    }


    const adminResponse =
        document.getElementById(
            "modalAdminResponse"
        );

    if (adminResponse) {

        adminResponse.value =
            ticket.admin_response || "";

    }


    const statusSelect =
        document.getElementById(
            "modalTicketStatus"
        );

    if (statusSelect) {

        const currentStatus =
            String(
                ticket.status || "Open"
            ).trim();


        const validStatuses = [
            "Open",
            "In Progress",
            "Resolved",
            "Closed"
        ];


        if (
            validStatuses.includes(
                currentStatus
            )
        ) {

            statusSelect.value =
                currentStatus;

        } else {

            statusSelect.value =
                "Open";

        }

    }


    const modal =
        document.getElementById(
            "supportModal"
        );

    if (modal) {

        modal.classList.add("show");

        document.body.style.overflow =
            "hidden";

    }

}

// ============================================================
// CLOSE MODAL
// ============================================================

function closeSupportModal() {

    const modal =
        document.getElementById(
            "supportModal"
        );


    if (modal) {

        modal.classList.remove(
            "show"
        );

    }


    document.body.style.overflow =
        "";


    currentSupportTicket =
        null;

}


// ============================================================
// UPDATE SUPPORT TICKET
// ============================================================

async function updateSupportTicket() {

    if (!currentSupportTicket) {
        return;
    }


    const responseElement =
        document.getElementById(
            "modalAdminResponse"
        );


    const statusElement =
        document.getElementById(
            "modalTicketStatus"
        );


    const adminResponse =
        responseElement
            ? responseElement.value.trim()
            : "";


    const status =
        statusElement
            ? statusElement.value.trim()
            : "Open";


    const validStatuses = [
        "Open",
        "In Progress",
        "Resolved",
        "Closed"
    ];


    // ------------------------------------------------------------
    // VALIDATE BEFORE SENDING
    // ------------------------------------------------------------

    if (!validStatuses.includes(status)) {

        alert(
            "Invalid ticket status selected."
        );

        return;

    }


    const saveButton =
        document.getElementById(
            "saveSupportResponse"
        );


    if (saveButton) {

        saveButton.disabled = true;

        saveButton.innerHTML = `
            <i class="fa-solid fa-spinner fa-spin"></i>
            Saving...
        `;

    }


    try {

        const ticketId =
            currentSupportTicket.id;


        if (!ticketId) {

            throw new Error(
                "Support ticket ID is missing."
            );

        }


        const response =
            await fetch(
                `/admin/api/support/${ticketId}`,
                {
                    method: "PUT",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            status:
                                status,

                            admin_response:
                                adminResponse

                        })

                }
            );


        const data =
            await response.json();


        console.log(
            "Update Support Response:",
            data
        );


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.message ||
                "Unable to update support ticket."
            );

        }


        closeSupportModal();


        await loadSupportTickets();

    }


    catch (error) {

        console.error(
            "Update support ticket error:",
            error
        );


        alert(
            error.message ||
            "Unable to update support ticket."
        );

    }


    finally {

        if (saveButton) {

            saveButton.disabled =
                false;

            saveButton.innerHTML = `
                <i class="fa-solid fa-paper-plane"></i>
                Save Response
            `;

        }

    }

}


// ============================================================
// SEARCH
// ============================================================

function initializeSupportSearch() {

    const search =
        document.getElementById(
            "supportSearch"
        );


    if (!search) {

        return;

    }


    search.addEventListener(
        "input",
        function () {

            renderSupportTickets(
                supportTickets
            );

        }
    );

}


// ============================================================
// STATUS FILTER
// ============================================================

function initializeStatusFilter() {

    const filter =
        document.getElementById(
            "supportStatusFilter"
        );


    if (!filter) {

        return;

    }


    filter.addEventListener(
        "change",
        function () {

            renderSupportTickets(
                supportTickets
            );

        }
    );

}


// ============================================================
// REFRESH
// ============================================================

function initializeRefresh() {

    const button =
        document.getElementById(
            "refreshSupport"
        );


    if (!button) {

        return;

    }


    button.addEventListener(
        "click",
        async function () {

            const icon =
                document.getElementById(
                    "refreshSupportIcon"
                );


            if (icon) {

                icon.classList.add(
                    "rotate"
                );

            }


            await loadSupportTickets();


            setTimeout(
                function () {

                    if (icon) {

                        icon.classList.remove(
                            "rotate"
                        );

                    }

                },
                700
            );

        }
    );

}


// ============================================================
// MODAL EVENTS
// ============================================================

function initializeSupportModal() {

    const closeButton =
        document.getElementById(
            "closeSupportModal"
        );


    const cancelButton =
        document.getElementById(
            "cancelSupportModal"
        );


    const saveButton =
        document.getElementById(
            "saveSupportResponse"
        );


    const overlay =
        document.querySelector(
            ".support-modal-overlay"
        );


    closeButton?.addEventListener(
        "click",
        closeSupportModal
    );


    cancelButton?.addEventListener(
        "click",
        closeSupportModal
    );


    overlay?.addEventListener(
        "click",
        closeSupportModal
    );


    saveButton?.addEventListener(
        "click",
        updateSupportTicket
    );


    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape" &&
                currentSupportTicket
            ) {

                closeSupportModal();

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


    if (!toggle ||
        !sidebar) {

        return;

    }


    toggle.addEventListener(
        "click",
        function () {

            sidebar.classList.toggle(
                "collapsed"
            );

        }
    );

}


// ============================================================
// SET TEXT
// ============================================================

function setText(id, value) {

    const element =
        document.getElementById(id);


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