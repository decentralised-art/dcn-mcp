#!/usr/bin/env sh
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/scripts/smoke_test.py"
