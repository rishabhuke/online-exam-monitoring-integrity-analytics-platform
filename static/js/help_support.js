document.addEventListener("DOMContentLoaded", function () {
    // FAQ accordion
    const faqItems = document.querySelectorAll(".faq-item");

    faqItems.forEach(item => {
        const questionBtn = item.querySelector(".faq-question");

        questionBtn.addEventListener("click", function () {
            item.classList.toggle("active");
        });
    });

    // Issue form submission
    const issueForm = document.getElementById("issueForm");

    if (issueForm) {
        issueForm.addEventListener("submit", function (e) {
            e.preventDefault();

            const name = document.getElementById("issueName").value.trim();
            const email = document.getElementById("issueEmail").value.trim();
            const issueType = document.getElementById("issueType").value.trim();
            const priority = document.getElementById("issuePriority").value.trim();
            const message = document.getElementById("issueMessage").value.trim();

            if (!name || !email || !issueType || !priority || !message) {
                alert("Please fill in all fields before submitting your issue.");
                return;
            }

            alert("Your issue has been submitted successfully. Support will review it soon.");
            issueForm.reset();
        });
    }
});