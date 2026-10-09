#!/usr/bin/env bash
# Run in a detached tmux session named tess: `tmux attach -t tess` to watch, Ctrl-b d to detach.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
tmux new-session -d -s tess "cd $ROOT && ./run.sh $*; echo finished; read"
echo "started tmux session 'tess'"
