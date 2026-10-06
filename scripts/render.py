#!/usr/bin/env python3
"""Render deck slides to PNG and run the deterministic slide checks.

  render.py DECK [--slides s01,s03] [--scale 1] [--no-sheet]

Writes out/png/<id>.png, out/contact-sheet.jpg and out/render-report.json. Exit code 1 when any slide has an
error-level finding. Passing these checks proves geometry, not design: still look at every slide.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import canvas_size, find_deck, launch_browser, serve, slide_files  # noqa: E402

CHECK_JS = r"""
async ({cw, ch}) => {
  if (document.fonts && document.fonts.ready) { await document.fonts.ready; }
  await Promise.all([...document.images].map(img => img.complete ? null :
    new Promise(resolve => { img.onload = img.onerror = resolve; })));
  const issues = [];
  const add = (level, kind, msg) => issues.push({level, kind, msg});
  const canvas = document.querySelector('.slide-canvas') || document.querySelector('[data-canvas-width]');
  if (!canvas) { add('error', 'canvas', 'no .slide-canvas element'); return {issues, stacks: {}}; }
  const cb = canvas.getBoundingClientRect();
  if (Math.round(cb.width) !== cw || Math.round(cb.height) !== ch) {
    add('error', 'canvas', `canvas is ${Math.round(cb.width)}x${Math.round(cb.height)}, expected ${cw}x${ch}`);
  }
  const dw = canvas.getAttribute('data-canvas-width'), dh = canvas.getAttribute('data-canvas-height');
  if (dw && (+dw !== cw || +dh !== ch)) add('error', 'canvas', `data-canvas-* says ${dw}x${dh}, expected ${cw}x${ch}`);
  if (document.querySelectorAll('.slide-canvas').length > 1) add('error', 'canvas', 'more than one .slide-canvas in the file');

  const visible = el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const label = el => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (el.classList.length) s += '.' + [...el.classList].slice(0, 2).join('.');
    const t = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 28);
    return t ? `${s} "${t}"` : s;
  };
  const clipAncestor = el => {
    for (let a = el; a && a !== canvas; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (/(hidden|clip)/.test(cs.overflow + cs.overflowX + cs.overflowY)) return a;
    }
    return null;
  };

  const items = [];
  const seen = new Set();
  const walker = document.createTreeWalker(canvas, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (!node.textContent.trim()) continue;
    const el = node.parentElement;
    if (!el || !visible(el)) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const rects = [...range.getClientRects()].filter(r => r.width > 1 && r.height > 1);
    const fs = parseFloat(getComputedStyle(el).fontSize);
    for (const r of rects) items.push({el, r});
    if (!seen.has(el)) {
      seen.add(el);
      if (fs < 18) add('warn', 'small-text', `${fs}px text is hard to read on a projected slide: ${label(el)}`);
    }
  }

  const flagged = new Set();
  for (const {el, r} of items) {
    const x0 = r.left - cb.left, y0 = r.top - cb.top, x1 = r.right - cb.left, y1 = r.bottom - cb.top;
    const key = el;
    if (flagged.has(key)) continue;
    if (x0 < -1 || y0 < -1 || x1 > cw + 1 || y1 > ch + 1) {
      add('error', 'text-outside', `text crosses the canvas edge: ${label(el)}`); flagged.add(key); continue;
    }
    const clip = clipAncestor(el);
    if (clip) {
      const c = clip.getBoundingClientRect();
      if (r.left < c.left - 2 || r.top < c.top - 2 || r.right > c.right + 2 || r.bottom > c.bottom + 2) {
        add('error', 'clipped', `text is cut off by ${label(clip)}: ${label(el)}`); flagged.add(key); continue;
      }
    }
    if (x0 < 24 || y0 < 16 || x1 > cw - 24 || y1 > ch - 16) {
      add('warn', 'edge', `text sits within 24px of the slide edge: ${label(el)}`); flagged.add(key);
    }
  }

  const textEls = [...seen];
  const spilled = new Set();
  for (const {el, r} of items) {
    if (spilled.has(el) || flagged.has(el)) continue;
    const b = el.getBoundingClientRect();
    if (r.right > b.right + 3 || r.bottom > b.bottom + 3 || r.left < b.left - 3 || r.top < b.top - 3) {
      spilled.add(el);
      add('warn', 'overflow', `text spills outside its own box (the PowerPoint text box will differ): ${label(el)}`);
    }
  }

  const overlapPairs = new Set();
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i], b = items[j];
      if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const w = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
      const h = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
      if (w <= 2 || h <= 2) continue;
      const area = w * h, smaller = Math.min(a.r.width * a.r.height, b.r.width * b.r.height);
      if (area > 0.2 * smaller) {
        const pair = [label(a.el), label(b.el)].sort().join(' ⟷ ');
        if (!overlapPairs.has(pair)) { overlapPairs.add(pair); add('error', 'text-overlap', `text overlaps text: ${pair}`); }
      }
    }
  }

  for (const img of canvas.querySelectorAll('img')) {
    if (!img.complete || img.naturalWidth === 0) add('error', 'image', `image failed to load: ${img.getAttribute('src')}`);
  }

  const stacks = {};
  for (const el of textEls) {
    const stack = getComputedStyle(el).fontFamily;
    stacks[stack] = (stacks[stack] || 0) + 1;
  }
  return {issues, stacks};
}
"""


PROBE_JS = r"""
(fam) => {
  const generic = ['serif', 'sans-serif', 'monospace', 'cursive', 'fantasy', 'system-ui', '-apple-system',
    'blinkmacsystemfont', 'ui-sans-serif', 'ui-serif', 'ui-monospace', 'ui-rounded', 'emoji', 'math'];
  if (generic.includes(fam.toLowerCase())) return true;
  const ctx = document.createElement('canvas').getContext('2d');
  const sample = 'mmmmmmmmmlli WQ@ 永和中文排版あ';
  const w = f => { ctx.font = f; return ctx.measureText(sample).width; };
  return w(`72px "${fam}", monospace`) !== w('72px monospace') || w(`72px "${fam}", serif`) !== w('72px serif');
}
"""


def font_report(page, stacks: dict, cache: dict) -> tuple[list, list]:
    """Which family each CSS stack really renders with; probed one family per call (macOS-safe)."""
    fonts, issues = [], []
    for stack, count in stacks.items():
        families = [f.strip().strip("'\"") for f in stack.split(",") if f.strip()]
        used = "(browser default)"
        for family in families:
            if family not in cache:
                cache[family] = bool(page.evaluate(PROBE_JS, family))
            if cache[family]:
                used = family
                break
        fonts.append({"stack": stack, "used": used, "count": count})
        if families and used != families[0]:
            issues.append({"level": "info", "kind": "font-fallback",
                           "msg": f'"{families[0]}" is not installed here; {count} text element(s) render in "{used}"'})
    return fonts, issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Render and check deck slides")
    parser.add_argument("deck")
    parser.add_argument("--slides", help="comma-separated slide ids")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--no-sheet", action="store_true")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright

    deck = find_deck(Path(args.deck))
    cw, ch = canvas_size(deck)
    files = slide_files(deck, args.slides.split(",") if args.slides else None)
    if not files:
        print("no slides found (expected slides/*.html)")
        raise SystemExit(1)
    png_dir = deck / "out" / "png"
    png_dir.mkdir(parents=True, exist_ok=True)

    report, errors, font_cache = [], 0, {}
    with serve(deck) as base, sync_playwright() as pw:
        browser = launch_browser(pw)
        context = browser.new_context(viewport={"width": cw, "height": ch}, device_scale_factor=args.scale)
        for path in files:
            page = context.new_page()
            external, console = [], []
            page.on("request", lambda req, ext=external: ext.append(req.url)
                    if not (req.url.startswith(base) or req.url.startswith(("data:", "blob:", "about:"))) else None)
            failed = []
            page.on("response", lambda resp, bad=failed: bad.append(f"{resp.status} {resp.url}")
                    if resp.status >= 400 and not resp.url.endswith("/favicon.ico") else None)
            page.on("requestfailed", lambda req, bad=failed: bad.append(f"failed {req.url}")
                    if not req.url.endswith("/favicon.ico") else None)
            page.on("console", lambda msg, con=console: con.append(msg.text)
                    if msg.type == "error" and "Failed to load resource" not in msg.text else None)
            page.on("pageerror", lambda exc, con=console: con.append(str(exc)))
            rel = path.relative_to(deck).as_posix()
            page.goto(f"{base}/{rel}", wait_until="load", timeout=45000)
            result = page.evaluate(CHECK_JS, {"cw": cw, "ch": ch})
            issues = result["issues"]
            fonts, font_issues = font_report(page, result.get("stacks") or {}, font_cache)
            issues += font_issues
            for url in dict.fromkeys(external):
                issues.append({"level": "warn", "kind": "network", "msg": f"external request (will break offline): {url[:120]}"})
            for text in dict.fromkeys(failed):
                issues.append({"level": "error", "kind": "missing-file", "msg": f"could not load {text[:160]}"})
            for text in dict.fromkeys(console):
                issues.append({"level": "warn", "kind": "console", "msg": text[:200]})
            out = png_dir / f"{path.stem}.png"
            target = page.locator(".slide-canvas")
            if target.count() == 1:
                target.screenshot(path=str(out), animations="disabled")
            else:
                page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": cw, "height": ch})
            page.close()
            n_err = sum(1 for i in issues if i["level"] == "error")
            n_warn = sum(1 for i in issues if i["level"] == "warn")
            errors += n_err
            mark = "✗" if n_err else "✓"
            print(f"{mark} {path.stem}: {n_err} error(s), {n_warn} warning(s) → {out.relative_to(deck)}")
            for issue in issues:
                print(f"    {issue['level']:5s} {issue['kind']}: {issue['msg']}")
            report.append({"slide": path.stem, "png": str(out), "issues": issues, "fonts": fonts})
        browser.close()

    from imgtool import contact_sheet

    pngs = [png_dir / f"{p.stem}.png" for p in files]
    if not args.no_sheet and not args.slides:
        sheet = contact_sheet([str(p) for p in pngs], cols=3 if len(pngs) <= 9 else 4, width=640)
        sheet_path = deck / "out" / "contact-sheet.jpg"
        sheet.convert("RGB").save(sheet_path, quality=88)
        print(f"contact sheet → {sheet_path.relative_to(deck)}")
    report_path = deck / "out" / "render-report.json"
    if args.slides and report_path.is_file():
        try:
            old = {r["slide"]: r for r in json.loads(report_path.read_text(encoding="utf-8"))}
        except (ValueError, KeyError, TypeError):
            old = {}
        old.update({r["slide"]: r for r in report})
        report = [old[k] for k in sorted(old)]
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
