# Brief for the daily meditation (content/YYYY-MM-DD.json)

Follow this for every meditation, in any future batch.

## Length and voice
- About 200 words in total (target 190–215), counting paragraphs + quote + closing.
- A meditation on the day's readings (first reading, psalm, second reading if any, Gospel), in plain, warm, unhurried prose.

## No signposting
- Do NOT announce unity. Ban stock phrases such as "the thread that runs through them all", "common thread", "the connecting theme", "all three readings…", "what these readings share", or similar.
- Instead, discern the unifying themes yourself and let them surface subtly through the texts' own imagery and wording (doors, oil, houses, thirst, a tree, etc.), placing the images side by side without explaining that they belong together.

## The Augustine quote (the only required quotation)
- Exactly one incisive quote from a real sermon of St Augustine on the day's Gospel (or the closest relevant Gospel / parallel).
- It must be verbatim from a real online text (default: newadvent.org/fathers, NPNF 1, vol. 6 sermons on the New Testament lessons). `tools/render.py` fetches `quote.url` and fails the build ("QUOTE NOT FOUND IN SOURCE") unless the text appears word for word. Never write a quote from memory.
- Keep `attribution`, `translation` and `url` in the JSON (needed for verification and provenance). The page does NOT display the citation or source; it shows only "— St Augustine".

## Other sources (optional, light touch)
Where fitting, draw on: Catholic Encyclopedia (newadvent.org/cathen), the Catechism of the Catholic Church, the Roman Catechism (Catechism of Trent), and the writings of John Henry Newman, J.R.R. Tolkien, Joseph Ratzinger / Benedict XVI, C.S. Lewis.
- Prefer paraphrase of an idea, lightly woven in, to quotation. Do not stack citations.
- Any quotation or specific attribution ("Newman saw…", "the Catechism teaches…") must be checked against a real text you actually retrieved (download the PDF/page and grep it). Never attribute from memory. If you cannot retrieve it, leave it out.
- Short quotes from these sources are allowed only when verified; none are required.

## JSON shape
```json
{"paragraphs": ["…", "…"],
 "quote": {"text": "…", "attribution": "…", "translation": "…", "url": "https://www.newadvent.org/fathers/…htm"},
 "closing": "…"}
```
Then run `python3 tools/render.py` (verifies the quote and renders pages).
