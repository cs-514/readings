#!/usr/bin/env python3
"""World English Bible, Catholic Edition (eBible.org, public domain): USFM -> compact per-book JSON in cache/web/.
usage: webc.py   (downloads https://eBible.org/Scriptures/eng-web-c_usfm.zip only if cache/web is missing; the JSON is committed)
Verse text keeps the WEB wording exactly; only markup (verse numbers, footnotes, cross-references, Strong's/lemma attributes,
section headings) is removed. Poetry/paragraph line structure is not kept (one string per verse)."""
import os, re, sys, json, zipfile, io, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{ROOT}/cache/web"; URL = "https://eBible.org/Scriptures/eng-web-c_usfm.zip"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120"}

def parse_usfm(t):
    t = re.sub(r"\\f .*?\\f\*", "", t, flags=re.S); t = re.sub(r"\\x .*?\\x\*", "", t, flags=re.S); t = re.sub(r"\\fig .*?\\fig\*", "", t, flags=re.S)
    chap = None; cur = None; out = {}
    SKIP = {"s", "s1", "s2", "s3", "r", "d", "cl", "cd", "ca", "mr", "sr", "rq", "ms", "ms1", "qa", "b", "h", "toc1", "toc2", "toc3", "mt1", "mt2", "mt3", "id", "ide", "im", "ip", "ili", "cp", "sp"}
    for ln in t.split("\n"):
        m = re.match(r"\\c (\d+)", ln)
        if m: chap = int(m.group(1)); cur = None; continue
        if chap is None: continue
        mk = re.match(r"\\(\w+)\*?\s*(.*)", ln)
        if not mk: continue
        tag, rest = mk.group(1), mk.group(2)
        if tag in SKIP:
            if tag in ("s", "s1", "s2", "s3", "r", "cd", "ms", "ms1", "d", "qa"): cur = None
            continue
        parts = re.split(r"\\v (\d+)[a-z]?\s*", ln if tag == "v" else rest)
        if len(parts) == 1:
            if cur is not None: out[(chap, cur)] += " " + rest
            continue
        if parts[0].strip() and cur is not None: out[(chap, cur)] += " " + parts[0]
        for i in range(1, len(parts), 2):
            cur = int(parts[i]); out.setdefault((chap, cur), ""); out[(chap, cur)] += " " + parts[i + 1]
    res = {}
    for (c, v), s in out.items():
        s = re.sub(r"\\\+?w ([^|\\]*)(\|[^\\]*)?\\\+?w\*", r"\1", s)
        s = re.sub(r"\\\+?\w+\*?", "", s); s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"\s+([,.;:!?])", r"\1", s)
        res.setdefault(str(c), {})[str(v)] = s
    return res

def ensure():
    if os.path.exists(f"{OUT}/PSA.json"): return
    os.makedirs(OUT, exist_ok=True)
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=120).read()))
    for n in z.namelist():
        if not n.endswith(".usfm"): continue
        t = z.read(n).decode("utf-8"); bid = re.search(r"\\id (\w+)", t).group(1)
        json.dump(parse_usfm(t), open(f"{OUT}/{bid}.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print("wrote", len(os.listdir(OUT)), "books")
if __name__ == "__main__": ensure()
