#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements/dev.txt
.venv/bin/python -m pip install -e .

echo "Virtual environment created. Activate it with: source .venv/bin/activate"
echo "Then run: python scripts/verify_setup.py"
