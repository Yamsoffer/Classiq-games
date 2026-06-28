#!/usr/bin/env bash
# Start the local dev server (live-reload) for Classiq-games.
#   ./serve.sh                 -> opens Albert/albert.html
#   ./serve.sh index.html      -> opens a specific page
#   ./serve.sh --port 9000     -> custom port
cd "$(dirname "$0")" || exit 1
exec python3 serve.py "$@"
