#!/usr/bin/env bash
# One-time setup on Cortex: Python 3.12 venv via uv.
set -euo pipefail
cd "$(dirname "$0")"
UV="${UV:-$HOME/.local/bin/uv}"
[ -d .venv ] || "$UV" venv --python 3.12 .venv
"$UV" pip install --python .venv/bin/python -r requirements.txt
echo "ok: $(.venv/bin/python --version)"
