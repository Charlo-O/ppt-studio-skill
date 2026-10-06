#!/usr/bin/env python3
"""Browse and apply the bundled slide-style library.

  styles.py categories
  styles.py list [--category Business] [--theme dark] [--imagery isometric]
  styles.py search <words...> [--top 8] [--theme light|dark] [--category X]
  styles.py show <ref> [--zh | --both] [--meta]
  styles.py use <ref> <deck_dir>                            (copies style into the deck)

<ref> is an id (1, 001), an English or Chinese style name, or a folder name; partial
names work when they are unambiguous.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import LIBRARY_DIR, die, load_deck, save_deck  # noqa: E402

DARK_WORDS = {"dark", "black", "night", "暗", "暗色", "深色", "黑", "黑色", "夜"}
LIGHT_WORDS = {"light", "white", "bright", "浅色", "白", "白色", "亮", "亮色", "明亮"}


def catalog() -> list[dict]:
    return json.loads((LIBRARY_DIR / "styles.json").read_text(encoding="utf-8"))


def style_dir(style: dict) -> Path:
    return LIBRARY_DIR / style["dir"]


def resolve(ref: str) -> dict:
    styles = catalog()
    text = str(ref).strip()
    if re.fullmatch(r"\d{1,3}", text):
        for s in styles:
            if s["id"] == int(text):
                return s
        die(f"no style with id {text}")
    low = text.lower().replace("_", " ")
    exact = [s for s in styles if low in {
        s["name"].lower(), s["name_zh"].lower(), Path(s["dir"]).name.lower().replace("_", " "),
        Path(s["dir"]).name.lower().replace("_", " ").split(" ", 1)[-1]}]
    if len(exact) == 1:
        return exact[0]
    partial = [s for s in styles if low in s["name"].lower() or low in s["name_zh"].lower()]
    if len(partial) == 1:
        return partial[0]
    if partial:
        options = ", ".join(f"{s['key']} {s['name']}" for s in partial[:12])
        die(f"'{ref}' matches several styles: {options}")
    die(f"no style matches '{ref}' (try: styles.py search {ref})")
    raise AssertionError


def row(s: dict) -> str:
    mood = ", ".join((s["mood"] or s["mood_zh"])[:3])
    tags = ",".join(s["imagery"][:4])
    return (f"{s['key']}  {s['name']} · {s['name_zh']}  [{s['category_en']}/{s['theme']}]"
            f"  mood: {mood}  imagery: {tags or '-'}")


def cmd_categories(_args) -> None:
    counts: dict[str, list] = {}
    for s in catalog():
        counts.setdefault(f"{s['category_en']} · {s['category']}", []).append(s["key"])
    for name, keys in counts.items():
        print(f"{name}: {len(keys)}  ({keys[0]}…)")


def _filter(styles, args):
    if getattr(args, "category", None):
        want = args.category.lower()
        styles = [s for s in styles if want in s["category_en"].lower() or want in s["category"]]
    if getattr(args, "theme", None):
        styles = [s for s in styles if s["theme"] == args.theme]
    if getattr(args, "imagery", None):
        styles = [s for s in styles if args.imagery in s["imagery"]]
    return styles


def cmd_list(args) -> None:
    for s in _filter(catalog(), args):
        print(row(s))


def cmd_search(args) -> None:
    tokens = [t for t in re.split(r"[\s,，、/]+", " ".join(args.words).lower()) if t]
    if not tokens:
        die("give at least one search word")
    results = []
    for s in _filter(catalog(), args):
        folder = style_dir(s)
        prompt = (folder / "prompt.txt").read_text(encoding="utf-8").lower()
        prompt_zh = (folder / "prompt.zh.txt").read_text(encoding="utf-8").lower()
        fields = [
            (6, f"{s['name']} {s['name_zh']} {Path(s['dir']).name}".lower()),
            (4, " ".join(s["mood"] + s["mood_zh"]).lower()),
            (3, f"{s['category']} {s['category_en']} {' '.join(s['imagery'])}".lower()),
            (2, f"{s['concept']} {s['concept_zh']}".lower()),
            (1, prompt + "\n" + prompt_zh),
        ]
        score, hits = 0.0, []
        for token in tokens:
            best = 0
            for weight, field in fields:
                if token in field:
                    best = max(best, weight)
            if token in DARK_WORDS and s["theme"] == "dark":
                best = max(best, 4)
            if token in LIGHT_WORDS and s["theme"] == "light":
                best = max(best, 2)
            if best:
                hits.append(token)
            score += best
        if score:
            coverage = len(set(hits)) / len(set(tokens))
            results.append((score * (0.5 + coverage), s, hits))
    results.sort(key=lambda item: (-item[0], item[1]["id"]))
    if not results:
        print("no matches; try broader words or `styles.py list --category ...`")
        return
    for score, s, hits in results[: args.top]:
        print(f"{row(s)}\n      matched: {', '.join(dict.fromkeys(hits))}  score {score:.1f}")


def cmd_show(args) -> None:
    s = resolve(args.ref)
    folder = style_dir(s)
    print(f"# {s['key']} {s['name']} · {s['name_zh']}")
    print(f"category: {s['category_en']} · {s['category']}   theme: {s['theme']} (background {s['background']})")
    print(f"palette: {' '.join(s['palette'])}")
    print(f"mood: {', '.join(s['mood'])} | {', '.join(s['mood_zh'])}")
    print(f"imagery: {', '.join(s['imagery']) or '-'}")
    if s["slide_types"]:
        print(f"slide types: {', '.join(s['slide_types'])}")
    print(f"prompt: {folder / 'prompt.txt'}")
    print(f"prompt (zh): {folder / 'prompt.zh.txt'}")
    if args.meta:
        return
    print()
    if args.zh:
        print((folder / "prompt.zh.txt").read_text(encoding="utf-8"))
    elif args.both:
        print((folder / "prompt.txt").read_text(encoding="utf-8"))
        print("\n----- 中文 -----\n")
        print((folder / "prompt.zh.txt").read_text(encoding="utf-8"))
    else:
        print((folder / "prompt.txt").read_text(encoding="utf-8"))


def cmd_use(args) -> None:
    s = resolve(args.ref)
    deck = Path(args.deck).resolve()
    if not (deck / "deck.json").is_file():
        die(f"{deck} is not a deck (no deck.json); create it with init_deck.py first")
    dest = deck / "style"
    dest.mkdir(parents=True, exist_ok=True)
    folder = style_dir(s)
    for name in ("prompt.txt", "prompt.zh.txt"):
        shutil.copy2(folder / name, dest / name)
    data = load_deck(deck)
    data["style"] = {k: s[k] for k in ("id", "key", "name", "name_zh", "category", "category_en",
                                       "theme", "background", "palette", "imagery")}
    data["style"]["library_dir"] = s["dir"]
    save_deck(deck, data)
    print(f"style {s['key']} {s['name']} · {s['name_zh']} copied into {dest}")
    print(f"read both full style prompts: {dest / 'prompt.txt'} and {dest / 'prompt.zh.txt'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Browse and apply the slide-style library")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("categories").set_defaults(fn=cmd_categories)
    p = sub.add_parser("list")
    p.add_argument("--category")
    p.add_argument("--theme", choices=["light", "dark"])
    p.add_argument("--imagery")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("search")
    p.add_argument("words", nargs="+")
    p.add_argument("--top", type=int, default=8)
    p.add_argument("--category")
    p.add_argument("--theme", choices=["light", "dark"])
    p.add_argument("--imagery")
    p.set_defaults(fn=cmd_search)
    p = sub.add_parser("show")
    p.add_argument("ref")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--zh", action="store_true", help="print the Chinese translation instead")
    group.add_argument("--both", action="store_true", help="print original and Chinese")
    group.add_argument("--meta", action="store_true", help="metadata and paths only")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("use")
    p.add_argument("ref")
    p.add_argument("deck")
    p.set_defaults(fn=cmd_use)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
