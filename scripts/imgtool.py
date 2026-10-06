#!/usr/bin/env python3
"""Image utilities for deck building (Pillow + numpy).

  imgtool.py info FILE...                         size, aspect, alpha and transparent-corner check
  imgtool.py grid REF -o OUT [--canvas 1920x1080] [--step 120]
                                                  reference scaled to the canvas with a labelled grid,
                                                  for reading slide coordinates off a reference
  imgtool.py measure IMG [--axis y|x] [--strips 18] [--canvas 1920x1080]
                                                  brightness and busyness per strip (find calm bands)
  imgtool.py crop SRC -o OUT --box x,y,w,h [--space canvas|pixels] [--canvas 1920x1080]
  imgtool.py fit SRC -o OUT --size 1920x1080 [--focus 0.5,0.5]
                                                  cover-crop and resize to an exact size
  imgtool.py key SRC -o OUT [--color auto|#RRGGBB] [--tolerance 36] [--mode flood|global]
                                                  remove a flat background, keep the subject (RGBA)
  imgtool.py trim SRC -o OUT [--pad 16]           crop transparent margins
  imgtool.py split SHEET -o DIR [--merge 6]       cut a transparent sheet of separate elements into
                                                  one trimmed file per element (sticker sheets)
  imgtool.py sheet FILE... -o OUT [--cols 3] [--width 640]
  imgtool.py pair LEFT RIGHT -o OUT [--labels "Reference,Render"]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _font(size: int):
    for path in ("/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
                 "/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/arial.ttf"):
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _size(text: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)x(\d+)", text)
    if not match:
        raise SystemExit(f"bad size '{text}', expected WIDTHxHEIGHT")
    return int(match.group(1)), int(match.group(2))


def _save(image: Image.Image, out: str) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        image.convert("RGB").save(path, quality=90)
    else:
        image.save(path)
    print(path)


def cmd_info(args) -> None:
    for name in args.files:
        with Image.open(name) as im:
            w, h = im.size
            has_alpha = "A" in im.getbands() or "transparency" in im.info
            line = f"{name}: {w}x{h} ({w / h:.3f}) {im.mode}"
            if has_alpha:
                alpha = np.asarray(im.convert("RGBA"))[:, :, 3]
                corners = [alpha[0, 0], alpha[0, -1], alpha[-1, 0], alpha[-1, -1]]
                clear = float((alpha < 8).mean())
                line += f" alpha: {clear:.0%} transparent, corners {'clear' if max(corners) < 8 else 'OPAQUE'}"
            else:
                line += " no alpha"
            print(line)


def cmd_grid(args) -> None:
    cw, ch = _size(args.canvas)
    base = Image.open(args.ref).convert("RGB").resize((cw, ch), Image.LANCZOS)
    overlay = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _font(max(14, cw // 110))
    step = args.step
    for x in range(0, cw + 1, step):
        major = x % (step * 4) == 0
        draw.line([(x, 0), (x, ch)], fill=(255, 0, 90, 150 if major else 70), width=2 if major else 1)
        draw.text((x + 3, 3), str(x), fill=(255, 0, 90, 230), font=font)
        draw.text((x + 3, ch - font.size - 6), str(x), fill=(255, 0, 90, 230), font=font)
    for y in range(0, ch + 1, step):
        major = y % (step * 4) == 0
        draw.line([(0, y), (cw, y)], fill=(0, 140, 255, 150 if major else 70), width=2 if major else 1)
        draw.text((3, y + 3), str(y), fill=(0, 120, 255, 230), font=font)
        draw.text((cw - 48, y + 3), str(y), fill=(0, 120, 255, 230), font=font)
    _save(Image.alpha_composite(base.convert("RGBA"), overlay), args.out)


def cmd_measure(args) -> None:
    cw, ch = _size(args.canvas)
    image = Image.open(args.image).convert("L").resize((cw, ch), Image.BILINEAR)
    lum = np.asarray(image, dtype=np.float32) / 255.0
    edges = np.asarray(image.filter(ImageFilter.FIND_EDGES), dtype=np.float32) / 255.0
    length = ch if args.axis == "y" else cw
    bounds = np.linspace(0, length, args.strips + 1).astype(int)
    print(f"{'from':>6} {'to':>6}  bright  busy   (canvas px along {args.axis}; busy < 0.04 is calm)")
    for a, b in zip(bounds[:-1], bounds[1:]):
        part_l = lum[a:b, :] if args.axis == "y" else lum[:, a:b]
        part_e = edges[a:b, :] if args.axis == "y" else edges[:, a:b]
        busy = float(part_e.mean())
        bar = "#" * min(30, int(busy * 300))
        print(f"{a:>6} {b:>6}  {part_l.mean():.2f}    {busy:.3f}  {bar}")


def cmd_crop(args) -> None:
    image = Image.open(args.src)
    x, y, w, h = (float(v) for v in args.box.split(","))
    if args.space == "canvas":
        cw, ch = _size(args.canvas)
        sx, sy = image.width / cw, image.height / ch
        x, y, w, h = x * sx, y * sy, w * sx, h * sy
    box = (round(x), round(y), round(x + w), round(y + h))
    _save(image.crop(box), args.out)


def fit_image(image: Image.Image, width: int, height: int, focus=(0.5, 0.5)) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize((max(width, round(image.width * scale)), max(height, round(image.height * scale))),
                           Image.LANCZOS)
    left = round((resized.width - width) * focus[0])
    top = round((resized.height - height) * focus[1])
    return resized.crop((left, top, left + width, top + height))


def cmd_fit(args) -> None:
    width, height = _size(args.size)
    fx, fy = (float(v) for v in args.focus.split(","))
    _save(fit_image(Image.open(args.src), width, height, (fx, fy)), args.out)


def _border_color(rgb: np.ndarray) -> tuple[int, int, int]:
    band = np.concatenate([rgb[:6].reshape(-1, 3), rgb[-6:].reshape(-1, 3),
                           rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)])
    return tuple(int(v) for v in np.median(band, axis=0))


def key_out(src, out, color: str = "auto", tolerance: int = 36, mode: str = "flood", soft: int = 24) -> Path:
    """Make a flat background transparent. `flood` removes only background connected to the border."""
    image = Image.open(src).convert("RGB")
    rgb = np.asarray(image, dtype=np.int32)
    if color == "auto":
        key = _border_color(rgb)
    else:
        raw = color.lstrip("#")
        key = tuple(int(raw[i:i + 2], 16) for i in (0, 2, 4))
    distance = np.sqrt(((rgb - np.array(key, dtype=np.int32)) ** 2).sum(axis=2))
    if mode == "global":
        background = distance <= tolerance
    else:
        marker = image.copy()
        sentinel = (key[0] ^ 0x55, key[1] ^ 0xAA, (key[2] ^ 0x5A) | 1)
        w, h = image.size
        seeds = [(x, 0) for x in range(0, w, 16)] + [(x, h - 1) for x in range(0, w, 16)]
        seeds += [(0, y) for y in range(0, h, 16)] + [(w - 1, y) for y in range(0, h, 16)]
        for seed in seeds:
            if distance[seed[1], seed[0]] <= tolerance and marker.getpixel(seed) != sentinel:
                ImageDraw.floodfill(marker, seed, sentinel, thresh=tolerance)
        background = np.all(np.asarray(marker, dtype=np.int32) == np.array(sentinel, dtype=np.int32), axis=2)
    alpha = np.where(background, 0, 255).astype(np.uint8)
    ramp = np.clip((distance - tolerance) / max(1, soft), 0, 1)
    edge_zone = ~background & (distance < tolerance + soft)
    alpha = np.where(edge_zone, (ramp * 255).astype(np.uint8), alpha)
    alpha_img = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.6))
    rgba = image.convert("RGBA")
    rgba.putalpha(alpha_img)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(out.with_suffix(".png") if out.suffix.lower() not in {".png", ".webp"} else out)
    return out


def cmd_key(args) -> None:
    print(key_out(args.src, args.out, args.color, args.tolerance, args.mode))


def cmd_trim(args) -> None:
    image = Image.open(args.src).convert("RGBA")
    bbox = image.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if not bbox:
        raise SystemExit("image is fully transparent")
    pad = args.pad
    box = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(image.width, bbox[2] + pad), min(image.height, bbox[3] + pad))
    _save(image.crop(box), args.out)


def split_sheet(src, out_dir, threshold: int = 24, merge: int = 6, min_frac: float = 0.002,
                pad: int = 12) -> list[Path]:
    """Cut a transparent sheet of separate elements into one trimmed RGBA file per element."""
    image = Image.open(src).convert("RGBA")
    width, height = image.size
    factor = max(1, round(max(width, height) / 640))
    small = image.getchannel("A").resize((max(1, width // factor), max(1, height // factor)), Image.BOX)
    grown = small.point(lambda a: 255 if a > threshold else 0).filter(ImageFilter.MaxFilter(merge * 2 + 1))
    mask = np.asarray(grown) > 0
    labels = np.zeros(mask.shape, dtype=np.int32)
    sh, sw = mask.shape
    components = []
    for y0 in range(sh):
        for x0 in range(sw):
            if not mask[y0, x0] or labels[y0, x0]:
                continue
            label = len(components) + 1
            labels[y0, x0] = label
            stack, count = [(y0, x0)], 0
            x_min = x_max = x0
            y_min = y_max = y0
            while stack:
                y, x = stack.pop()
                count += 1
                x_min, x_max, y_min, y_max = min(x_min, x), max(x_max, x), min(y_min, y), max(y_max, y)
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < sh and 0 <= nx < sw and mask[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = label
                        stack.append((ny, nx))
            components.append((label, count, x_min, y_min, x_max, y_max))
    keep = [c for c in components if c[1] >= min_frac * sh * sw]
    keep.sort(key=lambda c: (round(c[3] / max(1, sh / 6)), c[2]))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(src).stem
    written = []
    for index, (label, _count, x0, y0, x1, y1) in enumerate(keep, 1):
        own = Image.fromarray(((labels == label) * 255).astype(np.uint8)).resize((width, height), Image.NEAREST)
        own = own.filter(ImageFilter.MaxFilter(5))
        piece = image.copy()
        piece.putalpha(Image.fromarray(np.minimum(np.asarray(image.getchannel("A")), np.asarray(own))))
        box = (max(0, x0 * factor - pad), max(0, y0 * factor - pad),
               min(width, (x1 + 1) * factor + pad), min(height, (y1 + 1) * factor + pad))
        piece = piece.crop(box)
        bbox = piece.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
        if bbox:
            piece = piece.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                                min(piece.width, bbox[2] + pad), min(piece.height, bbox[3] + pad)))
        path = out_dir / f"{stem}-{index:02d}.png"
        piece.save(path)
        written.append(path)
    return written


def cmd_split(args) -> None:
    paths = split_sheet(args.src, args.out, args.threshold, args.merge)
    for path in paths:
        with Image.open(path) as im:
            print(f"{path}  {im.width}x{im.height}")
    if not paths:
        print("no separate elements found (is the background transparent?)")


def _flatten(image: Image.Image) -> Image.Image:
    """RGB view of an image; transparent areas show a light checkerboard so cutout edges are visible."""
    if "A" not in image.getbands() and "transparency" not in image.info:
        return image.convert("RGB")
    rgba = image.convert("RGBA")
    tile = 24
    board = Image.new("RGB", rgba.size, "#F4F4F2")
    draw = ImageDraw.Draw(board)
    for y in range(0, rgba.height, tile):
        for x in range((y // tile) % 2 * tile, rgba.width, tile * 2):
            draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill="#DCDCD8")
    board.paste(rgba, (0, 0), rgba)
    return board


def contact_sheet(files: list, cols: int = 3, width: int = 640, labels: list | None = None,
                  background: str = "#E9E9E6") -> Image.Image:
    tiles = []
    for index, name in enumerate(files):
        im = _flatten(Image.open(name))
        im = im.resize((width, max(1, round(im.height * width / im.width))), Image.LANCZOS)
        tiles.append((im, labels[index] if labels else Path(name).stem))
    cols = max(1, min(cols, len(tiles)))
    rows = (len(tiles) + cols - 1) // cols
    label_h, gap = 34, 18
    tile_h = max(t[0].height for t in tiles)
    sheet = Image.new("RGB", (cols * width + (cols + 1) * gap, rows * (tile_h + label_h) + (rows + 1) * gap), background)
    draw = ImageDraw.Draw(sheet)
    font = _font(20)
    for index, (im, label) in enumerate(tiles):
        x = gap + (index % cols) * (width + gap)
        y = gap + (index // cols) * (tile_h + label_h + gap)
        draw.text((x, y + 6), label, fill="#222222", font=font)
        sheet.paste(im, (x, y + label_h))
    return sheet


def cmd_sheet(args) -> None:
    _save(contact_sheet(args.files, args.cols, args.width), args.out)


def side_by_side(left, right, labels=("Reference", "Render"), width: int = 960) -> Image.Image:
    return contact_sheet([left, right], cols=2, width=width, labels=list(labels))


def cmd_pair(args) -> None:
    labels = tuple(args.labels.split(",")) if args.labels else ("Reference", "Render")
    _save(side_by_side(args.left, args.right, labels), args.out)


def main() -> None:
    parser = argparse.ArgumentParser(description="image utilities for ppt-studio")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("info"); p.add_argument("files", nargs="+"); p.set_defaults(fn=cmd_info)
    p = sub.add_parser("grid"); p.add_argument("ref"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--canvas", default="1920x1080"); p.add_argument("--step", type=int, default=120)
    p.set_defaults(fn=cmd_grid)
    p = sub.add_parser("measure"); p.add_argument("image"); p.add_argument("--axis", choices=["x", "y"], default="y")
    p.add_argument("--strips", type=int, default=18); p.add_argument("--canvas", default="1920x1080")
    p.set_defaults(fn=cmd_measure)
    p = sub.add_parser("crop"); p.add_argument("src"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--box", required=True, help="x,y,w,h")
    p.add_argument("--space", choices=["canvas", "pixels"], default="canvas")
    p.add_argument("--canvas", default="1920x1080"); p.set_defaults(fn=cmd_crop)
    p = sub.add_parser("fit"); p.add_argument("src"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--size", required=True); p.add_argument("--focus", default="0.5,0.5"); p.set_defaults(fn=cmd_fit)
    p = sub.add_parser("key"); p.add_argument("src"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--color", default="auto"); p.add_argument("--tolerance", type=int, default=36)
    p.add_argument("--mode", choices=["flood", "global"], default="flood"); p.set_defaults(fn=cmd_key)
    p = sub.add_parser("trim"); p.add_argument("src"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--pad", type=int, default=16); p.set_defaults(fn=cmd_trim)
    p = sub.add_parser("split"); p.add_argument("src"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--threshold", type=int, default=24); p.add_argument("--merge", type=int, default=6)
    p.set_defaults(fn=cmd_split)
    p = sub.add_parser("sheet"); p.add_argument("files", nargs="+"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--cols", type=int, default=3); p.add_argument("--width", type=int, default=640)
    p.set_defaults(fn=cmd_sheet)
    p = sub.add_parser("pair"); p.add_argument("left"); p.add_argument("right"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--labels"); p.set_defaults(fn=cmd_pair)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
