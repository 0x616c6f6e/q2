#!/usr/bin/env bash
# Linux firmware entry; use the active ESP-IDF Python, preserving every caller argument.
set -euo pipefail
q2_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
q2_python="${Q2_PYTHON:-python3}"
if ! command -v "$q2_python" >/dev/null 2>&1; then
    printf 'Q2: Python not found: %s. Activate ESP-IDF or set Q2_PYTHON.\n' "$q2_python" >&2
    exit 127
fi
# Explicit user --target overrides the firmware default through argparse.
exec "$q2_python" "$q2_root/q2.py" build --target esp32s3 "$@"
