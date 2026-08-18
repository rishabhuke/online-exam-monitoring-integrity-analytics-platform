// ==============================
// VARIABLES
// ==============================

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const photoPreview = document.getElementById("photoPreview");

const startCameraBtn = document.getElementById("startCamera");
const captureBtn = document.getElementById("captureBtn");

const registerForm = document.getElementById("registerForm");

let stream = null;
let capturedImage = "";

// ==============================
// MESSAGE MODAL
// ==============================

function showMessage(title, message, success = true, callback = null) {

    const modal = document.getElementById("messageModal");
    const icon = document.getElementById("messageIcon");
    const titleText = document.getElementById("messageTitle");
    const messageText = document.getElementById("messageText");
    const button = document.getElementById("messageBtn");

    titleText.textContent = title;
    messageText.textContent = message;

    if (success) {

        icon.innerHTML = "✔";
        icon.className = "message-icon message-success";

    } else {

        icon.innerHTML = "✖";
        icon.className = "message-icon message-error";

    }

    modal.style.display = "flex";

    button.onclick = function () {

        modal.style.display = "none";

        if (callback) {

            callback();

        }

    };

}

// ==============================
// START CAMERA
// ==============================

startCameraBtn.addEventListener("click", async () => {

    try {

        stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });

        video.srcObject = stream;

    } catch (error) {

        console.error(error);

        showMessage(
            "Camera Error",
            "Unable to access webcam. Please allow camera permission.",
            false
        );

    }

});

// ==============================
// CAPTURE PHOTO
// ==============================

captureBtn.addEventListener("click", () => {

    if (!stream) {

        showMessage(
            "Camera Not Started",
            "Please start the camera first.",
            false
        );

        return;

    }

    const context = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    context.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    capturedImage = canvas.toDataURL("image/png");

    photoPreview.src = capturedImage;
    photoPreview.style.display = "block";

});

// ==============================
// SHOW / HIDE PASSWORD
// ==============================

function togglePassword(id, icon) {

    const input = document.getElementById(id);

    if (input.type === "password") {

        input.type = "text";

        icon.innerHTML = `<i class="fa-solid fa-eye-slash"></i>`;

    } else {

        input.type = "password";

        icon.innerHTML = `<i class="fa-solid fa-eye"></i>`;

    }

}

// ==============================
// EMAIL VALIDATION
// ==============================

function validateEmail(email) {

    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    return regex.test(email);

}

// ==============================
// FORM SUBMIT
// ==============================

registerForm.addEventListener("submit", async function (e) {

    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    // -------------------------
    // Validation
    // -------------------------

    if (name.length < 3) {

        showMessage(
            "Invalid Name",
            "Name must contain at least 3 characters.",
            false
        );

        return;

    }

    if (!validateEmail(email)) {

        showMessage(
            "Invalid Email",
            "Enter a valid email address.",
            false
        );

        return;

    }

    if (password.length < 8) {

        showMessage(
            "Invalid Password",
            "Password must contain at least 8 characters.",
            false
        );

        return;

    }

    if (password !== confirmPassword) {

        showMessage(
            "Password Mismatch",
            "Passwords do not match.",
            false
        );

        return;

    }

    if (capturedImage === "") {

        showMessage(
            "Photo Required",
            "Please capture your photograph.",
            false
        );

        return;

    }

    const candidate = {

        name: name,
        email: email,
        password: password,
        photo_data: capturedImage

    };

    try {

        const response = await fetch("/register", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(candidate)

        });

        const result = await response.json();

        if (response.ok) {

            showMessage(
                "Registration Successful",
                result.message,
                true,
                function () {

                    registerForm.reset();

                    photoPreview.src = "";
                    photoPreview.style.display = "none";

                    capturedImage = "";

                    if (stream) {

                        stream.getTracks().forEach(track => track.stop());

                        stream = null;

                    }

                    window.location.href = "/login";

                }
            );

        } else {

            showMessage(
                "Registration Failed",
                result.message,
                false
            );

        }

    } catch (error) {

        console.error(error);

        showMessage(
            "Connection Error",
            "Unable to connect to the server.",
            false
        );

    }

});