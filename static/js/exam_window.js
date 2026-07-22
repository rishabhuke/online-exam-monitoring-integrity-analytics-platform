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

    // ==========================================================
    // Face presence monitoring capture loop (Milestone 2)
    // Owner: Rishabh - functional integration; Prashanthi, feel free
    // to adjust placement/styling of any visible status indicator.
    //
    // Reuses the same getUserMedia + canvas snapshot pattern as
    // webcam.js (registration capture), but runs continuously in the
    // background for the duration of the exam session instead of a
    // single manual capture. Expects a global `EXAM_ID` and the
    // hidden <video id="face-monitor-video"> / <canvas id="face-monitor-canvas">
    // pair added to exam_window.html.
    // ==========================================================
    const FACE_CHECK_INTERVAL_MS = 4000; // send one frame roughly every 4s

    const monitorVideo = document.getElementById("face-monitor-video");
    const monitorCanvas = document.getElementById("face-monitor-canvas");

    if (monitorVideo && monitorCanvas && typeof EXAM_ID !== "undefined") {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then((stream) => {
                monitorVideo.srcObject = stream;
                setInterval(captureAndSendFrame, FACE_CHECK_INTERVAL_MS);
            })
            .catch((err) => {
                console.error("Face monitoring: could not access webcam.", err);
            });

        window.addEventListener("beforeunload", () => {
            // Safety net: flush any still-open absence interval if the
            // candidate closes/navigates away without hitting Submit.
            navigator.sendBeacon(`/api/exam/${EXAM_ID}/end_monitoring`);
        });
    } else {
        console.warn("Face monitoring: required elements or EXAM_ID missing, skipping.");
    }

    function captureAndSendFrame() {
        if (!monitorVideo.videoWidth) return; // stream not ready yet

        const context = monitorCanvas.getContext("2d");
        monitorCanvas.width = monitorVideo.videoWidth;
        monitorCanvas.height = monitorVideo.videoHeight;
        context.drawImage(monitorVideo, 0, 0, monitorCanvas.width, monitorCanvas.height);
        const frame = monitorCanvas.toDataURL("image/png");

        fetch(`/api/exam/${EXAM_ID}/face_check`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ frame }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.status === "success" && !data.face_present) {
                    console.warn(
                        "Face monitoring: face not detected, ongoing absence:",
                        data.ongoing_absence_seconds, "s"
                    );
                }
            })
            .catch((err) => console.error("Face monitoring: request failed.", err));
    }
});
