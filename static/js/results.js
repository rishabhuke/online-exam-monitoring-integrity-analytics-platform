document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("resultSearch");
    const statusFilter = document.getElementById("statusFilter");
    const tableBody = document.getElementById("resultsTableBody");
    const rows = Array.from(tableBody.querySelectorAll("tr"));
    const noResultsMessage = document.getElementById("noResultsMessage");
    const reportButtons = document.querySelectorAll(".table-action-btn");

    function filterResults() {
        const searchValue = searchInput.value.trim().toLowerCase();
        const selectedStatus = statusFilter.value.toLowerCase();

        let visibleCount = 0;

        rows.forEach(row => {
            const examName = row.cells[0].textContent.trim().toLowerCase();
            const rowStatus = row.getAttribute("data-status");

            const matchesSearch = examName.includes(searchValue);
            const matchesStatus =
                selectedStatus === "all" || rowStatus === selectedStatus;

            if (matchesSearch && matchesStatus) {
                row.style.display = "";
                visibleCount++;
            } else {
                row.style.display = "none";
            }
        });

        noResultsMessage.style.display = visibleCount === 0 ? "block" : "none";
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterResults);
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", filterResults);
    }

    reportButtons.forEach(button => {
        button.addEventListener("click", function (e) {
            e.preventDefault();

            const row = this.closest("tr");
            const examName = row.cells[0].textContent.trim();

            alert(`Detailed report for "${examName}" will open here.`);
        });
    });
});