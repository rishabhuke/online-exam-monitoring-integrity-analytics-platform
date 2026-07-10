// ==========================================
// Candidate Dashboard
// Online Exam Monitoring Platform
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    // -------------------------------
    // Greeting based on time
    // -------------------------------

    

    const candidateName = localStorage.getItem("candidateName") || "Candidate";

    const nameElement = document.getElementById("candidateName");

    if (nameElement) {
        nameElement.textContent = `${greeting}, ${candidateName}`;
    }

    // -------------------------------
    // Session Status
    // -------------------------------

    console.log("Candidate Session Active");

    // -------------------------------
    // Card Click Animation
    // -------------------------------

    const cards = document.querySelectorAll(".service-card");

    cards.forEach(card => {

        card.addEventListener("click", () => {

            const title = card.querySelector("h3").innerText;

            alert(title + " module will be available after backend integration.");

        });

    });

});