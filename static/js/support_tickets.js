// ==========================================
// Invigilator Support Tickets
// Online Exam Monitoring Platform
// (Milestone 5 - support ticket backend port)
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    const ticketsList = document.getElementById("tickets-list");
    const statusFilter = document.getElementById("status-filter");
    const countSummary = document.getElementById("ticket-count-summary");

    async function fetchJSON(url, options) {
        const resp = await fetch(url, options);
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok) {
            throw new Error(data.message || `Request to ${url} failed with status ${resp.status}`);
        }
        return data;
    }

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

    function renderEmpty(message) {
        ticketsList.innerHTML = `<p class="invig-empty-row">${message}</p>`;
    }

    function renderTickets(tickets) {
        if (!tickets || tickets.length === 0) {
            renderEmpty("No support tickets match this filter.");
            countSummary.textContent = "";
            return;
        }

        countSummary.textContent = `${tickets.length} ticket${tickets.length === 1 ? "" : "s"}`;
        ticketsList.innerHTML = "";

        tickets.forEach(ticket => {
            const card = document.createElement("div");
            card.className = "ticket-card";
            card.dataset.ticketId = ticket.id;

            card.innerHTML = `
                <div class="ticket-card-top">
                    <div>
                        <div class="ticket-card-candidate">${ticket.candidate_name || ("Candidate #" + ticket.candidate_id)} &middot; ${ticket.issue_type}</div>
                        <div class="ticket-card-meta">Priority: ${ticket.priority} &middot; Submitted ${formatTime(ticket.created_at)}</div>
                    </div>
                    <span class="ticket-status-badge ${statusClass(ticket.status)}">${ticket.status}</span>
                </div>
                <p class="ticket-card-message">${ticket.message}</p>
                ${ticket.response ? `<div class="ticket-card-response-existing"><strong>Current response:</strong> ${ticket.response}</div>` : ""}
                <div class="ticket-card-actions">
                    <select class="ticket-status-select">
                        <option value="Open" ${ticket.status === "Open" ? "selected" : ""}>Open</option>
                        <option value="In Progress" ${ticket.status === "In Progress" ? "selected" : ""}>In Progress</option>
                        <option value="Resolved" ${ticket.status === "Resolved" ? "selected" : ""}>Resolved</option>
                    </select>
                    <input type="text" class="ticket-card-response-input" placeholder="Write a response...">
                    <button type="button" class="ticket-card-save-btn">Save</button>
                    <span class="ticket-card-save-status"></span>
                </div>
            `;

            const saveBtn = card.querySelector(".ticket-card-save-btn");
            const statusSelect = card.querySelector(".ticket-status-select");
            const responseInput = card.querySelector(".ticket-card-response-input");
            const saveStatus = card.querySelector(".ticket-card-save-status");

            saveBtn.addEventListener("click", async () => {
                const payload = { status: statusSelect.value };
                const responseText = responseInput.value.trim();
                if (responseText) payload.response = responseText;

                saveBtn.disabled = true;
                saveStatus.textContent = "Saving...";

                try {
                    await fetchJSON(`/api/support/${ticket.id}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    saveStatus.textContent = "Saved.";
                    loadTickets();
                } catch (err) {
                    saveStatus.textContent = "Could not save. Try again.";
                } finally {
                    saveBtn.disabled = false;
                }
            });

            ticketsList.appendChild(card);
        });
    }

    async function loadTickets() {
        renderEmpty("Loading tickets...");
        try {
            const status = statusFilter.value;
            const url = status ? `/api/support?status=${encodeURIComponent(status)}` : "/api/support";
            const data = await fetchJSON(url);
            renderTickets(data.tickets);
        } catch (err) {
            renderEmpty("Could not load support tickets. Please try again.");
        }
    }

    statusFilter.addEventListener("change", loadTickets);

    loadTickets();
});
