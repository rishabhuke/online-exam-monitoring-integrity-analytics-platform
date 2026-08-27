// ==========================================
// Candidate Dashboard
// Online Exam Monitoring Platform
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    // -------------------------------
    // Greeting based on time
    // -------------------------------

    const hour = new Date().getHours();
    const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

    const candidateName = localStorage.getItem("candidateName") || "Candidate";

    const nameElement = document.getElementById("candidateName");

    if (nameElement) {
        nameElement.textContent = `${greeting}, ${candidateName}`;
    }

    // -------------------------------
    // Session Status
    // -------------------------------

    console.log("Candidate Session Active");

});
