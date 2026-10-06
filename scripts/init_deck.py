#!/usr/bin/env python3
"""Create a new ppt-studio deck project.

  init_deck.py DIR [--title "..."] [--style REF] [--slides N] [--lang zh-CN]
               [--canvas 1920x1080] [--mode editable|image]

Refuses to touch an existing non-empty directory, so a deck the user already owns is never
overwritten by accident. Layout of the new project:

  deck.json  brief.md  outline.md  design-plan.md  render-review.md  theme.css
  style/  assets/  slides/  out/
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import STARTER_DIR, die  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a ppt-studio deck project")
    parser.add_argument("dir")
    parser.add_argument("--title", default="")
    parser.add_argument("--style", help="style id or name to copy into the deck")
    parser.add_argument("--slides", type=int, default=0, help="pre-create N slide entries")
    parser.add_argument("--lang", default="zh-CN")
    parser.add_argument("--canvas", default="1920x1080")
    parser.add_argument("--mode", choices=["editable", "image"], default="editable")
    args = parser.parse_args()

    deck = Path(args.dir).expanduser().resolve()
    if deck.exists() and any(deck.iterdir()):
        die(f"{deck} already exists and is not empty. Ask the user whether to continue that deck "
            "or pick a new folder name.")
    match = re.fullmatch(r"(\d+)x(\d+)", args.canvas)
    if not match:
        die("--canvas must look like 1920x1080")
    width, height = int(match.group(1)), int(match.group(2))

    for sub in ("style", "assets", "slides", "out"):
        (deck / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(STARTER_DIR / "theme.css", deck / "theme.css")
    template = (STARTER_DIR / "slides" / "_template.html").read_text(encoding="utf-8")
    template = template.replace('lang="zh-CN"', f'lang="{args.lang}"')
    template = template.replace('data-canvas-width="1920" data-canvas-height="1080"',
                                f'data-canvas-width="{width}" data-canvas-height="{height}"')
    (deck / "slides" / "_template.html").write_text(template, encoding="utf-8")
    css = (deck / "theme.css").read_text(encoding="utf-8")
    if (width, height) != (1920, 1080):
        css = css.replace("1920px", f"{width}px").replace("1080px", f"{height}px")
    lang = args.lang.lower()
    if lang.startswith("ja"):
        css = css.replace('"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
                          '"Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", sans-serif')
    elif not lang.startswith("zh"):
        css = css.replace('"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
                          '"Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif')
    (deck / "theme.css").write_text(css, encoding="utf-8")

    slides = [
        {"id": f"s{i:02d}", "file": f"slides/s{i:02d}.html", "type": "", "title": "", "notes": ""}
        for i in range(1, args.slides + 1)
    ]
    data = {
        "title": args.title,
        "lang": args.lang,
        "mode": args.mode,
        "canvas": {"width": width, "height": height},
        "style": None,
        "slides": slides,
        "created": dt.datetime.now().isoformat(timespec="seconds"),
    }
    (deck / "deck.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (deck / "brief.md").write_text("# Brief\n\n", encoding="utf-8")
    outline = ["# Outline", "", f"Deck: {args.title or '(title)'} · audience: · goal: · language: {args.lang}", ""]
    for slide in slides:
        outline += [f"## {slide['id']} · (type)", "- Title:", "- Body:", "- Visual:", "- Notes:", ""]
    (deck / "outline.md").write_text("\n".join(outline), encoding="utf-8")
    (deck / "design-plan.md").write_text(
        "# Design plan\n\n## Style requirements and implementation\n\n## Deck system\n\n## Agent-designed slides\n", encoding="utf-8")
    (deck / "render-review.md").write_text("# Render review\n", encoding="utf-8")

    if args.style:
        import styles  # noqa: E402

        styles.cmd_use(argparse.Namespace(ref=args.style, deck=str(deck)))

    print(f"deck created: {deck}")
    print(f"canvas {width}x{height} · mode {args.mode} · {len(slides)} slide entries")


if __name__ == "__main__":
    main()
