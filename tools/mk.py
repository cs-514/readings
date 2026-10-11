#!/usr/bin/env python3
"""Helper: build content/DATE.json by *extracting* verbatim segments from sources/SRC.txt (no retyping).
usage: mk.py DATE SRC "attribution" "lead-in" "start phrase>>end phrase" ["start2>>end2" ...]
Each segment runs from the first occurrence of 'start phrase' through the end of 'end phrase' (first occurrence after the start);
segments are joined with ' . . . '. Use 'start>>' alone is not allowed. Prints the result for review; render.py still verifies."""
import sys, os, re, json, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def disp(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"\{\d+\}|\[ ?Note \d+ ?\]", " ", t)
    t = t.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2014", "-").replace("\u2013", "-")
    t = re.sub(r"([.,;:!?)'\"])\d{1,3}(?=\s|$)", r"\1", t)
    t = re.sub(r"\s+", " ", t); t = re.sub(r"\s+([,.;:!?)])", r"\1", t); t = re.sub(r"\(\s+", "(", t)
    return t
def curly(t):
    t = re.sub(r'(^|[\s(\[])"', lambda m: m.group(1) + "\u201c", t); t = t.replace('"', "\u201d")
    t = re.sub(r"(^|[\s(\[\u201c])'", lambda m: m.group(1) + "\u2018", t); return t.replace("'", "\u2019")
def main():
    date, sid, attr, lead = sys.argv[1:5]; specs = sys.argv[5:]
    head, _, body = open(f"{ROOT}/sources/{sid}.txt").read().partition("\n\n")
    d = disp(body); dl = d.lower(); out = []; pos = 0
    for sp in specs:
        a, _, b = sp.partition(">>"); a = disp(a).strip(); b = disp(b).strip().rstrip()
        i = dl.find(a.lower(), pos)
        if i < 0: raise SystemExit(f"start not found: {a[:60]!r}")
        j = dl.find(b.lower(), i)
        if j < 0: raise SystemExit(f"end not found: {b[:60]!r}")
        seg = d[i:j + len(b)].strip(); pos = j + len(b)
        if not (seg[0].isupper() or seg[0] in "\"'(") or seg[-1] not in ".?!\"'": print("WARNING: boundary:", repr(seg[:30]), repr(seg[-15:]))
        out.append(seg)
    text = " . . . ".join(out); text = curly(text); w = len([x for x in text.replace(" . . . ", " ").split()])
    print(f"{date} [{sid}] {w} words, lead {len(lead.split())}\n{text}\n")
    if w > 200 or len(lead.split()) > 25: print("!!! TOO LONG")
    json.dump({"lead_in": lead, "excerpt": {"text": text, "source": sid, "attribution": attr}}, open(f"{ROOT}/content/{date}.json", "w"), indent=1, ensure_ascii=False)
main()
