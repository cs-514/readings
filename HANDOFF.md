# Handoff: Daily Mass Readings site

Live site: https://cs-514.github.io/readings/ · Repo: `cs-514/readings` (branch `main`).
Owner: Joel Trotter. This repo now holds **everything** needed to run the site. No outside bot, server or cron job is required.

## What the site is
A static PWA (installable, works offline via `public/sw.js`). It shows each day's Catholic Mass readings from the USCCB lectionary in the
**King James Version** (default) or the **World English Bible, Catholic Edition** (toggle). Each day also has a short **Meditation**:
a verbatim excerpt (≤200 words) from an approved Catholic source that shows the Old Testament/New Testament link in that day's readings
(CCC 129: "The New Testament lies hidden in the Old and the Old Testament is unveiled in the New"), with a one-sentence lead-in.
It also has a "Read this page" button (browser speech synthesis) and a plain, TTS-friendly page per day at `/d/YYYY-MM-DD/`.
App URL forms: `/?date=YYYY-MM-DD`, `/?tr=web`.

## Two parts, two ways they are updated
| Part | How it's made | Automated? |
|---|---|---|
| Readings (KJV + WEB-CE text) | `tools/build.py` scrapes `https://bible.usccb.org/bible/readings/MMDDYY.cfm`, maps NABRE citations to KJV (bible-api.com, incl. 1611 Apocrypha) and WEB-CE (`cache/web/*.json`) | **Yes.** GitHub Actions, daily |
| Meditation excerpt | A hand-picked file `content/YYYY-MM-DD.json` per day | **No.** Must be written ahead of time (this is the job for the new tool) |

**Status at handoff (Nov 26, 2026):** meditation files exist for 2026-10-09 through **2026-11-28**. From 2026-11-29 on, days show the
readings with no Meditation until `content/` files are added. The daily workflow now prints a warning listing the missing days
(`tools/coverage.py`).

## USCCB page formats (read this if a day shows no readings)
- Most days: readings are on `https://bible.usccb.org/bible/readings/MMDDYY.cfm`.
- **Multi-option days** (Thanksgiving, Christmas, some US-only memorials): the main page only lists links ("Readings for the ...").
  `tools/lib.py` follows each link, caches it as `cache/usccb/DATE~SLUG.html`, and tags each reading with `option` / `option_url`;
  the page shows a heading per option (e.g. "Thursday of the Thirty-fourth Week in Ordinary Time", then "Thanksgiving Day").
- USCCB changed its HTML in Nov 2026 (`<header class="content-header">` instead of `<div class="address">`). `tools/lib.py` parses both.
- If a day still parses with zero readings, `tools/build.py` prints a `::warning title=No readings parsed::` annotation in the
  Actions run, and the page shows a link to USCCB instead of a blank page. Fetched USCCB pages are cached in `cache/usccb/`;
  delete a day's file there to force a re-fetch.
- Build dates are computed in US Eastern time (the runner clock is UTC), starting one day back.

## Daily automation (already running)
`.github/workflows/daily.yml` (workflow name `daily-build`):
- Triggers: cron `15 4 * * *` (04:15 UTC ≈ 11:15 PM ET; GitHub often starts it later), every push to `main`, and manual `workflow_dispatch`.
- Steps: `python3 tools/build.py --days 45` (readings for the next 45 days) → `python3 tools/render.py` (merges `content/`,
  verifies excerpts, writes `public/d/DATE/index.html` and `public/data/index.json`, then runs `tools/rules.py`) →
  `python3 tools/coverage.py --gh` (warning only) → deploy `public/` to GitHub Pages (Pages source = "GitHub Actions").
- The workflow does **not** commit build output back; it builds fresh and deploys the artifact. Files under `public/data` and `public/d`
  in the repo are a snapshot from the last local build and are harmless.
- **No secrets or API keys are needed.** Python 3 standard library only (Pillow only for `tools/icons.py`, which is not in the build).

If `render.py` or `rules.py` fails (bad excerpt, straight quote, etc.) the whole build fails and the site is not redeployed, so the
last good version stays live. Check the Actions tab.

## What the new tool needs to do
Keep `content/` at least a couple of weeks ahead of today. For each date:
1. Read that day's readings: `public/data/DATE.json` (run `python3 tools/build.py --days 45` locally first if it's missing).
2. Follow **`MEDITATION_PROMPT.md`** exactly (it is the full brief: approved sources, selection procedure, hard rules, copyright).
3. Find a passage in the local library: `python3 tools/index.py build` (once), then
   `python3 tools/index.py search "key words from both readings" -n 10 [--src ccc,roman,ce,aug,newman,benedict,aq]`, and
   `python3 tools/index.py show SOURCE_ID "starting phrase"`.
