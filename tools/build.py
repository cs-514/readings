#!/usr/bin/env python3
"""Build static JSON for a date: USCCB citations -> KJV text (no verse numbers).
usage: build.py YYYY-MM-DD [YYYY-MM-DD ...] | --days N (from today) """
import sys, json, re, datetime, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib

MIN_SCORE = 0.22   # below this we refuse to show text (see README)
SHIFTS = [0, -1, -2, -3, 1, -4]
SECTION_KEEP = lambda l: not l.lower().startswith(("or", "alleluia", "verse before", "gospel acclamation", "lenten gospel acclamation", "sequence"))

# NABRE (Hebrew/Greek-based) -> KJV special cross-chapter mappings: (bid,c1,v1,c2,v2) -> [(bid,c1,v1,c2,v2)...]
def special(bid, el):
    c1, v1, c2, v2 = el
    web = lib.TRANS == "web"
    if bid == "ISA" and c1 == 8 and v1 == 23:                 # Isa 8:23-9:x == KJV 9:1-(x+1)
        return [("ISA", 9, 1, 9, v2 + 1 if c2 == 9 else 1)]
    if bid == "JOL" and c1 == 3: return [("JOL", 2, v1 + 27, 2, v2 + 27)] if v2 <= 5 else None
    if bid == "JOL" and c1 == 4: return [("JOL", 3, v1, c2 - 1, v2)]
    if bid == "MAL" and c1 == 3 and v1 >= 19: return [("MAL", 4, v1 - 18, 4, v2 - 18)]
    if bid == "JON" and c1 == 2 and v1 == 1: return [("JON", 1, 17, 2, v2 - 1)]
    if bid == "JON" and c1 == 2: return [("JON", 2, v1 - 1, 2, v2 - 1)]
    if web and bid == "ROM" and c1 == 16 and v1 >= 25: return [("ROM", 14, v1 - 1, 14, v2 - 1)]   # WEB (TR order) prints the doxology at Romans 14:24-26
    if web and bid == "DAN": return None            # WEB-CE has Daniel in its Greek form, numbered like the NABRE
    if bid == "DAN" and c1 == 3 and v1 >= 24 and c2 == 3: return [("S3Y", 1, v1 - 23, 1, v2 - 23)]
    if bid == "DAN" and c1 == 13: return [("SUS", 1, v1, c2 - 12, v2)] if c2 == 13 else [("SUS", 1, v1, 1, 64)]
    if bid == "DAN" and c1 == 14: return [("BEL", 1, v1, 1, v2)]
    if web and bid == "EST" and c1 >= 11: return "NOKJV"   # WEB-CE prints the additions inline within chapters 1-10
    if bid == "EST" and c1 >= 12: return "NOKJV"           # Additions to Esther (C, D) are not in the KJV Apocrypha text we have
    if bid == "HOS" and c1 == 2 and v1 <= 2: return [("HOS", 1, 9 + v1, 1, 9 + v2)]
    return None

REF_OVERRIDE = {  # NABRE ref -> list of (c1,v1,c2,v2) in KJV numbering (same book)
    "Isaiah 63:16b-17, 19b; 64:2-7": [(63, 16, 63, 17), (64, 1, 64, 7)],
    "Isaiah 63:16b-17, 19b; 64:2-7": [(63, 16, 63, 17), (64, 1, 64, 7)],
}

TNAME = {"kjv": "King James text", "web": "World English Bible (Catholic Edition) text"}

def parse_halves(ref):
    """{(chapter, verse): set(letters)} for the citation, keeping a/b suffixes ('' = whole verse)."""
    r = re.split(r"\s+or\s+", ref)[0].rstrip(" .").replace("&", ",").replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ")
    m = re.match(r"^((?:[123] )?[A-Za-z][A-Za-z ]*?)\s+(\d.*)$", r)
    if not m: return {}
    spec = re.sub(r"\s+and\s+", ", ", m.group(2)); out = {}; ch = None
    for part in re.split(r"\s*[;,]\s*", spec):
        mm = re.match(r"^(?:(\d+):)?(\d+)([a-z]*)(?:-(?:(\d+):)?(\d+)([a-z]*))?$", part)
        if not mm: continue
        c1, v1, l1, c2, v2, l2 = mm.groups()
        if c1 is None and ch is None: continue          # whole-chapter or single-chapter-book forms: no half-verses
        c1 = int(c1) if c1 else ch; ch = c1
        v1 = int(v1); c2 = int(c2) if c2 else c1
        if v2 is None: v2, l2 = v1, l1
        v2 = int(v2)
        if c1 == c2:
            for v in range(v1, v2 + 1):
                l = l1 if v == v1 else ""
                if v == v2 and (v2 != v1 or True) and (v != v1 or True):
                    l = l2 if v == v2 and v2 != v1 else l
                if v == v1 and v2 == v1: l = l1
                out.setdefault((c1, v), set()).add(l or "")
        ch = c2
    return out

