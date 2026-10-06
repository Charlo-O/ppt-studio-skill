#!/usr/bin/env python3
"""Find Lucide icons and print inline SVG markup for slides (no runtime requests).

  icons.py search <words...> [--top 15]
  icons.py svg <name> [<name> ...] [--size 48] [--stroke 2] [--color currentColor] [--class icon]
  icons.py inline FILE_OR_DIR ...
      replaces every <i data-icon="name" data-size="48" data-stroke="2" data-color="#hex"
      class="…" style="…"></i> placeholder with the inline SVG, in place (idempotent)

Lucide is an outline set. For styles that want solid icons, place the outline glyph in white on
a filled circle or rounded square; that reads as a solid badge and stays editable in PowerPoint.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "assets" / "icons" / "lucide"


def load():
    nodes = json.loads((DATA / "icon-nodes.json").read_text(encoding="utf-8"))
    tags = json.loads((DATA / "tags.json").read_text(encoding="utf-8"))
    return nodes, tags


def render(name: str, nodes: dict, size: int, stroke: float, color: str, css_class: str) -> str:
    if name not in nodes:
        raise SystemExit(f"unknown icon '{name}' (try: icons.py search {name})")
    inner = "".join(
        f"<{tag} " + " ".join(f'{key}="{html.escape(str(value))}"' for key, value in attrs.items()) + "/>"
        for tag, attrs in nodes[name]
    )
    class_attr = f' class="{css_class}"' if css_class else ""
    return (f'<svg{class_attr} xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round">{inner}</svg>')


PLACEHOLDER = re.compile(r'<i\b([^>]*\bdata-icon="[^"]+"[^>]*)>\s*</i>', re.I)
ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def inline_file(path: Path, nodes: dict) -> int:
    text = path.read_text(encoding="utf-8")
    count = 0

    def swap(match) -> str:
        nonlocal count
        attrs = dict(ATTR.findall(match.group(1)))
        markup = render(attrs["data-icon"], nodes, int(float(attrs.get("data-size", 48))),
                        float(attrs.get("data-stroke", 2)), attrs.get("data-color", "currentColor"),
                        attrs.get("class", ""))
        extra = "".join(f' {key}="{attrs[key]}"' for key in ("id", "style") if key in attrs)
        count += 1
        return markup.replace("<svg", "<svg" + extra, 1)

    updated = PLACEHOLDER.sub(swap, text)
    if count:
        path.write_text(updated, encoding="utf-8")
    return count


def cmd_inline(args) -> None:
    nodes, _ = load()
    files = []
    for target in args.paths:
        path = Path(target)
        files += sorted(path.glob("*.html")) if path.is_dir() else [path]
    total = 0
    for path in files:
        n = inline_file(path, nodes)
        total += n
        if n:
            print(f"{path}: {n} icon(s) inlined")
    print(f"{total} icon placeholder(s) replaced")


def cmd_search(args) -> None:
    nodes, tags = load()
    words = [w for w in re.split(r"[\s,]+", " ".join(args.words).lower()) if w]
    scored = []
    for name in nodes:
        name_words = name.split("-")
        score = 0
        for word in words:
            if word == name:
                score += 10
            elif word in name_words:
                score += 6
            elif word in name:
                score += 3
            elif any(word == t for t in tags.get(name, [])):
                score += 2
            elif any(word in t for t in tags.get(name, [])):
                score += 1
        if score:
            scored.append((score, name))
    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    for score, name in scored[: args.top]:
        print(f"{name:28s} {', '.join(tags.get(name, [])[:6])}")
    if not scored:
        print("no icon matches; try an English synonym (icons are named in English)")


def cmd_svg(args) -> None:
    nodes, _ = load()
    for name in args.names:
        markup = render(name, nodes, args.size, args.stroke, args.color, args.css_class)
        print(markup if len(args.names) == 1 else f"{name}: {markup}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Lucide icons for slides")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("search")
    p.add_argument("words", nargs="+")
    p.add_argument("--top", type=int, default=15)
    p.set_defaults(fn=cmd_search)
    p = sub.add_parser("svg")
    p.add_argument("names", nargs="+")
    p.add_argument("--size", type=int, default=48)
    p.add_argument("--stroke", type=float, default=2)
    p.add_argument("--color", default="currentColor")
    p.add_argument("--class", dest="css_class", default="icon")
    p.set_defaults(fn=cmd_svg)
    p = sub.add_parser("inline")
    p.add_argument("paths", nargs="+")
    p.set_defaults(fn=cmd_inline)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
