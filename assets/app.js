// Minimal, dependency-free table filtering for the OLBG3 board.
(function () {
  var q = document.getElementById('q');
  var fs = document.getElementById('fsport');
  var fc = document.getElementById('fconf');
  var count = document.getElementById('count');
  if (!q || !fs || !fc) return;

  // only the main board table: the page also has a coverage table and a picks table
  var rows = Array.prototype.slice.call(document.querySelectorAll('#tbl-all tbody tr'));

  function apply() {
    var term = q.value.trim().toLowerCase();
    var sport = fs.value;
    var conf = fc.value;
    var shown = 0;
    rows.forEach(function (r) {
      var okText = !term || (r.getAttribute('data-text') || '').indexOf(term) !== -1;
      var okSport = !sport || r.getAttribute('data-sport') === sport;
      var okConf = !conf || r.getAttribute('data-conf') === conf;
      var show = okText && okSport && okConf;
      r.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    if (count) count.textContent = (shown === rows.length ? rows.length + ' rows' : shown + ' of ' + rows.length + ' rows');
  }

  q.addEventListener('input', apply);
  fs.addEventListener('change', apply);
  fc.addEventListener('change', apply);
  apply();
})();
