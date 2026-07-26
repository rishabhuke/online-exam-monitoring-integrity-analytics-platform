// ======================================
// PASSWORD TOGGLE
// ======================================

function togglePassword() {

    const password = document.getElementById("password");
    const icon = document.querySelector(".togglePassword i");

    if (password.type === "password") {

        password.type = "text";

        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");

    } else {

        password.type = "password";

        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");

    }

}


// ======================================
// EMAIL VALIDATION
// ======================================

function validateEmail(email) {

    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    return regex.test(email);

}


// ======================================
// REMEMBER ME
// ======================================

window.onload = function () {

    const savedEmail = localStorage.getItem("candidate_email");

    if (savedEmail) {

        document.getElementById("email").value = savedEmail;
        document.getElementById("remember").checked = true;

    }

};


// ======================================
// LOGIN FORM
// ======================================

const loginForm = document.getElementById("loginForm");

loginForm.addEventListener("submit", async function (e) {

    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const remember = document.getElementById("remember").checked;

    // -------------------------
    // Validation
    // -------------------------

    if (!validateEmail(email)) {

        alert("Please enter a valid Email Address.");
        return;

    }

    if (password.length < 8) {

        alert("Password should contain at least 8 characters.");
        return;

    }

    // -------------------------
    // Remember Me
    // -------------------------

    if (remember) {

        localStorage.setItem("candidate_email", email);

    } else {

        localStorage.removeItem("candidate_email");

    }

    // -------------------------
    // Loading Button
    // -------------------------

    const loginBtn = document.querySelector(".login-btn");

    loginBtn.disabled = true;

    loginBtn.innerHTML = `
        <i class="fa-solid fa-spinner fa-spin"></i>
        Logging In...
    `;

    // -------------------------
    // LOGIN API
    // -------------------------

    try {

        const response = await fetch("/login", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                email: email,
                password: password

            })

        });

        const result = await response.json();

        if (response.ok && result.status === "success") {

            alert(result.message);

            window.location.href = "/dashboard";

        } else {

            alert(result.message);

        }

    } catch (error) {

        console.error(error);

        alert("Unable to connect to the server.");

    } finally {

        loginBtn.disabled = false;

        loginBtn.innerHTML = `
            <i class="fa-solid fa-right-to-bracket"></i>
            Login
        `;

    }

});