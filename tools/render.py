#!/usr/bin/env python3
"""Merge hand/LLM-authored content/DATE.json (meditation + verified Augustine quote) into public/data/DATE.json,
verify the quote against its source page, and prerender public/d/DATE/index.html (plain semantic HTML)."""
import sys, os, re, json, glob, html, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

def norm(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:!?)])", r"\1", t); t = re.sub(r"\(\s+", "(", t)
    return t.lower().strip()

def verify_quote(q):
    p = f"{ROOT}/cache/src_{re.sub(r'[^a-z0-9]+', '_', q['url'].lower())}.html"
    if not os.path.exists(p): open(p, "w").write(http(q["url"]))
    page = norm(open(p).read())
    return norm(q["text"]) in page

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
         '<p class="sub">Mass readings (USCCB lectionary), text of the King James Version</p>', "</header>"]
    for r in d["readings"]:
        lab = LABELS.get(r["label"], r["label"])
        h.append(f"<section><h2>{esc(lab)}</h2>")
        psalm = lab == "Psalm"
        for p in r["passages"]:
            h.append(f'<p class="cite">{esc(p["ref"])}</p>')
            if p["text"]: h.append(paras(p["text"], psalm))
            else: h.append(f'<p class="missing">{esc(p["note"])}</p>')
            if p["text"] and p.get("note"): h.append(f'<p class="note">{esc(p["note"])}</p>')
        h.append("</section>")
    m = d.get("meditation")
    h.append("<section><h2>Meditation</h2>")
    if m:
        for para in m["paragraphs"]: h.append(f"<p>{esc(para)}</p>")
        q = m["quote"]
        h.append(f'<blockquote><p>\u201c{esc(q["text"])}\u201d</p><footer>\u2014 {esc(q["attribution"])}</footer></blockquote>')
        if m.get("closing"): h.append(f'<p>{esc(m["closing"])}</p>')
    else:
        h.append('<p class="missing">The meditation for this day has not been prepared yet.</p>')
    h.append("</section>")
    src = f'<p class="src">Citations: <a href="{d["source"]}">USCCB daily readings</a>. Scripture text: King James Version (public domain) from bible-api.com; deuterocanonical books from the 1611 KJV Apocrypha.'
    if m: src += f' Augustine translation: {esc(m["quote"]["translation"])} (public domain), <a href="{m["quote"]["url"]}">source</a>.'
    h.append(src + "</p></article>")
    return "\n".join(h)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} \u2013 Mass readings, {date}</title>
<meta name="description" content="Mass readings for {date} in the King James Version, with a short meditation.">
<meta name="theme-color" content="#2b1b3d">
<link rel="stylesheet" href="../../style.css">
{data}</head><body><div class="wrap">
{article}
<p class="src"><a href="../../?date={date}">Open in the app</a></p>
</div></body></html>
"""

def main():
    os.makedirs(f"{ROOT}/public/d", exist_ok=True)
    dates = []
    for f in sorted(glob.glob(f"{ROOT}/public/data/????-??-??.json")):
        d = json.load(open(f)); date = d["date"]
        cp = f"{ROOT}/content/{date}.json"
        d.pop("meditation", None)
        if os.path.exists(cp):
            c = json.load(open(cp))
            if not verify_quote(c["quote"]): raise SystemExit(f"QUOTE NOT FOUND IN SOURCE for {date}")
            d["meditation"] = {"paragraphs": c["paragraphs"], "quote": c["quote"], "closing": c.get("closing")}
            wc = sum(len(p.split()) for p in c["paragraphs"]) + len(c["quote"]["text"].split()) + len((c.get("closing") or "").split())
            print(date, "meditation words:", wc, "quote verified")
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
