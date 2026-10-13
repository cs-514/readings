#!/usr/bin/env python3
"""Download the excerpt sources into sources/*.txt (plain text, one file per work/article/sermon).
Each file starts with 'TITLE: ...' and 'URL: ...' lines, then a blank line, then the text.
Excerpt verification (tools/render.py) reads these files, so they are committed to the repo.
usage: fetch_sources.py [--force]"""
import os, re, sys, html, json, subprocess, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = f"{ROOT}/sources"; os.makedirs(S, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
FORCE = "--force" in sys.argv

def get(url, binary=False):
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    return d if binary else d.decode("utf-8", "replace")

def write(sid, title, url, text):
    p = f"{S}/{sid}.txt"
    open(p, "w").write(f"TITLE: {title}\nURL: {url}\n\n{text.strip()}\n"); print("wrote", sid, len(text))

def html_text(h, start_re=None):
    h = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", h, flags=re.S)
    h = re.sub(r"</(p|div|h\d|li|tr|blockquote)>|<br\s*/?>", "\n", h, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    t = re.sub(r"[ \t\xa0]+", " ", t); t = re.sub(r"\n\s*\n+", "\n\n", t)
    return t

def pdf(sid, title, url, pdfurl):
    f = f"/tmp/{sid}.pdf"
    open(f, "wb").write(get(pdfurl, True))
    t = subprocess.run(["pdftotext", "-layout", f, "-"], capture_output=True, text=True).stdout
    write(sid, title, url, t)

def web(sid, title, url, marker=None):
    if os.path.exists(f"{S}/{sid}.txt") and not FORCE: return
    t = html_text(get(url))
    if marker and marker in t: t = t[t.index(marker):]
    write(sid, title, url, t)

if FORCE or not os.path.exists(f"{S}/ccc.txt"):
    pdf("ccc", "Catechism of the Catholic Church (USCCB)", "https://www.vatican.va/archive/ENG0015/_INDEX.HTM",
        "https://dn790005.ca.archive.org/0/items/catechismofthecatholicchurch/Catechism%20of%20the%20Catholic%20Church%20-%20USCCB.pdf")
if FORCE or not os.path.exists(f"{S}/roman_catechism.txt"):
    pdf("roman_catechism", "The Roman Catechism (Catechism of the Council of Trent)", "https://www.saintsbooks.net/books/The%20Roman%20Catechism.pdf",
        "https://www.saintsbooks.net/books/The%20Roman%20Catechism.pdf")

# Augustine, Sermons on the New Testament Lessons (NPNF 1, vol. 6) -- newadvent.org/fathers/1603.htm
idx = get("https://www.newadvent.org/fathers/1603.htm")
for sid in sorted(set(re.findall(r'fathers/(160\d{3})\.htm', idx))):
    if os.path.exists(f"{S}/aug_{sid}.txt") and not FORCE: continue
    h = get(f"https://www.newadvent.org/fathers/{sid}.htm")
    t = html_text(h); a = t.find("Sermon") if False else 0
    m = re.search(r"<title>([^<]*)</title>", h); title = "Augustine, " + (m.group(1).strip() if m else sid)
    write(f"aug_{sid}", title, f"https://www.newadvent.org/fathers/{sid}.htm", t)

CE = {"01055a": "Abraham", "13468a": "Sara", "08192a": "Ishmael", "08175a": "Isaac", "08497b": "Jonas", "08179b": "Isaias",
      "06336a": "Galatians, Epistle to the", "14135b": "Solomon", "10582c": "Law, Mosaic", "09703a": "Marriage, Mystical",
      "10212c": "Messias", "07271a": "Hermeneutics", "07409a": "Holy Ghost", "08573a": "Justification", "15107a": "Types in Scripture",
      "14629d": "Thessalonians, Epistles to the", "08549a": "Judgment, Divine", "01542a": "Annunciation of the Blessed Virgin Mary"}
for cid, name in CE.items():
    web(f"ce_{cid}", f"Catholic Encyclopedia, {name}", f"https://www.newadvent.org/cathen/{cid}.htm")

NEWMAN = {"PPS6-9": ("parochial/volume6/sermon9", "The Gospel Sign Addressed to Faith"), "PPS2-12": ("parochial/volume2/sermon12", "The Reverence Due to the Blessed Virgin Mary"),
          "PPS6-12": ("parochial/volume6/sermon12", "Faith the Title for Justification"), "PPS3-6": ("parochial/volume3/sermon6", "Faith and Obedience"),
          "PPS4-22": ("parochial/volume4/sermon22", "Watching"), "PPS3-18": ("parochial/volume3/sermon18", "The Gift of the Spirit"),
          "PPS1-15": ("parochial/volume1/sermon15", "Religious Faith Rational"), "SSD-3": ("subjects/sermon3", "Our Lord's Last Supper and His First"),
          "PPS6-13": ("parochial/volume6/sermon13", "Judaism of the Present Day")}
for sid, (path, title) in NEWMAN.items():
    web("newman_" + sid.lower().replace("-", "_"), f"John Henry Newman, {title} ({sid})", f"https://www.newmanreader.org/works/{path}.html")

BEN = {"ang_20111106": ("https://www.vatican.va/content/benedict-xvi/en/angelus/2011/documents/hf_ben-xvi_ang_20111106.html", "Benedict XVI, Angelus, 6 November 2011")}
for sid, (u, title) in BEN.items(): web("benedict_" + sid, title, u)

# ---- batch 2: more Catholic Encyclopedia, Augustine Tractates on John (vol 7) and Expositions on the Psalms (vol 8),
# Imitation of Christ (Gutenberg #1653), all of Newman's Parochial and Plain Sermons, Benedict XVI Angelus/homilies
from concurrent.futures import ThreadPoolExecutor
CE2 = {"14515b": "Teresa of Avila, Saint", "07644a": "Ignatius of Antioch, Saint", "13796b": "Simon the Apostle, Saint", "08542b": "Jude, Epistle of Saint",
       "03619a": "Charles Borromeo, Saint", "09154b": "Leo I (the Great), Pope", "09732b": "Martin of Tours, Saint", "08503b": "Josaphat Kuncevyc, Saint",
       "05389a": "Elizabeth of Hungary, Saint", "12400a": "Presentation of the Blessed Virgin Mary, Feast of the", "09014b": "Lateran, Saint John",
       "08420b": "Isaac Jogues, Saint", "02751b": "Brebeuf, Jean de", "01315b": "All Souls' Day", "01315a": "All Saints' Day", "12575a": "Purgatory",
       "14554c": "Thanksgiving before and after Meals", "14555a": "Thanksgiving Day", "04673a": "Dedication", "11789b": "Pharisees", "12789a": "Resurrection of Jesus Christ",
       "12792a": "Resurrection, General", "01594b": "Revelation, Book of", "02371a": "Beatitudes, The Eight", "08646a": "Kingdom of God", "01328f": "Alms and Almsgiving",
       "15666a": "Wisdom, Book of", "08755a": "Lamb, Paschal", "07170a": "Heaven", "11460a": "Parables", "12553d": "Publican", "09096a": "Lazarus", "12345b": "Prayer",
       "15617c": "Widow", "14495a": "Temple", "14499a": "Temple of Jerusalem", "13287b": "Sabbath", "07207a": "Hell", "07610a": "Hypocrisy", "11703a": "Persecution",
       "09736b": "Martyr", "01559a": "Antichrist", "10307a": "Millennium and Millenarianism", "08550a": "Judgment, Particular", "10198d": "Mercy, Corporal and Spiritual Works of",
       "05752c": "Faith", "03592a": "Charity and Charities", "12324a": "Poverty", "15571a": "Wealth, Use of", "07543b": "Humility", "12405a": "Pride", "07465b": "Hope",
       "06689a": "Grace", "12677d": "Redemption", "05485a": "Ephesians, Epistle to the", "12008a": "Philippians, Epistle to the", "08344a": "Jerusalem (Before A.D. 71)",
       "03744a": "Church, The", "12406a": "Priest", "02581b": "Bishop", "04171a": "Saints, Communion of", "09420a": "Luke, Gospel of Saint", "10057a": "Matthew, Gospel of Saint",
       "14746b": "Titus", "11797b": "Philemon", "08435a": "John, Epistles of", "12505b": "Proverbs, Book of", "05737b": "Ezekiel", "12533a": "Psalms", "10711a": "Nathan",
       "05549a": "Esther", "13323a": "Sadducees", "07687a": "Immortality", "02364a": "Beatific Vision", "08070a": "Intercession", "03637d": "Chastity", "09580b": "Mammon",
       "04664a": "Decalogue", "04153a": "Ten Commandments, The", "06628a": "Gog and Magog", "05584a": "Eucharist, as a Sacrament", "05590a": "Eucharist, Early Symbols of the",
       "14335a": "Sunday", "05528b": "Eschatology", "10596a": "Moses", "10156b": "Melchisedech", "09356a": "Prayer, Lord's", "04653a": "Prayers for the Dead",
       "15464b": "Virgin Mary, The", "13649a": "Seal", "02369a": "Beatitudes, Mount of", "08755b": "Lamb (in Early Christian Symbolism)", "06689x": "Grace, Actual",
       "09707a": "Marriage, Sacrament of", "05054c": "Divorce (in Moral Theology)"}
def ce_one(a):
    cid, name = a
    try: web(f"ce_{cid}", f"Catholic Encyclopedia, {name}", f"https://www.newadvent.org/cathen/{cid}.htm")
    except Exception as e: print("FAIL", cid, e)
with ThreadPoolExecutor(6) as ex: list(ex.map(ce_one, CE2.items()))

def na_one(a):
    pfx, base, sid = a
    if os.path.exists(f"{S}/{pfx}_{sid}.txt") and not FORCE: return
    try:
        h = get(f"https://www.newadvent.org/fathers/{sid}.htm"); m = re.search(r"<title>([^<]*)</title>", h)
        write(f"{pfx}_{sid}", f"Augustine, {m.group(1).strip() if m else sid}", f"https://www.newadvent.org/fathers/{sid}.htm", html_text(h))
    except Exception as e: print("FAIL", sid, e)
jobs = []
for pfx, idxid in (("augjn", "1701"), ("augps", "1801")):
    idx = get(f"https://www.newadvent.org/fathers/{idxid}.htm")
    jobs += [(pfx, idxid, s) for s in sorted(set(re.findall(rf'fathers/({idxid}\d{{3}})\.htm', idx)))]
with ThreadPoolExecutor(6) as ex: list(ex.map(na_one, jobs))

if FORCE or not os.path.exists(f"{S}/imitation.txt"):
    t = get("https://www.gutenberg.org/cache/epub/1653/pg1653.txt")
    if "*** START" in t: t = t.split("***", 2)[2] if False else t[t.index("*** START"):]
    if "*** END" in t: t = t[:t.index("*** END")]
    write("imitation", "Thomas a Kempis, The Imitation of Christ (tr. W. Benham, Project Gutenberg #1653)", "https://www.gutenberg.org/ebooks/1653", t)

def nm_one(a):
    sid, path, title = a
    try: web("newman_" + sid, f"John Henry Newman, {title} ({sid.upper().replace('_', '-')})", f"https://www.newmanreader.org/works/{path}.html")
    except Exception as e: print("FAIL", sid, e)
nj = []
for v in range(1, 9):
    try: ix = get(f"https://www.newmanreader.org/works/parochial/volume{v}/index.html")
    except Exception as e: print("FAIL vol", v, e); continue
    for m in re.finditer(r'href="(sermon(\d+)\.html)"[^>]*>(.*?)</a>', ix, re.S):
        tt = re.sub(r"<[^>]+>|\s+", " ", m.group(3)).strip()
        nj.append((f"pps{v}_{m.group(2)}", f"parochial/volume{v}/sermon{m.group(2)}", tt))
with ThreadPoolExecutor(5) as ex: list(ex.map(nm_one, nj))

# ---- Benedict XVI: Angelus, general audiences and homilies dated October-November (2005-2012) plus audiences on saints/Fathers
BV = "https://www.vatican.va/content/benedict-xvi/en"
def bn_one(a):
    kind, y, path = a
    sid = "benedict_" + path.split("hf_ben-xvi_")[1][:-5].replace("-", "_")
    if os.path.exists(f"{S}/{sid}.txt") and not FORCE: return
    try:
        h = get(f"{BV}/{kind}/{y}/documents/{path}"); m = re.search(r"<title>([^<]*)</title>", h)
        t = html_text(h)
        write(sid, "Benedict XVI, " + (m.group(1).strip() if m else sid), f"{BV}/{kind}/{y}/documents/{path}", t)
    except Exception as e: print("FAIL", path, e)
bj = []
for kind in ("angelus", "audiences", "homilies"):
    for y in range(2005, 2013):
        try: ix = get(f"{BV}/{kind}/{y}.index.html")
        except Exception as e: print("FAIL idx", kind, y); continue
        for p in sorted(set(re.findall(rf'{kind}/{y}/documents/(hf_ben-xvi_[a-z]+_{y}(?:10|11)\d\d[^"]*\.html)', ix))): bj.append((kind, y, p))
        if kind == "audiences":
            for p in sorted(set(re.findall(rf'audiences/{y}/documents/(hf_ben-xvi_aud_{y}\d{{4}}[^"]*\.html)', ix))):
                if (kind, y, p) not in bj: bj.append((kind, y, p))
print(len(bj), "benedict docs")
with ThreadPoolExecutor(5) as ex: list(ex.map(bn_one, bj))

# ---- St Thomas Aquinas (isidore.co/aquinas; newadvent.org/summa)
# Catena Aurea, tr. under J.H. Newman (Parker, Oxford 1841-45; public domain): one file per Gospel chapter, aq_ca_{mt,mk,lk,jn}_N.
# Scripture commentaries (isidore.co English pages; modern translations, e.g. Larcher, freely published there): aq_ss_{book}[_N].
# Summa Theologiae (Fathers of the English Dominican Province, 1920; public domain, newadvent.org): aq_st_{part}_qN.
ISI = "https://isidore.co/aquinas/english/"
def get_cp(url):
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
    try: return d.decode("utf-8")
    except UnicodeDecodeError: return d.decode("cp1252", "replace")
CA = {"lk": ("CALuke", "Luke"), "jn": ("CAJohn", "John")}
def ca_one(k):
    page, book = CA[k]
    if os.path.exists(f"{S}/aq_ca_{k}_1.txt") and not FORCE: return
    try: h = get_cp(ISI + page + ".htm")
    except Exception as e: print("FAIL", page, e); return
    parts = re.split(r'<a name="?(\d+)"?[^>]*>', h)
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        if n == 0: continue
        write(f"aq_ca_{k}_{n}", f"St Thomas Aquinas, Catena Aurea on {book} {n} (tr. J.H. Newman et al., 1841-45)", f"{ISI}{page}.htm#{n}", html_text(parts[i + 1]))
SSB = ["SSJohn", "SS1Cor", "SS2Cor", "SSGalatians", "SSEph", "SSPhilippians", "SSColossians", "SS1Thes", "SSPhilemon", "SSHebrews", "SSJob", "SSLamentations"]
def ss_one(page):
    key = page.replace("SS", "").replace("Chapters", "").lower()
    if any(f.startswith(f"aq_ss_{key}") for f in os.listdir(S)) and not FORCE: return
    try: h = get_cp(ISI + page + ".htm")
    except Exception as e: print("FAIL", page, e); return
    subs = sorted(set(re.findall(r'href="([A-Za-z0-9]+?(\d+)\.htm)(?:#[^"]*)?"', h)), key=lambda x: int(x[1]))
    name = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", (re.search(r"<title>(.*?)</title>", h, re.S) or [None, page])[1]))).strip()
    if subs:
        for f, n in subs:
            try: write(f"aq_ss_{key}_{n}", f"St Thomas Aquinas, {name}, ch. {n}", ISI + f, html_text(get_cp(ISI + f)))
            except Exception as e: print("FAIL", f, e)
    else: write(f"aq_ss_{key}", f"St Thomas Aquinas, {name}", ISI + page + ".htm", html_text(h))
ST = {"1": range(1, 120), "2": range(1, 115), "3": range(1, 190), "4": range(1, 91)}   # newadvent ids: 1 = I, 2 = I-II, 3 = II-II, 4 = III
STN = {"1": "I", "2": "I-II", "3": "II-II", "4": "III"}
STC = {"1": "1", "2": "1_2", "3": "2_2", "4": "3"}
def st_one(a):
    p, q = a; sid = f"aq_st_{STC[p]}_q{q}"
    if os.path.exists(f"{S}/{sid}.txt") and not FORCE: return
    u = f"https://www.newadvent.org/summa/{p}{q:03d}.htm"
    try: write(sid, f"St Thomas Aquinas, Summa Theologiae {STN[p]} q.{q}", u, html_text(get(u)))
    except Exception as e: print("FAIL", u, e)

# isidore.co's Matthew and Mark pages have lost their quotation marks (U+FFFD in the server copy), so those two
# Gospels come from CCEL's plain-text edition of the same 1841-45 translation instead (catena1 = Matthew, catena2 = Mark).
CCEL_CA = {"mt": ("catena1", "Matthew"), "mk": ("catena2", "Mark")}
def ccel_ca(k):
    vol, book = CCEL_CA[k]
    if os.path.exists(f"{S}/aq_ca_{k}_1.txt") and "isidore" not in open(f"{S}/aq_ca_{k}_1.txt").read(300) and not FORCE: return
    t = get(f"https://www.ccel.org/ccel/a/aquinas/{vol}/cache/{vol}.txt")
    t = t[:t.rindex("\nReferences")] if "\nReferences" in t else t
    if k == "mt":   # CCEL omits the "Chapter 11" heading
        t = t.replace("\n   1. And it came to pass, when Jesus had made an end of commanding", "\nChapter 11\n\n   1. And it came to pass, when Jesus had made an end of commanding", 1)
        t = "Chapter 1\n" + t[t.index("   Ver. 1. The book of the generation"):]
    parts = re.split(r"\nChapter (\d+)[^\n]*\n", "\n" + t)
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        write(f"aq_ca_{k}_{n}", f"St Thomas Aquinas, Catena Aurea on {book} {n} (tr. J.H. Newman et al., 1841-45; CCEL)", f"https://www.ccel.org/ccel/aquinas/{vol}", parts[i + 1].strip())
for k in CCEL_CA:
    try: ccel_ca(k)
    except Exception as e: print("FAIL ccel", k, e)
with ThreadPoolExecutor(4) as ex: list(ex.map(ca_one, CA)); list(ex.map(ss_one, SSB))
with ThreadPoolExecutor(6) as ex: list(ex.map(st_one, [(p, q) for p, r in ST.items() for q in r]))
