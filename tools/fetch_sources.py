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
