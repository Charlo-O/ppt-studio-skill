#!/usr/bin/env bash
# Package ppt-studio as a portable zip (no .venv, caches or OS files). Usage: bash tools/pack.sh [OUT.zip]
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$HOME/Desktop/ppt-studio.zip}"
cd "$(dirname "$SKILL_DIR")"
rm -f "$OUT"
zip -qr "$OUT" "$(basename "$SKILL_DIR")" -x "*/.venv/*" "*/__pycache__/*" "*.pyc" "*/.DS_Store"
echo "packed: $OUT ($(du -h "$OUT" | cut -f1))"
echo "install: unzip into ~/.claude/skills/ (Claude Code) or ~/.codex/skills/ (Codex); first use builds the runtime in ~/.cache/ppt-studio"
