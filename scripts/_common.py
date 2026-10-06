"""Shared helpers for ppt-studio scripts: paths, deck loading, local serving, browser launch."""

from __future__ import annotations

import json
import os
import sys
import threading
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
LIBRARY_DIR = SKILL_DIR / "library"
STARTER_DIR = SKILL_DIR / "assets" / "deck-starter"


def die(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def find_deck(start: Path) -> Path:
    """Return the deck root (the nearest directory holding deck.json)."""
    path = Path(start).resolve()
    if path.is_file():
        path = path.parent
    for candidate in [path, *path.parents]:
        if (candidate / "deck.json").is_file():
            return candidate
    die(f"no deck.json found at or above {start}")
    raise AssertionError


def load_deck(deck: Path) -> dict:
    return json.loads((deck / "deck.json").read_text(encoding="utf-8"))


def save_deck(deck: Path, data: dict) -> None:
    (deck / "deck.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def slide_files(deck: Path, only: Optional[List[str]] = None) -> List[Path]:
    """Slides in deck order: deck.json `slides[].file` when present, else slides/*.html sorted."""
    data = load_deck(deck)
    files: List[Path] = []
    for entry in data.get("slides") or []:
        rel = entry.get("file") or f"slides/{entry.get('id')}.html"
        path = deck / rel
        if path.is_file():
            files.append(path)
    if not files:
        files = sorted(p for p in (deck / "slides").glob("*.html") if not p.name.startswith("_"))
    if only:
        wanted = {name.strip() for name in only if name.strip()}
        files = [p for p in files if p.stem in wanted or p.name in wanted]
    return files


def canvas_size(deck: Path) -> tuple[int, int]:
    canvas = load_deck(deck).get("canvas") or {}
    return int(canvas.get("width", 1920)), int(canvas.get("height", 1080))


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format, *args):  # noqa: A003
        del args


@contextmanager
def serve(root: Path) -> Iterator[str]:
    """Serve `root` on a random loopback port so fonts and relative assets load like a real site."""
    handler = partial(_QuietHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def _browser_args() -> List[str]:
    return ["--no-sandbox"] if os.environ.get("PPT_STUDIO_NO_SANDBOX") == "1" else []


def launch_browser(playwright):
    """Launch Chromium: explicit path, then Playwright's own build, then installed Chrome or Edge."""
    errors = []
    explicit = os.environ.get("PPT_STUDIO_BROWSER")
    attempts = []
    if explicit:
        attempts.append(("path", explicit))
    attempts += [("bundled", None), ("channel", "chrome"), ("channel", "msedge")]
    for kind, value in attempts:
        try:
            if kind == "path":
                return playwright.chromium.launch(executable_path=value, args=_browser_args())
            if kind == "bundled":
                return playwright.chromium.launch(args=_browser_args())
            return playwright.chromium.launch(channel=value, args=_browser_args())
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{kind}={value}: {str(exc).splitlines()[0]}")
    raise RuntimeError("no usable Chromium browser:\n  " + "\n  ".join(errors))


def _browser_check() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = launch_browser(pw)
        print(f"browser ok: {browser.browser_type.name} {browser.version}")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "browser-check":
        _browser_check()
    else:
        print("usage: _common.py browser-check")
