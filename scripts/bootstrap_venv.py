from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT_DIR / ".venv"
STAMP = VENV_DIR / ".bootstrap-complete"


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    if not VENV_DIR.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    python = venv_python(VENV_DIR)
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "-e", str(ROOT_DIR)])

    STAMP.parent.mkdir(parents=True, exist_ok=True)
    STAMP.touch()
    print(f"Bootstrapped venv at {VENV_DIR}")
    print(f"Python: {python}")


if __name__ == "__main__":
    main()
