// =====================================
// Candidate Name
// =====================================

const candidateName =
    localStorage.getItem("candidateName") || "Candidate";

const candidateElement = document.getElementById("candidateName");

if (candidateElement) {
    candidateElement.textContent = candidateName;
}

// =====================================
// Swiper Initialization
// =====================================

const swiper = new Swiper(".dashboardSwiper", {

    slidesPerView: 1,

    spaceBetween: 0,

    loop: false,

    speed: 700,

    observer: true,

    observeParents: true,

    observeSlideChildren: true,

    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },

    autoplay: {
        delay: 1000,
        disableOnInteraction: false,
    }

});

// =====================================
// Load Dashboard Exam Slides
// =====================================

async function loadExamSlides() {

    try {

        const response = await fetch("/api/exams");

        if (!response.ok) {
            throw new Error("Failed to load exams.");
        }

        const exams = await response.json();

        const wrapper = document.querySelector(".dashboardSwiper .swiper-wrapper");

        // Remove previously generated slides
        document.querySelectorAll(".exam-dynamic").forEach(slide => slide.remove());

        // No exams
        if (!Array.isArray(exams) || exams.length === 0) {

            wrapper.appendChild(createNoExamSlide());

        } else {

            exams.forEach(exam => {

                wrapper.appendChild(createExamSlide(exam));

            });

        }

        swiper.update();

        swiper.slideTo(0, 0);

    }

    catch (err) {

        console.error(err);

    }

}

// =====================================
// Create Exam Slide
// =====================================

function createExamSlide(exam) {

    const slide = document.createElement("div");

    slide.className = "swiper-slide exam-dynamic";

    slide.innerHTML = `

        <div class="exam-slide">

            <div class="exam-info">

                <h2>${exam.title}</h2>

                <div class="exam-meta">


                    <span>
                        <i class="fa-solid fa-clock"></i>
                        ${exam.start_time}
                    </span>
                       <span>
        <i class="fa-solid fa-star"></i>
        ${exam.total_marks} Marks
    </span>

                    <span>
                        <i class="fa-solid fa-hourglass-half"></i>
                        ${exam.duration} Minutes
                    </span>

                </div>

                <p>
    ${
        exam.exam_status === "Available"
        ? "Your examination is now available. Ensure your webcam and microphone are active before starting. Complete the exam within the allotted duration."

        : exam.exam_status === "Completed"
        ? "You have successfully completed this examination. You can review your performance and results from the Results section."

        : "This examination has not started yet. Please return at the scheduled start time to begin your exam."
    }
</p>

                ${
    exam.exam_status === "Available"
    ? `
        <a href="/exam/${exam.id}" class="exam-btn">
            <i class="fa-solid fa-play"></i>
            Start Exam
        </a>
      `
    : exam.exam_status === "Completed"
    ? `
        <a href="/results" class="exam-btn completed-btn">
            <i class="fa-solid fa-circle-check"></i>
            Completed
        </a>
      `
    : `
        <button class="exam-btn" disabled style="opacity:.6;cursor:not-allowed;">
            <i class="fa-solid fa-lock"></i>
            Not Yet Available
        </button>
      `
}

            </div>

            <div class="exam-icon">

                <i class="fa-solid fa-book-open"></i>

            </div>

        </div>

    `;

    return slide;

}

// =====================================
// No Exams Slide
// =====================================

function createNoExamSlide() {

    const slide = document.createElement("div");

    slide.className = "swiper-slide exam-dynamic";

    slide.innerHTML = `

        <div class="exam-slide">

            <div class="exam-info">

                <h2>No Upcoming Exams</h2>

                <p>
                    There are currently no examinations scheduled for you.
                </p>

            </div>

            <div class="exam-icon">

                <i class="fa-solid fa-calendar-xmark"></i>

            </div>

        </div>

    `;

    return slide;

}

// =====================================
// Initial Load
// =====================================

document.addEventListener("DOMContentLoaded", () => {

    loadExamSlides();

});