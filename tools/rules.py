"""Hard checks for the user's standing editorial rules. Any failure aborts the build.
Each rule here came from a correction by the user; add new corrections here rather than only to prose docs."""
import glob, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPROVED = re.compile(r"^(aq_|aug|benedict_|ratzinger|ccc$|ce_|imitation$|newman_|roman_catechism$|lewis|tolkien)")
BRACKET_ELLIPSIS = re.compile(r"\[\s*(\u2026|(\.\s*){3})\s*\]")      # "[…]" / "[...]" never allowed
LEAD_ELLIPSIS = re.compile(r"\u2026|\.\.\.")                          # my own prose: only ". . ."
SUB = "Mass readings (USCCB lectionary), King James Version"
def check():
    errs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "content", "*.json"))):
        d = os.path.basename(f)[:-5]; c = json.load(open(f))
        extra = set(c) - {"lead_in", "excerpt"}
        if extra: errs.append(f"{d}: Meditation must be excerpt + lead-in only (no summaries/commentary); unexpected keys {sorted(extra)}")
        ex = c.get("excerpt") or {}
        if set(ex) - {"text", "attribution", "source"}: errs.append(f"{d}: unexpected excerpt keys {sorted(set(ex) - {'text','attribution','source'})}")
        if ex and not APPROVED.match(ex.get("source", "")): errs.append(f"{d}: source '{ex.get('source')}' is not on the approved list")
        for k, t in (("excerpt", ex.get("text", "")), ("lead-in", c.get("lead_in") or "")):
            # (excerpt text is otherwise checked word-for-word against the source, so the source's own punctuation and brackets are fine)
            if BRACKET_ELLIPSIS.search(t) or (k == "lead-in" and LEAD_ELLIPSIS.search(t)):
                errs.append(f"{d}: {k} marks an omission with a non-standard ellipsis; use a plain spaced '. . .' with no brackets")
    for f in sorted(glob.glob(os.path.join(ROOT, "public", "d", "*", "index.html"))):
        d = f.split(os.sep)[-2]; h = open(f, encoding="utf-8").read()
        if "<h2>Meditation</h2>" not in h: errs.append(f"{d}: missing the 'Meditation' heading")
        if SUB not in h: errs.append(f"{d}: subheading must read '{SUB}'")
        if re.search(r"LORD['\u2019]S", h): errs.append(f"{d}: 'LORD's' must use a lowercase s")
        vis = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", h, flags=re.S)
        vis = vis.replace("&quot;", '"').replace("&#x27;", "'").replace("&#39;", "'")
        sq = re.findall(r".{0,25}['\"].{0,25}", vis)
        if sq: errs.append(f"{d}: straight quotes in page text (use curly quotes): {sq[0]!r}")
        dd = json.load(open(os.path.join(ROOT, "public", "data", d + ".json")))
        def walk(o, k=None):
            if isinstance(o, dict): [walk(v, kk) for kk, v in o.items()]
            elif isinstance(o, list): [walk(v, k) for v in o]
            elif isinstance(o, str) and k not in ("date", "source", "url", "label", "id") and not o.startswith("http") and re.search(r"['\"]", o):
                errs.append(f"{d}: straight quote in {k}: {o[:50]!r}")
        walk(dd)
        if re.search(r"text of the", h, re.I): errs.append(f"{d}: contains the phrase 'text of the' (removed at user's request)")
    if errs: raise SystemExit("EDITORIAL RULE CHECK FAILED:\n  " + "\n  ".join(errs))
    print("editorial rules: all checks passed")
if __name__ == "__main__": check()
