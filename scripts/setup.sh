#!/usr/bin/env bash
# Prepare the ppt-studio Python runtime once. Later calls return immediately.
# Usage: bash scripts/setup.sh [--force]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# The runtime lives outside the skill folder: Playwright ships its own SKILL.md files, which a
# skills loader would otherwise pick up as extra skills.
VENV_DIR="${PPT_STUDIO_VENV:-${XDG_CACHE_HOME:-$HOME/.cache}/ppt-studio/venv}"
VENV_PY="$VENV_DIR/bin/python"
REQ="$SCRIPT_DIR/requirements.txt"

runtime_ready() {
  [[ -f "$VENV_DIR/.ready" && -x "$VENV_PY" ]] || return 1
  "$VENV_PY" -c "import playwright, pptx, PIL, numpy" >/dev/null 2>&1
}

if [[ "${1:-}" != "--force" ]] && runtime_ready; then
  echo "ppt-studio runtime is ready ($VENV_DIR)"
  exit 0
fi

supported() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

find_python() {
  local name path
  if [[ -n "${PPT_STUDIO_PYTHON:-}" ]]; then
    supported "$PPT_STUDIO_PYTHON" && { echo "$PPT_STUDIO_PYTHON"; return 0; }
    echo "PPT_STUDIO_PYTHON is not a Python 3.10+ executable: $PPT_STUDIO_PYTHON" >&2
    return 1
  fi
  for name in python3.13 python3.12 python3.11 python3.14 python3.10 python3 python; do
    path="$(command -v "$name" 2>/dev/null || true)"
    if [[ -n "$path" ]] && supported "$path"; then echo "$path"; return 0; fi
  done
  shopt -s nullglob
  for path in "$HOME"/.cache/codex-runtimes/*/dependencies/python/bin/python3; do
    if supported "$path"; then echo "$path"; return 0; fi
  done
  return 1
}

BASE_PY="$(find_python || true)"
if [[ -z "$BASE_PY" ]]; then
  echo "ppt-studio needs Python 3.10 or newer. Install one, or set PPT_STUDIO_PYTHON." >&2
  exit 1
fi

echo "Preparing ppt-studio runtime with $BASE_PY …"
rm -rf "$VENV_DIR"
mkdir -p "$(dirname "$VENV_DIR")"
if command -v uv >/dev/null 2>&1; then
  uv venv --quiet --python "$BASE_PY" "$VENV_DIR"
  uv pip install --quiet --python "$VENV_PY" -r "$REQ"
else
  "$BASE_PY" -m venv "$VENV_DIR"
  "$VENV_PY" -m pip install --quiet --disable-pip-version-check --upgrade pip
  "$VENV_PY" -m pip install --quiet --disable-pip-version-check -r "$REQ"
fi

# Use an installed Chrome/Edge when present; download Playwright Chromium only when none is found.
if ! "$VENV_PY" "$SCRIPT_DIR/_common.py" browser-check >/dev/null 2>&1; then
  echo "No usable Chrome/Edge found; downloading Playwright Chromium …"
  "$VENV_PY" -m playwright install chromium
  "$VENV_PY" "$SCRIPT_DIR/_common.py" browser-check
fi

date -u +%Y-%m-%dT%H:%M:%SZ > "$VENV_DIR/.ready"
echo "ppt-studio runtime is ready ($VENV_DIR)"
