#!/usr/bin/env bash
# Single source of truth for running tests locally. Requires Python >= 3.11.
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Prefer Homebrew Python 3.11 on macOS, but allow override via PYTHON_311.
PY311_DEFAULT="/opt/homebrew/bin/python3.11"
PY311="${PYTHON_311:-$PY311_DEFAULT}"

if [[ -x "$PY311" ]]; then
  PYBIN="$PY311"
elif command -v "$PY311" >/dev/null 2>&1; then
  PYBIN="$(command -v "$PY311")"
elif command -v python3.11 >/dev/null 2>&1; then
  PYBIN="$(command -v python3.11)"
else
  PYBIN="$(command -v python3)"
fi

if [[ ! -d .venv ]]; then
  echo "Creating .venv with $PYBIN"
  "$PYBIN" -m venv .venv
fi

source .venv/bin/activate
pip install -q -U pip
pip install -q -e ".[dev]"
pytest -v
