#!/usr/bin/env python3
"""Report which upcoming dates have Mass readings (public/data/DATE.json) but no Meditation excerpt (content/DATE.json).
  python3 tools/coverage.py [--days 21] [--gh]
--gh prints GitHub Actions ::warning annotations and writes a job summary. Always exits 0 (informational only)."""
import os, sys, glob, datetime, argparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument("--days", type=int, default=21); ap.add_argument("--gh", action="store_true")
a = ap.parse_args()
try:
    from zoneinfo import ZoneInfo; today = datetime.datetime.now(ZoneInfo("America/New_York")).date()
except Exception:
    today = datetime.date.today()
have_readings = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, "public", "data", "20??-??-??.json"))}
have_med = {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, "content", "20??-??-??.json"))}
window = [(today + datetime.timedelta(d)).isoformat() for d in range(a.days)]
missing = [d for d in window if d not in have_med]
last = max(have_med) if have_med else "none"
msg = f"Meditation excerpts exist through {last}. Missing for {len(missing)} of the next {a.days} days" + (f": {', '.join(missing)}" if missing else ".")
print(msg)
no_read = [d for d in window if d not in have_readings]
if no_read: print(f"(no readings data yet for: {', '.join(no_read)}; run tools/build.py)")
if a.gh:
    if missing: print(f"::warning title=Meditation excerpts needed::{msg}")
    s = os.environ.get("GITHUB_STEP_SUMMARY")
    if s:
        with open(s, "a") as f: f.write(f"### Meditation coverage\n\n{msg}\n\nSee HANDOFF.md and MEDITATION_PROMPT.md to add `content/DATE.json` files.\n")
