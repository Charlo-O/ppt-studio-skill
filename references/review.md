# Render review

A deck you have not looked at is not finished. `ppt render` proves geometry — canvas size,
overflow, overlap, missing files, fonts. It cannot see that a title is weak, that artwork brought
its own lettering, or that slide 7 forgot the style. That part is you, looking.

## 1. Automatic checks (`ppt render <deck>`)

| Level | Finding | Usual fix |
| --- | --- | --- |
| error | `canvas` — size or `data-canvas-*` not 1920×1080, or two canvases | fix the template copy |
| error | `text-outside` — text crosses the canvas edge | move or shorten |
| error | `clipped` — text cut off by an `overflow: hidden` box | widen the box or shorten the copy |
| error | `text-overlap` — two text blocks collide | re-place; check the design-plan rectangles |
| error | `image`, `missing-file` — an asset did not load | fix the path (`../assets/…`) |
| warn | `small-text` — under 18px | enlarge, or cut the text |
| warn | `overflow` — text spills out of its own box (PowerPoint's box will differ) | give the box room, or `white-space: nowrap` for one-liners |
| warn | `edge` — text within 24px of the edge | respect the safe area unless it is a deliberate bleed |
| warn | `network`, `console` — external request or page error | remove it |
| info | `font-fallback` — the first family in a stack is not installed | intended only if the next family is the one you want |

Re-render only what changed: `ppt render <deck> --slides s03,s07`.

## 2. Look at every slide

Open `out/contact-sheet.jpg` for the deck at a glance, then each `out/png/sNN.png`
at full size, with the original style prompt and design plan available. Count only what you can point at:

**Text**

- Read every line on the image, aloud, in order. Anything you cannot read is a defect, however
  correct the markup is.
- Clipped, cut, covered or crowded text; text too close to a frame, rule, image edge or neighbour.
- Text meant to sit in a pill, card, ribbon or dark band: its bounds stay inside the carrier,
  aligned, without the backing floating off.
- Contrast wherever text sits over artwork; add a panel, scrim or gradient when it is short.
- Placeholder or leftover copy: "Title", "Lorem ipsum", "LOGO", "Your Name", English filler in a
  Chinese deck, wording the outline doesn't have.
- Typography inside CJK lines: middle dots `·` centred between characters, Chinese quotes and dashes,
  digits in a consistent face; big numerals and commas evenly spaced. Zoom in to check details:
  `ppt img crop out/png/sNN.png -o out/zoom.png --box x,y,w,h`.

**Artwork**

- Lettering, numbers or pseudo-text inside generated images (signs, screens, packaging, books).
- A visual that doesn't match its content: wrong subject, wrong count of items or steps.
- Unintended repetition: the same image or icon standing for two different ideas.
- Seams, mismatched light or perspective between pieces; dirty cutout edges; stretched images.

**Against the written style and Agent's design plan**

Check the defining traits recorded in `style/notes.md` against the full prompt and the actual
page: headline weight and scale, major region proportions, asymmetry, density, whitespace,
structural motifs and image treatment. Point to what implements each trait. Matching only
colours is insufficient. If a “bold editorial” slide has an ordinary heading and empty generic
columns, reconsider the composition and typography even when there are no geometry errors.

Confirm the message and evidence have the visual priority planned for this slide. A deliberate
layout improvement is welcome; update the plan to explain it. Never mark a style requirement
satisfied solely because it appears in notes or CSS—it must be visible in the rendered page.

**Deck consistency**

- Coherent typography, kicker treatment, page numbers and alignment logic; layout variation
  follows the style and content.
- One palette, one icon style and size, one illustration medium.
- The style's signature motifs present throughout — not only on the cover.
- Rhythm: varied layouts across the deck, not the same template ten times; no two adjacent slides
  that look accidentally identical.

## 3. Record and iterate

Append one numbered pass per real review cycle to `render-review.md`:

```markdown
## Pass 2
Findings: s04 card titles wrap to 3 lines at 40px; s07 photo contains sign lettering; s09 page
number missing.
Changes: s04 title size 36px + card width 540; regenerated s07-street with blank signage; added
.page to s09.
Style evidence: s04 oversized title remains dominant; yellow bands organise the three claims.
Result: s04 ok, s07 ok, s09 ok (render timestamp).
```

A clean pass records `Findings: none` and `Result: pass`. A taste preference is not a defect —
don't invent findings. If the same problem survives two fixes, stop and look again; the diagnosis
is wrong, not the wording.

After the defects are gone, one **optimization pass**: review the written style requirements and the
brief for missing visual support, weak icon-to-text pairing, slides that became text-only, or a
flat sequence. Apply only the single highest-impact improvement, re-render, and record it — or
record `Optimization: none`.

## 4. Export check

After `ppt export`, confirm from its summary: slide count equals the deck; every content slide
has text boxes (a slide with 0 text boxes was flattened — usually an SVG-only or full-image
slide); expected fonts listed (Latin and East Asian). The image PPTX and PDF should match
`out/png/` in appearance (JPEG compression may introduce small pixel differences).
When a PPTX renderer is available, inspect exported pages too: conversion can change font weight,
line breaks or shape treatment. If only structural checks were possible, report that limit.
