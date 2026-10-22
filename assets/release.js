/* A static page must not keep a HIGH release alive after its official cutoff.
   This changes publication labels only, never predicts final scores or outcomes. */
(function () {
  'use strict';
  function refresh() {
    var now = Date.now();
    document.querySelectorAll('[data-expires-at]').forEach(function (node) {
      var cutoff = Date.parse(node.getAttribute('data-expires-at'));
      if (!Number.isFinite(cutoff) || now < cutoff || node.getAttribute('data-clock-expired') === 'true') return;
      node.setAttribute('data-clock-expired', 'true');
      node.setAttribute('data-conf', 'MEDIUM');
      node.setAttribute('data-release', 'release_expired');
      node.querySelectorAll('.pill.high, .badge-high').forEach(function (badge) {
        badge.classList.remove('high', 'badge-high');
        badge.classList.add('medium');
        badge.textContent = 'ANALYSIS';
      });
      var notice = document.createElement(node.tagName === 'TR' ? 'span' : 'p');
      notice.className = 'note release-expired';
      notice.textContent = 'Release expired — scheduled start or source-age cutoff reached. Research only; result unverified.';
      if (node.tagName === 'TR') {
        var cell = node.querySelector('.release-cell') || node.lastElementChild;
        if (cell) cell.appendChild(notice);
      } else node.insertBefore(notice, node.firstChild);
    });
    var remaining = document.querySelectorAll('[data-current-high]:not([data-clock-expired="true"])').length;
    document.querySelectorAll('[data-high-count]').forEach(function (node) { node.textContent = remaining; });
    window.dispatchEvent(new Event('release-refresh'));
  }
  refresh();
  window.setInterval(refresh, 60000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) refresh(); });
})();
