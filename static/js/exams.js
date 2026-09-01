document.addEventListener("DOMContentLoaded", function () {
    const startButtons = document.querySelectorAll(".start-btn");
    const modalOverlay = document.getElementById("startExamModalOverlay");
    const modalBody = document.getElementById("startExamModalBody");
    const cancelBtn = document.getElementById("cancelStartExamBtn");
    const confirmBtn = document.getElementById("confirmStartExamBtn");

    let pendingExamLink = null;

    function openStartExamModal(examTitle, examLink) {
        pendingExamLink = examLink;
        modalBody.textContent = `Do you want to start "${examTitle}" now?`;
        modalOverlay.hidden = false;
    }

    function closeStartExamModal() {
        modalOverlay.hidden = true;
        pendingExamLink = null;
    }

    // ===============================
    // START EXAM BUTTON
    // ===============================
    startButtons.forEach(button => {
        button.addEventListener("click", function (e) {
            e.preventDefault();

            const examCard = this.closest(".exam-card");
            const examTitle = examCard.querySelector("h3").textContent.trim();
            const examLink = this.getAttribute("href");

            openStartExamModal(examTitle, examLink);
        });
    });

    if (cancelBtn) {
        cancelBtn.addEventListener("click", closeStartExamModal);
    }

    if (confirmBtn) {
        confirmBtn.addEventListener("click", function () {
            if (pendingExamLink) {
                window.location.href = pendingExamLink;
            }
        });
    }

    if (modalOverlay) {
        modalOverlay.addEventListener("click", (e) => {
            if (e.target === modalOverlay) closeStartExamModal();
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && !modalOverlay.hidden) closeStartExamModal();
        });
    }
});
