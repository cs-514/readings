# Brief for the daily "Meditation" excerpt (content/YYYY-MM-DD.json)

The daily feature is no longer an original meditation. Each day shows a **verbatim excerpt of at most 200 words** from an approved source, chosen because, applied to that day's readings, it demonstrates **CCC 129**: *"The New Testament lies hidden in the Old and the Old Testament is unveiled in the New"* (Augustine, Quaestiones in Heptateuchum 2,73): typology, fulfilment, an Old Testament figure, sign or promise illuminated in the New, and the New foreshadowed in the Old. (Related: CCC 128–130, 117, 1094, 140.)

The Meditation section has two parts, summaries first, then the sourced excerpt (below). Besides the excerpt's lead-in, the only original prose is the plain summary block described next.

## Approved sources (all must be retrieved as real text; never quote from memory)
Catechism of the Catholic Church; Roman Catechism (Catechism of Trent); Catholic Encyclopedia (newadvent.org/cathen); Augustine's sermons on the New Testament lessons (NPNF 1, vol. 6, newadvent.org/fathers/1603.htm); John Henry Newman (newmanreader.org); Benedict XVI / Ratzinger (vatican.va homilies and Angelus: fine); The Imitation of Christ; J.R.R. Tolkien and C.S. Lewis (in copyright: only if the text can actually be retrieved, and keep excerpts short; none are in the index at present).
Texts live in `sources/*.txt` (committed). Add more with `tools/fetch_sources.py` (a dict of ids per source type) and re-run `python3 tools/index.py build`.

## JSON shape (content/YYYY-MM-DD.json)
```json
{"summaries": [{"label": "First Reading", "text": "…"}, {"label": "Psalm", "text": "…"}, {"label": "Gospel", "text": "…"}],
 "unity": "…",
 "lead_in": "One sentence (max ~25 words) saying which reading(s) it illuminates.",
 "excerpt": {"text": "Verbatim words. A spaced ellipsis \". . .\" marks an omission. Separate paragraphs with a blank line.",
             "source": "ccc | roman_catechism | aug_160340 | ce_15107a | newman_pps6_9 | benedict_… (a file in sources/)",
             "attribution": "Author, work, section/paragraph/page, enough to find it",
             "url": "optional; defaults to the URL in the source file's header"}}
```
## Hard rules (enforced by tools/render.py; the build aborts on violation)
1. Every segment of `excerpt.text` (split at `. . .`) must occur verbatim, and in order, in `sources/<source>.txt`. Matching ignores case, whitespace, curly vs straight quotes, space before punctuation, footnote numbers glued to punctuation (CCC) and `{page}` / `[ Note n ]` markers (Newman Reader). Do not change a word.
2. Excerpt ≤ 200 words (programmatic count, ellipses excluded). Lead-in ≤ 25 words; excerpt + lead-in ≤ 230.
3. Trim only at sentence boundaries: each segment must begin with a capital (or opening quote) and end with `.`, `?`, `!` or a closing quote. Mark every omission with a spaced ellipsis `. . .` (period-space-period-space-period) with NO brackets: when modifying a quotation, use `. . .`, never `[…]`. Put a space before it when it follows a sentence end (`garment? . . . You are`). The verifier also still tolerates legacy `[…]`, and accepts a genuine `. . .` already present in a source if the whole excerpt matches contiguously.
4. Attribution is displayed (author, work, section/paragraph/page) and linked to the source URL. Give the section number or page so a reader can find it.
5. The lead-in may say what the excerpt does for the readings, but must not put words in the author's mouth or add claims the excerpt does not make.


## Summary block (summaries + unity)
Each day that has content also gets, above the excerpt: one concise plain-English summary paragraph per reading (first reading, psalm, second reading if any, Gospel, in that order), then one final unifying paragraph.
- **Each reading summary: 1-3 sentences, at most 60 words.** Say what the passage actually says (events, claims, commands, images), using the USCCB/KJV/WEB text in `public/data/DATE.json`, never memory. No interpretation beyond the text.
- **Unity paragraph: 1-2 sentences, at most 50 words.** Show how the readings fit together, using the old/new hermeneutic of CCC 129 when it applies (OT figure/promise and its NT fulfilment), and end with a plain, practical application (something a person can do today or this week).
- Style: workmanlike, grounded in the text, not creative or flowery. No stock signposting ("the thread that runs through them all", "common thread", "all the readings share").
- JSON: `"summaries": [{"label": "First Reading", "text": "..."}, ...]` and `"unity": "..."`. Labels must be exactly the page labels (First Reading, Psalm, Second Reading, Gospel) in the order of the day's readings. `summaries` and `unity` must be given together or both omitted (a day without them renders without the block). `tools/render.py` aborts on a label mismatch or an over-length paragraph. Summaries are not source-quoted, so there is no verbatim check; they are checked by reading against the day's data.

## Selection procedure (no LLM needed; do it by hand with the local index)
1. Read the day's readings (`public/data/DATE.json`). Name the typological pairs: figure/event in the OT reading or psalm ↔ fulfilment in the NT reading or Gospel (e.g. finger of God/Sinai ↔ Spirit; Jonah ↔ Resurrection; Sarah and Hagar ↔ two covenants; Isaiah's banquet ↔ wedding feast; Eve's seed ↔ Mary; bridegroom of the prophets ↔ Christ). Prefer days where the pair is explicit in the texts.
2. `python3 tools/index.py build` (once), then search with the key terms of both sides, e.g.
   `python3 tools/index.py search "sign of Jonah three days type of Christ" -n 10 [--src ccc,roman,ce,aug,newman,benedict]`
   Also try the typology-explicit passages: `ccc §§128–130, 1094, 117`, `ce_15107a` (Types in Scripture).
3. Prefer, in this order: a passage that names *both* sides of the pair and the relation between them; a short passage (50–120 words) that stands on its own; a source most closely tied to the day's Gospel (Augustine's sermon on that Gospel, the CCC paragraph on that figure).
4. Open the candidate with `python3 tools/index.py show SOURCE_ID "starting phrase"`, copy the words exactly, cut at sentence boundaries, mark omissions with `. . .`.
5. Run `python3 tools/render.py`. If it aborts, fix the text; never loosen the check. Then commit, push, and confirm the Pages deploy.

## Copyright
Public-domain texts (Augustine NPNF, Newman, Catholic Encyclopedia, Imitation of Christ, Roman Catechism) and Vatican-published texts (CCC, Benedict XVI on vatican.va) are fine. For Tolkien, Lewis and Ratzinger books keep to a few sentences and only if actually retrieved.