4. Write the file with the extractor so wording is never retyped:
   `python3 tools/mk.py DATE SOURCE_ID "Attribution" "One-sentence lead-in." "start phrase>>end phrase" ["start2>>end2" ...]`
5. `python3 tools/render.py` must pass (never loosen a check to make it pass). Optionally `python3 tools/coverage.py`.
6. Commit `content/DATE.json` and push to `main`; the push triggers a deploy.

An LLM can do steps 1–4, but the excerpt must come from `sources/*.txt` verbatim; `render.py` rejects anything else.
If you automate this with an LLM inside GitHub Actions, put the key in a repo secret (e.g. `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`)
and give the workflow `contents: write`. None is set up today.

### content/YYYY-MM-DD.json shape
```json
{"lead_in": "One sentence (≤25 words) saying which reading(s) it illuminates.",
 "excerpt": {"text": "Verbatim words. Omissions marked with a spaced . . . (no brackets). Blank line between paragraphs.",
             "source": "file id in sources/, e.g. ccc, aug_160340, newman_pps6_9, aq_ca_mt_22",
             "attribution": "Author, work, section/paragraph, enough to find it"}}
```
Only the keys `lead_in` and `excerpt` (with `text`, `source`, `attribution`) are allowed.

## Joel's editorial rules (enforced in `tools/rules.py`; the build aborts on violation)
- Meditation = excerpt + lead-in only. No summaries, commentary or original meditations.
- Sources must be on the approved list (`aq_`, `aug*`, `benedict_`, `ratzinger`, `ccc`, `ce_`, `imitation`, `newman_`, `roman_catechism`, `lewis`, `tolkien`).
- Excerpt ≤200 words, lead-in ≤25, total ≤230; cut only at sentence boundaries.
- Omissions: plain spaced `. . .`, never `[…]`, `[...]` or `…`.
- Heading must read "Meditation"; subheading "Mass readings (USCCB lectionary), King James Version".
- "LORD's" with a lowercase s. Never use the phrase "text of the".
- All displayed quotes and apostrophes are curly, never straight.
When Joel corrects something, add a check to `tools/rules.py`, not just a note.

## File layout
```
.github/workflows/daily.yml  daily build + Pages deploy
tools/build.py      USCCB -> KJV/WEB-CE readings, writes public/data/DATE.json (verse alignment logic, special cases)
tools/lib.py        shared helpers (fetching with cache, smart quotes, etc.)
tools/render.py     merges content/, verifies excerpts, prerenders public/d/DATE/index.html, public/data/index.json
tools/rules.py      Joel's editorial rules as hard checks
tools/coverage.py   lists upcoming days without a Meditation
tools/index.py      local search over sources/*.txt (build/search/show)
tools/mk.py         writes content/DATE.json from verbatim source segments
tools/fetch_sources.py  downloads more source texts into sources/
tools/webc.py       converts the eBible WEB-C USFM zip into cache/web/*.json (already done and committed)
tools/icons.py      regenerates app icons (needs Pillow)
content/            one Meditation file per day (hand-authored)
sources/            ~1,800 approved source texts (plain text, header then body)
cache/              committed fetch caches (kjv, na, usccb, web); cache/index.json is generated and git-ignored
public/             the site: index.html, app.js, tr.js (translation toggle), sw.js, style.css, manifest, icons, data/, d/
tests/toggle_test.py Playwright check of the KJV | WEB-CE toggle, plain pages and app view: python3 tests/toggle_test.py http://localhost:8099/
refresh.sh / serve.sh  local rebuild / local server on :8099
MEDITATION_PROMPT.md   full brief for choosing excerpts
```

## Build and preview locally
```
./refresh.sh            # build.py --days 45 && render.py (log in refresh.log)
./serve.sh              # http://localhost:8099/
```
When you change `public/app.js`, `sw.js` or styles, bump the service-worker cache version in `public/sw.js` so installed copies update.

## Copyright
Public-domain and Vatican-published texts are fine. Keep in-copyright texts (Tolkien, Lewis, Ratzinger books, modern Aquinas translations)
to a few sentences. See `MEDITATION_PROMPT.md`.
