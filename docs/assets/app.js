/* Search, filter and sort for the static tables. No dependencies. */
(function () {
  function textOf(row) { return (row.textContent || "").toLowerCase(); }

  function wireFilter(table, input, sel) {
    var rows = Array.prototype.slice.call(table.tBodies[0].rows);
    var countEl = document.getElementById("count");
    function apply() {
      var q = (input && input.value || "").toLowerCase().trim();
      var conf = sel ? sel.value : "";
      var shown = 0;
      rows.forEach(function (r) {
        var okQ = !q || textOf(r).indexOf(q) !== -1;
        var okC = !conf || textOf(r).indexOf(conf) !== -1;
        var show = okQ && okC;
        r.style.display = show ? "" : "none";
        if (show) shown++;
      });
      if (countEl) countEl.textContent = shown + " of " + rows.length + " rows";
    }
    if (input) input.addEventListener("input", apply);
    if (sel) sel.addEventListener("change", apply);
    apply();
  }

  document.querySelectorAll("table.filterable").forEach(function (t) {
    wireFilter(t, document.getElementById("q"), document.getElementById("conf"));
  });

  document.querySelectorAll("table.sortable").forEach(function (table) {
    var ths = table.tHead ? table.tHead.rows[0].cells : [];
    Array.prototype.forEach.call(ths, function (th, idx) {
      th.style.cursor = "pointer";
      th.title = "Sort by this column";
      var dir = 1;
      th.addEventListener("click", function () {
        var body = table.tBodies[0];
        var rows = Array.prototype.slice.call(body.rows);
        rows.sort(function (a, b) {
          var av = a.cells[idx] ? a.cells[idx].textContent.trim() : "";
          var bv = b.cells[idx] ? b.cells[idx].textContent.trim() : "";
          var an = parseFloat(av.replace(/[^0-9.\-]/g, ""));
          var bn = parseFloat(bv.replace(/[^0-9.\-]/g, ""));
          if (!isNaN(an) && !isNaN(bn) && (th.classList.contains("num") || /^[0-9]/.test(av))) {
            return (an - bn) * dir;
          }
          return av.localeCompare(bv) * dir;
        });
        dir = -dir;
        rows.forEach(function (r) { body.appendChild(r); });
      });
    });
  });
})();
