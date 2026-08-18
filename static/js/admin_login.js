document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("adminLoginForm");
    const messageBox = document.getElementById("messageBox");

    form.addEventListener("submit", loginAdmin);

    async function loginAdmin(e) {

        e.preventDefault();

        messageBox.style.display = "block";
        messageBox.className = "message";
        messageBox.innerHTML = "Logging in...";

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;

        if (username === "" || password === "") {

            messageBox.classList.add("error");
            messageBox.innerHTML = "Please enter Username and Password.";
            return;

        }

        try {

            const response = await fetch("/api/admin/login", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                credentials: "same-origin",

                body: JSON.stringify({

                    username: username,
                    password: password

                })

            });

            const result = await response.json();

            if (response.ok && result.status === "success") {

                messageBox.className = "message success";
                messageBox.innerHTML = "Login Successful! Redirecting...";

                setTimeout(() => {

                    window.location.href = "/admin/dashboard";

                }, 1000);

            }

            else {

                messageBox.className = "message error";
                messageBox.innerHTML = result.message;

            }

        }

        catch (error) {

            console.error(error);

            messageBox.className = "message error";
            messageBox.innerHTML = "Unable to connect to the server.";

        }

    }

});