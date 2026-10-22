// Dependency-free table filtering for the board. Shows publication state, never scores.
(function () {
  'use strict';
  var q = document.getElementById('q');
  var fs = document.getElementById('fsport');
  var fc = document.getElementById('fconf');
  var fr = document.getElementById('frelease');
  var reset = document.getElementById('reset-filters');
  var count = document.getElementById('count');
  var rows = Array.prototype.slice.call(document.querySelectorAll('#tbl-all tbody tr'));

  function apply() {
    var term = q ? q.value.trim().toLowerCase() : '';
    var sport = fs ? fs.value : '';
    var conf = fc ? fc.value : '';
    var release = fr ? fr.value : '';
    var shown = 0;
    rows.forEach(function (r) {
      var show = (!term || (r.getAttribute('data-text') || '').indexOf(term) !== -1) &&
        (!sport || r.getAttribute('data-sport') === sport) &&
        (!conf || r.getAttribute('data-conf') === conf) &&
        (!release || r.getAttribute('data-release') === release);
      r.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    if (count) count.textContent = (shown === rows.length ? rows.length + ' rows' : shown + ' of ' + rows.length + ' rows');
  }

  if (rows.length) {
    [q, fs, fc, fr].forEach(function (el) {
      if (el) el.addEventListener(el === q ? 'input' : 'change', apply);
    });
    if (reset) reset.addEventListener('click', function () {
      [q, fs, fc, fr].forEach(function (el) { if (el) el.value = ''; });
      apply();
    });
    window.addEventListener('release-refresh', apply);
    apply();
  }

  var ds = document.getElementById('discovery-search');
  var dt = document.getElementById('discovery-table');
  if (ds && dt) {
    var drows = Array.prototype.slice.call(dt.tBodies[0].rows);
    ds.addEventListener('input', function () {
      var term = ds.value.trim().toLowerCase();
      drows.forEach(function (r) {
        r.style.display = !term || r.textContent.toLowerCase().indexOf(term) !== -1 ? '' : 'none';
      });
    });
  }
})();
