document.addEventListener("DOMContentLoaded", function () {

    console.log("Admin profile page loaded");


    /* =====================================================
       LOAD ADMIN PROFILE
    ===================================================== */

    async function loadAdminProfile() {

        try {

            const response = await fetch(
                "/admin/api/admin-profile",
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


            if (!response.ok) {

                throw new Error(
                    "Profile request failed: " +
                    response.status
                );

            }


            const data = await response.json();


            console.log("Admin profile response:", data);


            if (!data.success) {

                throw new Error(
                    data.message ||
                    "Unable to load admin profile"
                );

            }


            const admin = data.admin;


            /* =================================================
               PROFILE HEADER
            ================================================= */

            setText(
                "profileName",
                admin.full_name || admin.name || "Administrator"
            );


            setText(
                "profileUsername",
                admin.username
                    ? "@" + admin.username
                    : "@admin"
            );


            /* =================================================
               PROFILE DETAILS
            ================================================= */

            setText(
                "profileAdminId",
                admin.id || "--"
            );


            setText(
                "profileEmpId",
                admin.employee_id || "--"
            );


            setText(
                "profileUsernameValue",
                admin.username || "--"
            );


            setText(
                "profileEmail",
                admin.email || "--"
            );


            /*
             * Your Admins table does not have a role column.
             * Therefore we use Administrator as the role.
             */

            setText(
                "profileRole",
                "Administrator"
            );


            setText(
                "profileRoleValue",
                "Administrator"
            );


            /* =================================================
               CREATED DATE
            ================================================= */

            setText(
                "profileCreatedAt",
                formatDate(admin.created_at)
            );


        }
        catch (error) {

            console.error(
                "Admin profile error:",
                error
            );


            setText(
                "profileName",
                "Unable to load profile"
            );


            setText(
                "profileAdminId",
                "--"
            );


            setText(
                "profileEmpId",
                "--"
            );


            setText(
                "profileUsernameValue",
                "--"
            );


            setText(
                "profileEmail",
                "--"
            );


            setText(
                "profileCreatedAt",
                "--"
            );

        }

    }



    /* =====================================================
       HELPER
    ===================================================== */

    function setText(id, value) {

        const element =
            document.getElementById(id);


        if (element) {

            element.textContent =
                value ?? "--";

        }

    }



    /* =====================================================
       FORMAT DATE
    ===================================================== */

    function formatDate(value) {

        if (!value) {

            return "--";

        }


        const date =
            new Date(value);


        if (Number.isNaN(date.getTime())) {

            return value;

        }


        return date.toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );

    }



    /* =====================================================
       SIDEBAR TOGGLE
    ===================================================== */

    const toggleSidebar =
        document.getElementById("toggleSidebar");


    const sidebar =
        document.querySelector(".sidebar");


    if (
        toggleSidebar &&
        sidebar
    ) {

        toggleSidebar.addEventListener(
            "click",
            function () {

                sidebar.classList.toggle(
                    "collapsed"
                );

            }
        );

    }


    /* =====================================================
       LOAD PROFILE
    ===================================================== */

    loadAdminProfile();

});