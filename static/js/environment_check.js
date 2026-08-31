document.addEventListener("DOMContentLoaded", function () {
    const checks = ["camera", "microphone", "internet", "browser", "fullscreen", "face"];
    const results = {}; // checkName -> "ready" | "blocked"

    const video = document.getElementById("env-video");
    const canvas = document.getElementById("env-canvas");
    let cameraStream = null; // kept alive only while Camera/Face checks need it

    function setStatus(checkName, state, label) {
        const statusEl = document.getElementById(`${checkName}Status`);
        if (!statusEl) return;
        statusEl.classList.remove("pending", "checking", "ready", "blocked");
        statusEl.classList.add(state);
        statusEl.textContent = label;
    }

    function updateOverallReadiness() {
        const readinessScore = document.getElementById("readinessScore");
        const overallBadge = document.getElementById("overallBadge");
        const readyCount = Object.values(results).filter((s) => s === "ready").length;

        readinessScore.textContent = `${readyCount} / ${checks.length} Ready`;

        if (readyCount === checks.length) {
            overallBadge.textContent = "All Checks Completed";
            overallBadge.classList.remove("pending-badge");
            overallBadge.classList.add("ready-badge");
        } else {
            overallBadge.textContent = "Pending Checks";
            overallBadge.classList.remove("ready-badge");
            overallBadge.classList.add("pending-badge");
        }
        updateStartButton();
    }

    function updateStartButton() {
        const section = document.getElementById("startExamSection");
        const btn = document.getElementById("startExamBtn");
        const helpText = document.getElementById("startExamHelpText");
        if (!section || !btn || !helpText) return;

        const examId = section.dataset.examId;
        const allReady = checks.every((c) => results[c] === "ready");

        if (!examId) {
            helpText.textContent = "No exam selected. Open this check from your exam list.";
            btn.classList.add("disabled-btn");
            btn.setAttribute("aria-disabled", "true");
            btn.removeAttribute("href");
            return;
        }

        if (allReady) {
            helpText.textContent = "All checks passed. You may start the examination.";
            btn.classList.remove("disabled-btn");
            btn.removeAttribute("aria-disabled");
            btn.setAttribute("href", `/start_exam/${examId}`);
        } else {
            helpText.textContent = "Complete all required checks above before starting.";
            btn.classList.add("disabled-btn");
            btn.setAttribute("aria-disabled", "true");
            btn.removeAttribute("href");
        }
    }

    async function ensureCameraStream() {
        if (cameraStream) return cameraStream;
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = cameraStream;
        await video.play().catch(() => {});
        return cameraStream;
    }

    function stopCameraStream() {
        if (!cameraStream) return;
        cameraStream.getTracks().forEach((t) => t.stop());
        cameraStream = null;
    }

    async function checkCamera() {
        setStatus("camera", "checking", "Checking...");
        try {
            await ensureCameraStream();
            results.camera = "ready";
            setStatus("camera", "ready", "Ready");
        } catch (e) {
            results.camera = "blocked";
            setStatus("camera", "blocked", "Blocked");
        }
        updateOverallReadiness();
    }

    async function checkMicrophone() {
        setStatus("microphone", "checking", "Checking...");
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach((t) => t.stop());
            results.microphone = "ready";
            setStatus("microphone", "ready", "Ready");
        } catch (e) {
            results.microphone = "blocked";
            setStatus("microphone", "blocked", "Blocked");
        }
        updateOverallReadiness();
    }

    async function checkInternet() {
        setStatus("internet", "checking", "Checking...");
        if (!navigator.onLine) {
            results.internet = "blocked";
            setStatus("internet", "blocked", "Offline");
            updateOverallReadiness();
            return;
        }
        try {
            const resp = await fetch("/", { method: "HEAD", cache: "no-store" });
            if (resp.ok) {
                results.internet = "ready";
                setStatus("internet", "ready", "Ready");
            } else {
                results.internet = "blocked";
                setStatus("internet", "blocked", "Unstable");
            }
        } catch (e) {
            results.internet = "blocked";
            setStatus("internet", "blocked", "Offline");
        }
        updateOverallReadiness();
    }

    function checkBrowser() {
        setStatus("browser", "checking", "Checking...");
        const hasMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
        const hasFullscreen = !!(document.documentElement.requestFullscreen);
        const hasFetch = typeof fetch === "function";

        if (hasMedia && hasFullscreen && hasFetch) {
            results.browser = "ready";
            setStatus("browser", "ready", "Ready");
        } else {
            results.browser = "blocked";
            setStatus("browser", "blocked", "Unsupported");
        }
        updateOverallReadiness();
    }

    async function checkFullscreen() {
        setStatus("fullscreen", "checking", "Checking...");
        if (!document.documentElement.requestFullscreen) {
            results.fullscreen = "blocked";
            setStatus("fullscreen", "blocked", "Unavailable");
            updateOverallReadiness();
            return;
        }
        try {
            await document.documentElement.requestFullscreen();
            results.fullscreen = "ready";
            setStatus("fullscreen", "ready", "Ready");
            if (document.exitFullscreen) {
                await document.exitFullscreen().catch(() => {});
            }
        } catch (e) {
            results.fullscreen = "blocked";
            setStatus("fullscreen", "blocked", "Blocked");
        }
        updateOverallReadiness();
    }

    async function checkFace() {
        setStatus("face", "checking", "Checking...");
        try {
            await ensureCameraStream();
            // give the video element a moment to have a real frame
            await new Promise((resolve) => setTimeout(resolve, 300));

            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const frame = canvas.toDataURL("image/png");

            const resp = await fetch("/api/exam/environment/face_check", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ frame }),
            });
            const data = await resp.json();

            if (data.status === "success" && data.face_present) {
                results.face = "ready";
                setStatus("face", "ready", "Ready");
            } else {
                results.face = "blocked";
                setStatus("face", "blocked", "Not Detected");
            }
        } catch (e) {
            results.face = "blocked";
            setStatus("face", "blocked", "Failed");
        }
        updateOverallReadiness();
    }

    const runners = {
        camera: checkCamera,
        microphone: checkMicrophone,
        internet: checkInternet,
        browser: checkBrowser,
        fullscreen: checkFullscreen,
        face: checkFace,
    };

    window.runCheck = function (checkName) {
        const fn = runners[checkName];
        if (fn) fn();
    };

    const runAllBtn = document.getElementById("runAllChecksBtn");
    if (runAllBtn) {
        runAllBtn.addEventListener("click", function () {
            checks.forEach((check, index) => {
                setTimeout(() => {
                    runners[check]();
                }, index * 350);
            });
        });
    }

    window.addEventListener("beforeunload", stopCameraStream);

    updateOverallReadiness();
});
