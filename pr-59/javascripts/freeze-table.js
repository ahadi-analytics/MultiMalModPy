document.addEventListener("DOMContentLoaded", function () {
    const tables = document.querySelectorAll("table");

    tables.forEach(table => {
        table.style.position = "relative";
        table.style.borderCollapse = "collapse";

        const thead = table.querySelector("thead");
        if (thead) {
            thead.style.position = "sticky";
            thead.style.top = "0";
            thead.style.background = "white";
            thead.style.zIndex = "2";
        }

        table.querySelectorAll("tr").forEach(row => {
            const firstCell = row.cells[0];
            if (firstCell) {
                firstCell.style.position = "sticky";
                firstCell.style.left = "0";
                firstCell.style.background = "white";
                firstCell.style.zIndex = "3";
            }
        });
    });
});




//document.addEventListener("DOMContentLoaded", function () {
//    const tables = document.querySelectorAll("table");
//
//    tables.forEach(table => {
//        makeTableScrollable(table);
//        freezeTableHeaders(table);
//        freezeFirstColumn(table);
//    });
//});
//
///**
// * Wraps the table inside a scrollable container.
// * Ensures the table is limited to 20 rows with vertical scrolling.
// *
// * @param {HTMLTableElement} table - The table element to modify.
// */
//function makeTableScrollable(table) {
//    const wrapper = document.createElement("div");
//    wrapper.style.overflowY = "auto";
//    wrapper.style.border = "1px solid #ddd";
//    wrapper.style.position = "relative";
//
//    // Calculate row height dynamically
//    const firstRow = table.querySelector("tr");
//    if (firstRow) {
//        const rowHeight = firstRow.getBoundingClientRect().height;
//        wrapper.style.maxHeight = `${rowHeight * 21}px`; // 20 rows + 1 header row
//    } else {
//        wrapper.style.maxHeight = "500px"; // Fallback
//    }
//
//    table.parentNode.insertBefore(wrapper, table);
//    wrapper.appendChild(table);
//}
//
///**
// * Makes the first row (header) of the table sticky.
// * Ensures that the table headers remain visible when scrolling down.
// *
// * @param {HTMLTableElement} table - The table element to modify.
// */
//function freezeTableHeaders(table) {
//    const thead = table.querySelector("thead");
//    const firstRow = table.querySelector("tbody tr:first-child");
//
//    if (thead) {
//        thead.style.position = "sticky";
//        thead.style.top = "0";
//        thead.style.background = "white";
//        thead.style.zIndex = "2";
//    }
//
//    // Ensure first row inside tbody is also sticky
//    if (firstRow) {
//        firstRow.style.position = "sticky";
//        firstRow.style.top = thead ? `${thead.offsetHeight}px` : "0";
//        firstRow.style.background = "white";
//        firstRow.style.zIndex = "1";
//    }
//}
//
///**
// * Makes the first column of the table sticky.
// * Ensures that the first column remains visible when scrolling horizontally.
// *
// * @param {HTMLTableElement} table - The table element to modify.
// */
//function freezeFirstColumn(table) {
//    table.querySelectorAll("tr").forEach(row => {
//        const firstCell = row.cells[0];
//        if (firstCell) {
//            firstCell.style.position = "sticky";
//            firstCell.style.left = "0";
//            firstCell.style.background = "white";
//            firstCell.style.zIndex = "3";
//        }
//    });
//}
