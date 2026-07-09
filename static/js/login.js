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

    const regex =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    const remember =
        document.getElementById("remember").checked;

    // -------------------------

    if (!validateEmail(email)) {

        alert("Please enter a valid Email Address.");

        return;

    }

    if (password.length < 6) {

        alert("Password should contain at least 6 characters.");

        return;

    }

    // -------------------------
    // Remember Me
    // -------------------------

    if (remember) {

        localStorage.setItem(
            "candidate_email",
            email
        );

    } else {

        localStorage.removeItem(
            "candidate_email"
        );

    }

    // -------------------------
    // Button Loading
    // -------------------------

    const loginBtn =
        document.querySelector(".login-btn");

    loginBtn.disabled = true;

    loginBtn.innerHTML = `
        <i class="fa-solid fa-spinner fa-spin"></i>
        Logging In...
    `;

    // -------------------------
    // API CALL
    // -------------------------

    try {

        /*
        const response = await fetch("/login",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({

                email:email,
                password:password

            })

        });

        const result = await response.json();

        if(result.success){

            window.location.href="/dashboard";

        }

        else{

            alert(result.message);

        }
        */

        // Temporary Demo

        setTimeout(() => {

            alert("Login Successful!");

            window.location.href = "/dashboard";

        }, 1500);

    }

    catch (error) {

        console.log(error);

        alert("Something went wrong.");

    }

});