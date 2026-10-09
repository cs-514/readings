#!/bin/sh
cd "$(dirname "$0")/public" && exec python3 -m http.server ${1:-8099}
