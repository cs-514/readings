#!/usr/bin/env python3
"""(Excerpt brief: see MEDITATION_PROMPT.md.) Merge content/DATE.json (verbatim excerpt <=200 words + lead-in) into public/data/DATE.json,
verify the excerpt against sources/*.txt, and prerender public/d/DATE/index.html (plain semantic HTML)."""
import sys, os, re, json, glob, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

def norm(t, fn=True):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"\{\d+\}|\[ ?Note \d+ ?\]", " ", t)          # page / note markers in Newman Reader texts
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2014", "-").replace("\u2013", "-")
    if fn: t = re.sub(r"([.,;:!?)'\"])\d{1,3}(?=\s|$)", r"\1", t)         # footnote numbers glued to punctuation (CCC, Roman Catechism)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:!?)])", r"\1", t); t = re.sub(r"\(\s+", "(", t)
    return t.lower().strip()

MAX_EXCERPT_WORDS = 200; MAX_LEAD_WORDS = 25; MAX_TOTAL_WORDS = 230
OMIT_RE = re.compile(r"\s+\. \. \.(?=\s|$)|\s*\[\u2026\]\s*")   # ". . ." (preferred, preceded by a space) or legacy "[\u2026]"
def source_text(sid):
    p = f"{ROOT}/sources/{sid}.txt"
    if not os.path.exists(p): raise SystemExit(f"unknown source '{sid}' (no sources/{sid}.txt; run tools/fetch_sources.py)")
    head, _, body = open(p).read().partition("\n\n")
    return head, body

def verify_excerpt(date, ex):
    """The excerpt must occur verbatim in the source text. If the whole text matches contiguously (e.g. the source itself contains
    a genuine ". . ."), it is accepted as is. Otherwise it is split at omission marks (". . ." or legacy "[\u2026]") and every
    segment must occur verbatim, and in order, in the source."""
    head, body = source_text(ex["source"]); FN = ex["source"] in ("ccc", "roman_catechism"); src = norm(body, FN); pos = 0
    if norm(ex["text"], FN) in src: segs = [ex["text"]]
    else: segs = [x for x in OMIT_RE.split(ex["text"]) if x.strip()]
    for sg in segs:
        n = norm(sg, FN); i = src.find(n, pos)
        if i < 0: raise SystemExit(f"EXCERPT NOT FOUND VERBATIM IN SOURCE {ex['source']} for {date}: {sg[:80]!r}")
        pos = i + len(n)
        t = sg.strip()
        if not (t[0].isupper() or t[0] in "\u201c\"'(") or t[-1] not in ".?!\u201d\"'": raise SystemExit(f"{date}: excerpt segment must start and end at sentence boundaries: {t[:40]!r}...{t[-20:]!r}")
    words = len([w for w in OMIT_RE.sub(" ", ex["text"]).split() if w != "."])
    if words > MAX_EXCERPT_WORDS: raise SystemExit(f"{date}: excerpt has {words} words (max {MAX_EXCERPT_WORDS})")
    return words, head

LABELS = {"Reading 1": "First Reading", "Reading 2": "Second Reading", "Responsorial Psalm": "Psalm"}
esc = html.escape

def paras(text, psalm):
    out = []
    for blk in text.split("\n\n"):
        if psalm: out.append('<p class="psalm">' + "<br>\n".join(esc(l) for l in blk.split("\n")) + "</p>")
        else: out.append("<p>" + esc(blk.replace("\n", " ")) + "</p>")
    return "\n".join(out)

