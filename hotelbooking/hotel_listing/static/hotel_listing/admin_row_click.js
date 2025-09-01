document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("tr").forEach(function (row) {
        let link = row.querySelector("th > a");  // default Django admin link
        if (link) {
            row.style.cursor = "pointer"; // show clickable cursor
            row.addEventListener("click", function () {
                window.location = link.href; // redirect on row click
            });
        }
    });
});
