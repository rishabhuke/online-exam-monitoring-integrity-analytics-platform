/*
 * Candidate registration form handling.
 * Camera capture is owned entirely by webcam.js (video#webcam, canvas#snapshot,
 * button#capture-btn, img#preview, input#photo_data) — do not duplicate that
 * logic here; this file only validates the rest of the form and submits to
 * the real POST /register backend (routes/auth.py).
 */

(function () {
    const form = document.getElementById("registerForm");
    if (!form) return;

    const nameInput = document.getElementById("name");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirmPassword");
    const photoDataInput = document.getElementById("photo_data");
    const messageDiv = document.getElementById("message");
    const registerBtn = document.getElementById("registerBtn");

    const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    document.querySelectorAll(".toggle-password").forEach((btn) => {
        btn.addEventListener("click", function () {
            const targetId = btn.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (!input) return;
            const isHidden = input.type === "password";
            input.type = isHidden ? "text" : "password";
            btn.innerHTML = isHidden
                ? '<i class="fa-solid fa-eye-slash"></i>'
                : '<i class="fa-solid fa-eye"></i>';
            btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
        });
    });

    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = "message-box " + type;
        messageDiv.style.display = "block";
    }

    function clearFieldErrors() {
        document.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
    }

    function setLoading(isLoading) {
        registerBtn.disabled = isLoading;
        registerBtn.innerHTML = isLoading
            ? '<i class="fa-solid fa-spinner fa-spin"></i> Registering...'
            : "<span class=\"btn-label\">Register</span>";
    }

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        messageDiv.style.display = "none";
        clearFieldErrors();

        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const confirmPassword = confirmInput.value;
        const photo_data = photoDataInput.value;

        let valid = true;
        if (name.length < 3) {
            document.getElementById("name-error").textContent = "Name must be at least 3 characters.";
            valid = false;
        }
        if (!EMAIL_REGEX.test(email)) {
            document.getElementById("email-error").textContent = "Enter a valid email address.";
            valid = false;
        }
        if (password.length < 8) {
            document.getElementById("password-error").textContent = "Password must be at least 8 characters.";
            valid = false;
        }
        if (password !== confirmPassword) {
            document.getElementById("confirmPassword-error").textContent = "Passwords do not match.";
            valid = false;
        }
        if (!photo_data) {
            document.getElementById("photo-error").textContent = "Please capture your face photo before registering.";
            valid = false;
        }
        if (!valid) return;

        setLoading(true);
        try {
            const response = await fetch("/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password, photo_data }),
            });
            const result = await response.json().catch(() => ({}));

            if (response.ok && result.status === "success") {
                showMessage(result.message || "Registration successful. Redirecting to login...", "success");
                setTimeout(() => {
                    window.location.href = "/login";
                }, 1800);
                return;
            }

            showMessage(result.message || "Registration failed. Please check your details.", "error");
        } catch (err) {
            console.error("Registration request failed:", err);
            showMessage("Could not reach the server. Please try again.", "error");
        } finally {
            setLoading(false);
        }
    });
})();
