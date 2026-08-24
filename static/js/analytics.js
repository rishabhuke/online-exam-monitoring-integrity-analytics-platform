document.addEventListener(
    "DOMContentLoaded",
    loadCandidateAnalytics
);


async function loadCandidateAnalytics() {

    try {

        const response =
            await fetch(
                "/api/candidate/analytics",
                {
                    method: "GET",
                    credentials: "include"
                }
            );


        const data =
            await response.json();


        if (!response.ok || !data.success) {

            throw new Error(
                data.message ||
                "Unable to load analytics"
            );

        }


        renderStats(
            data.stats
        );


        renderOverview(
            data.stats,
            data.overview
        );


        renderInsights(
            data.insights
        );


        renderSubjects(
            data.subjects
        );


        renderRecentActivity(
            data.recent_activity
        );


        renderSuggestions(
            data.suggestions
        );


    } catch (error) {

        console.error(
            "Analytics error:",
            error
        );

        showAnalyticsError(
            error.message
        );

    }

}
function renderStats(stats) {

    document.getElementById(
        "totalExams"
    ).textContent =
        stats.total_exams;


    document.getElementById(
        "averageScore"
    ).textContent =
        `${stats.average_score}%`;


    document.getElementById(
        "bestScore"
    ).textContent =
        `${stats.best_score}%`;


    document.getElementById(
        "consistency"
    ).textContent =
        `${stats.consistency}%`;

}
function renderOverview(
    stats,
    overview
) {

    const total =
        stats.total_exams;


    const passed =
        overview.passed_exams;


    let passedPercentage = 0;


    if (total > 0) {

        passedPercentage =
            (passed / total) * 100;

    }


    document.getElementById(
        "passedExams"
    ).textContent =
        `${passed} / ${total}`;


    document.getElementById(
        "passedBar"
    ).style.width =
        `${passedPercentage}%`;


    document.getElementById(
        "accuracy"
    ).textContent =
        `${overview.accuracy}%`;


    document.getElementById(
        "accuracyBar"
    ).style.width =
        `${Math.min(
            Math.max(
                overview.accuracy,
                0
            ),
            100
        )}%`;


    /*
     * Improvement can be negative.
     *
     * For the visual bar, clamp it
     * between 0 and 100.
     */

    const improvement =
        Math.max(
            0,
            Math.min(
                overview.improvement_rate,
                100
            )
        );


    document.getElementById(
        "improvementRate"
    ).textContent =
        `${overview.improvement_rate}%`;


    document.getElementById(
        "improvementBar"
    ).style.width =
        `${improvement}%`;

}
function renderInsights(insights) {

    const container =
        document.getElementById(
            "insightList"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(insights) ||
        insights.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-lightbulb"></i>
                Not enough exam data to generate insights.
            </div>
        `;

        return;

    }


    insights.forEach(
        function (insight) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "insight-card";


            let icon =
                "fa-lightbulb";


            if (
                insight.type ===
                "strength"
            ) {

                icon =
                    "fa-arrow-trend-up";

            } else if (
                insight.type ===
                "improvement"
            ) {

                icon =
                    "fa-triangle-exclamation";

            } else if (
                insight.type ===
                "progress"
            ) {

                icon =
                    "fa-chart-line";

            } else if (
                insight.type ===
                "accuracy"
            ) {

                icon =
                    "fa-bullseye";

            }


            item.innerHTML = `

                <i class="fa-solid ${icon}"></i>

                <div>

                    <h4>
                        ${escapeHtml(
                            insight.title
                        )}
                    </h4>

                    <p>
                        ${escapeHtml(
                            insight.description
                        )}
                    </p>

                </div>

            `;


            container.appendChild(
                item
            );

        }
    );

}
function renderSubjects(subjects) {

    const container =
        document.getElementById(
            "subjectPerformance"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(subjects) ||
        subjects.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-book"></i>
                No subject performance available yet.
            </div>
        `;

        return;

    }


    subjects.forEach(
        function (subject, index) {

            const percentage =
                Math.max(
                    0,
                    Math.min(
                        Number(
                            subject.percentage
                        ),
                        100
                    )
                );


            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "subject-card";


            card.innerHTML = `

                <div class="subject-top">

                    <h3>
                        ${escapeHtml(
                            subject.subject
                        )}
                    </h3>

                    <span>
                        ${percentage}%
                    </span>

                </div>


                <div class="subject-progress">

                    <div
                        class="subject-progress-fill"
                        style="
                            width:${percentage}%;
                            background:${getSubjectColor(index)};
                        "
                    ></div>

                </div>


                <p>
                    Based on
                    ${subject.exam_count}
                    completed
                    ${
                        subject.exam_count === 1
                            ? "assessment"
                            : "assessments"
                    }.
                </p>

            `;


            container.appendChild(
                card
            );

        }
    );

}
function getSubjectColor(index) {

    const colors = [
        "linear-gradient(90deg,#2563eb,#3b82f6)",
        "linear-gradient(90deg,#16a34a,#22c55e)",
        "linear-gradient(90deg,#7c3aed,#8b5cf6)",
        "linear-gradient(90deg,#f59e0b,#f97316)"
    ];


    return colors[
        index % colors.length
    ];

}
function renderRecentActivity(
    activities
) {

    const container =
        document.getElementById(
            "activityList"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(activities) ||
        activities.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-clock"></i>
                No completed exams yet.
            </div>
        `;

        return;

    }


    activities.forEach(
        function (activity, index) {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "activity-item";


            const iconClass =
                getActivityIcon(
                    activity.topic
                );


            const iconColor =
                getActivityIconClass(
                    index
                );


            item.innerHTML = `

                <div
                    class="activity-icon ${iconColor}"
                >

                    <i class="fa-solid ${iconClass}">
                    </i>

                </div>


                <div class="activity-content">

                    <h4>
                        ${escapeHtml(
                            activity.title
                        )}
                    </h4>

                    <p>

                        Completed on
                        ${formatDate(
                            activity.submitted_at
                        )}

                        ·

                        Score:
                        ${activity.score}/
                        ${activity.total_questions}

                        ·

                        ${activity.percentage}%

                    </p>

                </div>

            `;


            container.appendChild(
                item
            );

        }
    );

}

function getActivityIcon(topic) {

    const value =
        String(
            topic || ""
        ).toLowerCase();


    if (value.includes("java")) {
        return "fa-code";
    }


    if (
        value.includes("database") ||
        value.includes("dbms") ||
        value.includes("sql")
    ) {

        return "fa-database";

    }


    if (
        value.includes("web") ||
        value.includes("html") ||
        value.includes("css") ||
        value.includes("javascript")
    ) {

        return "fa-globe";

    }


    if (value.includes("python")) {
        return "fa-python";
    }


    return "fa-file-lines";

}


function getActivityIconClass(index) {

    const classes = [
        "blue-icon",
        "green-icon",
        "orange-icon"
    ];


    return classes[
        index % classes.length
    ];

}
function renderSuggestions(
    suggestions
) {

    const container =
        document.getElementById(
            "suggestionList"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(suggestions) ||
        suggestions.length === 0
    ) {

        container.innerHTML = `
            <li>
                Continue practicing consistently.
            </li>
        `;

        return;

    }


    suggestions.forEach(
        function (suggestion) {

            const li =
                document.createElement(
                    "li"
                );


            li.textContent =
                suggestion;


            container.appendChild(
                li
            );

        }
    );

}
function escapeHtml(value) {

    if (value === null ||
        value === undefined) {

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


function formatDate(value) {

    if (!value) {
        return "Unknown date";
    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

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


function showAnalyticsError(
    message
) {

    const containers = [
        "insightList",
        "subjectPerformance",
        "activityList"
    ];


    containers.forEach(
        function (id) {

            const element =
                document.getElementById(
                    id
                );


            if (element) {

                element.innerHTML = `

                    <div class="empty-state">

                        <i class="fa-solid fa-circle-exclamation"></i>

                        ${escapeHtml(
                            message
                        )}

                    </div>

                `;

            }

        }
    );

}