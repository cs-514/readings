#!/usr/bin/env python3
"""Build static JSON for a date: USCCB citations -> KJV text (no verse numbers).
usage: build.py YYYY-MM-DD [YYYY-MM-DD ...] | --days N (from today) """
import sys, json, re, datetime, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

MIN_SCORE = 0.22   # below this we refuse to show text (see README)
SHIFTS = [0, -1, -2, -3, 1, -4]
SECTION_KEEP = lambda l: not l.lower().startswith(("or", "alleluia", "verse before", "gospel acclamation", "lenten gospel acclamation", "sequence"))

# NABRE (Hebrew/Greek-based) -> KJV special cross-chapter mappings: (bid,c1,v1,c2,v2) -> [(bid,c1,v1,c2,v2)...]
def special(bid, el):
    c1, v1, c2, v2 = el
    if bid == "ISA" and c1 == 8 and v1 == 23:                 # Isa 8:23-9:x == KJV 9:1-(x+1)
        return [("ISA", 9, 1, 9, v2 + 1 if c2 == 9 else 1)]
    if bid == "JOL" and c1 == 3: return [("JOL", 2, v1 + 27, 2, v2 + 27)] if v2 <= 5 else None
    if bid == "JOL" and c1 == 4: return [("JOL", 3, v1, c2 - 1, v2)]
    if bid == "MAL" and c1 == 3 and v1 >= 19: return [("MAL", 4, v1 - 18, 4, v2 - 18)]
    if bid == "JON" and c1 == 2 and v1 == 1: return [("JON", 1, 17, 2, v2 - 1)]
    if bid == "JON" and c1 == 2: return [("JON", 2, v1 - 1, 2, v2 - 1)]
    if bid == "DAN" and c1 == 3 and v1 >= 24 and c2 == 3: return [("S3Y", 1, v1 - 23, 1, v2 - 23)]
    if bid == "DAN" and c1 == 13: return [("SUS", 1, v1, c2 - 12, v2)] if c2 == 13 else [("SUS", 1, v1, 1, 64)]
    if bid == "DAN" and c1 == 14: return [("BEL", 1, v1, 1, v2)]
    if bid == "EST" and c1 >= 12: return "NOKJV"           # Additions to Esther (C, D) are not in the KJV Apocrypha text we have
    if bid == "HOS" and c1 == 2 and v1 <= 2: return [("HOS", 1, 9 + v1, 1, 9 + v2)]
    return None

REF_OVERRIDE = {  # NABRE ref -> list of (c1,v1,c2,v2) in KJV numbering (same book)
    "Isaiah 63:16b-17, 19b; 64:2-7": [(63, 16, 63, 17), (64, 1, 64, 7)],
    "Isaiah 63:16b-17, 19b; 64:2-7": [(63, 16, 63, 17), (64, 1, 64, 7)],
}
def gather(ref):
    book, els = parse_ref(ref)
    if ref in REF_OVERRIDE: els = REF_OVERRIDE[ref]
    bid = BOOKS[book]
    # specials first
    sp = [special(bid, e) for e in els]
    if any(s == "NOKJV" for s in sp):
        return None, "Additions to Esther are not part of the KJV text available here."
    def render(shift):
        verses = []
        for e, s in zip(els, sp):
            if s:
                for (b, a1, a2, a3, a4) in s: verses += [(b, c, v, t) for c, v, t in fetch_range(b, a1, a2, a3, a4, 0)]
            else:
                verses += [(bid, c, v, t) for c, v, t in fetch_range(bid, *e, shift)]
        return verses
    allow_shift = not any(sp) and ref not in REF_OVERRIDE and len({e[0] for e in els}) == 1 and all(e[0] == e[2] for e in els)
    return (render, allow_shift), None

def bid_is_nt(ref):
    try: return BOOKS[parse_ref(ref)[0]] in NT
    except Exception: return False
NT = set('MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS 1PE 2PE 1JN 2JN 3JN JUD REV'.split())

def build_ref(ref, usccb_text):
    try: g, err = gather(ref)
    except Exception as e: g, err = None, "This citation could not be interpreted automatically, so no text is shown."
    if err: return {"ref": ref, "text": None, "note": err}
    render, allow = g
    usccb_text = re.split(r"\n\s*or\s*\n", usccb_text)[0]
    ref_text = "\n".join(l for l in usccb_text.split("\n") if not re.match(r"^\s*R\.", l))
    best = None
    for s in (SHIFTS if allow else [0]):
        vs = render(s)
        sc = similarity(ref_text, " ".join(t for *_, t in vs)) if vs else 0
        if best is None or sc > best[0] + 0.04: best = (sc, vs, s)
    sc, vs, s = best
    isnt = bid_is_nt(ref)
    if not vs or sc < (0.10 if isnt else MIN_SCORE):
        return {"ref": ref, "text": None, "score": round(sc, 2),
                "note": "This passage could not be reliably matched to the King James text (the USCCB/NABRE verse numbering or wording differs). Not shown to avoid displaying the wrong text."}
    poetic = vs[0][0] == "PSA"
    seen, paras, prev = set(), [], None
    for b_, c, v, t in vs:
        if (b_, c, v) in seen: continue
        seen.add((b_, c, v))
        t = clean(t)
        if prev is None or not (prev[0] == b_ and prev[1] == c and v == prev[2] + 1) :
            paras.append([t])
        else: paras[-1].append(t)
        prev = (b_, c, v)
    text = "\n\n".join(("\n" if poetic else " ").join(p) for p in paras)
    note = None
    if s != 0 or any(b != vs[0][0] for b, *_ in vs) or vs[0][0] in ("S3Y", "SUS", "BEL"):
        used = sorted({b for b, *_ in vs})
        note = "Verse numbering differs between the USCCB (NABRE) and the King James Version; matched to the equivalent KJV verses" + (f" (KJV: {', '.join(used)})." if used != [BOOKS[parse_ref(ref)[0]]] else ".")
    if vs[0][0] in ("WIS", "SIR", "TOB", "JDT", "BAR", "1MA", "2MA", "S3Y", "SUS", "BEL"):
        note = (note + " " if note else "") + "Taken from the KJV 1611 Apocrypha."
    return {"ref": ref, "text": text, "score": round(sc, 2), "shift": s, "note": note}

def build_day(date):
    title, secs = usccb(date)
    out = {"date": date, "title": title, "source": f"https://bible.usccb.org/bible/readings/{datetime.date.fromisoformat(date):%m%d%y}.cfm", "readings": []}
    for s in secs:
        if not SECTION_KEEP(s["label"]) : continue
        refs = s["refs"]
        if not refs: continue
        item = {"label": s["label"], "ref": "; ".join(refs), "passages": []}
        if len(refs) == 1: item["passages"].append(build_ref(refs[0], s["usccb_text"]))
        else:
            for r in refs: item["passages"].append(build_ref(r, s["usccb_text"]))
        out["readings"].append(item)
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--days":
        t = datetime.date.today(); dates = [(t + datetime.timedelta(i)).isoformat() for i in range(int(a[1]))]
    else: dates = a
    for d in dates:
        try: o = build_day(d)
        except Exception as e: print(d, "FAILED", repr(e)); continue
        json.dump(o, open(f"{ROOT}/public/data/{d}.json", "w"), indent=1, ensure_ascii=False)
        print(d, o["title"][:50], [(r["label"][:8], r["ref"], [(p.get("score"), p.get("shift"), p["text"] is None) for p in r["passages"]]) for r in o["readings"]])
