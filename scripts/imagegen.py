#!/usr/bin/env python3
"""Generate images for a deck through whichever image backend this machine has.

  imagegen.py check
  imagegen.py gen --prompt-file FILE[#section] --out OUT.png [--ref IMG ...]
                  [--aspect 16:9] [--transparent] [--kind asset] [--backend auto]
  imagegen.py batch JOBS.json [--concurrency 4] [--force] [--backend auto] [--dry-run]

Backends, in `auto` order:
  codex   the built-in image_gen tool of the Codex CLI, driven headlessly through
          `codex exec` with the user's ChatGPT login (no API key needed)
  openai  OpenAI Images API (OPENAI_API_KEY; model PPT_STUDIO_OPENAI_MODEL, default gpt-image-2)
  gemini  Gemini image models (GEMINI_API_KEY or GOOGLE_API_KEY; model PPT_STUDIO_GEMINI_MODEL,
          default gemini-3-pro-image-preview)

A jobs file looks like:
  {"defaults": {"aspect": "16:9", "kind": "asset"},
   "jobs": [{"id": "hero", "prompt_file": "prompts.md#hero",
             "out": "assets/hero.png", "transparent": true}]}
Optional refs are source assets for subject identity or image editing, not slide layouts.
Relative paths resolve against the deck root (the folder holding deck.json) or, outside a deck,
against the jobs file's folder. Existing outputs are skipped unless --force, so re-running a batch
retries only what failed. Results are written next to the jobs file as *.results.json.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

ASPECTS = {
    "16:9": ("16:9 widescreen landscape, clearly wider than tall", "2048x1152"),
    "9:16": ("9:16 tall portrait, clearly taller than wide", "1152x2048"),
    "1:1": ("1:1 square, equal width and height", "1536x1536"),
    "4:3": ("4:3 landscape, wider than tall", "1536x1152"),
    "3:4": ("3:4 portrait, taller than wide", "1152x1536"),
    "3:2": ("3:2 landscape, wider than tall", "1536x1024"),
    "2:3": ("2:3 portrait, taller than wide", "1024x1536"),
    "4:5": ("4:5 portrait, slightly taller than wide", "1024x1280"),
    "5:4": ("5:4 landscape, slightly wider than tall", "1280x1024"),
    "21:9": ("21:9 ultra-wide panorama", "2016x864"),
}
LEGACY_OPENAI_SIZES = {"landscape": "1536x1024", "portrait": "1024x1536", "square": "1024x1024"}

OCCUPANT_PHRASES = re.compile(
    r"(?i)(for (the )?(headline|title|text|copy|logo|caption|price)|space for|room for|copy ?space|"
    r"text area|placeholder|leave (clean |empty )?(negative )?space for)")
REFUSAL_WORDS = re.compile(r"(?i)(can'?t|cannot|unable|not able|policy|not allowed|won'?t|refus)")

DEFAULT_TIMEOUT = int(os.environ.get("PPT_STUDIO_TIMEOUT", "900"))
DEFAULT_CONCURRENCY = int(os.environ.get("PPT_STUDIO_CONCURRENCY", "4"))
_print_lock = threading.Lock()


class GenError(Exception):
    def __init__(self, message: str, kind: str = "transient"):
        super().__init__(message)
        self.kind = kind


def say(message: str) -> None:
    with _print_lock:
        print(message, flush=True)


def find_deck_root(start: Path) -> Optional[Path]:
    for candidate in [start, *start.parents]:
        if (candidate / "deck.json").is_file():
            return candidate
    return None


def load_prompt(spec: str, base: Path) -> str:
    """Read a prompt file; `file.md#name` selects the `## name` section of a multi-prompt file."""
    path_part, _, section = spec.partition("#")
    path = (base / path_part).resolve() if not Path(path_part).is_absolute() else Path(path_part)
    if not path.is_file():
        raise GenError(f"prompt file not found: {path}", "config")
    text = path.read_text(encoding="utf-8")
    if section:
        lines = text.splitlines()
        start = None
        for index, line in enumerate(lines):
            if re.match(r"^##\s+", line) and line[2:].strip().strip("`").lower() == section.strip().lower():
                start = index + 1
                break
        if start is None:
            raise GenError(f"no '## {section}' heading in {path}", "config")
        end = next((i for i in range(start, len(lines)) if re.match(r"^#{1,2}\s+", lines[i])), len(lines))
        text = "\n".join(lines[start:end])
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()
    if not text:
        raise GenError(f"empty prompt: {spec}", "config")
    return text


def image_info(path: Path) -> dict:
    """Width, height and alpha for PNG/JPEG/WebP without needing Pillow."""
    data = path.read_bytes()[:4096]
    info = {"width": 0, "height": 0, "alpha": False, "format": "unknown"}
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", data[16:24])
        color_type = data[25]
        info.update(format="png", width=width, height=height,
                    alpha=color_type in (4, 6) or b"tRNS" in path.read_bytes())
    elif data[:2] == b"\xff\xd8":
        info["format"] = "jpeg"
        blob = path.read_bytes()
        i = 2
        while i < len(blob) - 9:
            if blob[i] != 0xFF:
                i += 1
                continue
            marker = blob[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", blob[i + 5:i + 9])
                info.update(width=width, height=height)
                break
            i += 2 + struct.unpack(">H", blob[i + 2:i + 4])[0]
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        info["format"] = "webp"
        try:
            from PIL import Image

            with Image.open(path) as im:
                info.update(width=im.width, height=im.height, alpha="A" in im.getbands())
        except Exception:  # noqa: BLE001
            pass
    return info


def write_image_bytes(blob: bytes, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    is_png = blob[:8] == b"\x89PNG\r\n\x1a\n"
    if out.suffix.lower() == ".png" and not is_png:
        try:
            from io import BytesIO

            from PIL import Image

            Image.open(BytesIO(blob)).save(out)
            return
        except Exception:  # noqa: BLE001
            pass
    out.write_bytes(blob)


# ----------------------------------------------------------------------------- codex backend

_codex_cache: dict = {}


def find_codex() -> Optional[str]:
    if "path" in _codex_cache:
        return _codex_cache["path"]
    candidates = [
        os.environ.get("PPT_STUDIO_CODEX"),
        "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex",
        "/Applications/Codex.app/Contents/Resources/codex-cli/bin/codex",
        "/Applications/Codex.app/Contents/Resources/codex",
        shutil.which("codex"),
        str(Path.home() / ".local/bin/codex"),
        "/opt/homebrew/bin/codex",
        "/usr/local/bin/codex",
    ]
    found = None
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        try:
            probe = subprocess.run([candidate, "--version"], capture_output=True, text=True, timeout=30)
        except Exception:  # noqa: BLE001
            continue
        if probe.returncode == 0 and "codex" in (probe.stdout + probe.stderr).lower():
            found = candidate
            break
    _codex_cache["path"] = found
    return found


def relay_prompt(prompt: str, n_refs: int, aspect: str, transparent: bool) -> str:
    lines = [
        "You are an image-generation relay inside an automated pipeline.",
        "Call the built-in image generation tool exactly once. Use the IMAGE PROMPT below verbatim "
        "as the prompt: do not shorten, translate, summarize or embellish it.",
    ]
    if n_refs:
        lines.append(
            f"The {n_refs} attached image(s) are reference inputs, numbered Image 1 to Image {n_refs} "
            "in attachment order. Pass all of them to the image generation tool as reference images; "
            "the IMAGE PROMPT explains how each one is used.")
    lines.append(f"Output shape: {ASPECTS.get(aspect, (aspect,))[0]}; pick the tool's size setting that "
                 "matches this shape.")
    if transparent:
        lines.append("Ask the tool for a genuinely transparent background (PNG with a real alpha "
                     "channel), never a drawn checkerboard.")
    lines += [
        "Do not run shell commands, do not read or write files, and do not ask questions. "
        "After the tool returns, reply with the single word DONE.",
        "",
        "IMAGE PROMPT:",
        "<<<",
        prompt,
        ">>>",
    ]
    return "\n".join(lines)


def gen_codex(prompt: str, refs: list[Path], aspect: str, transparent: bool, out: Path,
              timeout: int, dry_run: bool = False) -> dict:
    codex = find_codex()
    if not codex:
        raise GenError("Codex CLI not found (set PPT_STUDIO_CODEX to its path)", "config")
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    with tempfile.TemporaryDirectory(prefix="ppt-imagegen-") as work:
        cmd = [codex, "exec", "--json", "--skip-git-repo-check", "--ephemeral",
               "-s", "read-only", "-c", 'model_reasoning_effort="low"', "-C", work]
        if os.environ.get("PPT_STUDIO_CODEX_USER_CONFIG") != "1":
            cmd.append("--ignore-user-config")
        for ref in refs:
            cmd += ["-i", str(ref)]
        cmd += shlex.split(os.environ.get("PPT_STUDIO_CODEX_ARGS", ""))
        relay = relay_prompt(prompt, len(refs), aspect, transparent)
        if dry_run:
            return {"dry_run": True, "command": " ".join(shlex.quote(c) for c in cmd), "stdin": relay}
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, cwd=work, start_new_session=True)
        try:
            stdout, stderr = proc.communicate(relay, timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            proc.communicate()
            raise GenError(f"codex timed out after {timeout}s")

    thread_id, messages, errors = None, [], []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.get("type")
        if kind == "thread.started":
            thread_id = event.get("thread_id")
        elif kind == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message":
                messages.append(item.get("text", ""))
            elif item.get("type") == "error":
                text = item.get("message", "")
                if "unrecognized configuration" not in text and "is ignored" not in text:
                    errors.append(text)
        elif kind in ("turn.failed", "error"):
            errors.append(json.dumps(event, ensure_ascii=False)[:600])

    produced = []
    if thread_id:
        folder = home / "generated_images" / thread_id
        produced = sorted((p for p in folder.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}),
                          key=lambda p: p.stat().st_mtime)
    if not produced:
        detail = " | ".join(m.strip() for m in messages if m.strip())[-600:]
        tail = "\n".join(l for l in stderr.splitlines() if "Reading prompt" not in l)[-600:]
        problem = "; ".join(errors)[-600:]
        kind = "refused" if REFUSAL_WORDS.search(detail) and "DONE" not in detail else "transient"
        if proc.returncode not in (0, None) and not detail:
            kind = "transient"
        raise GenError(f"codex produced no image (exit {proc.returncode}). agent: {detail or '-'} "
                       f"errors: {problem or '-'} stderr: {tail or '-'}", kind)
    chosen = produced[-1]
    write_image_bytes(chosen.read_bytes(), out)
    if os.environ.get("PPT_STUDIO_CODEX_CLEANUP") == "1":
        shutil.rmtree(chosen.parent, ignore_errors=True)
    result = {"thread_id": thread_id, "source": str(chosen)}
    if len(produced) > 1:
        result["note"] = f"codex returned {len(produced)} images; kept the newest"
    return result


# ----------------------------------------------------------------------------- HTTP backends

def _http_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers})
    return _send(request, timeout)


def _send(request: urllib.request.Request, timeout: int) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "replace")[:800]
        kind = "refused" if exc.code == 400 and re.search(r"(?i)safety|policy|moderation", text) else (
            "config" if exc.code in (401, 403, 404) else "transient")
        raise GenError(f"HTTP {exc.code}: {text}", kind)
    except urllib.error.URLError as exc:
        raise GenError(f"network error: {exc.reason}")


def gen_openai(prompt: str, refs: list[Path], aspect: str, transparent: bool, out: Path,
               timeout: int, dry_run: bool = False) -> dict:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise GenError("OPENAI_API_KEY is not set", "config")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("PPT_STUDIO_OPENAI_MODEL", "gpt-image-2")
    size = ASPECTS.get(aspect, ("", "auto"))[1]
    if model.startswith("gpt-image-1"):
        w, h = (int(x) for x in size.split("x"))
        size = LEGACY_OPENAI_SIZES["landscape" if w > h else "portrait" if h > w else "square"]
    fields = {"model": model, "prompt": prompt, "size": size, "n": "1",
              "quality": os.environ.get("PPT_STUDIO_OPENAI_QUALITY", "high")}
    if transparent:
        fields["background"] = "transparent"
    if dry_run:
        return {"dry_run": True, "endpoint": f"{base}/images/{'edits' if refs else 'generations'}",
                "fields": {k: v for k, v in fields.items() if k != "prompt"}, "refs": [str(r) for r in refs]}
    headers = {"Authorization": f"Bearer {key}"}
    if refs:
        boundary = uuid.uuid4().hex
        chunks = []
        for name, value in fields.items():
            chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
        for ref in refs:
            mime = mimetypes.guess_type(ref.name)[0] or "image/png"
            chunks.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"image[]\"; "
                           f"filename=\"{ref.name}\"\r\nContent-Type: {mime}\r\n\r\n").encode())
            chunks.append(ref.read_bytes() + b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode())
        request = urllib.request.Request(f"{base}/images/edits", data=b"".join(chunks), headers={
            **headers, "Content-Type": f"multipart/form-data; boundary={boundary}"})
        data = _send(request, timeout)
    else:
        payload = dict(fields, n=1)
        data = _http_json(f"{base}/images/generations", payload, headers, timeout)
    try:
        blob = base64.b64decode(data["data"][0]["b64_json"])
    except (KeyError, IndexError, TypeError):
        raise GenError(f"unexpected OpenAI response: {json.dumps(data)[:400]}")
    write_image_bytes(blob, out)
    return {"model": model, "size": size}


def gen_gemini(prompt: str, refs: list[Path], aspect: str, transparent: bool, out: Path,
               timeout: int, dry_run: bool = False) -> dict:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise GenError("GEMINI_API_KEY / GOOGLE_API_KEY is not set", "config")
    model = os.environ.get("PPT_STUDIO_GEMINI_MODEL", "gemini-3-pro-image-preview")
    if transparent:
        prompt += ("\n\nIsolate the subject on a perfectly flat, uniform pure green (#00FF00) background "
                   "with no shadow, gradient or texture, so it can be keyed out cleanly.")
    parts = [{"text": prompt}]
    for ref in refs:
        mime = mimetypes.guess_type(ref.name)[0] or "image/png"
        parts.append({"inlineData": {"mimeType": mime, "data": base64.b64encode(ref.read_bytes()).decode()}})
    image_config = {"aspectRatio": aspect if aspect in ASPECTS else "16:9"}
    if "pro-image" in model:
        image_config["imageSize"] = os.environ.get("PPT_STUDIO_GEMINI_SIZE", "2K")
    payload = {"contents": [{"role": "user", "parts": parts}],
               "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": image_config}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    if dry_run:
        return {"dry_run": True, "endpoint": url, "imageConfig": image_config, "refs": [str(r) for r in refs]}
    data = _http_json(url, payload, {"x-goog-api-key": key}, timeout)
    blob = None
    for candidate in data.get("candidates") or []:
        for part in (candidate.get("content") or {}).get("parts") or []:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                blob = base64.b64decode(inline["data"])
    if blob is None:
        reason = json.dumps(data.get("promptFeedback") or data.get("candidates") or data)[:500]
        raise GenError(f"Gemini returned no image: {reason}", "refused" if "SAFETY" in reason else "transient")
    write_image_bytes(blob, out)
    result = {"model": model}
    if transparent:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from imgtool import key_out  # noqa: E402

            key_out(out, out, "#00FF00")
            result["note"] = "keyed out the green background locally"
        except Exception as exc:  # noqa: BLE001
            result["note"] = f"green background left in place ({exc})"
    return result


BACKENDS = {"codex": gen_codex, "openai": gen_openai, "gemini": gen_gemini}


def pick_backend(name: str) -> str:
    if name != "auto":
        return name
    forced = os.environ.get("PPT_STUDIO_IMAGE_BACKEND")
    if forced:
        return forced
    if find_codex():
        return "codex"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    raise GenError("no image backend: install/log in to the Codex CLI, or set OPENAI_API_KEY or "
                   "GEMINI_API_KEY", "config")


# ----------------------------------------------------------------------------- jobs

def lint(job: dict, prompt: str) -> list[str]:
    warnings = []
    if job.get("kind", "asset") == "asset":
        if OCCUPANT_PHRASES.search(prompt):
            warnings.append("asset prompt names what will occupy a region (e.g. 'space for the title'); "
                            "describe the region's appearance instead")
        quoted = re.findall(r"[\"“「『]([^\"”」』]{2,40})[\"”」』]", prompt)
        if quoted:
            warnings.append(f"asset prompt quotes text ({quoted[:3]}); shipping assets must stay text-free")
    return warnings


def run_job(job: dict, base: Path, backend: str, timeout: int, dry_run: bool) -> dict:
    started = time.time()
    out = (base / job["out"]).resolve()
    refs = [(base / r).resolve() for r in job.get("refs") or []]
    result = {"id": job["id"], "out": str(out), "backend": backend, "ok": False}
    try:
        if job.get("kind", "asset") != "asset":
            raise GenError("only artwork asset jobs are supported; compose slides in HTML", "config")
        missing = [str(r) for r in refs if not r.is_file()]
        if missing:
            raise GenError(f"reference image(s) not found: {missing}", "config")
        prompt = job.get("prompt") or load_prompt(job["prompt_file"], base)
        result["warnings"] = lint(job, prompt)
        aspect = job.get("aspect", "16:9")
        attempts = 0
        while True:
            attempts += 1
            try:
                extra = BACKENDS[backend](prompt, refs, aspect, bool(job.get("transparent")), out,
                                          int(job.get("timeout", timeout)), dry_run)
                break
            except GenError as exc:
                if exc.kind != "transient" or attempts >= 2 or dry_run:
                    raise
                say(f"  · {job['id']}: retrying once after a transient failure ({str(exc)[:160]})")
        result.update(extra)
        if not dry_run:
            info = image_info(out)
            result.update(info)
            if job.get("transparent") and not info["alpha"]:
                result.setdefault("warnings", []).append(
                    "asked for transparency but the file has no alpha channel; key it out with "
                    "`imgtool.py key` or regenerate")
        result["ok"] = True
    except GenError as exc:
        result.update(error=str(exc), error_kind=exc.kind)
    except Exception as exc:  # noqa: BLE001
        result.update(error=f"{type(exc).__name__}: {exc}", error_kind="internal")
    result["seconds"] = round(time.time() - started, 1)
    return result


def describe(result: dict) -> str:
    if result.get("dry_run"):
        return f"[dry-run] {result['id']} → {result.get('command') or result.get('endpoint')}"
    if result["ok"]:
        size = f"{result.get('width')}x{result.get('height')}"
        alpha = " alpha" if result.get("alpha") else ""
        text = f"✓ {result['id']}  {size}{alpha}  {result['seconds']}s  → {result['out']}"
    else:
        text = f"✗ {result['id']}  [{result.get('error_kind')}] {result.get('error')}"
    for warning in result.get("warnings") or []:
        text += f"\n    ! {warning}"
    if result.get("note"):
        text += f"\n    · {result['note']}"
    return text


def cmd_batch(args) -> int:
    jobs_path = Path(args.jobs).resolve()
    spec = json.loads(jobs_path.read_text(encoding="utf-8"))
    jobs = spec["jobs"] if isinstance(spec, dict) else spec
    defaults = spec.get("defaults", {}) if isinstance(spec, dict) else {}
    if isinstance(spec, dict) and spec.get("base"):
        base = (jobs_path.parent / spec["base"]).resolve()
    else:
        base = find_deck_root(jobs_path.parent) or jobs_path.parent
    merged, seen_ids, seen_outs = [], set(), set()
    for raw in jobs:
        job = {**defaults, **raw}
        if not job.get("id") or not job.get("out") or not (job.get("prompt") or job.get("prompt_file")):
            print(f"error: every job needs id, out and prompt/prompt_file: {raw}", file=sys.stderr)
            return 2
        if job["id"] in seen_ids or job["out"] in seen_outs:
            print(f"error: duplicate job id or output: {job['id']} / {job['out']}", file=sys.stderr)
            return 2
        seen_ids.add(job["id"])
        seen_outs.add(job["out"])
        merged.append(job)
    if args.only:
        wanted = set(args.only.split(","))
        merged = [j for j in merged if j["id"] in wanted]
    pending = [j for j in merged if args.force or args.dry_run or not (base / j["out"]).exists()]
    skipped = len(merged) - len(pending)
    try:
        backend = pick_backend(args.backend)
    except GenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    say(f"{len(pending)} image(s) to generate with {backend} (concurrency {args.concurrency})"
        + (f", {skipped} already exist" if skipped else ""))
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        futures = {pool.submit(run_job, job, base, backend, args.timeout, args.dry_run): job for job in pending}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            say(describe(result))
    order = {job["id"]: i for i, job in enumerate(merged)}
    results.sort(key=lambda r: order.get(r["id"], 0))
    if not args.dry_run:
        report = jobs_path.with_name(jobs_path.stem + ".results.json")
        previous = {}
        if report.is_file():
            try:
                previous = {r["id"]: r for r in json.loads(report.read_text(encoding="utf-8"))}
            except (ValueError, KeyError, TypeError):
                previous = {}
        previous.update({r["id"]: r for r in results})
        report.write_text(json.dumps([previous[k] for k in sorted(previous, key=lambda k: order.get(k, 0))],
                                     ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [r for r in results if not r["ok"]]
    say(f"done: {len(results) - len(failed)} ok, {len(failed)} failed")
    return 1 if failed else 0


def cmd_gen(args) -> int:
    try:
        backend = pick_backend(args.backend)
    except GenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    cwd = Path.cwd()
    job = {"id": Path(args.out).stem, "out": str(Path(args.out).resolve()), "kind": args.kind,
           "refs": [str(Path(r).resolve()) for r in args.ref or []], "aspect": args.aspect,
           "transparent": args.transparent}
    if args.prompt_file:
        spec = args.prompt_file
        path_part, sep, section = spec.partition("#")
        job["prompt_file"] = str(Path(path_part).resolve()) + (sep + section if sep else "")
    elif args.prompt:
        job["prompt"] = args.prompt
    else:
        print("error: give --prompt-file or --prompt", file=sys.stderr)
        return 2
    result = run_job(job, cwd, backend, args.timeout, args.dry_run)
    if result.get("dry_run"):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(describe(result))
    return 0 if result["ok"] else 1


def cmd_check(_args) -> int:
    codex = find_codex()
    print(f"codex : {codex or 'not found'}")
    if codex:
        status = subprocess.run([codex, "login", "status"], capture_output=True, text=True, timeout=30)
        print(f"        {(status.stdout or status.stderr).strip().splitlines()[0] if (status.stdout or status.stderr).strip() else 'unknown login state'}")
    print(f"openai: {'OPENAI_API_KEY set' if os.environ.get('OPENAI_API_KEY') else 'no key'}")
    print(f"gemini: {'key set' if (os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')) else 'no key'}")
    try:
        print(f"auto  → {pick_backend('auto')}")
        return 0
    except GenError as exc:
        print(f"auto  → none ({exc})")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="ppt-studio image generation bridge")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").set_defaults(fn=cmd_check)

    p = sub.add_parser("gen")
    p.add_argument("--prompt-file")
    p.add_argument("--prompt")
    p.add_argument("--out", required=True)
    p.add_argument("--ref", action="append")
    p.add_argument("--aspect", default="16:9", choices=sorted(ASPECTS))
    p.add_argument("--transparent", action="store_true")
    p.add_argument("--kind", choices=["asset"], default="asset")
    p.add_argument("--backend", default="auto", choices=["auto", *BACKENDS])
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_gen)

    p = sub.add_parser("batch")
    p.add_argument("jobs")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    p.add_argument("--force", action="store_true", help="regenerate even when the output exists")
    p.add_argument("--only", help="comma-separated job ids to run")
    p.add_argument("--backend", default="auto", choices=["auto", *BACKENDS])
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_batch)

    args = parser.parse_args()
    raise SystemExit(args.fn(args))


if __name__ == "__main__":
    main()
