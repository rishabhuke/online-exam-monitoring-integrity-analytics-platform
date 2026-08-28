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
            submitExam(true);
        }
    }

    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);

    // ==========================================
    // Question loading, rendering, navigation
    // ==========================================

    const paletteGrid = document.getElementById("paletteGrid");
    const questionNumber = document.getElementById("questionNumber");
    const questionText = document.getElementById("questionText");
    const optionsList = document.getElementById("optionsList");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");

    let questions = [];
    let currentIndex = 0;
    const answers = {};

    async function fetchJSON(url) {
        const resp = await fetch(url, {
            headers: { "Accept": "application/json" }
        });
        if (!resp.ok) {
            throw new Error(`Request to ${url} failed with status ${resp.status}`);
        }
        return resp.json();
    }

    function renderPalette() {
        paletteGrid.innerHTML = "";
        questions.forEach((q, i) => {
            const btn = document.createElement("button");
            btn.className = "palette-btn";
            if (i === currentIndex) btn.classList.add("active");
            if (answers[q.id]) btn.classList.add("answered");
            btn.textContent = i + 1;
            btn.addEventListener("click", () => {
                currentIndex = i;
                renderQuestion();
            });
            paletteGrid.appendChild(btn);
        });
    }

    function renderQuestion() {
        const q = questions[currentIndex];
        if (!q) return;

        questionNumber.textContent = `Question ${currentIndex + 1}`;
        questionText.textContent = q.question;

        optionsList.innerHTML = "";
        [["a", q.option_a], ["b", q.option_b], ["c", q.option_c], ["d", q.option_d]].forEach(([letter, text]) => {
            const label = document.createElement("label");
            label.className = "option-item";

            const input = document.createElement("input");
            input.type = "radio";
            input.name = `q${q.id}`;
            input.value = letter;
            if (answers[q.id] === letter) input.checked = true;
            input.addEventListener("change", () => {
                answers[q.id] = letter;
                renderPalette();
            });

            const span = document.createElement("span");
            span.textContent = text;

            label.appendChild(input);
            label.appendChild(span);
            optionsList.appendChild(label);
        });

        prevBtn.disabled = currentIndex === 0;
        nextBtn.disabled = currentIndex === questions.length - 1;

        renderPalette();
    }

    async function loadExam() {
        try {
            questions = await fetchJSON(`/api/exam/${EXAM_ID}`);
            if (questions.length === 0) {
                questionNumber.textContent = "No questions available";
                questionText.textContent = "";
                return;
            }
            renderQuestion();
        } catch (err) {
            questionNumber.textContent = "Failed to load exam";
            console.error(err);
        }
    }

    prevBtn.addEventListener("click", () => {
        if (currentIndex > 0) {
            currentIndex--;
            renderQuestion();
        }
    });

    nextBtn.addEventListener("click", () => {
        if (currentIndex < questions.length - 1) {
            currentIndex++;
            renderQuestion();
        }
    });

    async function submitExam(auto) {
        const unanswered = questions.length - Object.keys(answers).length;

        if (!auto && unanswered > 0) {
            const noun = unanswered === 1 ? "question" : "questions";
            const proceed = confirm(`You have ${unanswered} unanswered ${noun}. Do you want to submit?`);
            if (!proceed) return;
        }

        const payload = {
            exam_id: EXAM_ID,
            answers: Object.entries(answers).map(([questionId, selectedOption]) => ({
                question_id: Number(questionId),
                selected_option: selectedOption
            }))
        };

        submitBtn.disabled = true;

        try {
            const resp = await fetch("/submit_exam", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) {
                throw new Error(`Submit failed with status ${resp.status}`);
            }

            window.location.href = "/results";
        } catch (err) {
            submitBtn.disabled = false;
            alert("Failed to submit exam. Please try again.");
            console.error(err);
        }
    }

    submitBtn.addEventListener("click", () => submitExam(false));

    loadExam();
// ==========================================================
// Browser monitoring (Milestone 3)
// Capture tab switches and focus loss.
// ==========================================================
let tabSwitchDetected = false;

function logBrowserEvent(eventType, details) {
    if (typeof EXAM_ID === "undefined") {
        console.warn("Browser monitoring: EXAM_ID missing.");
        return;
    }

    fetch("/api/monitoring/browser-event", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            exam_id: EXAM_ID,
            event_type: eventType,
            details: details,
            event_timestamp: new Date().toISOString()
        })
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.status !== "success") {
                console.error("Browser event logging failed:", data);
            }
        })
        .catch((error) => {
            console.error("Browser event request failed:", error);
        });
}

document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") {
        tabSwitchDetected = true;

        logBrowserEvent(
            "TAB_SWITCH",
            "Exam page became hidden."
        );
    } else {
        tabSwitchDetected = false;
    }
});

window.addEventListener("blur", function () {
    if (!tabSwitchDetected && document.visibilityState === "visible") {
        logBrowserEvent(
            "FOCUS_LOSS",
            "Exam window lost focus."
        );
    }
});

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
