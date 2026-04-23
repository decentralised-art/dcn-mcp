#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT_DIR/.venv/bin/activate"

python -m unittest discover -s "$ROOT_DIR/tests" -v
python -m dcn_mcp.server list-tools >/dev/null
python -m dcn_mcp.server list-resources >/dev/null
python -m dcn_mcp.server invoke core.build_parent_connector '{"name":"piece","child_names":["a","b"]}' >/dev/null

echo "dcn-mcp smoke test passed"
