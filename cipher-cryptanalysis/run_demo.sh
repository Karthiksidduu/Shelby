#!/usr/bin/env bash
# One command for the lecture, from this folder: ./run_demo.sh
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  exec python3 run_demo.py
fi
exec python run_demo.py
