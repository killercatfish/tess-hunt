# sourced by the wrappers: repo root, venv, low priority, 1 thread per worker
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONWARNINGS=ignore
NICE="nice -n 19 ionice -c3"
cd "$ROOT"