def article(d):
    dt = datetime.date.fromisoformat(d["date"])
    nice = f"{dt:%A, %B} {dt.day}, {dt.year}"
    h = [f'<article lang="en" id="reading">', "<header>", f"<h1>{esc(d['title'])}</h1>",
         f'<p class="date"><time datetime="{d["date"]}">{nice}</time></p>',
         '<p class="sub"><span class="tr-kjv">Mass readings (USCCB lectionary), King James Version</span><span class="tr-web">Mass readings (USCCB lectionary), World English Bible, Catholic Edition</span></p>', "</header>"]
    for r in d["readings"]:
        lab = LABELS.get(r["label"], r["label"])
        h.append(f"<section><h2>{esc(lab)}</h2>")
        psalm = lab == "Psalm"
        for p in r["passages"]:
            h.append(f'<p class="cite">{esc(p["ref"])}</p>')
            h.append('<div class="tr-kjv">')
            if p["text"]: h.append(paras(p["text"], psalm))
            else: h.append(f'<p class="missing">{esc(p["note"])}</p>')
            if p["text"] and p.get("note"): h.append(f'<p class="note">{esc(p["note"])}</p>')
            h.append("</div>")
            w = p.get("web") or {"text": None, "note": "The World English Bible (Catholic Edition) text is not available for this passage."}
            h.append('<div class="tr-web">')
            if w.get("text"): h.append(paras(w["text"], psalm))
            else: h.append(f'<p class="missing">{esc(w.get("note") or "")}</p>')
            if w.get("text") and w.get("note"): h.append(f'<p class="note">{esc(w["note"])}</p>')
            h.append("</div>")
        h.append("</section>")
    m = d.get("excerpt")
    h.append("<section><h2>Meditation</h2>")
    if m:
        if m.get("lead_in"): h.append(f'<p class="lead"><em>{esc(m["lead_in"])}</em></p>')
        h.append("<blockquote>" + "".join(f"<p>{esc(x.replace(chr(10), ' '))}</p>" for x in m["text"].split("\n\n")))
        u = m.get("url"); at = esc(m["attribution"])
        h.append(f'<footer>\u2014 {f"<a href=\"{esc(u)}\">{at}</a>" if u else at}</footer></blockquote>')
    else:
        h.append('<p class="missing">No excerpt has been chosen for this day yet.</p>')
    h.append("</section>")
    src = f'<p class="src">Citations: <a href="{d["source"]}">USCCB daily readings</a>. <span class="tr-kjv">Scripture text: King James Version (public domain) from bible-api.com; deuterocanonical books from the 1611 KJV Apocrypha.</span>'
    src += ' <span class="tr-web">Scripture text: World English Bible, Catholic Edition, from <a href="https://ebible.org/find/details.php?id=engwebc">eBible.org</a>. Public domain (not copyrighted); \u201cWorld English Bible\u201d is a trademark of eBible.org. The wording is unaltered; only verse numbers and notes are omitted.</span>'
    h.append(src + "</p></article>")
    return "\n".join(h)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} \u2013 Mass readings, {date}</title>
<meta name="description" content="Mass readings for {date} in the King James Version, with an excerpt showing how the Old and New Testaments illuminate each other.">
<meta name="theme-color" content="#2b1b3d">
<link rel="stylesheet" href="../../style.css">
<script src="../../tr.js"></script>
{data}</head><body><div class="wrap">
{article}
<p class="src"><a href="../../?date={date}" data-app>Open in the app</a></p>
</div></body></html>
"""

def main():
    os.makedirs(f"{ROOT}/public/d", exist_ok=True)
    dates = []
    for f in sorted(glob.glob(f"{ROOT}/public/data/????-??-??.json")):
        d = json.load(open(f)); date = d["date"]
        cp = f"{ROOT}/content/{date}.json"
        d.pop("meditation", None); d.pop("excerpt", None)
        if os.path.exists(cp):
            c = json.load(open(cp))
            ex = c["excerpt"]; lead = c.get("lead_in") or ""
            words, head = verify_excerpt(date, ex)
            lw = len(lead.split())
            if lw > MAX_LEAD_WORDS or words + lw > MAX_TOTAL_WORDS: raise SystemExit(f"{date}: lead-in {lw} words / total {words + lw} too long")
            d["excerpt"] = {"lead_in": lead, "text": ex["text"], "attribution": ex["attribution"], "source": ex["source"],
                            "url": ex.get("url") or re.search(r"URL: (\S+)", head).group(1)}
            print(date, "excerpt words:", words, "+ lead-in", lw, "- verified verbatim in", ex["source"])
        json.dump(d, open(f, "w"), indent=1, ensure_ascii=False)
        os.makedirs(f"{ROOT}/public/d/{date}", exist_ok=True)
        art = article(d)
        dt = datetime.date.fromisoformat(date)
        data = '<script type="application/json" id="day-data">' + json.dumps(d, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
        page = PAGE.format(title=esc(d["title"]), date=date, article=art, data=data)
        open(f"{ROOT}/public/d/{date}/index.html", "w").write(page)
        dates.append(date)
    json.dump({"dates": dates, "generated": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"}, open(f"{ROOT}/public/data/index.json", "w"))
    print(len(dates), "days rendered")
main()
