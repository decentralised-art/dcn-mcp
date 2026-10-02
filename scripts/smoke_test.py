from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT_DIR / ".venv"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run(args: list[str], *, quiet: bool = False) -> None:
    env = os.environ.copy()
    src = str(ROOT_DIR / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not existing else src + os.pathsep + existing
    stdout = subprocess.DEVNULL if quiet else None
    subprocess.run(args, cwd=str(ROOT_DIR), env=env, check=True, stdout=stdout)


def main() -> None:
    python = str(venv_python())
    run([python, "-m", "unittest", "discover", "-s", str(ROOT_DIR / "tests"), "-v"])
    run([python, "-m", "decentralised_art_mcp.server", "list-tools"], quiet=True)
    run([python, "-m", "decentralised_art_mcp.server", "list-resources"], quiet=True)
    payload = json.dumps({"name": "piece", "child_names": ["a", "b"]})
    run([python, "-m", "decentralised_art_mcp.server", "invoke", "core.build_parent_connector", payload], quiet=True)
    print("decentralised.art MCP smoke test passed")


if __name__ == "__main__":
    main()
