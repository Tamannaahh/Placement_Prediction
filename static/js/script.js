document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const content = document.getElementById("main-content");
    const collapseBtn = document.getElementById("sidebarCollapse");

    // Debugging: Check if button is found
    if (!collapseBtn) {
        console.error("Error: Toggle button not found!");
        return;
    }

    collapseBtn.addEventListener("click", function () {
        // Toggle the class 'active' on both elements
        sidebar.classList.toggle("active");
        content.classList.toggle("active");
    });
});