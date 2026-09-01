// ==========================================
// Help & Support
// Online Exam Monitoring Platform
// (Milestone 5 - support ticket backend port)
// ==========================================

document.addEventListener("DOMContentLoaded", function () {
    // -------------------------------
    // FAQ accordion
    // -------------------------------
    const faqItems = document.querySelectorAll(".faq-item");

    faqItems.forEach(item => {
        const questionBtn = item.querySelector(".faq-question");

        questionBtn.addEventListener("click", function () {
            item.classList.toggle("active");
        });
    });

    // -------------------------------
    // Contact Admin -> scroll to the issue form (candidate-only section;
    // for a logged-out visitor there's no form on the page, so this is a
    // no-op there rather than erroring).
    // -------------------------------
    const contactAdminBtn = document.getElementById("contactAdminBtn");
    if (contactAdminBtn) {
        contactAdminBtn.addEventListener("click", function () {
            const issueForm = document.getElementById("issueForm");
            if (issueForm) {
                issueForm.scrollIntoView({ behavior: "smooth", block: "start" });
                const firstField = document.getElementById("issueType");
                if (firstField) firstField.focus();
            } else {
                window.location.href = "/help-support#issue-report";
            }
        });
    }

    // -------------------------------
    // Issue form submission -> POST /api/support (real ticket, not alert())
    // -------------------------------
    const issueForm = document.getElementById("issueForm");
    const issueFormStatus = document.getElementById("issueFormStatus");

    function setFormStatus(message, isError) {
        if (!issueFormStatus) return;
        issueFormStatus.textContent = message;
        issueFormStatus.classList.toggle("issue-form-status-error", !!isError);
        issueFormStatus.classList.toggle("issue-form-status-success", !isError && !!message);
    }

    if (issueForm) {
        issueForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            const contactName = document.getElementById("issueName").value.trim();
            const contactEmail = document.getElementById("issueEmail").value.trim();
            const issueType = document.getElementById("issueType").value.trim();
            const priority = document.getElementById("issuePriority").value.trim();
            const message = document.getElementById("issueMessage").value.trim();

            if (!issueType || !priority || !message) {
                setFormStatus("Please fill in issue type, priority, and description.", true);
                return;
            }

            const submitBtn = issueForm.querySelector(".submit-btn");
            if (submitBtn) submitBtn.disabled = true;
            setFormStatus("Submitting...", false);

            try {
                const resp = await fetch("/api/support", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        issue_type: issueType,
                        priority: priority,
                        message: message,
                        contact_name: contactName,
                        contact_email: contactEmail,
                    }),
                });

                const data = await resp.json();

                if (!resp.ok || data.status !== "success") {
                    setFormStatus(data.message || "Could not submit your issue. Please try again.", true);
                    return;
                }

                setFormStatus("Your issue has been submitted. Track it below under My Support Tickets.", false);
                issueForm.reset();
                document.getElementById("issueName").value = contactName;
                document.getElementById("issueEmail").value = contactEmail;
                loadMyTickets();
            } catch (err) {
                setFormStatus("Could not reach the server. Please try again.", true);
            } finally {
                if (submitBtn) submitBtn.disabled = false;
            }
        });
    }

    // -------------------------------
    // My Support Tickets list -> GET /api/support (candidate session
    // scopes this to the caller's own tickets server-side, see
    // routes/support.py::list_tickets())
    // -------------------------------
    const myTicketsList = document.getElementById("myTicketsList");

    function formatTime(iso) {
        if (!iso) return "—";
        const d = new Date(iso.replace(" ", "T"));
        if (isNaN(d.getTime())) return iso;
        return d.toLocaleString();
    }

    function statusClass(status) {
        if (status === "Resolved") return "ticket-status-resolved";
        if (status === "In Progress") return "ticket-status-progress";
        return "ticket-status-open";
    }

    function renderTickets(tickets) {
        if (!myTicketsList) return;

        if (!tickets || tickets.length === 0) {
            myTicketsList.innerHTML = '<p class="my-tickets-empty">You haven\'t submitted any support tickets yet.</p>';
            return;
        }

        myTicketsList.innerHTML = "";
        tickets.forEach(ticket => {
            const item = document.createElement("div");
            item.className = "my-ticket-item";
            item.innerHTML = `
                <div class="my-ticket-top">
                    <span class="my-ticket-type">${ticket.issue_type}</span>
                    <span class="ticket-status-badge ${statusClass(ticket.status)}">${ticket.status}</span>
                </div>
                <p class="my-ticket-message">${ticket.message}</p>
                <p class="my-ticket-meta">Priority: ${ticket.priority} &middot; Submitted ${formatTime(ticket.created_at)}</p>
                ${ticket.response ? `<div class="my-ticket-response"><strong>Invigilator response:</strong> ${ticket.response}</div>` : ""}
            `;
            myTicketsList.appendChild(item);
        });
    }

    async function loadMyTickets() {
        if (!myTicketsList) return;
        try {
            const resp = await fetch("/api/support", { headers: { "Accept": "application/json" } });
            if (!resp.ok) throw new Error("request failed");
            const data = await resp.json();
            renderTickets(data.tickets);
        } catch (err) {
            myTicketsList.innerHTML = '<p class="my-tickets-empty">Could not load your tickets right now.</p>';
        }
    }

    if (myTicketsList) {
        loadMyTickets();
    }
});
