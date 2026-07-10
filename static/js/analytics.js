document.addEventListener("DOMContentLoaded", function () {
    const bars = document.querySelectorAll(".metric-bar, .subject-progress-fill");

    bars.forEach(bar => {
        const finalWidth = bar.style.width || window.getComputedStyle(bar).width;
        bar.style.width = "0";

        setTimeout(() => {
            bar.style.width = finalWidth;
        }, 250);
    });
});