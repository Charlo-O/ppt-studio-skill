#!/usr/bin/env python3
"""Rebuild ppt-studio/library from the NotebookLM slide-style collection.

Usage:
    .venv/bin/python tools/build_library.py /path/to/notebooklm-slide-gallery-中文资料库

Reads 资料索引.json from the collection, then writes:
    library/styles.json                    machine-readable catalog
    library/INDEX.md                       human-readable catalog by category
    library/SOURCE.md                      provenance and credits
    library/styles/NNN_Slug/prompt.txt     original style prompt (YAML-like)
    library/styles/NNN_Slug/prompt.zh.txt  Chinese translation
    library/styles/NNN_Slug/board.jpg      3x3 example board (style anchor)
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

SKILL_DIR = Path(__file__).resolve().parents[1]
OUT = SKILL_DIR / "library"

CATEGORY_EN = {
    "商务": "Business",
    "杂志排版": "Editorial",
    "界面与现代": "UI & Modern",
    "极简与单色": "Minimal & Mono",
    "流行与多彩": "Pop & Color",
    "艺术与创意": "Art & Creative",
    "品牌": "Brand",
    "等距视图": "Isometric",
    "信息图表": "Infographic",
    "复古与趣味": "Retro & Fun",
    "角色": "Character",
    "摄影与立体": "Photo & 3D",
}

IMAGERY_KEYWORDS = {
    "photo": [r"\bphoto", r"写真", r"cinematic"],
    "illustration": [r"illustrat", r"イラスト"],
    "isometric": [r"isometric", r"アイソメ"],
    "3d": [r"\b3d\b", r"\brender", r"\bclay\b", r"miniature", r"ミニチュア", r"立体"],
    "character": [r"character", r"mascot", r"キャラクター", r"マスコット"],
    "collage": [r"collage", r"コラージュ", r"cut-?out"],
    "watercolor": [r"watercolou?r", r"水彩"],
    "hand-drawn": [r"doodle", r"hand[- ]drawn", r"手描き", r"\bsketch", r"crayon"],
    "texture": [r"texture", r"\bgrain", r"risograph", r"テクスチャ"],
    "glass": [r"glass", r"ガラス"],
    "neon": [r"\bneon", r"ネオン"],
    "icons": [r"\bicons?\b", r"アイコン"],
    "ui": [r"\bui\b", r"\bwindows?\b", r"neumorph", r"interface"],
}
NEGATIVE_HEADER = re.compile(
    r"(?i)^(avoid|restrictions?|don'?t|do not|prohibited|forbidden|never|ng|negative|bad|"
    r"禁止|避ける|ng例)\b")
NEGATION = re.compile(r"(?i)(\bno\b|\bnot\b|\bavoid|\bwithout\b|\bnever\b|禁止|しない|避け|なし|ng\b)")
HEADER = re.compile(r"^\s*[#]?\s*[A-Za-z\u3040-\u30ff\u4e00-\u9fff][^:：\n]{0,40}[:：]\s*(>|\|)?\s*$")


def luminance(hex_code: str) -> float:
    r, g, b = (int(hex_code[i : i + 2], 16) / 255 for i in (1, 3, 5))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def list_after(text: str, header_regex: str) -> list[str]:
    """Collect `- "item"` / `* item` lines directly following the first header that matches."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(header_regex, line.strip()):
            items = []
            for follow in lines[index + 1 :]:
                stripped = follow.strip()
                if stripped.startswith(("- ", "* ")):
                    items.append(stripped[2:].strip().strip('"').strip())
                elif stripped == "":
                    if items:
                        break
                else:
                    break
            if items:
                return items
    return []


def first_value(text: str, key_regex: str) -> str:
    """Value of the first `Key: value` line; follows YAML block scalars (`Key: >`)."""
    match = re.search(rf"(?im)^\s*(?:#\s*)?{key_regex}\s*[:：]\s*(.*)$", text)
    if not match:
        return ""
    value = match.group(1).strip()
    if value not in {">", "|", ">-", "|-", ""}:
        return value.strip('"').strip()
    parts = []
    for line in text[match.end():].splitlines()[1:]:
        if not line.strip():
            if parts:
                parts.append(" ")
            continue
        if HEADER.match(line) or re.match(r"^\s*[A-Za-z][\w /&()-]*\s*:", line):
            break
        parts.append(line.strip())
    joined = "".join(parts).strip()
    return re.sub(r"\s+", " ", joined)


def background_hex(text: str, palette: list[str]) -> str:
    match = re.search(r"(?is)Background:\s*(?:\n[^\n#]*?)*?(#[0-9A-Fa-f]{6})", text)
    if match:
        return match.group(1).upper()
    return palette[0] if palette else "#FFFFFF"


def slide_types(text: str) -> list[str]:
    match = re.search(r"(?im)^\s*Slide Types\s*:\s*$", text)
    if not match:
        return []
    names = []
    for line in text[match.end() :].splitlines():
        if not line.strip():
            continue
        if re.match(r"^[A-Z][A-Za-z /&()-]*:\s*$", line) and not line.startswith(" "):
            name = line.strip().rstrip(":")
            if name in {"Components", "Spacing", "Animation Feel", "Restrictions", "Rules", "Avoid"}:
                break
            if name not in {"Layout", "Elements", "Style"}:
                names.append(name)
        if len(names) > 14:
            break
    return names


