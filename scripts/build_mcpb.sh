#!/usr/bin/env sh
set -eu

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT_DIR/.venv/bin/python" -m decentralised_art_mcp.mcpb
