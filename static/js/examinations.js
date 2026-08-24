/* ==========================================================
   EXAMINATIONS PAGE
========================================================== */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializeSidebar();

        initializeLogout();

        initializeSearch();

        initializeFilters();

        initializePagination();

        initializeModal();

        initializeUpcomingButton();

        loadExaminations();

    }
);


/* ==========================================================
   GLOBAL DATA
========================================================== */

let allExaminations = [];

let filteredExaminations = [];

let currentPage = 1;

let rowsPerPage = 6;

let selectedExam = null;


/* ==========================================================
   API URL
========================================================== */

const EXAMINATIONS_API =
    "/admin/api/examinations";


/* ==========================================================
   SIDEBAR
========================================================== */

function initializeSidebar() {

    const toggleButton =
        document.getElementById(
            "toggleSidebar"
        );

    const sidebar =
        document.querySelector(
            ".sidebar"
        );

    if (
        !toggleButton ||
        !sidebar
    ) {
        return;
    }

    toggleButton.addEventListener(
        "click",
        function () {

            sidebar.classList.toggle(
                "collapsed"
            );

        }
    );

}


/* ==========================================================
   LOGOUT
========================================================== */

function initializeLogout() {

    const logout =
        document.querySelector(
            '.sidebar a[href="/admin/logout"]'
        );

    if (!logout) {
        return;
    }

    logout.addEventListener(
        "click",
        function (event) {

            const confirmed =
                confirm(
                    "Are you sure you want to logout?"
                );

            if (!confirmed) {

                event.preventDefault();

            }

        }
    );

}


/* ==========================================================
   LOAD EXAMINATIONS
========================================================== */

async function loadExaminations() {

    const refreshButton =
        document.getElementById(
            "refreshExams"
        );

    if (refreshButton) {

        refreshButton.classList.add(
            "loading"
        );

        refreshButton.disabled = true;

    }

    showTableLoading();

    try {

        console.log(
            "Loading examinations from:",
            EXAMINATIONS_API
        );


        const response =
            await fetch(
                EXAMINATIONS_API,
                {
                    method: "GET",

                    headers: {
                        "Accept":
                            "application/json"
                    },

                    credentials:
                        "same-origin",

                    cache: "no-store"
                }
            );


        console.log(
            "Examinations HTTP status:",
            response.status
        );


        if (!response.ok) {

            let errorMessage =
                `Server returned HTTP ${response.status}`;

            try {

                const errorData =
                    await response.json();

                if (
                    errorData.message
                ) {

                    errorMessage =
                        errorData.message;

                }

            }
            catch (error) {

                console.warn(
                    "Could not parse error response."
                );

            }

            throw new Error(
                errorMessage
            );

        }


        const result =
            await response.json();


        console.log(
            "===== EXAMINATIONS API RESPONSE ====="
        );

        console.log(
            result
        );

        console.log(
            "======================================"
        );


        if (
            !result ||
            result.success !== true
        ) {

            throw new Error(
                result?.message ||
                "Unable to load examinations."
            );

        }


        if (
            !Array.isArray(
                result.exams
            )
        ) {

            throw new Error(
                "Invalid examinations data received from server."
            );

        }


        /* ==================================================
           NORMALIZE BACKEND DATA
        ================================================== */

        allExaminations =
            result.exams.map(
                function (exam) {

                    const normalizedExam = {

                        id:
                            exam.id,

                        title:
                            exam.title ?? "",

                        topic:
                            exam.topic ?? "",

                        difficulty:
                            exam.difficulty ?? "",

                        description:
                            exam.description ?? "",

                        duration:
                            Number(
                                exam.duration ?? 0
                            ),

                        total_questions:
                            Number(
                                exam.total_questions ?? 0
                            ),

                        total_marks:
                            Number(
                                exam.total_marks ?? 0
                            ),

                        start_time:
                            exam.start_time ?? null,

                        end_time:
                            exam.end_time ?? null,

                        created_at:
                            exam.created_at ?? null

                    };


                    console.log(
                        "Normalized examination:",
                        normalizedExam
                    );


                    return {

                        ...normalizedExam,

                        status:
                            calculateExamStatus(
                                normalizedExam
                            )

                    };

                }
            );


        console.log(
            "===== NORMALIZED EXAMINATIONS ====="
        );

        console.table(
            allExaminations
        );

        console.log(
            "===================================="
        );


        currentPage = 1;


        updateStatistics();


        populateSubjectFilter();


        applyFilters();


        loadUpcomingExaminations();

    }
    catch (error) {

        console.error(
            "EXAMINATION LOADING ERROR:",
            error
        );

        showTableError(
            error.message ||
            "Unable to load examinations."
        );

    }
    finally {

        if (refreshButton) {

            refreshButton.classList.remove(
                "loading"
            );

            refreshButton.disabled = false;

        }

    }

}


