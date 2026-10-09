#!/usr/bin/env bash
# Start (or resume) processing. Ctrl-C is safe: at most the stars in progress are redone.
#   ./run.sh                 queued pilot stars, then report
#   ./run.sh --workers 3     override worker count
source "$(dirname "$0")/scripts/_env.sh"
exec $NICE "$PY" -m tesshunt run "$@"
