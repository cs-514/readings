# Brief for the daily "Meditation" excerpt (content/YYYY-MM-DD.json)

The daily feature is no longer an original meditation. Each day shows a **verbatim excerpt of at most 200 words** from an approved source, chosen because, applied to that day's readings, it demonstrates **CCC 129**: *"The New Testament lies hidden in the Old and the Old Testament is unveiled in the New"* (Augustine, Quaestiones in Heptateuchum 2,73): typology, fulfilment, an Old Testament figure, sign or promise illuminated in the New, and the New foreshadowed in the Old. (Related: CCC 128–130, 117, 1094, 140.)

No original prose is written, apart from the one-sentence lead-in below.

## Approved sources (all must be retrieved as real text; never quote from memory)
Catechism of the Catholic Church; Roman Catechism (Catechism of Trent); Catholic Encyclopedia (newadvent.org/cathen); Augustine's sermons on the New Testament lessons (NPNF 1, vol. 6, newadvent.org/fathers/1603.htm); John Henry Newman (newmanreader.org); Benedict XVI / Ratzinger (vatican.va homilies and Angelus: fine); The Imitation of Christ; J.R.R. Tolkien and C.S. Lewis (in copyright: only if the text can actually be retrieved, and keep excerpts short; none are in the index at present).
Texts live in `sources/*.txt` (committed). Add more with `tools/fetch_sources.py` (a dict of ids per source type) and re-run `python3 tools/index.py build`.

## JSON shape (content/YYYY-MM-DD.json)
```json
{"lead_in": "One sentence (max ~25 words) saying which reading(s) it illuminates.",
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