/* ==========================================================
   CALCULATE EXAM STATUS
========================================================== */

function calculateExamStatus(exam) {

    const start =
        parseDate(
            exam.start_time
        );

    const end =
        parseDate(
            exam.end_time
        );


    if (
        !start &&
        !end
    ) {

        return "Draft";

    }


    const now =
        new Date();


    if (
        start &&
        now < start
    ) {

        return "Upcoming";

    }


    if (
        start &&
        end &&
        now >= start &&
        now <= end
    ) {

        return "Active";

    }


    if (
        end &&
        now > end
    ) {

        return "Completed";

    }


    if (
        start &&
        !end &&
        now >= start
    ) {

        return "Active";

    }


    return "Draft";

}


/* ==========================================================
   DATE PARSER
========================================================== */

function parseDate(value) {

    if (!value) {
        return null;
    }

    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return null;

    }


    return date;

}


/* ==========================================================
   STATISTICS
========================================================== */

function updateStatistics() {

    const total =
        allExaminations.length;


    const upcoming =
        allExaminations.filter(
            function (exam) {

                return (
                    exam.status ===
                    "Upcoming"
                );

            }
        ).length;


    const active =
        allExaminations.filter(
            function (exam) {

                return (
                    exam.status ===
                    "Active"
                );

            }
        ).length;


    const completed =
        allExaminations.filter(
            function (exam) {

                return (
                    exam.status ===
                    "Completed"
                );

            }
        ).length;


    setText(
        "totalExaminations",
        total
    );

    setText(
        "upcomingExaminations",
        upcoming
    );

    setText(
        "activeExaminations",
        active
    );

    setText(
        "completedExaminations",
        completed
    );

}


/* ==========================================================
   SUBJECT FILTER
========================================================== */

function populateSubjectFilter() {

    const select =
        document.getElementById(
            "subjectFilter"
        );

    if (!select) {
        return;
    }


    const currentValue =
        select.value;


    const subjects =
        [
            ...new Set(
                allExaminations
                    .map(
                        function (exam) {

                            return String(
                                exam.topic || ""
                            ).trim();

                        }
                    )
                    .filter(Boolean)
            )
        ].sort(
            function (a, b) {

                return a.localeCompare(b);

            }
        );


    select.innerHTML = `
        <option value="all">
            All Subjects
        </option>
    `;


    subjects.forEach(
        function (subject) {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                subject;

            option.textContent =
                subject;

            select.appendChild(
                option
            );

        }
    );


    if (
        currentValue &&
        [
            ...select.options
        ].some(
            function (option) {

                return (
                    option.value ===
                    currentValue
                );

            }
        )
    ) {

        select.value =
            currentValue;

    }

}


/* ==========================================================
   SEARCH
========================================================== */

function initializeSearch() {

    const search =
        document.getElementById(
            "examSearch"
        );

    if (!search) {
        return;
    }


    search.addEventListener(
        "input",
        function () {

            currentPage = 1;

            applyFilters();

        }
    );

}


/* ==========================================================
   FILTERS
========================================================== */

function initializeFilters() {

    const statusFilter =
        document.getElementById(
            "statusFilter"
        );

    const subjectFilter =
        document.getElementById(
            "subjectFilter"
        );

    const sortFilter =
        document.getElementById(
            "sortFilter"
        );

    const refreshButton =
        document.getElementById(
            "refreshExams"
        );


    if (statusFilter) {

        statusFilter.addEventListener(
            "change",
            function () {

                currentPage = 1;

                applyFilters();

            }
        );

    }


    if (subjectFilter) {

        subjectFilter.addEventListener(
            "change",
            function () {

                currentPage = 1;

                applyFilters();

            }
        );

    }


    if (sortFilter) {

        sortFilter.addEventListener(
            "change",
            function () {

                currentPage = 1;

                applyFilters();

            }
        );

    }


    if (refreshButton) {

        refreshButton.addEventListener(
            "click",
            function () {

                loadExaminations();

            }
        );

    }

}


