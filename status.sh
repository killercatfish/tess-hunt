#!/usr/bin/env bash
source "$(dirname "$0")/scripts/_env.sh"
"$PY" -m tesshunt status "$@"
echo "--- last log lines"; tail -n 5 logs/run.log 2>/dev/null
