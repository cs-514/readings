(function () {
  var view = document.getElementById('view'), pick = document.getElementById('datepick'), toastEl = document.getElementById('toast');
  var current = null, dataCache = {};
  function iso(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function todayIso() { return iso(new Date()); }
  function shift(s, n) { var p = s.split('-'); var d = new Date(+p[0], +p[1] - 1, +p[2] + n); return iso(d); }
  function valid(s) { return /^\d{4}-\d{2}-\d{2}$/.test(s || ''); }
  function qDate() { var m = /[?&]date=(\d{4}-\d{2}-\d{2})/.exec(location.search); return m ? m[1] : null; }
  function toast(m) { toastEl.textContent = m; toastEl.classList.add('show'); clearTimeout(toast.t); toast.t = setTimeout(function () { toastEl.classList.remove('show'); }, 1800); }
  function pageLink(date) { return location.origin + location.pathname.replace(/index\.html$/, '') + '?date=' + date; }

  function plainText(d) {
    var dt = new Date(d.date + 'T12:00:00');
    var nice = dt.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    var L = { 'Reading 1': 'First Reading', 'Reading 2': 'Second Reading', 'Responsorial Psalm': 'Psalm' };
    var out = [d.title, nice, 'Mass readings, King James Version', ''];
    d.readings.forEach(function (r) {
      var lab = L[r.label] || r.label;
      r.passages.forEach(function (p) {
        out.push(lab + ': ' + p.ref);
        out.push(p.text ? p.text.replace(/\n\n/g, '\n\n') : p.note);
        out.push('');
      });
    });
    out.push('Meditation');
    if (d.meditation) {
      d.meditation.paragraphs.forEach(function (p) { out.push(p); out.push(''); });
      out.push('\u201c' + d.meditation.quote.text + '\u201d');
      out.push('\u2014 St Augustine');
      if (d.meditation.closing) { out.push(''); out.push(d.meditation.closing); }
    } else out.push('The meditation for this day has not been prepared yet.');
    out.push(''); out.push(pageLink(d.date));
    return out.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
  }

  function copy(text, ok) {
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', '');
      ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); ta.setSelectionRange(0, 1e6);
      var good = false; try { good = document.execCommand('copy'); } catch (e) {} document.body.removeChild(ta);
      toast(good ? ok : 'Copy failed \u2013 long-press to copy instead');
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(function () { toast(ok); }, fallback); else fallback();
  }

  function load(date, push) {
    if (!valid(date)) date = todayIso();
    current = date; pick.value = date;
    if (push) history.pushState(null, '', '?date=' + date);
    view.innerHTML = '<p>Loading\u2026</p>';
    fetch('d/' + date + '/index.html').then(function (r) {
      if (!r.ok) throw new Error('missing');
      return r.text();
    }).then(function (t) {
      var doc = new DOMParser().parseFromString(t, 'text/html');
      var art = doc.getElementById('reading'), js = doc.getElementById('day-data');
      if (!art) throw new Error('bad');
      dataCache[date] = JSON.parse(js.textContent);
      view.innerHTML = ''; view.appendChild(document.importNode(art, true));
      document.title = dataCache[date].title + ' \u2013 ' + date;
    }).catch(function () {
      dataCache[date] = null;
      fetch('data/index.json').then(function (r) { return r.json(); }).catch(function () { return { dates: [] }; }).then(function (ix) {
        var last = ix.dates && ix.dates[ix.dates.length - 1];
        view.innerHTML = '<article id="reading"><h1>Readings not available</h1><p class="missing">The readings for ' + date + ' have not been generated yet' +
          (navigator.onLine === false ? ' (and you appear to be offline)' : '') + '.' + (last ? ' Available through ' + last + '.' : '') + '</p></article>';
      });
    });
  }

  document.getElementById('prev').onclick = function () { load(shift(current, -1), true); };
  document.getElementById('next').onclick = function () { load(shift(current, 1), true); };
  document.getElementById('today').onclick = function () { load(todayIso(), true); };
  pick.onchange = function () { if (valid(pick.value)) load(pick.value, true); };
  window.onpopstate = function () { load(qDate() || todayIso(), false); };
  document.getElementById('copytext').onclick = function () {
    var d = dataCache[current]; if (!d) { toast('Nothing to copy for this date'); return; }
    copy(plainText(d), 'Full text copied');
  };
  document.getElementById('copylink').onclick = function () { copy(pageLink(current), 'Link copied'); };
  load(qDate() || todayIso(), false);
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(function () {});
})();
