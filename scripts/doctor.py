#!/usr/bin/env python3
"""Check that ppt-studio can run here.

  doctor.py           runtime, browser, style library, icons, image backend
  doctor.py --fonts   also list which slide-worthy font families are installed, by role
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import LIBRARY_DIR, SKILL_DIR, launch_browser  # noqa: E402

FONT_ROLES = {
    "CJK sans (黑体)": ["PingFang SC", "Hiragino Sans GB", "Heiti SC", "STHeiti", "Microsoft YaHei",
                       "Noto Sans SC", "Noto Sans CJK SC", "Source Han Sans SC", "Source Han Sans CN"],
    "CJK serif (宋体/明朝)": ["Songti SC", "STSong", "SimSun", "Noto Serif SC", "Noto Serif CJK SC",
                           "Source Han Serif SC", "Hiragino Mincho ProN"],
    "CJK kai / brush (楷体)": ["Kaiti SC", "STKaiti", "KaiTi", "Baoli SC", "Xingkai SC", "Libian SC", "Weibei SC"],
    "CJK rounded (圆体)": ["Yuanti SC", "Hiragino Maru Gothic ProN", "Arial Rounded MT Bold"],
    "Japanese": ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Hiragino Mincho ProN", "Yu Mincho"],
    "Latin sans": ["Helvetica Neue", "Helvetica", "Avenir Next", "Avenir", "Arial", "Segoe UI", "Inter",
                   "Gill Sans", "Optima", "Verdana", "Trebuchet MS"],
    "Latin geometric": ["Futura", "Century Gothic", "Avenir Next", "Montserrat", "Poppins"],
    "Latin condensed / display": ["Avenir Next Condensed", "DIN Condensed", "DIN Alternate", "Impact",
                                  "Helvetica Neue Condensed Bold", "Arial Narrow", "Bebas Neue", "Oswald",
                                  "Futura Condensed ExtraBold", "Bahnschrift"],
    "Latin serif": ["Didot", "Bodoni 72", "Baskerville", "Georgia", "Times New Roman", "Hoefler Text",
                    "Big Caslon", "Palatino", "Charter", "Iowan Old Style", "Playfair Display"],
    "Mono / typewriter": ["SF Mono", "Menlo", "Monaco", "Courier New", "American Typewriter", "Consolas"],
    "Hand / playful": ["Chalkboard SE", "Marker Felt", "Comic Sans MS", "Noteworthy", "Bradley Hand",
                       "Snell Roundhand", "Party LET", "Hannotate SC", "HanziPen SC", "Wawati SC", "Yuppy SC"],
}

PROBE_JS = r"""
(fam) => {
  const ctx = document.createElement('canvas').getContext('2d');
  const sample = 'mmmmmmmmmlli WQ@ 永和中文排版あ';
  const w = f => { ctx.font = f; return ctx.measureText(sample).width; };
  return w(`72px "${fam}", monospace`) !== w('72px monospace') || w(`72px "${fam}", serif`) !== w('72px serif');
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="ppt-studio health check")
    parser.add_argument("--fonts", action="store_true")
    args = parser.parse_args()
    ok = True

    print(f"python   {sys.version.split()[0]} ({sys.executable})")
    for module in ("playwright", "pptx", "PIL", "numpy"):
        try:
            mod = __import__(module)
            print(f"  {module:10s} {getattr(mod, '__version__', 'ok')}")
        except ImportError:
            print(f"  {module:10s} MISSING  → bash scripts/setup.sh --force")
            ok = False

    styles = json.loads((LIBRARY_DIR / "styles.json").read_text(encoding="utf-8"))
    complete = sum(1 for s in styles if all(
        (LIBRARY_DIR / s["dir"] / name).is_file() for name in ("prompt.txt", "prompt.zh.txt")))
    print(f"library  {len(styles)} styles, {complete} complete text specifications")
    ok &= complete == len(styles)
    icons = SKILL_DIR / "assets" / "icons" / "lucide" / "icon-nodes.json"
    print(f"icons    {len(json.loads(icons.read_text()))} Lucide icons" if icons.is_file() else "icons    MISSING")

    available = {}
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = launch_browser(pw)
            print(f"browser  {browser.browser_type.name} {browser.version}")
            if args.fonts:
                page = browser.new_page()
                names = sorted({f for fams in FONT_ROLES.values() for f in fams})
                available = {name: page.evaluate(PROBE_JS, name) for name in names}
            browser.close()
    except Exception as exc:  # noqa: BLE001
        print(f"browser  FAILED: {exc}")
        ok = False

    import imagegen

    print("images")
    ok &= imagegen.cmd_check(None) == 0

    if args.fonts:
        print("fonts installed (usable in slides and kept as live text in PPTX)")
        for role, fams in FONT_ROLES.items():
            have = [f for f in fams if available.get(f)]
            print(f"  {role:28s} {', '.join(have) if have else '-'}")
    print("ready" if ok else "NOT READY")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
