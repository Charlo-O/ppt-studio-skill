# Slide HTML

Each slide is a fixed 1920×1080 "poster" in HTML with live text. This file is the contract that
makes slides render predictably and convert into an editable PowerPoint where every text block,
card and image is its own object.

## Contents

1. File contract
2. What becomes what in PowerPoint
3. Layout
4. Typography and fonts
5. Icons
6. Charts, tables and diagrams
7. Images
8. Skeleton

## 1. File contract

- One slide per file: `slides/sNN.html`, copied from `slides/_template.html`. It links
  `../theme.css` and holds slide-specific CSS in one `<style>` block.
- Exactly one `<main class="slide-canvas" data-canvas-width="1920" data-canvas-height="1080">`.
- Every block is a direct child of the canvas, `position: absolute`, placed with `left`, `top`,
  `width` (and `height` where it matters) in **px**. No `vw`, `vh`, `%`, `em` for layout
  (decorative values like gradient stops, radii, shadow spread are free).
- `* { box-sizing: border-box; }` (in the starter theme). Without it, measured widths grow by
  their padding when the layout is read back.
- Palette and font stacks are custom properties on `:root` in `theme.css`; slides reference them.
- Assets are referenced relatively: `../assets/<id>.png`. No web fonts, CDNs, scripts,
  animations or network requests — the deck must render offline and identically every time.
- Semantic class names for blocks (`.title`, `.kicker`, `.stat-value`, `.step-card`). No comments.

## 2. What becomes what in PowerPoint

The exporter walks the rendered DOM and classifies every element:

| HTML | PowerPoint |
| --- | --- |
| element with its own text (`h1`, `p`, `span`, `div` with text) | **text box** — keeps font, size, colour, weight (regular/bold only), italic, letter-spacing, line-height, alignment, rotation, vertical writing |
| same element with a background colour, border or radius | text box with that fill/outline (pills, tags, buttons) |
| box with fill/border/radius/shadow **and children** | **native rounded rectangle**; children drawn on top |
| leaf box with a plain fill (bars, dots, rules, blobs drawn as circles) | **native shape** |
| leaf box with a gradient, uneven radii, partial border or rotation | its own transparent **picture** |
| `<img>`, inline `<svg>` | its own **picture** (clipped exactly as shown) |
| anything covering ≥ 90% of the canvas (page background, full-bleed backdrop) | stays in the slide's background picture |
| outer `box-shadow` of shapes and images | kept as a soft halo in the background picture |

Consequences for how you write slides:

- **Inline styling stays one text box.** `<p>增长 <b>38%</b> 来自新客</p>` becomes one text box
  with a bold run. Words that must move independently need their own element.
- **Gaps make separate boxes.** Text spread by flex `gap` or margins between inline items is split
  into separate text boxes at their measured positions.
- **Weights collapse to regular/bold** (≥ 600 is bold). Pick families whose regular and bold
  carry the hierarchy; don't rely on 300 vs 400 or 500 vs 600.
- **Pseudo-elements** (`::before`, `::after`) are flattened into a picture or the background.
  Never put meaningful text in them; use them only for decoration, or prefer real elements.
- **Gradients on cards with children** stay in the background picture (not editable). Use solid
  fills for cards that hold content; put gradients on leaf elements.
- **Inset shadows, blur, backdrop-filter** don't survive as shape effects; the image PPTX keeps
  the exact look. For glass/neumorphic styles keep the structure readable without them.
- **Multiply blend** on white-backed line art is converted to transparency; other blend modes are
  not reproduced.

## 3. Layout

- **Margins and grid.** Work inside a safe area: about 96–128px left/right, 72–96px top/bottom,
  unless the style bleeds deliberately. Use a 12-column grid (column ≈ 120px, gutter 24–32px)
  or the style's own grid; align edges exactly — near-alignment reads as error.
- **Consistent frame.** Recurring metadata follows shared alignment rules. Title placement and major regions
  follow the Agent's content-specific plan and the style's layout language.
- **Hierarchy is the job.** Each slide is read in three passes — hook (title or key visual), claim
  (the key number or statement), detail. Make the steps clearly different in size, weight and
  colour. Two elements of equal weight compete.
