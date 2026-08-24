const checks = {
    camera: false,
    microphone: false,
    internet: false,
    browser: false,
    fullscreen: false,
    face: false
};

let mediaStream = null;
let selectedExam = null;


document.addEventListener("DOMContentLoaded", async function () {

    await loadEnvironmentData();

    document
        .getElementById("runAllChecksBtn")
        .addEventListener(
            "click",
            runAllChecks
        );

    document
        .getElementById("startExamBtn")
        .addEventListener(
            "click",
            startExam
        );

    updateReadiness();

});



async function loadEnvironmentData() {

    try {

        const response = await fetch(
            "/api/candidate/environment",
            {
                method: "GET",
                credentials: "same-origin"
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {

            showGlobalError(
                data.message ||
                "Unable to load environment information."
            );

            return;
        }


        const candidate =
            data.candidate;

        document.getElementById(
            "candidateName"
        ).textContent =
            candidate.name || "Candidate";


        document.getElementById(
            "candidateEmail"
        ).textContent =
            candidate.email || "";


        /*
         * Select the first currently
         * available exam.
         */

        const availableExam =
            data.exams.find(
                exam =>
                    exam.status === "Available"
            );


        if (availableExam) {

            selectedExam =
                availableExam;

            displayExam(
                availableExam
            );

        } else {

            document.getElementById(
                "examTitle"
            ).textContent =
                "No exam available";

            document.getElementById(
                "startExamMessage"
            ).textContent =
                "There is currently no available examination.";

        }


        document.getElementById(
            "environmentDescription"
        ).textContent =
            "Verify your system before starting the examination. " +
            "Camera, microphone, internet, browser, fullscreen, " +
            "and face visibility must be ready.";


    } catch (error) {

        console.error(
            "Environment loading error:",
            error
        );

        showGlobalError(
            "Unable to connect to the server."
        );

    }

}



function displayExam(exam) {

    document.getElementById(
        "examTitle"
    ).textContent =
        exam.title;


    document.getElementById(
        "examDuration"
    ).textContent =
        `${exam.duration} minutes`;


    document.getElementById(
        "examQuestions"
    ).textContent =
        exam.total_questions;

}



async function runCheck(type) {

    setStatus(
        type,
        "checking"
    );


    try {

        let result = false;


        switch (type) {

            case "camera":
                result =
                    await checkCamera();
                break;


            case "microphone":
                result =
                    await checkMicrophone();
                break;


            case "internet":
                result =
                    await checkInternet();
                break;


            case "browser":
                result =
                    checkBrowser();
                break;


            case "fullscreen":
                result =
                    await checkFullscreen();
                break;


            case "face":
                result =
                    await checkFace();
                break;

        }


        checks[type] = result;

        setStatus(
            type,
            result
                ? "passed"
                : "failed"
        );


        updateReadiness();


    } catch (error) {

        console.error(
            `${type} check failed:`,
            error
        );

        checks[type] = false;

        setStatus(
            type,
            "failed"
        );

        updateReadiness();

    }

}



async function checkCamera() {

    try {

        if (!navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia) {

            return false;
        }


        mediaStream =
            await navigator.mediaDevices.getUserMedia({
                video: true
            });


        const video =
            document.getElementById(
                "cameraPreview"
            );


        video.srcObject =
            mediaStream;


        await video.play();


        document.getElementById(
            "previewStatus"
        ).textContent =
            "Camera active";


        document.getElementById(
            "cameraMessage"
        ).textContent =
            "Camera is working. Keep your face inside the guide.";


        return true;


    } catch (error) {

        document.getElementById(
            "previewStatus"
        ).textContent =
            "Camera unavailable";


        document.getElementById(
            "cameraMessage"
        ).textContent =
            "Camera permission was denied or no camera was detected.";


        return false;

    }

}



async function checkMicrophone() {

    try {

        if (!navigator.mediaDevices ||
            !navigator.mediaDevices.getUserMedia) {

            return false;
        }


        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });


        stream
            .getTracks()
            .forEach(
                track => track.stop()
            );


        return true;


    } catch (error) {

        return false;

    }

}



async function checkInternet() {

    if (!navigator.onLine) {
        return false;
    }


    try {

        const start =
            performance.now();


        const response =
            await fetch(
                "/api/candidate/environment",
                {
                    method: "GET",
                    cache: "no-store",
                    credentials: "same-origin"
                }
            );


        const end =
            performance.now();


        const latency =
            end - start;


        /*
         * Server must respond successfully.
         */

        if (!response.ok) {
            return false;
        }


        /*
         * Very high latency is treated
         * as unstable for readiness.
         */

        return latency < 3000;


    } catch (error) {

        return false;

    }

}



function checkBrowser() {

    const supported =
        !!(
            navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia &&
            document.fullscreenEnabled &&
            window.fetch &&
            window.Promise &&
            window.localStorage
        );


    const browser =
        navigator.userAgent;


    const isSupportedBrowser =
        browser.includes("Chrome") ||
        browser.includes("Edg");


    return (
        supported &&
        isSupportedBrowser
    );

}