def positive_lines(text: str) -> list[str]:
    """Lines that describe what the style uses: skip Avoid/Restrictions blocks and negated lines."""
    keep, negative = [], False
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if HEADER.match(line):
            negative = bool(NEGATIVE_HEADER.match(stripped))
            continue
        if negative or NEGATION.search(stripped):
            continue
        keep.append(stripped.lower())
    return keep


def imagery_tags(text: str) -> list[str]:
    lines = positive_lines(text)
    tags = []
    for tag, patterns in IMAGERY_KEYWORDS.items():
        hits = sum(1 for line in lines for p in patterns if re.search(p, line))
        if hits >= (2 if tag in {"texture", "icons", "3d", "glass", "ui"} else 1):
            tags.append(tag)
    return tags


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    src = Path(sys.argv[1]).resolve()
    index = json.loads((src / "资料索引.json").read_text(encoding="utf-8"))

    styles_dir = OUT / "styles"
    if styles_dir.exists():
        shutil.rmtree(styles_dir)
    styles_dir.mkdir(parents=True)

    catalog = []
    for item in index:
        n = int(item["n"])
        folder = Path(item["image"]).parent.name
        slug = folder.split("_", 1)[1] if "_" in folder else folder
        rel = Path("styles") / f"{n:03d}_{slug}"
        dest = OUT / rel
        dest.mkdir(parents=True)

        original = item["prompt_original"].strip() + "\n"
        chinese = item["prompt_zh"].strip() + "\n"
        (dest / "prompt.txt").write_text(original, encoding="utf-8")
        (dest / "prompt.zh.txt").write_text(chinese, encoding="utf-8")

        board = Image.open(src / item["image"]).convert("RGB")
        board.save(dest / "board.jpg", "JPEG", quality=88, optimize=True, progressive=True)

        palette = []
        for code in re.findall(r"#[0-9A-Fa-f]{6}\b", original):
            code = code.upper()
            if code not in palette:
                palette.append(code)
        bg = background_hex(original, palette)
        mood = list_after(original, r"^(Mood|Tone|Keywords)\s*:$")
        mood_zh = list_after(chinese, r"^(氛围|基调|调性|语气|情绪|关键词)\s*[:：]$")
        category = item["category"]
        catalog.append({
            "id": n,
            "key": f"{n:03d}",
            "name": item["title"],
            "name_zh": item["title_zh"],
            "category": category,
            "category_en": CATEGORY_EN.get(category, category),
            "concept": first_value(original, "Concept"),
            "concept_zh": first_value(chinese, "设计理念"),
            "mood": mood[:8],
            "mood_zh": mood_zh[:8],
            "theme": "dark" if luminance(bg) < 0.3 else "light",
            "background": bg,
            "palette": palette[:12],
            "imagery": imagery_tags(original),
            "slide_types": slide_types(original),
            "dir": rel.as_posix(),
            "source": {"note": item.get("note", ""), "x": item.get("x", ""), "image": item.get("source_image", "")},
        })

    catalog.sort(key=lambda s: s["id"])
    (OUT / "styles.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    order = list(CATEGORY_EN)
    lines = [
        "# Style library index",
        "",
        f"{len(catalog)} slide styles in {len(order)} categories. Each style folder holds `prompt.txt` "
        "(original design spec), `prompt.zh.txt` (Chinese translation) and `board.jpg` (3x3 example board).",
        "Search with `scripts/ppt styles search <words>`; open one with `scripts/ppt styles show <id>`.",
        "",
    ]
    for category in order:
        rows = [s for s in catalog if s["category"] == category]
        if not rows:
            continue
        lines += [f"## {CATEGORY_EN[category]} · {category} ({len(rows)})", "",
                  "| ID | Style | 中文名 | Theme | Mood | Palette | Imagery |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for s in rows:
            mood = ", ".join(s["mood"][:4])
            palette = " ".join(s["palette"][:5])
            imagery = ", ".join(s["imagery"][:5])
            lines.append(f"| {s['key']} | {s['name']} | {s['name_zh']} | {s['theme']} | {mood} | {palette} | {imagery} |")
        lines.append("")
    (OUT / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    readme = (src / "README.md").read_text(encoding="utf-8") if (src / "README.md").is_file() else ""
    source_line = next((l for l in readme.splitlines() if l.startswith("来源")), "")
    curator_line = next((l for l in readme.splitlines() if "整理者" in l), "")
    (OUT / "SOURCE.md").write_text(
        "# Provenance\n\n"
        "The style prompts and example boards come from the NotebookLM Slide Style Gallery "
        "curated by KUMIKO SHIRAKI (https://notebooklm-slide-gallery.shirakippt.chatgpt.site/). "
        "Per-style source links (note article, X post, original image) are kept in `styles.json`.\n\n"
        "The Chinese translations were machine-translated with revised category, style-name and "
        "design-term wording by the collection's compiler. Example boards were re-encoded from PNG "
        "to JPEG for size; their content is unchanged.\n\n"
        "The prompts and images remain the work of their original author. This library is bundled "
        "for local, personal use with the ppt-studio skill; credit the original author when sharing "
        "decks that closely follow a library style, and do not redistribute the library itself.\n\n"
        f"Collection notes: {source_line} {curator_line}\n",
        encoding="utf-8",
    )
    print(f"wrote {len(catalog)} styles to {OUT}")


if __name__ == "__main__":
    main()
