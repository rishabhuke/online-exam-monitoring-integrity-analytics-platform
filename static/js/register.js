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
// START CAMERA
// ==============================

startCameraBtn.addEventListener("click", async () => {

    try {

        stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });

        video.srcObject = stream;

    } catch (error) {

        alert("Unable to access webcam.\nPlease allow camera permission.");

        console.error(error);

    }

});

// ==============================
// CAPTURE PHOTO
// ==============================

captureBtn.addEventListener("click", () => {

    if (!stream) {

        alert("Please start the camera first.");

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

// ==============================
// FORM SUBMIT
// ==============================

registerForm.addEventListener("submit", async function (e) {

    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    // Validation

    if (name.length < 3) {
        alert("Name must contain at least 3 characters.");
        return;
    }

    if (!validateEmail(email)) {
        alert("Enter a valid email address.");
        return;
    }

    if (password.length < 8) {
        alert("Password must contain at least 8 characters.");
        return;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return;
    }

    if (capturedImage === "") {
        alert("Please capture your photograph.");
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

            alert(result.message);

            registerForm.reset();

            photoPreview.src = "";
            photoPreview.style.display = "none";

            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }

            window.location.href = "/login";

        } else {

            alert(result.message);

        }

    } catch (error) {

        console.error(error);

        alert("Unable to connect to the server.");

    }

});