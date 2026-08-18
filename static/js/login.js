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
function showMessage(title, message, success = true, callback = null){

    const modal = document.getElementById("messageModal");

    const icon = document.getElementById("messageIcon");

    const titleText = document.getElementById("messageTitle");

    const messageText = document.getElementById("messageText");

    const button = document.getElementById("messageBtn");

    titleText.textContent = title;

    messageText.textContent = message;

    if(success){

        icon.innerHTML = "✔";

        icon.className = "message-icon message-success";

    }
    else{

        icon.innerHTML = "✖";

        icon.className = "message-icon message-error";

    }

    modal.style.display = "flex";

    button.onclick = function(){

        modal.style.display = "none";

        if(callback){

            callback();

        }

    };

}
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

        showMessage(
    "Invalid Email",
    "Please enter a valid Email Address.",
    false
);  
        return;

    }

    if (password.length < 8) {

        showMessage(
    "Invalid Password",
    "Password should contain at least 8 characters.",
    false
); 
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

            showMessage(
    "Login Successful",
    result.message,
    true,
    function(){

        window.location.href="/dashboard";

    }
);

        } else {

            showMessage(
    "Login Failed",
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

    } finally {

        loginBtn.disabled = false;

        loginBtn.innerHTML = `
            <i class="fa-solid fa-right-to-bracket"></i>
            Login
        `;

    }

});