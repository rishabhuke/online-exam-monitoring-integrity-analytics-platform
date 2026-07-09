document.addEventListener("DOMContentLoaded", function () {
    const startButtons = document.querySelectorAll(".start-btn");
    const disabledButtons = document.querySelectorAll(".disabled-btn");

    // ===============================
    // START EXAM BUTTON
    // ===============================
    startButtons.forEach(button => {
        button.addEventListener("click", function (e) {
            e.preventDefault();

            const examCard = this.closest(".exam-card");
            const examTitle = examCard.querySelector("h3").textContent.trim();
            const examLink = this.getAttribute("href");

            const confirmStart = confirm(`Do you want to start "${examTitle}" now?`);

            if (confirmStart) {
                window.location.href = examLink;
            }
        });
    });

    // ===============================
    // NOT AVAILABLE BUTTON
    // ===============================
    disabledButtons.forEach(button => {
        button.addEventListener("click", function () {
            const examCard = this.closest(".exam-card");
            const examTitle = examCard.querySelector("h3").textContent.trim();

            alert(`"${examTitle}" is not available yet. Please wait until the scheduled date/time.`);
        });
    });
});