- **Whitespace is structure.** Don't fill every gap; one strong visual beats four small ones.
- **Commit to the style.** Reproduce its signature motifs (from `style/notes.md`) on every slide;
  avoid generic UI-card grids, badges and ribbons the style doesn't use.
- **Text over images** gets an explicit contrast treatment (panel, scrim, gradient) sized to the
  text block — see `assets.md` §5.
- Nothing closer than ~24px to the canvas edge unless it is a deliberate bleed.

## 4. Typography and fonts

Starting scale for a 1920×1080 canvas (1px ≈ 0.5pt in the exported PPTX). Adjust to the
full style prompt: these ranges are not caps on poster headlines or a universal layout:

| Role | px | ≈ pt | Line height |
| --- | --- | --- | --- |
| cover title / statement | 120–200 | 60–100 | 1.05–1.15 |
| slide title | 60–88 | 30–44 | 1.1–1.25 |
| big number / KPI | 96–180 | 48–90 | 1.0 |
| subtitle / lead | 36–48 | 18–24 | 1.3–1.4 |
| body / bullets | 26–34 | 13–17 | 1.45–1.7 |
| label / caption / source | 20–24 | 10–12 | 1.4 |

Never below 18px. Each step should be clearly larger than the one below; 10% steps read as a
mistake.

**Fonts that survive export.** The editable PPTX references font family names; installed system
fonts stay live, exact text. Run `ppt doctor --fonts` to see what this machine has. On macOS the
useful set includes:

| Role | Families |
| --- | --- |
| CJK sans | PingFang SC (default), Hiragino Sans GB, Heiti SC |
| CJK serif | Songti SC, STSong |
| CJK kai / brush | Kaiti SC, STKaiti, Baoli SC, Xingkai SC, Libian SC, Weibei SC |
| CJK rounded / playful | Yuanti SC, Hannotate SC, HanziPen SC, Wawati SC, Yuppy SC |
| Latin sans | Helvetica Neue, Avenir Next, Gill Sans, Optima |
| Latin geometric | Futura, Avenir Next |
| Latin condensed / display | Avenir Next Condensed, DIN Condensed, DIN Alternate, Impact |
| Latin serif | Didot, Bodoni 72, Baskerville, Georgia, Hoefler Text, Big Caslon |
| Mono / typewriter | Menlo, Courier New, American Typewriter |
| Hand / playful Latin | Chalkboard SE, Marker Felt, Noteworthy, Bradley Hand |

Stack rules:

