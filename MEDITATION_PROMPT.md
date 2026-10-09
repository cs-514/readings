# Brief for the daily meditation (content/YYYY-MM-DD.json)

Follow this for every meditation, in any future batch.

## Quality bar: excellent, not merely good
- The meditation must follow the readings and synthesize and unite ALL of them: first reading, psalm, second reading (if any) and Gospel. Each carries real weight; none is mere atmosphere.
- Use the psalm's actual distinctive lines (the refrain, specific verses, its imagery), not a generic summary of it. The psalm is usually the weak joint; make it do work in the argument.
- Offer practical application and inspiration: say concretely what living the readings looks like (e.g. what "occupying the house" means in practice: named, doable acts). A developed application, not a single image or antithesis, ending on a memorable closing line.
- Discern the unifying themes and explicate them subtly, through the texts' own wording and imagery. No stock signposting ("the thread that runs through them all", "common thread", "all three readings…", "what these readings share").

## Length
About 200 words in total, 190–215, counting everything on the page (the quote included).

## The Augustine quote (the only required quotation)
- One incisive quote from a real sermon of St Augustine on the day's Gospel (or closest relevant Gospel / parallel), woven INTO the prose as a reading of the Gospel passage: introduce it naturally ("Augustine says that “…”", "Augustine answers that it is charity: “…”"). Not a block quote, not a footer, no displayed citation.
- In the JSON, put the token `{{quote}}` inside a paragraph where the quote text belongs (inside your own quotation marks). The renderer substitutes `quote.text` there. The quote must start and end cleanly: start with a capital if the sentence begins there, or a lowercase fragment only when introduced grammatically (e.g. after "says that").
- It must be verbatim from a real online text (default: newadvent.org/fathers, NPNF 1, vol. 6 sermons on the New Testament lessons). `tools/render.py` fetches `quote.url` and aborts the build ("QUOTE NOT FOUND IN SOURCE") unless the text appears word for word. Never write a quote from memory.
- Keep `attribution`, `translation` and `url` in the JSON for verification and provenance; the page does not display them.

## Other sources: only if they earn their place
Acceptable: Catholic Encyclopedia (newadvent.org/cathen), the Catechism of the Catholic Church, the Roman Catechism (Trent), The Imitation of Christ (Thomas à Kempis; e.g. Project Gutenberg #1653 or CCEL), and the writings of John Henry Newman, J.R.R. Tolkien, Joseph Ratzinger / Benedict XVI, C.S. Lewis.
- Consult them, but include one only if the readings require it and it advances the movement of the argument. Otherwise omit. Never interrupt the flow with an inserted authority.
- Prefer a light paraphrase of the idea to quotation. Any quotation or specific attribution must be checked against a real text you actually retrieved (download the PDF/page and grep). Never attribute from memory; if you cannot retrieve it, leave it out.

## Critique used to set the standard (Oct 9 first draft)
"Good, not excellent: unites Paul and Luke tightly, treats the psalm as atmosphere, ends with one sharp application rather than a developed one. Strengths to keep: Galatians synthesized as one movement (Abraham's faith, blessing of nations, curse of the law, Christ a curse on the tree -> promise arrives as the Spirit given to those who trust); the Gospel handled precisely (strong man, stronger one strips armor, swept garnished house as the point); finger of God = the Spirit, same Spirit promised in the first reading; 'whoever does not gather, scatters'; the close 'Better to be occupied by the promise than merely tidy.' Weaknesses: Psalm 111 is the weak joint; it also supplies the refrain, the heritage of the nations, and a God gracious and full of compassion; those lines could carry Abraham's blessing into the Gospel's spoils. The Newman sentence does not earn its place; the Augustine sentence arrived as an inserted authority rather than as a reading of the parable, and the meditation never says what occupying the house looks like. A fuller version lets the psalm's remembered covenant and the heritage of the nations become the goods the Stronger One places in the house, so faith is not only the expulsion of the strong man but the indwelling that keeps the last state from being worse than the first."
Apply the same standard to every day.

## JSON shape
```json
{"paragraphs": ["… {{quote}} …", "…"],
 "quote": {"text": "verbatim Augustine", "attribution": "…", "translation": "…", "url": "https://www.newadvent.org/fathers/…htm"},
 "closing": null}
```
Then run `python3 tools/render.py` (verifies the quote, substitutes it, renders pages).