/* ==========================================================
   APPLY FILTERS
========================================================== */

function applyFilters() {

    const searchInput =
        document.getElementById(
            "examSearch"
        );

    const statusFilter =
        document.getElementById(
            "statusFilter"
        );

    const subjectFilter =
        document.getElementById(
            "subjectFilter"
        );

    const sortFilter =
        document.getElementById(
            "sortFilter"
        );


    const searchValue =
        searchInput
            ? searchInput.value
                .trim()
                .toLowerCase()
            : "";


    const statusValue =
        statusFilter
            ? statusFilter.value.toLowerCase()
            : "all";


    const subjectValue =
        subjectFilter
            ? subjectFilter.value
            : "all";


    const sortValue =
        sortFilter
            ? sortFilter.value
            : "newest";


    filteredExaminations =
        allExaminations.filter(
            function (exam) {

                const title =
                    String(
                        exam.title || ""
                    ).toLowerCase();


                const topic =
                    String(
                        exam.topic || ""
                    ).toLowerCase();


                const difficulty =
                    String(
                        exam.difficulty || ""
                    ).toLowerCase();


                const description =
                    String(
                        exam.description || ""
                    ).toLowerCase();


                const matchesSearch =
                    !searchValue ||
                    title.includes(
                        searchValue
                    ) ||
                    topic.includes(
                        searchValue
                    ) ||
                    difficulty.includes(
                        searchValue
                    ) ||
                    description.includes(
                        searchValue
                    );


                const matchesStatus =
                    statusValue === "all" ||
                    String(
                        exam.status ||
                        "Draft"
                    ).toLowerCase() ===
                    statusValue;


                const matchesSubject =
                    subjectValue === "all" ||
                    String(
                        exam.topic || ""
                    ) ===
                    subjectValue;


                return (
                    matchesSearch &&
                    matchesStatus &&
                    matchesSubject
                );

            }
        );


    sortExaminations(
        filteredExaminations,
        sortValue
    );


    renderExaminations();

}


/* ==========================================================
   SORT EXAMINATIONS
========================================================== */

function sortExaminations(
    exams,
    sortValue
) {

    exams.sort(
        function (a, b) {

            if (
                sortValue === "title"
            ) {

                return String(
                    a.title || ""
                ).localeCompare(
                    String(
                        b.title || ""
                    )
                );

            }


            if (
                sortValue === "questions"
            ) {

                return (
                    Number(
                        b.total_questions || 0
                    ) -
                    Number(
                        a.total_questions || 0
                    )
                );

            }


            const dateA =
                parseDate(
                    a.created_at ||
                    a.start_time
                );


            const dateB =
                parseDate(
                    b.created_at ||
                    b.start_time
                );


            const timeA =
                dateA
                    ? dateA.getTime()
                    : 0;


            const timeB =
                dateB
                    ? dateB.getTime()
                    : 0;


            if (
                sortValue === "oldest"
            ) {

                return (
                    timeA - timeB
                );

            }


            return (
                timeB - timeA
            );

        }
    );

}


/* ==========================================================
   RENDER EXAMINATIONS
========================================================== */

