document.addEventListener("DOMContentLoaded", function () {

    loadFAQs();

    loadSupportTickets();


    const issueForm =
        document.getElementById("issueForm");


    if (issueForm) {

        issueForm.addEventListener(
            "submit",
            submitSupportRequest
        );

    }

});


async function loadFAQs() {

    const container =
        document.getElementById("faqContainer");

    if (!container) {
        return;
    }

    try {

        const response =
            await fetch("/api/faqs");

        const data =
            await response.json();

        if (!data.success) {

            container.innerHTML =
                `<div class="empty-state">
                    Unable to load FAQs.
                </div>`;

            return;
        }


        if (!data.faqs || data.faqs.length === 0) {

            container.innerHTML =
                `<div class="empty-state">
                    No FAQs available.
                </div>`;

            return;
        }


        container.innerHTML = "";


        data.faqs.forEach(function (faq) {

            const item =
                document.createElement("div");

            item.className =
                "faq-item";


            item.innerHTML = `

                <button
                    type="button"
                    class="faq-question"
                >

                    <span>
                        ${escapeHtml(faq.question)}
                    </span>

                    <i class="fa-solid fa-chevron-down"></i>

                </button>


                <div class="faq-answer">

                    <p>
                        ${escapeHtml(faq.answer)}
                    </p>

                </div>

            `;


            const button =
                item.querySelector(".faq-question");


            button.addEventListener(
                "click",
                function () {

                    item.classList.toggle("active");

                }
            );


            container.appendChild(item);

        });

    } catch (error) {

        console.error(
            "FAQ loading error:",
            error
        );

        container.innerHTML =
            `<div class="empty-state">
                Unable to load FAQs.
            </div>`;
    }
}


async function submitSupportRequest(event) {

    event.preventDefault();


    const issueType =
        document.getElementById(
            "issueType"
        ).value.trim();


    const priority =
        document.getElementById(
            "issuePriority"
        ).value.trim();


    const subject =
        document.getElementById(
            "issueSubject"
        ).value.trim();


    const message =
        document.getElementById(
            "issueMessage"
        ).value.trim();


    if (
        !issueType ||
        !priority ||
        !subject ||
        !message
    ) {

        alert(
            "Please complete all required fields."
        );

        return;
    }


    const submitButton =
        document.querySelector(
            ".support-submit-btn"
        );


    submitButton.disabled = true;

    submitButton.innerHTML =
        `<i class="fa-solid fa-spinner fa-spin"></i>
         Submitting...`;


    try {

        const response =
            await fetch(
                "/api/candidate/support",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        issue_type:
                            issueType,

                        priority:
                            priority,

                        subject:
                            subject,

                        message:
                            message

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            alert(
                data.message ||
                "Unable to submit support request."
            );

            return;
        }


        alert(
            `Support request submitted successfully.\n\nTicket ID: #${data.ticket_id}`
        );


        document
            .getElementById("issueForm")
            .reset();


        loadSupportTickets();

    } catch (error) {

        console.error(
            "Support submission error:",
            error
        );

        alert(
            "Unable to connect to the support service."
        );

    } finally {

        submitButton.disabled = false;

        submitButton.innerHTML =
            `<i class="fa-solid fa-paper-plane"></i>
             Submit Request`;

    }
}


async function loadSupportTickets() {

    const container =
        document.getElementById(
            "ticketContainer"
        );


    if (!container) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/candidate/support"
            );


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            container.innerHTML =
                `<div class="empty-state">
                    Unable to load support requests.
                </div>`;

            return;
        }


        if (
            !data.tickets ||
            data.tickets.length === 0
        ) {

            container.innerHTML =
                `<div class="empty-state">

                    <i class="fa-solid fa-ticket"></i>

                    <p>
                        You have not submitted any
                        support requests yet.
                    </p>

                </div>`;

            return;
        }


        container.innerHTML = "";


        data.tickets.forEach(function (ticket) {

            const item =
                document.createElement("div");


            item.className =
                "ticket-item";


            item.innerHTML = `

                <div class="ticket-main">

                    <div class="ticket-title-row">

                        <h3>
                            ${escapeHtml(
                                ticket.subject
                            )}
                        </h3>

                        <span class="
                            ticket-status
                            status-${ticket.status
                                .toLowerCase()
                                .replace(/\s+/g, "-")}
                        ">

                            ${escapeHtml(
                                ticket.status
                            )}

                        </span>

                    </div>


                    <p class="ticket-message">

                        ${escapeHtml(
                            ticket.message
                        )}

                    </p>


                    <div class="ticket-meta">

                        <span>
                            <i class="fa-solid fa-hashtag"></i>
                            ${ticket.id}
                        </span>

                        <span>
                            <i class="fa-solid fa-tag"></i>
                            ${escapeHtml(
                                ticket.issue_type
                            )}
                        </span>

                        <span>
                            <i class="fa-solid fa-flag"></i>
                            ${escapeHtml(
                                ticket.priority
                            )}
                        </span>

                        <span>
                            <i class="fa-solid fa-calendar"></i>
                            ${escapeHtml(
                                ticket.created_at
                            )}
                        </span>

                    </div>


                    ${
                        ticket.admin_response
                        ?
                        `
                        <div class="admin-response">

                            <strong>
                                <i class="fa-solid fa-user-shield"></i>
                                Admin Response
                            </strong>

                            <p>
                                ${escapeHtml(
                                    ticket.admin_response
                                )}
                            </p>

                            ${
                                ticket.admin_name
                                ?
                                `<small>
                                    Responded by
                                    ${escapeHtml(
                                        ticket.admin_name
                                    )}
                                </small>`
                                :
                                ""
                            }

                        </div>
                        `
                        :
                        `
                        <div class="waiting-response">

                            <i class="fa-solid fa-hourglass-half"></i>

                            Waiting for administrator response.

                        </div>
                        `
                    }

                </div>

            `;


            container.appendChild(item);

        });

    } catch (error) {

        console.error(
            "Ticket loading error:",
            error
        );

        container.innerHTML =
            `<div class="empty-state">
                Unable to load support requests.
            </div>`;
    }
}


function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}