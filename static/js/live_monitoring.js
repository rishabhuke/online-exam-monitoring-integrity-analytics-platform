"use strict";

let selectedExamId = null;
let selectedCandidateId = null;
let monitoringTimer = null;


/* =========================================================
   LOAD LIVE MONITORING
========================================================= */

async function loadLiveMonitoring() {

    try {

        let url = "/admin/api/live-monitoring";

        if (selectedExamId) {

            url += "?exam_id=" + selectedExamId;

        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(
                "HTTP error: " + response.status
            );
        }

        const data = await response.json();

        console.log(
            "Live Monitoring API:",
            data
        );

        if (!data.success) {

            console.error(
                data.message || "API failed"
            );

            return;
        }


        /* =====================================================
           EXAM
        ===================================================== */

        renderExam(data.exam);


        /* =====================================================
           STATISTICS
        ===================================================== */

        renderStatistics(
            data.statistics
        );


        /* =====================================================
           STUDENTS
        ===================================================== */

        renderStudents(
            data.students || []
        );


        /* =====================================================
           SELECTED STUDENT
        ===================================================== */

        renderSelectedStudent(
            data.students || []
        );

    }

    catch (error) {

        console.error(
            "Live monitoring error:",
            error
        );

    }

}


/* =========================================================
   EXAM
========================================================= */

function renderExam(exam) {

    const title =
        document.getElementById(
            "selectedExamName"
        );

    if (!title) {

        console.error(
            "selectedExamName element not found"
        );

        return;
    }


    if (!exam) {

        title.textContent =
            "No active examination";

        return;
    }


    title.textContent =
        exam.title || "Untitled Exam";

}


/* =========================================================
   STATISTICS
========================================================= */

function renderStatistics(stats) {

    if (!stats)
        return;


    const total =
        document.getElementById(
            "totalStudents"
        );

    const monitored =
        document.getElementById(
            "monitoredStudents"
        );

    const violations =
        document.getElementById(
            "liveViolationCount"
        );

    const evidence =
        document.getElementById(
            "evidenceCount"
        );


    if (total) {

        total.textContent =
            stats.total_students ?? 0;

    }


    if (monitored) {

        monitored.textContent =
            stats.monitored ?? 0;

    }


    if (violations) {

        violations.textContent =
            stats.violations ?? 0;

    }


    if (evidence) {

        evidence.textContent =
            stats.evidence ?? 0;

    }

}


/* =========================================================
   STUDENTS
========================================================= */

function renderStudents(students) {

    const container =
        document.getElementById(
            "studentList"
        );

    if (!container)
        return;


    container.innerHTML = "";


    if (!students || students.length === 0) {

        container.innerHTML = `

            <div class="no-students">

                <i class="fa-solid fa-users"></i>

                <p>
                    No students are currently
                    attending this exam.
                </p>

            </div>

        `;

        return;
    }


    students.forEach(
        student => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "student-item";


            if (
                selectedCandidateId ===
                student.candidate_id
            ) {

                item.classList.add(
                    "selected"
                );

            }


            let statusClass =
                "online";


            if (
                student.status ===
                "Warning"
            ) {

                statusClass =
                    "warning";

            }


            if (
                student.status ===
                "Violation"
            ) {

                statusClass =
                    "danger";

            }


            const name =
                student.name ||
                "Unknown Student";


            const email =
                student.email ||
                "";


            const initial =
                name.charAt(0)
                .toUpperCase();


            item.innerHTML = `

                <div class="student-avatar">

                    ${
                        student.photo

                        ?

                        `<img
                            src="${student.photo}"
                            alt=""
                        >`

                        :

                        `<span>
                            ${initial}
                        </span>`
                    }

                </div>


                <div class="student-info">

                    <strong>
                        ${name}
                    </strong>

                    <small>
                        ${email}
                    </small>

                </div>


                <div class="
                    student-status
                    ${statusClass}
                ">

                    <span></span>

                    ${student.status || "Online"}

                </div>

            `;


            item.addEventListener(
                "click",
                () => {

                    selectedCandidateId =
                        student.candidate_id;


                    renderStudents(
                        students
                    );


                    renderSelectedStudent(
                        students
                    );

                }
            );


            container.appendChild(
                item
            );

        }
    );

}


/* =========================================================
   SELECTED STUDENT
========================================================= */

