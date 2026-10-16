(function () {
  var view = document.getElementById('view'), pick = document.getElementById('datepick'), toastEl = document.getElementById('toast');
  var current = null, dataCache = {};
  function iso(d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function todayIso() { return iso(new Date()); }
  function shift(s, n) { var p = s.split('-'); var d = new Date(+p[0], +p[1] - 1, +p[2] + n); return iso(d); }
  function valid(s) { return /^\d{4}-\d{2}-\d{2}$/.test(s || ''); }
  function qDate() { var m = /[?&]date=(\d{4}-\d{2}-\d{2})/.exec(location.search); return m ? m[1] : null; }
  function toast(m) { toastEl.textContent = m; toastEl.classList.add('show'); clearTimeout(toast.t); toast.t = setTimeout(function () { toastEl.classList.remove('show'); }, 1800); }
  function curTr() { return window.drTr ? window.drTr.get() : 'kjv'; }
  function pageLink(date) { return location.origin + location.pathname.replace(/index\.html$/, '') + '?date=' + date + (curTr() === 'web' ? '&tr=web' : ''); }

  function plainText(d) {
    var dt = new Date(d.date + 'T12:00:00');
    var nice = dt.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    var L = { 'Reading 1': 'First Reading', 'Reading 2': 'Second Reading', 'Responsorial Psalm': 'Psalm' };
    var web = curTr() === 'web';
    var out = [d.title, nice, web ? 'Mass readings, World English Bible, Catholic Edition' : 'Mass readings, King James Version', ''];
    d.readings.forEach(function (r) {
      var lab = L[r.label] || r.label;
      r.passages.forEach(function (p) {
        out.push(lab + ': ' + p.ref);
        var src = web ? (p.web || { text: null, note: 'The World English Bible (Catholic Edition) text is not available for this passage.' }) : p;
        out.push(src.text ? src.text : src.note);
        out.push('');
      });
    });
    out.push('Meditation');
    if (d.excerpt) {
      if (d.excerpt.lead_in) { out.push(d.excerpt.lead_in); out.push(''); }
      out.push('\u201c' + d.excerpt.text + '\u201d');
      out.push(''); out.push('\u2014 ' + d.excerpt.attribution);
    } else out.push('No excerpt has been chosen for this day yet.');
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
    if (window.speechSynthesis && typeof stopReading === 'function' && reading) stopReading();
    if (!valid(date)) date = todayIso();
    current = date; pick.value = date;
    if (push) history.pushState(null, '', '?date=' + date + (curTr() === 'web' ? '&tr=web' : ''));
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

  // Read aloud (built-in device voices)
  var synth = window.speechSynthesis, rBtn = document.getElementById('readaloud'), pBtn = document.getElementById('readpause'), reading = false;
  if (!synth) rBtn.hidden = true;
  function bestVoice() {
    var v = (synth.getVoices() || []).filter(function (x) { return /^en(-|_)/i.test(x.lang); });
    function score(x) { var n = x.name; return (/premium/i.test(n) ? 40 : /enhanced/i.test(n) ? 30 : 0) + (/en.US/i.test(x.lang) ? 5 : 0) + (/samantha|ava|zoe|evan|nathan|allison|tom/i.test(n) ? 3 : 0) - (/eloquence|novelty|bad news|bells|bubbles|cellos|jester|organ|trinoids|whisper|zarvox|albert|bahh|boing|fred|junior|ralph|kathy|grandma|grandpa|rocko|shelley|reed|sandy|flo|eddy/i.test(n) ? 50 : 0); }
    return v.sort(function (a, b) { return score(b) - score(a); })[0] || null;
  }
  function split(t) {
    t = t.replace(/https?:\S+/g, '').replace(/\u2014 /g, '').replace(/\. \. \./g, ',');
    var out = [];
    t.split(/\n+/).forEach(function (para) {
      para = para.trim(); if (!para) return;
      var buf = '';
      (para.match(/[^.!?;:]+[.!?;:]*["\u201d\u2019]*\s*/g) || [para]).forEach(function (s) {
        if (buf && (buf + s).length > 220) { out.push(buf.trim()); buf = ''; }
        buf += s;
      });
      if (buf.trim()) out.push(buf.trim());
    });
    return out;
  }
  function stopReading() { reading = false; synth.cancel(); rBtn.textContent = '\u25b6 Read this page'; pBtn.hidden = true; pBtn.textContent = 'Pause'; }
  rBtn.onclick = function () {
    if (reading) { stopReading(); return; }
    var d = dataCache[current]; if (!d) { toast('Nothing to read for this date'); return; }
    synth.cancel();
    var parts = split(plainText(d)), voice = bestVoice(), i = 0;
    reading = true; rBtn.textContent = '\u25a0 Stop reading'; pBtn.hidden = false;
    function next() {
      if (!reading || i >= parts.length) { stopReading(); return; }
      var u = new SpeechSynthesisUtterance(parts[i++]);
      if (voice) { u.voice = voice; u.lang = voice.lang; } else u.lang = 'en-US';
      u.rate = 0.95; u.onend = next; u.onerror = function (e) { if (e.error !== 'interrupted' && e.error !== 'canceled') next(); };
      synth.speak(u);
    }
    next();
  };
  pBtn.onclick = function () {
    if (synth.paused) { synth.resume(); pBtn.textContent = 'Pause'; } else { synth.pause(); pBtn.textContent = 'Resume'; }
  };
  if (synth) { synth.getVoices(); synth.onvoiceschanged = function () {}; }
  window.addEventListener('pagehide', function () { if (reading) stopReading(); });
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(function () {});
})();
