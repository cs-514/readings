import re, json, os, html, time, urllib.request, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (daily-readings personal PWA build)"}

def http(url, tries=4):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            err = e; time.sleep(1.5 * (i + 1))
    raise err

# ---------- USCCB ----------
def usccb(date):
    p = f"{ROOT}/cache/usccb/{date}.html"
    if not os.path.exists(p):
        d = datetime.date.fromisoformat(date)
        open(p, "w").write(http(f"https://bible.usccb.org/bible/readings/{d:%m%d%y}.cfm"))
    h = open(p).read()
    title = html.unescape(re.search(r'og:title" content="([^"]+?)(?: \| USCCB)?"', h).group(1)).strip()
    secs = []
    for m in re.finditer(r'<h3 class="name">(.*?)</h3>\s*<div class="address">(.*?)</div>\s*</div>\s*<div class="content-body">(.*?)</div>', h, re.S):
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
        refs = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", a))).strip() for a in re.findall(r"<a [^>]*>(.*?)</a>", m.group(2), re.S)]
        body = m.group(3)
        body = re.sub(r"<br\s*/?>", "\n", body); body = re.sub(r"</p>", "\n\n", body)
        body = html.unescape(re.sub(r"<[^>]+>", "", body))
        secs.append({"label": label, "refs": refs, "usccb_text": re.sub(r"\n{3,}", "\n\n", body).strip()})
    return title, secs

# ---------- reference parsing ----------
BOOKS = {  # USCCB name -> (bible-api id)
"Genesis":"GEN","Exodus":"EXO","Leviticus":"LEV","Numbers":"NUM","Deuteronomy":"DEU","Joshua":"JOS","Judges":"JDG","Ruth":"RUT",
"1 Samuel":"1SA","2 Samuel":"2SA","1 Kings":"1KI","2 Kings":"2KI","1 Chronicles":"1CH","2 Chronicles":"2CH","Ezra":"EZR","Nehemiah":"NEH",
"Tobit":"TOB","Judith":"JDT","Esther":"EST","1 Maccabees":"1MA","2 Maccabees":"2MA","Job":"JOB","Psalm":"PSA","Psalms":"PSA","Proverbs":"PRO",
"Ecclesiastes":"ECC","Song of Songs":"SNG","Wisdom":"WIS","Sirach":"SIR","Isaiah":"ISA","Jeremiah":"JER","Lamentations":"LAM","Baruch":"BAR",
"Ezekiel":"EZK","Daniel":"DAN","Hosea":"HOS","Joel":"JOL","Amos":"AMO","Obadiah":"OBA","Jonah":"JON","Micah":"MIC","Nahum":"NAM","Habakkuk":"HAB",
"Zephaniah":"ZEP","Haggai":"HAG","Zechariah":"ZEC","Malachi":"MAL","Matthew":"MAT","Mark":"MRK","Luke":"LUK","John":"JHN","Acts":"ACT",
"Acts of the Apostles":"ACT","Romans":"ROM","1 Corinthians":"1CO","2 Corinthians":"2CO","Galatians":"GAL","Ephesians":"EPH","Philippians":"PHP",
"Colossians":"COL","1 Thessalonians":"1TH","2 Thessalonians":"2TH","1 Timothy":"1TI","2 Timothy":"2TI","Titus":"TIT","Philemon":"PHM","Hebrews":"HEB",
"James":"JAS","1 Peter":"1PE","2 Peter":"2PE","1 John":"1JN","2 John":"2JN","3 John":"3JN","Jude":"JUD","Revelation":"REV","Revelation of John":"REV"}
SINGLE = {"OBA","PHM","2JN","3JN","JUD"}