def split_points(t):
    return [i for i in range(1, len(t)) if t[i - 1] in ".;:!?," and t[i] == " "] + [len(t)]

def trim_half(t, keep, ref_toks):
    """Cut verse text t at a clause boundary: keep the first part ('a') or the last part ('b'), choosing the boundary that best
    separates words found in the USCCB text from words that are not."""
    pts = split_points(t); best = None
    for i in pts[:-1]:
        head, tail = t[:i].strip(), t[i:].strip()
        if not head or not tail: continue
        want, other = (head, tail) if keep == "a" else (tail, head)
        W, O = toks(want), toks(other)
        sc = len(W & ref_toks) + len(O - ref_toks) - len(W - ref_toks) - len(O & ref_toks)
        if best is None or sc > best[0]: best = (sc, head if keep == "a" else tail)
    return best[1] if best else None

def apply_halves(ref, vs, shift, ref_text):
    hv = parse_halves(ref)
    if not any(l not in ("", None) for ls in hv.values() for l in ls): return vs, None
    R = toks(ref_text); out = []; done = []; fail = []
    for (b, c, v, t) in vs:
        ls = hv.get((c, v - shift))
        if ls and "" not in ls and not ({"a", "b"} <= ls) and len(ls) == 1 and next(iter(ls)) not in ("ab", "abc", "abcd"):
            l = next(iter(ls))
            if l in ("a", "b"):
                nt = trim_half(clean(t), l, R)
                if nt: out.append((b, c, v, nt)); done.append(f"{c}:{v - shift}{l}"); continue
                fail.append(f"{c}:{v - shift}{l}")
            else: fail.append(f"{c}:{v - shift}{l}")
        out.append((b, c, v, t))
    note = None
    if done: note = f"Half-verse ({', '.join(done)}) is cut at a sentence or clause boundary chosen by comparison with the USCCB text; the lectionary\u2019s division may differ slightly."
    if fail: note = (note + " " if note else "") + f"Half-verse ({', '.join(fail)}) could not be divided automatically, so the whole verse is shown."
    return out, note

def gather(ref):
    book, els = parse_ref(ref)
    if ref in REF_OVERRIDE: els = REF_OVERRIDE[ref]
    bid = BOOKS[book]
    # specials first
    sp = [special(bid, e) for e in els]
    if any(s == "NOKJV" for s in sp):
        return None, ("Additions to Esther are printed inline within chapters 1\u201310 in the World English Bible (Catholic Edition), so they cannot be matched to this citation automatically." if lib.TRANS == "web" else "Additions to Esther are not part of the KJV text available here.")
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
                "note": f"This passage could not be reliably matched to the {TNAME[lib.TRANS]} (the USCCB/NABRE verse numbering or wording differs). Not shown to avoid displaying the wrong text."}
    half_note = None
    if lib.TRANS == "web":
        vs, half_note = apply_halves(ref, vs, s, ref_text)
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
    if lib.TRANS == "web":
        if s != 0 or any(b != vs[0][0] for b, *_ in vs):
            note = "Verse numbering differs between the USCCB (NABRE) and the World English Bible (Catholic Edition); matched to the equivalent verses."
        if half_note: note = (note + " " if note else "") + half_note
        return {"ref": ref, "text": text, "score": round(sc, 2), "shift": s, "note": note}
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
        for r in refs:
            lib.TRANS = "kjv"; p = build_ref(r, s["usccb_text"])
            lib.TRANS = "web"
            try: w = build_ref(r, s["usccb_text"])
            except Exception as e: w = {"ref": r, "text": None, "note": "This passage could not be matched automatically in the World English Bible (Catholic Edition)."}
            lib.TRANS = "kjv"
            p["web"] = {k: w.get(k) for k in ("text", "note", "score", "shift") if w.get(k) is not None or k in ("text", "note")}
            item["passages"].append(p)
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
