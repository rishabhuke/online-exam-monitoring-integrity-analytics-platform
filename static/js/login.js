/*
 * Candidate login form handling.
 * Real backend integration against POST /login (routes/auth.py).
 * No mock/demo behavior — do not reintroduce a fake "Login Successful"
 * timeout here. See PR description for why this file was rewritten.
 */

(function () {
    const form = document.getElementById("loginForm");
    if (!form) return;

    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const rememberInput = document.getElementById("remember");
    const messageDiv = document.getElementById("message");
    const loginBtn = document.getElementById("loginBtn");
    const toggleBtn = document.getElementById("togglePassword");

    const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    // Restore remembered email (non-sensitive convenience only).
    const savedEmail = localStorage.getItem("candidate_email");
    if (savedEmail) {
        emailInput.value = savedEmail;
        if (rememberInput) rememberInput.checked = true;
    }

    if (toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const isHidden = passwordInput.type === "password";
            passwordInput.type = isHidden ? "text" : "password";
            toggleBtn.innerHTML = isHidden
                ? '<i class="fa-solid fa-eye-slash"></i>'
                : '<i class="fa-solid fa-eye"></i>';
            toggleBtn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
        });
    }

    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = "message-box " + type;
        messageDiv.style.display = "block";
    }

    function clearFieldErrors() {
        document.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
    }

    function setLoading(isLoading) {
        loginBtn.disabled = isLoading;
        loginBtn.innerHTML = isLoading
            ? '<i class="fa-solid fa-spinner fa-spin"></i> Logging in...'
            : "<span class=\"btn-label\">Login</span>";
    }

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        messageDiv.style.display = "none";
        clearFieldErrors();

        const email = emailInput.value.trim();
        const password = passwordInput.value;
        let valid = true;

        if (!EMAIL_REGEX.test(email)) {
            document.getElementById("email-error").textContent = "Enter a valid email address.";
            valid = false;
        }
        if (!password) {
            document.getElementById("password-error").textContent = "Password is required.";
            valid = false;
        }
        if (!valid) return;

        if (rememberInput && rememberInput.checked) {
            localStorage.setItem("candidate_email", email);
        } else {
            localStorage.removeItem("candidate_email");
        }

        setLoading(true);
        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const result = await response.json().catch(() => ({}));

            if (response.ok && result.status === "success") {
                showMessage(result.message || "Login successful.", "success");
                window.location.href = "/dashboard";
                return;
            }

            showMessage(result.message || "Login failed. Please check your credentials.", "error");
        } catch (err) {
            console.error("Login request failed:", err);
            showMessage("Could not reach the server. Please try again.", "error");
        } finally {
            setLoading(false);
        }
    });
})();
