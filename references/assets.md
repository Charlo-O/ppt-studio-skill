# Artwork assets

Assets are photographs, illustrations, cutouts, backdrops and textures used in the actual deck.
The Agent designs the slide first, then briefs each needed asset using the full style prompt's
image-related clauses and the planned region. A slide can also use only text and editable shapes.

## 1. Choose how the artwork participates

| Form | Use | Implementation |
| --- | --- | --- |
| Slot | photo or illustration within a content region | one image per region; Agent owns grid and captions |
| Code-native | charts, tables, timelines, diagrams, simple decoration | editable shapes, live text, SVG icons |
| Backdrop | continuous scene sharing light and perspective | one picture; the Agent specifies calm and detailed regions |
| Cutout | movable mascot, object or product | separate transparent PNG |
| Collage | layered fragments and varied crops | separate images; geometry, frames and tape in CSS where possible |

Keep a continuous physical scene together. Split objects when independent placement, replacement
or reuse helps. Let distinct concepts have distinct visuals. Recurring mascots or textures can
repeat when that serves the style. Rules, bands, dots and simple frames belong in editable code.

## 2. Write the asset prompt

Include subject, medium, colour treatment, viewpoint, lighting, texture, crop and relevant spatial
requirements. Use the art-direction clauses from `style/prompt.txt`; do not shrink the full
slide style to a palette. Prompt in English for the image backend; final slide copy stays in HTML.

Example for a planned right-side cutout:

```text
A compact isometric customer-support desk scene, viewed from above at a three-quarter angle.
One seated operator, a simple desk and monitor with abstract coloured blocks on the screen.
Cobalt blue #4F7EF7 and warm yellow #FFC83D, smooth matte surfaces, soft ambient shading,
crisp simplified geometry. The scene is centred, with the entire desk visible and clear space
around its silhouette. Transparent background.
```

Set the intended aspect ratio in the tool/job and `transparent: true` for cutouts. Inspect actual
size and alpha after generation. Use `object-fit: cover` for photo crops and `contain` for cutouts;
never stretch a picture to force a slot.

**Describe surfaces rather than future occupants.** “The left 40% is a softly lit pale wall with
low detail” is preferable to “space for the headline”, which can produce banners or lettering.
Specify calm regions through light, material and detail density. Generated images should contain
no text; inspect for stray lettering even when the prompt requests none. Screens can display
abstract blocks, packaging plain material, and books unlabelled cloth covers.

**Composition remains the Agent's decision.** If the planned backdrop has a calm left region and
a subject on the right, describe those regions directly. Adjust the crop or regenerate when the
asset cannot support the plan. Image-generation proportions are approximate, so measure the
result before placing text over it.

**Consistency.** Reuse the relevant written art direction across related assets. For a recurring
subject, an existing character or product image can preserve identity across poses. Such an input
is for that subject only; its surrounding layout does not govern the page. User-supplied logos,
product screenshots and factual diagrams retain their authenticity and may contain real text.

**Decorative plates and sheets.** Botanical edges, paper textures or collage fragments may be
requested directly from the Agent's planned positions and written style. Specify which regions
are plain. Generate movable focal subjects separately. A transparent sheet of small separated
ornaments can be split with `ppt img split`; leave wide gaps between elements.

## 3. Files

`asset-plan.json` records each asset's role; `prompts.md` has one `## asset-id` heading per prompt.

```json
{
  "art_direction": "clean isometric forms, cobalt and yellow, soft ambient shading",
  "assets": [
    {"id": "s04-desk", "slide": "s04", "form": "cutout", "rect": [1180, 300, 640, 620],
     "layer": "foreground", "prompt": "s04-desk", "aspect": "1:1", "transparent": true,
     "source": "generated"}
  ],
  "html_layers": {"s04": ["background", "title", "steps", "s04-desk", "page-number"]}
}
```

Generated jobs in `assets/jobs.json`:

```json
{
  "defaults": {"kind": "asset"},
  "jobs": [
    {"id": "s04-desk", "prompt_file": "prompts.md#s04-desk", "out": "assets/s04-desk.png",
     "aspect": "1:1", "transparent": true}
  ]
}
```

Run independent artwork in one batch with `ppt imagegen batch assets/jobs.json`, or use the host's
native image tool. If a pose depends on a generated character asset, finish and inspect the
character first. The complete style prompt guides Agent composition; these prompts guide only
the artwork in their named slots.

## 4. Inspect and repair

Use `ppt img info assets/*.png` and inspect an asset sheet or individual files. Check subject,
ratio, resolution, unwanted text, calm regions and transparency. Revise the prompt and regenerate
only failed assets. Follow the host image tool's instructions for edits; generic file utilities
support crop, fit, trim, split and flat-background keying when permitted.

Cropping existing user media is fine when it preserves the subject, fits the region and has enough
resolution. Record its source in the plan. Do not turn illustrative AI imagery into documentary
proof about a real product or project.

## 5. Text over images

Measure the actual crop and contrast where text lands. Prefer the planned calm region; add a
style-appropriate scrim, panel or gradient when needed. Size it to the text block and avoid a
visible unintended edge. Keep all newly authored slide copy live and editable.
