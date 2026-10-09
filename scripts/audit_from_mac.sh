#!/usr/bin/env bash
# Run ON THE MAC. Mirrors survivor pages from Cortex, runs one fresh read-only `claude -p` per
# survivor, pushes the notes back, and imports them into Cortex's DB + report.
#   scripts/audit_from_mac.sh                       # pilot candidates
#   scripts/audit_from_mac.sh validation/out/candidates validation   # validation set
set -euo pipefail
REMOTE="${REMOTE:-cortex-lan}"
DIR="${1:-candidates}"
MODE="${2:-pilot}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL="$(mktemp -d)"
rsync -a --include='*/' --include='sig*.png' --include='sig*.json' --include='sig*.audit.txt' --exclude='*' \
  "$REMOTE:dev/tess-hunt/$DIR/" "$LOCAL/"
python3 "$HERE/scripts/claude_audit.py" "$LOCAL"
rsync -a --include='*/' --include='sig*.audit.txt' --exclude='*' "$LOCAL/" "$REMOTE:dev/tess-hunt/$DIR/"
if [ "$MODE" = validation ]; then
  ssh "$REMOTE" "cd ~/dev/tess-hunt && .venv/bin/python -c 'from tesshunt import config, validate, audit, report; c=validate.vcfg(config.load()); print(\"imported\", audit.import_notes(c)); report.build(c, title=\"tess-hunt VALIDATION survivors\")'"
else
  ssh "$REMOTE" "cd ~/dev/tess-hunt && .venv/bin/python -m tesshunt audit --import-notes"
fi
rm -rf "$LOCAL"