async function checkFullscreen() {

    /*
     * Browser cannot enter fullscreen
     * without user interaction.
     *
     * Therefore the button itself triggers
     * this function.
     */

    try {

        if (!document.fullscreenEnabled) {
            return false;
        }


        await document.documentElement.requestFullscreen();


        return !!document.fullscreenElement;


    } catch (error) {

        return false;

    }

}



async function checkFace() {

    /*
     * Basic environment-level face visibility.
     *
     * We first verify that the camera is active
     * and that video frames are available.
     *
     * Actual AI face detection should be performed
     * by your monitoring system during the exam.
     */

    const video =
        document.getElementById(
            "cameraPreview"
        );


    if (!video.srcObject) {

        const cameraReady =
            await checkCamera();

        if (!cameraReady) {
            return false;
        }

    }


    if (
        video.readyState <
        HTMLMediaElement.HAVE_CURRENT_DATA
    ) {

        return false;

    }


    /*
     * Check that video has usable dimensions.
     */

    if (
        video.videoWidth <= 0 ||
        video.videoHeight <= 0
    ) {

        return false;

    }


    /*
     * Take a frame from the camera.
     */

    const canvas =
        document.createElement(
            "canvas"
        );


    canvas.width =
        video.videoWidth;


    canvas.height =
        video.videoHeight;


    const context =
        canvas.getContext("2d");


    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );


    const imageData =
        context.getImageData(
            0,
            0,
            canvas.width,
            canvas.height
        );


    /*
     * Basic brightness check.
     *
     * This does NOT claim that a face exists.
     * It only prevents obviously unusable
     * dark camera frames.
     */

    let brightness = 0;

    const data =
        imageData.data;


    for (
        let i = 0;
        i < data.length;
        i += 4
    ) {

        brightness +=
            (
                data[i] +
                data[i + 1] +
                data[i + 2]
            ) / 3;

    }


    brightness /=
        data.length / 4;


    if (brightness < 20) {

        document.getElementById(
            "cameraMessage"
        ).textContent =
            "Camera image is too dark. Improve your lighting.";

        return false;

    }


    document.getElementById(
        "cameraMessage"
    ).textContent =
        "Camera image is visible. Make sure your face is clearly inside the guide.";


    return true;

}



function setStatus(type, status) {

    const element =
        document.getElementById(
            `${type}Status`
        );


    if (!element) {
        return;
    }


    element.classList.remove(
        "pending",
        "checking",
        "passed",
        "failed"
    );


    element.classList.add(
        status
    );


    const labels = {

        pending: "Pending",

        checking: "Checking...",

        passed: "Ready",

        failed: "Failed"

    };


    element.textContent =
        labels[status] ||
        status;

}



function updateReadiness() {

    const total =
        Object.keys(checks).length;


    const ready =
        Object.values(checks)
            .filter(Boolean)
            .length;


    document.getElementById(
        "readinessScore"
    ).textContent =
        `${ready} / ${total} Ready`;


    const badge =
        document.getElementById(
            "overallBadge"
        );


    const startButton =
        document.getElementById(
            "startExamBtn"
        );


    if (ready === total) {

        badge.textContent =
            "Ready to Start";


        badge.className =
            "readiness-badge ready-badge";


        document.getElementById(
            "readinessDescription"
        ).textContent =
            "All required environment checks have passed.";


        document.getElementById(
            "startExamMessage"
        ).textContent =
            "Your system is ready. You can start the examination.";


        startButton.disabled =
            !selectedExam;


    } else {

        badge.textContent =
            "Checks Pending";


        badge.className =
            "readiness-badge pending-badge";


        document.getElementById(
            "readinessDescription"
        ).textContent =
            `Complete ${total - ready} remaining check(s) before starting.`;


        startButton.disabled =
            true;

    }

}



async function runAllChecks() {

    const button =
        document.getElementById(
            "runAllChecksBtn"
        );


    button.disabled =
        true;


    button.innerHTML =
        `<i class="fa-solid fa-spinner fa-spin"></i>
         Running Checks...`;


    const types = [
        "camera",
        "microphone",
        "internet",
        "browser",
        "fullscreen",
        "face"
    ];


    for (const type of types) {

        await runCheck(type);

    }


    button.disabled =
        false;


    button.innerHTML =
        `<i class="fa-solid fa-rotate"></i>
         Run All Checks`;

}



async function startExam() {

    if (!selectedExam) {

        alert(
            "No examination is currently available."
        );

        return;

    }


    const allPassed =
        Object.values(checks)
            .every(Boolean);


    if (!allPassed) {

        alert(
            "Please complete all environment checks first."
        );

        return;

    }


    /*
     * Stop preview before entering exam.
     */

    stopCamera();


    /*
     * Navigate to your existing exam page.
     */

    window.location.href =
        `/candidate/exam/${selectedExam.id}`;

}



function stopCamera() {

    if (!mediaStream) {
        return;
    }


    mediaStream
        .getTracks()
        .forEach(
            track => track.stop()
        );


    mediaStream = null;

}



function showGlobalError(message) {

    const description =
        document.getElementById(
            "environmentDescription"
        );


    description.textContent =
        message;


    description.style.color =
        "#fecaca";

}