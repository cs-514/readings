# Daily Mass Readings (KJV) – PWA
Static site. `tools/build.py` reads USCCB (https://bible.usccb.org/bible/readings/MMDDYY.cfm), maps citations to KJV (bible-api.com data endpoint, incl. 1611 Apocrypha) and writes `public/data/DATE.json`.
`content/DATE.json` holds the meditation + Augustine quote; `tools/render.py` verifies the quote verbatim against its newadvent.org page, then writes `public/d/DATE/index.html` (plain, TTS-friendly) and `public/data/index.json`.
Run `./refresh.sh` (cron does this daily), `./serve.sh` to serve `public/` on :8099. App URL form: `/?date=YYYY-MM-DD`; plain page: `/d/YYYY-MM-DD/`.
Verse alignment: NABRE vs KJV numbering is resolved by trying shifts (0,-1,-2,-3,+1,-4) and keeping the best word-overlap with the USCCB text, plus special-case tables (Isaiah 8:23, Joel, Malachi, Jonah, Hosea, Daniel additions). Below threshold => a note is shown instead of text.

Daily excerpt: `content/DATE.json` holds a verbatim excerpt (<=200 words) illustrating CCC 129 (OT/NT typology), verified by `tools/render.py` against `sources/*.txt`. See `MEDITATION_PROMPT.md` for the brief and selection procedure; Approved sources include St Thomas Aquinas (Catena Aurea, Summa Theologiae, scripture commentaries; files `aq_*`). `tools/fetch_sources.py` and `tools/index.py` build/search the local source index.

Omissions in an excerpt are marked with a spaced ellipsis `. . .` (no brackets); the verifier checks each segment between ellipses verbatim against `sources/`.

Translations: KJV (default, bible-api.com) and World English Bible, Catholic Edition (eBible.org, public domain). `tools/webc.py` converts the eBible USFM zip into `cache/web/*.json` (committed, so the Action needs no download). `tools/build.py` matches each USCCB citation in both translations (shared shift/special-case/word-overlap logic; half-verses a/b split at clause boundaries; unmatched passages get a note instead of text) and stores the WEB text under `passages[].web`. `public/tr.js` provides the KJV | WEB-CE toggle (localStorage `dr-tr`, `?tr=web`).