function renderExaminations() {

    const tbody =
        document.getElementById(
            "examinationTableBody"
        );

    if (!tbody) {
        return;
    }


    const total =
        filteredExaminations.length;


    const totalPages =
        Math.max(
            1,
            Math.ceil(
                total /
                rowsPerPage
            )
        );


    if (
        currentPage >
        totalPages
    ) {

        currentPage =
            totalPages;

    }


    const start =
        (
            currentPage - 1
        ) *
        rowsPerPage;


    const end =
        start +
        rowsPerPage;


    const pageExams =
        filteredExaminations.slice(
            start,
            end
        );


    if (
        !pageExams.length
    ) {

        tbody.innerHTML = `

            <tr>

                <td colspan="7">

                    <div class="table-empty">

                        <i class="fa-regular fa-folder-open"></i>

                        <strong>
                            No examinations found
                        </strong>

                        <p>
                            Try changing your search or filters.
                        </p>

                    </div>

                </td>

            </tr>

        `;

        updatePagination();

        return;

    }


    tbody.innerHTML = "";


    pageExams.forEach(
        function (exam) {

            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>

                    <div class="exam-name-cell">

                        <div class="exam-type-icon">

                            <i class="${getExamIcon(exam)}"></i>

                        </div>

                        <div class="exam-name-info">

                            <strong>
                                ${escapeHTML(
                                    exam.title ||
                                    "Untitled Examination"
                                )}
                            </strong>

                            <span>
                                ${escapeHTML(
                                    exam.topic ||
                                    "General Examination"
                                )}
                            </span>

                        </div>

                    </div>

                </td>


                <td>

                    <span class="subject-text">

                        ${escapeHTML(
                            exam.topic ||
                            "-"
                        )}

                    </span>

                </td>


                <td>

                    <strong>
                        ${Number(
                            exam.total_questions ?? 0
                        )}
                    </strong>

                </td>


                <td>

                    ${Number(
                        exam.duration ?? 0
                    )}
                    min

                </td>


                <td>

                    <div class="availability-cell">

                        <strong>
                            ${formatDateTime(
                                exam.start_time
                            )}
                        </strong>

                        <span>
                            to
                            ${formatDateTime(
                                exam.end_time
                            )}
                        </span>

                    </div>

                </td>


                <td>

                    ${getStatusBadge(
                        exam.status
                    )}

                </td>


                <td>

                    <div class="exam-actions">

                        <button
                            type="button"
                            class="exam-action-btn"
                            title="View Examination"
                            data-action="view"
                            data-id="${exam.id}"
                        >

                            <i class="fa-regular fa-eye"></i>

                        </button>


                        <button
                            type="button"
                            class="exam-action-btn delete-action-btn"
                            title="Delete Examination"
                            data-action="delete"
                            data-id="${exam.id}"
                        >

                            <i class="fa-solid fa-trash"></i>

                        </button>


                        <button
                            type="button"
                            class="exam-action-btn"
                            title="More"
                            data-action="more"
                            data-id="${exam.id}"
                        >

                            <i class="fa-solid fa-ellipsis-vertical"></i>

                        </button>

                    </div>

                </td>

            `;


            tbody.appendChild(
                row
            );

        }
    );


    attachTableActions();

    updatePagination();

}


/* ==========================================================
   TABLE ACTIONS
========================================================== */

function attachTableActions() {

    document
        .querySelectorAll(
            ".exam-action-btn"
        )
        .forEach(
            function (button) {

                button.addEventListener(
                    "click",
                    function () {

                        const id =
                            this.dataset.id;

                        const action =
                            this.dataset.action;


                        const exam =
                            allExaminations.find(
                                function (item) {

                                    return (
                                        String(
                                            item.id
                                        ) ===
                                        String(
                                            id
                                        )
                                    );

                                }
                            );


                        if (!exam) {

                            console.error(
                                "Examination not found:",
                                id
                            );

                            return;

                        }


                        if (
                            action === "view"
                        ) {

                            openExamModal(
                                exam
                            );

                            return;

                        }


                        if (
                            action === "delete"
                        ) {

                            deleteExamination(
                                exam
                            );

                            return;

                        }


                        if (
                            action === "more"
                        ) {

                            showExamOptions(
                                exam
                            );

                        }

                    }
                );

            }
        );

}


/* ==========================================================
   DELETE EXAMINATION
========================================================== */

async function deleteExamination(
    exam
) {

    if (
        !exam ||
        !exam.id
    ) {

        alert(
            "Invalid examination."
        );

        return;

    }


    const examTitle =
        exam.title ||
        "this examination";


    const confirmed =
        confirm(
            `Are you sure you want to delete "${examTitle}"?\n\n` +
            `This action cannot be undone.`
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `${EXAMINATIONS_API}/${encodeURIComponent(exam.id)}`,
                {
                    method: "DELETE",

                    headers: {
                        "Accept":
                            "application/json"
                    },

                    credentials:
                        "same-origin"
                }
            );


        let result = {};


        try {

            result =
                await response.json();

        }
        catch (error) {

            console.warn(
                "Delete response was not JSON."
            );

        }


        if (
            !response.ok ||
            result.success !== true
        ) {

            throw new Error(
                result.message ||
                `Unable to delete examination. HTTP ${response.status}`
            );

        }


        allExaminations =
            allExaminations.filter(
                function (item) {

                    return (
                        String(
                            item.id
                        ) !==
                        String(
                            exam.id
                        )
                    );

                }
            );


        allExaminations =
            allExaminations.map(
                function (item) {

                    return {

                        ...item,

                        status:
                            calculateExamStatus(
                                item
                            )

                    };

                }
            );


        updateStatistics();

        populateSubjectFilter();

        applyFilters();

        loadUpcomingExaminations();

        closeExamModal();


        alert(
            "Examination deleted successfully."
        );

    }
    catch (error) {

        console.error(
            "Delete examination error:",
            error
        );

        alert(
            error.message ||
            "Unable to delete examination."
        );

    }

}


/* ==========================================================
   VIEW EXAMINATION
========================================================== */

function openExamModal(
    exam
) {

    selectedExam =
        exam;


    console.log(
        "Opening examination:",
        exam
    );


    setText(
        "modalExamTitle",
        exam.title ||
        "Examination"
    );


    setText(
        "modalExamTopic",
        exam.topic ||
        "No topic"
    );


    setText(
        "modalSubject",
        exam.topic ||
        "-"
    );


    setText(
        "modalDifficulty",
        exam.difficulty ||
        "-"
    );


    setText(
        "modalQuestions",
        Number(
            exam.total_questions ?? 0
        )
    );


    setText(
        "modalDuration",
        Number(
            exam.duration ?? 0
        ) +
        " minutes"
    );


    setText(
        "modalStart",
        formatDateTime(
            exam.start_time
        )
    );


    setText(
        "modalEnd",
        formatDateTime(
            exam.end_time
        )
    );


    setText(
        "modalDescription",
        exam.description ||
        "No description available."
    );


    const modal =
        document.getElementById(
            "examModal"
        );


    if (modal) {

        modal.classList.add(
            "show"
        );

        document.body.classList.add(
            "modal-open"
        );

    }

}


/* ==========================================================
   MODAL INITIALIZATION
========================================================== */

function initializeModal() {

    const modal =
        document.getElementById(
            "examModal"
        );


    const closeButton =
        document.getElementById(
            "closeExamModal"
        );


    const overlay =
        modal
            ? modal.querySelector(
                ".modal-overlay"
            )
            : null;


    const closeModalButton =
        document.getElementById(
            "closeExamDetails"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeExamModal
        );

    }


    if (overlay) {

        overlay.addEventListener(
            "click",
            closeExamModal
        );

    }


    if (closeModalButton) {

        closeModalButton.addEventListener(
            "click",
            closeExamModal
        );

    }


    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key ===
                "Escape"
            ) {

                closeExamModal();

            }

        }
    );

}


/* ==========================================================
   CLOSE MODAL
========================================================== */

function closeExamModal() {

    const modal =
        document.getElementById(
            "examModal"
        );


    if (modal) {

        modal.classList.remove(
            "show"
        );

    }


    document.body.classList.remove(
        "modal-open"
    );


    selectedExam =
        null;

}


/* ==========================================================
   MORE OPTIONS
========================================================== */

function showExamOptions(
    exam
) {

    const message =

        "Examination: " +
        (
            exam.title ||
            "Untitled"
        ) +

        "\n\n" +

        "Status: " +
        (
            exam.status ||
            "Draft"
        ) +

        "\n" +

        "Questions: " +
        (
            exam.total_questions ??
            0
        ) +

        "\n" +

        "Duration: " +
        (
            exam.duration ??
            0
        ) +
        " minutes" +

        "\n" +

        "Total Marks: " +
        (
            exam.total_marks ??
            0
        );


    alert(
        message
    );

}


/* ==========================================================
   UPCOMING EXAMINATIONS
========================================================== */

function loadUpcomingExaminations() {

    const container =
        document.getElementById(
            "upcomingExamList"
        );


    if (!container) {
        return;
    }


    const upcoming =
        allExaminations
            .filter(
                function (exam) {

                    return (
                        exam.status ===
                        "Upcoming"
                    );

                }
            )
            .sort(
                function (a, b) {

                    const dateA =
                        parseDate(
                            a.start_time
                        );

                    const dateB =
                        parseDate(
                            b.start_time
                        );


                    return (
                        (
                            dateA
                                ? dateA.getTime()
                                : 0
                        ) -
                        (
                            dateB
                                ? dateB.getTime()
                                : 0
                        )
                    );

                }
            )
            .slice(
                0,
                4
            );


    if (
        !upcoming.length
    ) {

        container.innerHTML = `

            <div class="side-loading">

                No upcoming examinations.

            </div>

        `;

        return;

    }


    container.innerHTML = "";


    upcoming.forEach(
        function (exam) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "upcoming-item";


            item.innerHTML = `

                <strong>

                    ${escapeHTML(
                        exam.title ||
                        "Untitled Examination"
                    )}

                </strong>

                <span>

                    ${formatDateTime(
                        exam.start_time
                    )}

                </span>

            `;


            item.style.cursor =
                "pointer";


            item.addEventListener(
                "click",
                function () {

                    openExamModal(
                        exam
                    );

                }
            );


            container.appendChild(
                item
            );

        }
    );

}


/* ==========================================================
   UPCOMING VIEW ALL
========================================================== */

function initializeUpcomingButton() {

    const button =
        document.getElementById(
            "viewAllUpcoming"
        );


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        function () {

            const status =
                document.getElementById(
                    "statusFilter"
                );


            if (status) {

                status.value =
                    "upcoming";

            }


            currentPage = 1;


            applyFilters();


            const table =
                document.querySelector(
                    ".exam-table-panel"
                );


            if (table) {

                table.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }

        }
    );

}


/* ==========================================================
   PAGINATION
========================================================== */

function initializePagination() {

    const previous =
        document.getElementById(
            "previousPage"
        );


    const next =
        document.getElementById(
            "nextPage"
        );


    const rows =
        document.getElementById(
            "rowsPerPage"
        );


    if (previous) {

        previous.addEventListener(
            "click",
            function () {

                if (
                    currentPage > 1
                ) {

                    currentPage--;

                    renderExaminations();

                }

            }
        );

    }


    if (next) {

        next.addEventListener(
            "click",
            function () {

                const totalPages =
                    Math.max(
                        1,
                        Math.ceil(
                            filteredExaminations.length /
                            rowsPerPage
                        )
                    );


                if (
                    currentPage <
                    totalPages
                ) {

                    currentPage++;

                    renderExaminations();

                }

            }
        );

    }


    if (rows) {

        rows.addEventListener(
            "change",
            function () {

                rowsPerPage =
                    Number(
                        this.value
                    ) || 6;


                currentPage = 1;


                renderExaminations();

            }
        );

    }

}


/* ==========================================================
   UPDATE PAGINATION
========================================================== */

function updatePagination() {

    const total =
        filteredExaminations.length;


    const totalPages =
        Math.max(
            1,
            Math.ceil(
                total /
                rowsPerPage
            )
        );


    const previous =
        document.getElementById(
            "previousPage"
        );


    const next =
        document.getElementById(
            "nextPage"
        );


    const pageNumbers =
        document.getElementById(
            "pageNumbers"
        );


    if (previous) {

        previous.disabled =
            currentPage <= 1;

    }


    if (next) {

        next.disabled =
            currentPage >=
            totalPages;

    }


    if (pageNumbers) {

        pageNumbers.innerHTML =
            "";


        const maxVisiblePages =
            5;


        let startPage =
            Math.max(
                1,
                currentPage -
                Math.floor(
                    maxVisiblePages / 2
                )
            );


        let endPage =
            Math.min(
                totalPages,
                startPage +
                maxVisiblePages -
                1
            );


        if (
            endPage -
            startPage +
            1 <
            maxVisiblePages
        ) {

            startPage =
                Math.max(
                    1,
                    endPage -
                    maxVisiblePages +
                    1
                );

        }


        for (
            let i = startPage;
            i <= endPage;
            i++
        ) {

            const button =
                document.createElement(
                    "button"
                );


            button.type =
                "button";


            button.className =
                "page-number";


            if (
                i === currentPage
            ) {

                button.classList.add(
                    "active"
                );

            }


            button.textContent =
                i;


            button.addEventListener(
                "click",
                function () {

                    currentPage =
                        i;

                    renderExaminations();

                }
            );


            pageNumbers.appendChild(
                button
            );

        }

    }


    const start =
        total === 0
            ? 0
            :
            (
                (
                    currentPage -
                    1
                ) *
                rowsPerPage
            ) + 1;


    const end =
        Math.min(
            currentPage *
            rowsPerPage,
            total
        );


    setText(
        "paginationInfo",
        `Showing ${start} to ${end} of ${total} examinations`
    );


    setText(
        "tableSummary",
        `${total} examination${
            total === 1
                ? ""
                : "s"
        } found`
    );

}


/* ==========================================================
   TABLE LOADING
========================================================== */

function showTableLoading() {

    const tbody =
        document.getElementById(
            "examinationTableBody"
        );


    if (!tbody) {
        return;
    }


    tbody.innerHTML = `

        <tr>

            <td colspan="7">

                <div class="table-loading">

                    <div class="spinner"></div>

                    Loading examinations...

                </div>

            </td>

        </tr>

    `;

}


/* ==========================================================
   TABLE ERROR
========================================================== */

function showTableError(
    message
) {

    const tbody =
        document.getElementById(
            "examinationTableBody"
        );


    if (!tbody) {
        return;
    }


    tbody.innerHTML = `

        <tr>

            <td colspan="7">

                <div class="table-empty">

                    <i class="fa-solid fa-circle-exclamation"></i>

                    <strong>
                        Unable to load examinations
                    </strong>

                    <p>
                        ${escapeHTML(
                            message ||
                            "Please try again."
                        )}
                    </p>

                    <button
                        type="button"
                        class="retry-exam-btn"
                        id="retryExaminations"
                    >

                        <i class="fa-solid fa-rotate"></i>

                        Try Again

                    </button>

                </div>

            </td>

        </tr>

    `;


    const retry =
        document.getElementById(
            "retryExaminations"
        );


    if (retry) {

        retry.addEventListener(
            "click",
            loadExaminations
        );

    }


    setText(
        "tableSummary",
        "Unable to load examinations"
    );

}


/* ==========================================================
   STATUS BADGE
========================================================== */

function getStatusBadge(
    status
) {

    const normalized =
        String(
            status ||
            "Draft"
        ).toLowerCase();


    let label =
        "Draft";


    let className =
        "draft";


    if (
        normalized ===
        "active"
    ) {

        label =
            "Active";

        className =
            "active";

    }
    else if (
        normalized ===
        "upcoming"
    ) {

        label =
            "Upcoming";

        className =
            "upcoming";

    }
    else if (
        normalized ===
        "completed"
    ) {

        label =
            "Completed";

        className =
            "completed";

    }
    else if (
        normalized ===
        "cancelled"
    ) {

        label =
            "Cancelled";

        className =
            "cancelled";

    }


    return `

        <span class="exam-status ${className}">

            ${label}

        </span>

    `;

}


/* ==========================================================
   EXAM ICON
========================================================== */

function getExamIcon(
    exam
) {

    const title =
        String(
            exam.title || ""
        ).toLowerCase();


    const topic =
        String(
            exam.topic || ""
        ).toLowerCase();


    const text =
        `${title} ${topic}`;


    if (
        text.includes("java")
    ) {

        return "fa-brands fa-java";

    }


    if (
        text.includes("python")
    ) {

        return "fa-brands fa-python";

    }


    if (
        text.includes("database") ||
        text.includes("dbms") ||
        text.includes("sql")
    ) {

        return "fa-solid fa-database";

    }


    if (
        text.includes("web") ||
        text.includes("html") ||
        text.includes("javascript") ||
        text.includes("css")
    ) {

        return "fa-solid fa-globe";

    }


    if (
        text.includes("data structure") ||
        text.includes("algorithm") ||
        text.includes("dsa") ||
        text.includes("tree")
    ) {

        return "fa-solid fa-code";

    }


    if (
        text.includes("operating system") ||
        text.includes("operating")
    ) {

        return "fa-solid fa-microchip";

    }


    if (
        text.includes("computer network") ||
        text.includes("network")
    ) {

        return "fa-solid fa-network-wired";

    }


    if (
        title.includes("c++") ||
        title === "cpp"
    ) {

        return "fa-solid fa-code";

    }


    if (
        text.includes("c programming") ||
        title === "c"
    ) {

        return "fa-solid fa-c";

    }


    return "fa-regular fa-file-lines";

}


/* ==========================================================
   DATE FORMAT
========================================================== */

function formatDateTime(
    value
) {

    const date =
        parseDate(
            value
        );


    if (!date) {

        return "Not scheduled";

    }


    return date.toLocaleString(
        "en-IN",
        {
            day: "2-digit",

            month: "short",

            year: "numeric",

            hour: "2-digit",

            minute: "2-digit"
        }
    );

}


/* ==========================================================
   SET TEXT
========================================================== */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {
        return;
    }


    element.textContent =
        value ?? "";

}


/* ==========================================================
   ESCAPE HTML
========================================================== */

function escapeHTML(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}