document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("adminSignupForm");
    const messageBox = document.getElementById("messageBox");

    form.addEventListener("submit", registerAdmin);

    async function registerAdmin(e) {

        e.preventDefault();

        messageBox.style.display = "block";
        messageBox.className = "message";
        messageBox.innerHTML = "Creating administrator account...";

        const full_name = document.getElementById("fullName").value.trim();
        const email = document.getElementById("email").value.trim();
        const employee_id = document.getElementById("employeeId").value.trim();
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirmPassword").value;
        const organization_code = document.getElementById("organizationCode").value.trim();

        if (
            full_name === "" ||
            email === "" ||
            employee_id === "" ||
            username === "" ||
            password === "" ||
            confirmPassword === "" ||
            organization_code === ""
        ) {

            messageBox.className = "message error";
            messageBox.innerHTML = "Please fill all the required fields.";
            return;

        }

        if (password !== confirmPassword) {

            messageBox.className = "message error";
            messageBox.innerHTML = "Passwords do not match.";
            return;

        }

        if (password.length < 8) {

            messageBox.className = "message error";
            messageBox.innerHTML = "Password must contain at least 8 characters.";
            return;

        }

        try {

            const response = await fetch("/api/admin/register", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                credentials: "same-origin",

                body: JSON.stringify({

                    full_name,
                    email,
                    employee_id,
                    username,
                    password,
                    organization_code

                })

            });

            const result = await response.json();

            if (response.ok && result.status === "success") {

                messageBox.className = "message success";
                messageBox.innerHTML = "Registration Successful! Redirecting to Login...";

                form.reset();

                setTimeout(() => {

                    window.location.href = "/admin/login";

                }, 1200);

            } else {

                messageBox.className = "message error";
                messageBox.innerHTML = result.message || "Registration failed.";

            }

        } catch (error) {

            console.error(error);

            messageBox.className = "message error";
            messageBox.innerHTML = "Unable to connect to the server.";

        }

    }

});