function renderSelectedStudent(students) {

    const name =
        document.getElementById(
            "monitorStudentName"
        );

    const id =
        document.getElementById(
            "monitorStudentId"
        ) ||
        document.querySelector(
            ".student-monitor-header h2 span"
        );

    const video =
        document.getElementById(
            "studentVideo"
        );

    const placeholder =
        document.getElementById(
            "cameraPlaceholder"
        );

    if (!students || students.length === 0) {

        if (name) name.textContent = "--";
        if (id) id.textContent = "";

        if (video) {
            video.src = "";
            video.style.display = "none";
        }

        if (placeholder) {
            placeholder.style.display = "flex";
        }

        renderViolations(null);
        renderStatus(null);
        return;

    }


    if (
        !selectedCandidateId ||
        !students.some(s => s.candidate_id === selectedCandidateId)
    ) {

        selectedCandidateId =
            students[0].candidate_id;

    }


    const student =
        students.find(
            s =>
                s.candidate_id ===
                selectedCandidateId
        ) || students[0];


    if (!student)
        return;


    if (name) {

        name.textContent =
            student.name || "Unknown Candidate";

    }


    if (id) {

        id.textContent =
            "(" +
            student.candidate_id +
            ")";

    }


    /*
       Display live frame if available
    */

    if (
        video &&
        student.live_frame
    ) {

        video.src =
            student.live_frame +
            (student.live_frame.includes("?") ? "&" : "?") +
            "t=" +
            Date.now();

        video.style.display = "block";

        if (placeholder) {
            placeholder.style.display = "none";
        }

        video.onerror = () => {
            video.style.display = "none";
            if (placeholder) {
                placeholder.style.display = "flex";
            }
        };

    } else {

        if (video) {
            video.src = "";
            video.style.display = "none";
        }

        if (placeholder) {
            placeholder.style.display = "flex";
        }

    }


    renderViolations(
        student
    );


    renderStatus(
        student
    );

}


/* =========================================================
   VIOLATIONS
========================================================= */

function renderViolations(student) {

    const container =
        document.getElementById(
            "violationList"
        );

    if (!container)
        return;


    container.innerHTML = "";


    if (!student || !student.latest_violation) {

        container.innerHTML = `

            <div class="no-violations" style="padding: 16px; text-align: center; color: #10b981; font-weight: 500;">

                <span>✓</span>

                No violations detected

            </div>

        `;

        return;
    }


    const violation =
        student.latest_violation;


    container.innerHTML = `

        <div class="violation-item">

            <div>

                <strong>
                    ${formatViolation(
                        violation.type
                    )}
                </strong>

                <small>
                    ${violation.time || ""}
                </small>

            </div>

            <span class="danger">
                LIVE
            </span>

        </div>

    `;

}


/* =========================================================
   STATUS
========================================================= */

function renderStatus(student) {

    const face =
        document.getElementById(
            "faceStatus"
        );

    const camera =
        document.getElementById(
            "cameraStatus"
        );

    const connection =
        document.getElementById(
            "connectionStatus"
        );

    const screen =
        document.getElementById(
            "screenStatus"
        );

    const multipleFaces =
        document.getElementById(
            "multipleFaceStatus"
        );


    if (!student) {

        if (face) face.innerHTML = '<i class="fa-solid fa-circle-check"></i> --';
        if (camera) camera.innerHTML = '<i class="fa-solid fa-circle-check"></i> --';
        if (connection) connection.innerHTML = '<i class="fa-solid fa-circle-check"></i> --';
        if (screen) screen.innerHTML = '<i class="fa-solid fa-circle-check"></i> --';
        if (multipleFaces) multipleFaces.innerHTML = '<i class="fa-solid fa-circle-check"></i> --';
        return;

    }


    if (face) {

        const isViolation = student.status === "Violation";

        face.className = isViolation ? "danger" : "success";

        face.innerHTML = `
            <i class="fa-solid ${isViolation ? 'fa-triangle-exclamation' : 'fa-circle-check'}"></i>
            ${isViolation ? 'Alert' : 'Present'}
        `;

    }


    if (camera) {

        camera.innerHTML = `
            <i class="fa-solid fa-circle-check"></i>
            ${student.camera || "Active"}
        `;

    }


    if (connection) {

        connection.innerHTML = `
            <i class="fa-solid fa-circle-check"></i>
            ${student.connection || "Stable"}
        `;

    }


    if (screen) {

        screen.innerHTML = `
            <i class="fa-solid fa-circle-check"></i>
            Active
        `;

    }


    if (multipleFaces) {

        const hasMulti = student.latest_violation &&
            String(student.latest_violation.type || '').toUpperCase().includes('MULTIPLE');

        multipleFaces.className = hasMulti ? "danger" : "success";

        multipleFaces.innerHTML = `
            <i class="fa-solid ${hasMulti ? 'fa-triangle-exclamation' : 'fa-circle-check'}"></i>
            ${hasMulti ? 'Detected' : 'Single'}
        `;

    }

}


/* =========================================================
   VIOLATION FORMAT
========================================================= */

function formatViolation(value) {

    if (!value)
        return "Violation";


    return value
        .replaceAll("_", " ")
        .toLowerCase()
        .replace(
            /\b\w/g,
            c => c.toUpperCase()
        );

}


/* =========================================================
   AUTO REFRESH
========================================================= */

function startLiveMonitoring() {

    loadLiveMonitoring();


    if (monitoringTimer) {

        clearInterval(
            monitoringTimer
        );

    }


    monitoringTimer =
        setInterval(
            loadLiveMonitoring,
            5000
        );

}


/* =========================================================
   SEARCH
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const search =
            document.getElementById(
                "studentSearch"
            );


        if (search) {

            search.addEventListener(
                "input",
                function () {

                    const keyword =
                        this.value
                            .toLowerCase();


                    document
                        .querySelectorAll(
                            ".student-item"
                        )
                        .forEach(
                            item => {

                                item.style.display =
                                    item.innerText
                                        .toLowerCase()
                                        .includes(
                                            keyword
                                        )
                                        ? ""
                                        : "none";

                            }
                        );

                }
            );

        }


        startLiveMonitoring();

    }
);