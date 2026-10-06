# Notices

## Style library (`library/`)

Slide-style prompts from the NotebookLM Slide Style Gallery, curated by
KUMIKO SHIRAKI (https://notebooklm-slide-gallery.shirakippt.chatgpt.site/). Chinese translations
by the collection's compiler (machine translation with revised terms). Example boards and the external source collection are excluded from this repository. The prompts
remain the work of their author; they are included for personal use only and are not
covered by any license in this folder. Per-style sources: `library/styles.json`, `library/SOURCE.md`.

## HTML → PPTX conversion core (`scripts/vendor/html_to_pptx.py`)

Adapted from Editable Design `skills/html-to-pptx/scripts/_html_to_pptx.py`
(https://github.com/yejy53/Editable-Design), licensed under the Apache License 2.0
(`scripts/vendor/LICENSE.html-to-pptx`). Modified for ppt-studio; every change is listed in the
module docstring and marked "ppt-studio": deck-root serving, browser fallback to installed
Chrome/Edge, multi-slide presentations, separate East Asian fonts per text run, and outer
shadows kept in the slide background.

## Method

The text-free artwork prompting and live-text assembly guidance were adapted from Editable
Design's `editable-design` skill (Apache License 2.0). The current workflow has the Agent compose
slides directly from written style specifications and review the rendered implementation.

## Icons (`assets/icons/lucide/`)

Lucide icon data (`lucide-static`, see `VERSION`), ISC License, `assets/icons/lucide/LICENSE`.

## Runtime dependencies (installed separately into `~/.cache/ppt-studio/venv`)

Playwright for Python (Apache-2.0), python-pptx (MIT), Pillow (HPND/MIT-CMU), NumPy (BSD-3-Clause).
