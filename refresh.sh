#!/bin/sh
# Rebuild readings (USCCB -> KJV) for the next 45 days and re-render pages. Meditations appear only for dates with content/DATE.json.
cd "$(dirname "$0")" && python3 tools/build.py --days 45 >> refresh.log 2>&1 && python3 tools/render.py >> refresh.log 2>&1
