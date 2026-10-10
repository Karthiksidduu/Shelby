"""Start the lecture demo with one command.

From this folder:

    python run_demo.py

On macOS or Linux you can also double-click nothing and run ``./run_demo.sh``.
On Windows, double-click ``run_demo.bat``.

The script creates ``.venv`` if it is missing, installs the requirements,
prints the five clicks, and opens the Streamlit app.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _venv_python() -> Path:
    """Path to the interpreter inside this project's virtual environment."""
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def _reexec(python: Path) -> None:
    """Replace this process with the same script running under ``python``."""
    script = str(Path(__file__).resolve())
    os.execv(str(python), [str(python), script, *sys.argv[1:]])


def _skip_streamlit_prompts() -> None:
    """Write Streamlit's first-run files so it does not ask for an email."""
    folder = Path.home() / ".streamlit"
    folder.mkdir(parents=True, exist_ok=True)
    credentials = folder / "credentials.toml"
    if not credentials.exists():
        credentials.write_text("[general]\nemail = \"\"\n", encoding="utf-8")
    config = folder / "config.toml"
    if not config.exists():
        config.write_text("[browser]\ngatherUsageStats = false\n", encoding="utf-8")


def _print_clicks() -> None:
    """Print the only five clicks needed once the browser opens."""
    print()
    print("Lecture demo is starting. When the browser opens, use Pages in the left sidebar:")
    print("  Break Caesar Cipher")
    print("  Break Substitution Cipher")
    print("  Encrypt Demo")
    print("  Why Monoalphabetic Ciphers Fail")
    print()
    print("Leave this window open until the presentation is over.")
    print()


def main() -> None:
    """Create the environment if needed, then launch Streamlit."""
    os.chdir(ROOT)
    venv_python = _venv_python()

    if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
        _reexec(venv_python)

    if not venv_python.exists():
        print("Creating a virtual environment in .venv ...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(ROOT / ".venv")])
        except subprocess.CalledProcessError:
            print("Could not create .venv. Using this Python instead.")
            print("On Ubuntu, install it later with: sudo apt install python3-venv")
        else:
            _reexec(venv_python)

    try:
        import streamlit  # noqa: F401
    except ImportError:
        print("Installing the packages from requirements.txt ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")]
        )

    _skip_streamlit_prompts()
    _print_clicks()
    os.execv(
        sys.executable,
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py")],
    )


if __name__ == "__main__":
    main()
