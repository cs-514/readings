/* Translation toggle (KJV | WEB-CE). Progressive enhancement: without JS the pages show KJV only. */
(function () {
  var KEY = 'dr-tr', root = document.documentElement;
  function stored() { try { return localStorage.getItem(KEY) === 'web' ? 'web' : 'kjv'; } catch (e) { return 'kjv'; } }
  function fromUrl() { var m = /[?&]tr=(web|kjv)\b/.exec(location.search); return m ? m[1] : null; }
  function get() { return root.getAttribute('data-tr') === 'web' ? 'web' : 'kjv'; }
  function syncUrl(t) {
    var s = location.search.replace(/([?&])tr=[^&]*&?/, '$1').replace(/[?&]$/, '');
    if (t === 'web') s += (s ? '&' : '?') + 'tr=web';
    try { history.replaceState(history.state, '', location.pathname + s + location.hash); } catch (e) {}
  }
  function paint(t) {
    root.setAttribute('data-tr', t);
    var bs = document.querySelectorAll('.trtoggle button');
    for (var i = 0; i < bs.length; i++) bs[i].setAttribute('aria-pressed', String(bs[i].getAttribute('data-tr') === t));
    var as = document.querySelectorAll('a[data-app]');
    for (var j = 0; j < as.length; j++) as[j].href = as[j].href.replace(/&tr=web/, '') + (t === 'web' ? '&tr=web' : '');
  }
  function set(t, user) {
    paint(t);
    if (user) { try { localStorage.setItem(KEY, t); } catch (e) {} syncUrl(t); }
    document.dispatchEvent(new CustomEvent('trchange', { detail: t }));
  }
  root.setAttribute('data-tr', fromUrl() || stored());
  window.drTr = { get: get, set: function (t) { set(t, true); } };
  document.addEventListener('DOMContentLoaded', function () {
    var box = document.createElement('div');
    box.className = 'trtoggle'; box.setAttribute('role', 'group'); box.setAttribute('aria-label', 'Bible translation');
    box.innerHTML = '<button type="button" data-tr="kjv">KJV</button><button type="button" data-tr="web">WEB-CE</button>';
    box.addEventListener('click', function (e) { var b = e.target.closest && e.target.closest('button[data-tr]'); if (b) set(b.getAttribute('data-tr'), true); });
    var anchor = document.querySelector('.actions'), wrap = document.querySelector('.wrap');
    if (anchor) anchor.parentNode.insertBefore(box, anchor); else if (wrap) wrap.insertBefore(box, wrap.firstChild);
    paint(get());
  });
})();