def parse_ref(ref):
    """-> (book_name, [(c1,v1,c2,v2)]) ; raises ValueError."""
    r = re.split(r"\s+or\s+", ref)[0].rstrip(" .")
    r = r.replace("&", ",")
    r = re.sub(r"(\d+)(?:-\d+){2,}", lambda m: m.group(0).split("-")[0] + "-" + m.group(0).split("-")[-1], r)
    r = r.replace("\u2014", "-").replace("\u2013", "-").replace("\u00a0", " ").strip()
    m = re.match(r"^((?:[123] )?[A-Za-z][A-Za-z ]*?)\s+(\d.*)$", r)
    if not m: raise ValueError("unparseable: " + ref)
    book, spec = m.group(1), m.group(2)
    if book not in BOOKS:  # USCCB typos (e.g. "Phiippians")
        import difflib
        c = difflib.get_close_matches(book, list(BOOKS), n=1, cutoff=0.8)
        if not c: raise ValueError("unknown book: " + ref)
        book = c[0]
    bid = BOOKS[book]
    spec = re.sub(r"(?<=\d)[a-z]+", "", spec)  # 1b, 3cd -> 1, 3
    spec = re.sub(r"\s+and\s+", ", ", spec)
    out, ch = [], None
    for part in re.split(r"\s*[;,]\s*", spec):
        if not part: continue
        m = re.match(r"^(?:(\d+):)?(\d+)(?:-(?:(\d+):)?(\d+))?$", part)
        if not m: raise ValueError("cannot parse: " + ref)
        c1, v1, c2, v2 = m.groups()
        if c1 is None and (ch is None):
            if bid in SINGLE: c1 = "1"
            else:  # whole chapter(s) e.g. "Psalm 23" -> treat number as chapter
                c1 = v1; v1 = "1"; v2 = "999"
        ch = int(c1) if c1 else ch
        c1 = ch
        c2 = int(c2) if c2 else c1
        v2 = int(v2) if v2 else int(v1)
        out.append((c1, int(v1), c2, v2)); ch = c2
    return book, out

# ---------- KJV ----------
def kjv_chapter(bid, ch):
    p = f"{ROOT}/cache/kjv/{bid}_{ch}.json"
    if not os.path.exists(p):
        txt = http(f"https://bible-api.com/data/kjv/{bid}/{ch}")
        json.loads(txt); open(p, "w").write(txt)
    d = json.load(open(p))
    return {v["verse"]: v["text"] for v in d.get("verses", [])}

def clean(t):
    t = t.replace("¶", "").replace("\u2019", "'")
    t = re.sub(r"\bLORD'S\b", "LORD's", t)        # source data has "LORD'S"; the possessive s is lowercase ("LORD's")
    return re.sub(r"\s+", " ", t).strip()

STOP = set("that this with from have they will were been shall their there which them then unto when what said also thou thee thy thine your yours into upon over such than these those would could should about because while where whom whose".split())
def toks(t):
    out = set()
    for w in re.findall(r"[a-z]+", t.lower()):
        if len(w) < 4 or w in STOP: continue
        for suf in ("eth", "est", "ing", "ed", "es", "s", "e"):
            if w.endswith(suf) and len(w) - len(suf) >= 4: w = w[:-len(suf)]; break
        out.add(w)
    return out

def similarity(a, b):
    A, B = toks(a), toks(b)
    return len(A & B) / len(A) if A else 0.0

# ---------- WEB-CE ----------
TRANS = "kjv"          # active translation for fetch_range: "kjv" | "web"
WEB_BOOK = {"EST": "ESG", "DAN": "DAG"}   # WEB-CE files contain the Greek forms of Esther and Daniel
_web = {}
def web_chapter(bid, ch):
    bid = WEB_BOOK.get(bid, bid)
    if bid not in _web:
        import webc; webc.ensure()
        p = f"{ROOT}/cache/web/{bid}.json"
        _web[bid] = json.load(open(p)) if os.path.exists(p) else {}
    return {int(v): t for v, t in _web[bid].get(str(ch), {}).items()}

def fetch_range(bid, c1, v1, c2, v2, shift):
    """verses (list of (c,v,text)) for range with verse shift applied to both ends."""
    res = []
    for c in range(c1, c2 + 1):
        vs = web_chapter(bid, c) if TRANS == "web" else kjv_chapter(bid, c)
        if not vs: continue
        lo = v1 + shift if c == c1 else 1
        hi = v2 + shift if c == c2 else max(vs)
        if hi > 900: hi = max(vs)
        for v in sorted(vs):
            if lo <= v <= hi and (TRANS != "web" or vs[v].strip()): res.append((c, v, vs[v]))
    return res
