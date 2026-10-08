# Notices

## HTML → PPTX conversion core (`scripts/vendor/html_to_pptx.py`)

Adapted from Editable Design `skills/html-to-pptx/scripts/_html_to_pptx.py`
(https://github.com/yejy53/Editable-Design), licensed under the Apache License 2.0
(`scripts/vendor/LICENSE.html-to-pptx`). Modified for ppt-studio; every change is listed in the
module docstring and marked "ppt-studio": deck-root serving, browser fallback to installed
Chrome/Edge, multi-slide presentations, separate East Asian fonts per text run, and outer
shadows kept in the slide background.

## Icons (`assets/icons/lucide/`)

Lucide icon data (`lucide-static`, see `VERSION`), ISC License, `assets/icons/lucide/LICENSE`.

## Runtime dependencies (installed separately into `~/.cache/ppt-studio/venv`)

Playwright for Python (Apache-2.0), python-pptx (MIT), Pillow (HPND/MIT-CMU), NumPy (BSD-3-Clause).
