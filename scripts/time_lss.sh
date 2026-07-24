#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: scripts/time_lss.sh <path> [runs]" >&2
    exit 1
fi

target_path=$1
runs=${2:-20}

if [[ ! -d .venv ]]; then
    echo "Error: expected .venv in repo root: $(pwd)/.venv" >&2
    exit 1
fi

if [[ ! -d lib/pyseq ]]; then
    echo "Error: expected to run from repo root containing lib/pyseq" >&2
    exit 1
fi

if ! [[ $runs =~ ^[0-9]+$ ]] || [[ $runs -lt 1 ]]; then
    echo "Error: runs must be a positive integer" >&2
    exit 1
fi

echo "# repo: $(pwd)"
echo "# target: $target_path"
echo "# runs: $runs"
echo "# python: $(realpath .venv/bin/python3)"

PYTHONPATH=lib .venv/bin/python3 - <<'PY'
import sys
import pyseq
import pyseq.seq
print(f"# pyseq: {pyseq.__file__}")
print(f"# pyseq.seq: {pyseq.seq.__file__}")
print(f"# sys.executable: {sys.executable}")
PY

for run in $(seq 1 "$runs"); do
    seconds=$(
        {
            /usr/bin/time -f '%e' \
                env PYTHONPATH=lib .venv/bin/python3 -m pyseq.lss "$target_path" \
                >/dev/null
        } 2>&1
    )
    echo "$run $seconds"
done
