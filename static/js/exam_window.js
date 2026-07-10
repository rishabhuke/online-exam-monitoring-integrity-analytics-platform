document.addEventListener("DOMContentLoaded", function () {
    let totalSeconds = 60 * 60; // 60 minutes
    const timerElement = document.getElementById("examTimer");

    function updateTimer() {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        timerElement.textContent =
            `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

        if (totalSeconds > 0) {
            totalSeconds--;
        } else {
            clearInterval(timerInterval);
            alert("Time is up! Your exam will be submitted.");
        }
    }

    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);
});