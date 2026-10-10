#!/usr/bin/env python3
"""Local search index over sources/*.txt (no LLM, no network).
  python3 tools/index.py build                 -> cache/index.json
  python3 tools/index.py search "query words" [-n 10] [--src ccc,aug,ce,newman,roman,benedict]
Each hit shows source id, location (CCC paragraph no., sermon/section, etc.), score and a snippet.
  python3 tools/index.py show SOURCE_ID "starting phrase" [words]   -> print text from a phrase (to copy an excerpt)"""
import os, re, sys, json, math, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP = set("the of and to in a is that it his he for as with was be by on not this are or from which but had they have you all who their will one him so we our them shall said unto thou thee thy hath"
           .split())

def toks(s): return [w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2]

def read(path):
    t = open(path).read(); head, _, body = t.partition("\n\n"); return head, body

def chunks_for(sid, title, body):
    out = []
    if sid == "ccc":
        # paragraphs are numbered sequentially: "NNN Text..." at line start
        lines = body.split("\n"); cur = None; buf = []; nxt = 1; started = False
        for ln in lines:
            m = re.match(r"^\s{0,3}(\d{1,4}) (?=\S)", ln)
            if m and int(m.group(1)) == nxt and (started or nxt == 1 and re.match(r"^\s*1 God", ln)):
                if cur: out.append((f"CCC §{cur}", " ".join(buf)))
                cur = nxt; nxt += 1; buf = [ln[m.end():]]; started = True
            elif cur: buf.append(ln)
        if cur: out.append((f"CCC §{cur}", " ".join(buf)))
        return [(l, re.sub(r"\s+", " ", t).strip()) for l, t in out]
    head = ""
    if sid == "roman_catechism":
        loc = "Roman Catechism"; paras = re.split(r"\n\s*\n", body)
        for p in paras:
            p1 = re.sub(r"\s+", " ", p).strip()
            if re.match(r"^(PART|ARTICLE|THE [A-Z ]+(SACRAMENT|COMMANDMENT)|[IVX]+ ?COMMANDMENT|PETITION)", p1) and len(p1) < 160: loc = "Roman Catechism, " + p1.title()
            elif len(p1.split()) > 25: out.append((loc, p1))
        return out
    # generic: paragraph windows of ~120-220 words
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", body)]
    paras = [p for p in paras if p]
    label = title; sec = ""
    buf = []; n = 0
    def flush():
        nonlocal buf, n
        if buf: out.append((f"{label}{(', ' + sec) if sec else ''}", " ".join(buf)))
        buf = []; n = 0
    for p in paras:
        m = re.match(r"^(\d{1,2})\. ", p)
        if m: sec = f"§{m.group(1)}"
        w = len(p.split())
        if n + w > 220: flush()
        buf.append(p); n += w
        if n >= 120: flush()
    flush()
    return out

def build():
    docs = []
    for f in sorted(glob.glob(f"{ROOT}/sources/*.txt")):
        sid = os.path.basename(f)[:-4]; head, body = read(f)
        title = re.search(r"TITLE: (.*)", head).group(1)
        for loc, text in chunks_for(sid, title, body):
            docs.append({"src": sid, "loc": loc, "text": text})
    os.makedirs(f"{ROOT}/cache", exist_ok=True)
    json.dump(docs, open(f"{ROOT}/cache/index.json", "w"))
    print(len(docs), "chunks"); return docs

def search(q, n=10, src=None):
    docs = json.load(open(f"{ROOT}/cache/index.json"))
    if src: docs = [d for d in docs if any(d["src"].startswith(s) or (s == "roman" and d["src"].startswith("roman")) for s in src)]
    df = collections.Counter(); tl = []
    for d in docs:
        t = toks(d["text"]); tl.append(collections.Counter(t)); df.update(set(t))
    N = len(docs); avg = sum(sum(c.values()) for c in tl) / N
    qt = toks(q); res = []
    for d, c in zip(docs, tl):
        L = sum(c.values()); s = 0
        for w in qt:
            if c[w]:
                idf = math.log(1 + (N - df[w] + .5) / (df[w] + .5))
                s += idf * c[w] * 2.2 / (c[w] + 1.2 * (.25 + .75 * L / avg))
        if s: res.append((s, d))
    res.sort(key=lambda x: -x[0]); return res[:n]

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "build": build()
    elif a[0] == "search":
        n = 10; src = None; q = []
        i = 1
        while i < len(a):
            if a[i] == "-n": n = int(a[i + 1]); i += 2
            elif a[i] == "--src": src = a[i + 1].split(","); i += 2
            else: q.append(a[i]); i += 1
        for s, d in search(" ".join(q), n, src):
            print(f"[{s:.1f}] {d['src']} | {d['loc']}\n    {d['text'][:300]}\n")
    elif a[0] == "show":
        head, body = read(f"{ROOT}/sources/{a[1]}.txt"); t = re.sub(r"\s+", " ", body)
        i = t.find(a[2]); print(t[i:i + 1500] if i >= 0 else "NOT FOUND")