- **Chinese or Japanese text: CJK family first**, then its Windows equivalent, then a generic:
  `"PingFang SC", "Microsoft YaHei", sans-serif` (PingFang carries good Latin letters and digits).
  With a Latin family first, the punctuation that both scripts share — `·`, `“ ”`, `—`, `…` — and
  the digits inside Chinese sentences take the Latin face: middle dots drift off-centre, quotes turn
  Western, numbers change rhythm. (Measured in this skill's test deck.)
- **Latin-led text** (English decks, big numerals, English kickers): Latin family first, then the
  CJK family: `"Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif`. The browser draws Latin
  glyphs with the first and CJK glyphs with the second; the exporter writes them as the run's Latin
  and East Asian fonts, which is how PowerPoint does the same.
- Mix them per element: a Chinese label in the CJK-first body stack, its number in a
  `<span class="num">` with a Latin display face. Each span keeps its own font in PowerPoint.
- Large serif numerals (120px+) often have loose figure and comma spacing; tighten with
  `letter-spacing: -0.04em` and `font-variant-numeric: proportional-nums`, then look again.
- Weight comes from the family: Kai, brush and handwriting faces stay thin — use them for short
  accents, not for headlines that must carry a page. No synthetic bold or italic on CJK faces.
- CJK display text tolerates tighter tracking than CJK body text; mixed lines need the Latin face
  first so digits use Latin proportions.
- Vertical CJK (`writing-mode: vertical-rl`): `white-space: nowrap` and centre with flex.
- A single-line block with `letter-spacing` needs `white-space: nowrap` or a width with room to
  spare; trailing tracking can push the last glyph onto a new line after export.
- If the audience opens the deck on Windows, export with `--windows-fonts`; macOS names are swapped
  for their Windows equivalents (PingFang SC → Microsoft YaHei, Helvetica Neue → Arial…).

## 5. Icons

```bash
ppt icons search chart growth          # names and tags (English)
ppt icons svg trending-up --size 48 --stroke 2 --color "#1500FF"
```

Easiest: write placeholders in the slide and expand them all at once —

```html
<i class="icon i1" data-icon="trending-up" data-size="48" data-stroke="2" data-color="#1500FF"></i>
```

```bash
ppt icons inline <deck>/slides          # replaces each placeholder with inline SVG, in place
```

`class`, `id` and `style` carry over to the `<svg>`; re-running is harmless. Keep one size, stroke width and colour treatment across a deck.
Lucide is an outline set; for styles with solid icons, put a white glyph on a filled circle or
rounded square — it reads as a solid badge and the circle stays a native shape. Each icon becomes
its own picture in PowerPoint.

## 6. Charts, tables and diagrams

Build data visuals from HTML so they stay accurate and mostly editable:

- **Bar/column charts:** one absolutely positioned `div` per bar (native shapes), value labels and
  axis labels as text. Compute heights from the data; keep a visible baseline.
- **Progress, KPI rings, donuts, lines, areas:** inline SVG (one picture each) plus live text for
  values and labels.
- **Tables:** a grid of positioned `div` cells or rows (shapes + text boxes); header fill from the
  style; numbers right-aligned with tabular figures where the font has them.
- **Processes, timelines, org charts:** cards (shapes) + connectors (thin `div` rules or small SVG
  arrows) + text.
- Every value comes from the outline. Label units and periods; cite the source in small text
  when the data is external.

## 7. Images

- Place assets as `<img>`; set `object-fit: cover` and `object-position` toward what matters.
  Never stretch.
- Rounded or masked photos: give the `<img>` (or a wrapper with `overflow: hidden`) the radius.
  The exported picture is clipped exactly as rendered.
- Transparent cutouts can overlap cards and text; order layers with `z-index`.
- Full-bleed backdrops are `<img class="bg">` at 0,0,1920,1080 as the first child; they become the
  slide's background picture.

## 8. Skeleton

```html
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>s04</title>
<link rel="stylesheet" href="../theme.css">
<style>
.kicker { left: 120px; top: 92px; font: 700 24px/1 var(--font-body); letter-spacing: 4px; color: var(--accent); white-space: nowrap; }
.title { left: 120px; top: 132px; width: 1100px; font: 800 72px/1.15 var(--font-display); color: var(--ink); }
.card { top: 360px; width: 520px; height: 520px; background: var(--surface); border-radius: 32px; box-shadow: 0 24px 60px rgba(17,17,17,.08); }
.c1 { left: 120px; } .c2 { left: 700px; } .c3 { left: 1280px; }
.card-title { position: absolute; left: 48px; top: 200px; width: 424px; font: 700 40px/1.25 var(--font-display); }
.card-body { position: absolute; left: 48px; top: 268px; width: 424px; font: 400 28px/1.6 var(--font-body); color: var(--ink-2); }
.badge { position: absolute; left: 48px; top: 56px; width: 104px; height: 104px; border-radius: 52px; background: var(--accent); display: flex; align-items: center; justify-content: center; }
.page { right: 120px; bottom: 64px; font: 500 22px/1 var(--font-num); color: var(--muted); }
</style>
</head>
<body>
<main class="slide-canvas" data-canvas-width="1920" data-canvas-height="1080">
  <div class="kicker">SOLUTION</div>
  <h2 class="title">三步完成一次咨询</h2>
  <div class="card c1">
    <div class="badge"><i data-icon="message-circle" data-size="56" data-color="#FFFFFF"></i></div>
    <div class="card-title">自动识别问题</div>
    <div class="card-body">理解客户意图，判断问题类别与紧急程度</div>
  </div>
  <div class="card c2">…</div>
  <div class="card c3">…</div>
  <div class="page">04</div>
</main>
</body>
</html>
```

Note `.page` uses `right`/`bottom`; that is fine — every position is still in px.
