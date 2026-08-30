document.addEventListener("DOMContentLoaded", function () {
    // ==========================================================
    // Timer - reads the real exam duration from the server-rendered
    // data attribute instead of a hardcoded 60 minutes.
    // ==========================================================
    const timerBox = document.querySelector(".exam-timer-box");
    const durationMinutes = timerBox ? parseInt(timerBox.dataset.durationMinutes, 10) || 60 : 60;
    let totalSeconds = durationMinutes * 60;
    const timerElement = document.getElementById("examTimer");
    const monitoringWarning = document.getElementById("monitoringWarning");

    function showWarning(message) {
        if (!monitoringWarning) return;
        monitoringWarning.textContent = message;
        monitoringWarning.hidden = false;
    }

    function updateTimer() {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        timerElement.textContent =
            `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

        timerElement.classList.toggle("timer-critical", totalSeconds <= 300 && totalSeconds > 0);

        if (totalSeconds > 0) {
            totalSeconds--;
        } else {
            clearInterval(timerInterval);
            showWarning("Time is up. Your exam is being submitted automatically.");
            submitExam(true);
        }
    }

    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);

    // ==========================================================
    // Question loading, rendering, navigation
    // ==========================================================

    const paletteGrid = document.getElementById("paletteGrid");
    const paletteProgress = document.getElementById("paletteProgress");
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
            btn.type = "button";
            const isAnswered = Boolean(answers[q.id]);
            if (i === currentIndex) btn.classList.add("active");
            if (isAnswered) btn.classList.add("answered");
            btn.textContent = i + 1;
            btn.setAttribute(
                "aria-label",
                `Question ${i + 1}${isAnswered ? ", answered" : ", not answered yet"}${i === currentIndex ? ", current question" : ""}`
            );
            btn.addEventListener("click", () => {
                currentIndex = i;
                renderQuestion();
            });
            paletteGrid.appendChild(btn);
        });

        if (paletteProgress) {
            const answeredCount = Object.keys(answers).length;
            paletteProgress.textContent = `${answeredCount} of ${questions.length} answered`;
        }
    }

    function renderQuestion() {
        const q = questions[currentIndex];
        if (!q) return;

        questionNumber.textContent = `Question ${currentIndex + 1} of ${questions.length}`;
        questionText.textContent = q.question;

        optionsList.innerHTML = "";
        [["a", q.option_a], ["b", q.option_b], ["c", q.option_c], ["d", q.option_d]].forEach(([letter, text]) => {
            const label = document.createElement("label");
            label.className = "option-item";
            if (answers[q.id] === letter) label.classList.add("selected");

            const input = document.createElement("input");
            input.type = "radio";
            input.name = `q${q.id}`;
            input.value = letter;
            if (answers[q.id] === letter) input.checked = true;
            input.addEventListener("change", () => {
                answers[q.id] = letter;
                optionsList.querySelectorAll(".option-item").forEach(el => el.classList.remove("selected"));
                label.classList.add("selected");
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
                questionText.textContent = "This exam has no questions configured yet. Please contact your invigilator.";
                submitBtn.disabled = true;
                submitBtn.textContent = "No Questions to Submit";
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                return;
            }
            renderQuestion();
        } catch (err) {
            questionNumber.textContent = "Failed to load exam";
            questionText.textContent = "Please refresh the page. If this keeps happening, contact your invigilator.";
            submitBtn.disabled = true;
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

    // ==========================================================
    // Submission - confirmation modal (no window.confirm/alert)
    // ==========================================================

    const submitBtn = document.getElementById("submitBtn");
    const modalOverlay = document.getElementById("submitModalOverlay");
    const modalBody = document.getElementById("submitModalBody");
    const continueExamBtn = document.getElementById("continueExamBtn");
    const confirmSubmitBtn = document.getElementById("confirmSubmitBtn");

    function openSubmitModal() {
        if (monitoringWarning) monitoringWarning.hidden = true;
        const unanswered = questions.length - Object.keys(answers).length;
        const answered = questions.length - unanswered;
        if (unanswered > 0) {
            const noun = unanswered === 1 ? "question" : "questions";
            modalBody.textContent =
                `You have answered ${answered} of ${questions.length} questions. ${unanswered} ${noun} remain unanswered. Are you sure you want to submit?`;
        } else {
            modalBody.textContent = `You have answered all ${questions.length} questions. Submit your exam now?`;
        }
        modalOverlay.hidden = false;
    }

    function closeSubmitModal() {
        modalOverlay.hidden = true;
    }

    if (continueExamBtn) {
        continueExamBtn.addEventListener("click", closeSubmitModal);
    }
    if (modalOverlay) {
        modalOverlay.addEventListener("click", (e) => {
            if (e.target === modalOverlay) closeSubmitModal();
        });
    }
    if (confirmSubmitBtn) {
        confirmSubmitBtn.addEventListener("click", () => {
            closeSubmitModal();
            submitExam(false);
        });
    }

    async function submitExam(auto) {
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

            if (resp.status === 401) {
                showWarning("Your session has expired. Please log in again to submit your exam.");
                submitBtn.disabled = false;
                return;
            }

            if (!resp.ok) {
                throw new Error(`Submit failed with status ${resp.status}`);
            }

            window.location.href = "/results";
        } catch (err) {
            submitBtn.disabled = false;
            showWarning("Failed to submit exam. Please check your connection and try again.");
            console.error(err);
        }
    }

    submitBtn.addEventListener("click", () => {
        if (questions.length === 0) return;
        openSubmitModal();
    });

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
    //
    // Reuses the same getUserMedia + canvas snapshot pattern as
    // webcam.js (registration capture), but runs continuously in the
    // background for the duration of the exam session instead of a
    // single manual capture. Expects a global `EXAM_ID` and the
    // hidden <video id="face-monitor-video"> / <canvas id="face-monitor-canvas">
    // pair added to exam_window.html.
    //
    // Also requests audio in the same getUserMedia call so the visible
    // monitoring status bar's "Microphone" indicator reflects a real
    // permission/stream state rather than a hardcoded label. The audio
    // track itself isn't processed further yet.
    // ==========================================================
    const FACE_CHECK_INTERVAL_MS = 4000; // send one frame roughly every 4s

    const monitorVideo = document.getElementById("face-monitor-video");
    const monitorCanvas = document.getElementById("face-monitor-canvas");

    const statusCamera = document.getElementById("statusCamera");
    const statusMic = document.getElementById("statusMic");
    const statusIntegrity = document.getElementById("statusIntegrity");

    function setStatus(el, state, text) {
        if (!el) return;
        el.classList.remove("status-ok", "status-error");
        if (state) el.classList.add(state);
        const textEl = el.querySelector(".status-text");
        if (textEl) textEl.textContent = text;
    }

    const webcamPreviewFallback = document.getElementById("webcamPreviewFallback");

    function showPreviewFallback(text) {
        if (monitorVideo) monitorVideo.style.display = "none";
        if (webcamPreviewFallback) {
            webcamPreviewFallback.hidden = false;
            const span = webcamPreviewFallback.querySelector("span");
            if (span && text) span.textContent = text;
        }
    }

    if (monitorVideo && monitorCanvas && typeof EXAM_ID !== "undefined") {
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .then((stream) => {
                monitorVideo.srcObject = stream;

                const hasVideo = stream.getVideoTracks().length > 0;
                const hasAudio = stream.getAudioTracks().length > 0;

                setStatus(statusCamera, hasVideo ? "status-ok" : "status-error", hasVideo ? "Connected" : "Unavailable");
                setStatus(statusMic, hasAudio ? "status-ok" : "status-error", hasAudio ? "Active" : "Unavailable");
                setStatus(statusIntegrity, "status-ok", "Active");

                if (!hasVideo) {
                    showPreviewFallback("Camera unavailable");
                    showWarning("Your camera isn't available. Monitoring may be incomplete - contact your invigilator if this continues.");
                } else {
                    setInterval(captureAndSendFrame, FACE_CHECK_INTERVAL_MS);
                }
            })
            .catch((err) => {
                console.error("Face monitoring: could not access webcam/microphone.", err);
                setStatus(statusCamera, "status-error", "Permission denied");
                setStatus(statusMic, "status-error", "Permission denied");
                setStatus(statusIntegrity, "status-error", "Limited");
                showPreviewFallback("Camera blocked");
                showWarning("Camera/microphone access was blocked. Please allow access and reload this page, or contact your invigilator.");
            });

        window.addEventListener("beforeunload", () => {
            // Safety net: flush any still-open absence interval if the
            // candidate closes/navigates away without hitting Submit.
            navigator.sendBeacon(`/api/exam/${EXAM_ID}/end_monitoring`);
        });
    } else {
        console.warn("Face monitoring: required elements or EXAM_ID missing, skipping.");
        setStatus(statusCamera, "status-error", "Unavailable");
        setStatus(statusMic, "status-error", "Unavailable");
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
