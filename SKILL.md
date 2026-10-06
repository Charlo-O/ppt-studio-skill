---
name: ppt-studio
description: Design and build complete presentations (PPT / 幻灯片 / 演示文稿 / pitch deck / keynote) using 160 bundled visual-style prompts. The AI Agent reads the full style specification, designs each slide's composition from the content and communication goal, creates any needed text-free artwork, and implements live editable text and shapes on a 1920×1080 canvas. Render, review and export editable PPTX, image PPTX and PDF. Use for making, redesigning or restyling a presentation, including 做个PPT、汇报、路演、课件、宣传介绍 and requests for a particular visual style. Not for merely extracting or text-editing an existing PPTX.
---

# PPT Studio

The Agent is the presentation designer. Use the user's brief and the full written style prompt
to decide the story, hierarchy, composition, typography and imagery of each slide. Implement
those decisions directly as editable slides; render the actual slides to evaluate the design.

Default outputs inside the deck folder:

- `out/<name>.pptx`: live text boxes, native shapes, separately movable images and icons
- `out/<name>-images.pptx`: one rendered image per slide
- `out/<name>.pdf`, `out/png/sNN.png`, `out/contact-sheet.jpg`

## Design ownership

- **Written style → Agent decisions → implementation → rendered review.** Keep the complete
  style prompt available through all four stages. Notes and asset prompts supplement it.
- The Agent chooses composition from content, reading order and the style's layout language.
  Do not generate whole-slide concept images, attach style boards, or derive coordinates from
  example pictures. Archived gallery images are outside this workflow.
- Image generation supplies artwork: photographs, illustrations, cutouts and textures. Text,
  information structure, charts and geometric decoration belong to the editable layout.
- Consistency comes from shared typography, colour roles, motifs and image treatment. Vary
  composition with the message; a common style does not require one repeated template.

## Working with the user

Speak the user's language and explain decisions in terms of their deck. Choose routine design
details yourself and proceed. If no style is specified, name your choice and briefly explain
its fit so the user can redirect. Seek approval only when the user requested that checkpoint.
Ask about missing facts that would otherwise be invented; group essential questions and continue
independent work. Use qualitative claims when unsupported numbers are unnecessary.

Give concise updates on the direction, meaningful findings during work, and the finished result.
Show actual rendered pages when a visual update helps. Do not promise a fixed generation count;
some styles need many assets, others can be built entirely from text and shapes.

## Tools

Use `bash <skill-dir>/scripts/ppt <command> ...` (abbreviated below as `ppt`).

| Command | Use |
| --- | --- |
| `ppt doctor --fonts` | inspect runtime, browser, image backend and installed fonts |
| `ppt styles search/show/list/use` | find, read and apply written style specifications |
| `ppt init DIR --title T --slides N --lang zh-CN [--style ID]` | create a deck project |
| `ppt imagegen batch assets/jobs.json` | generate planned artwork when needed |
| `ppt img info/crop/fit/key/trim/split/sheet` | inspect and prepare image assets |
| `ppt icons search/svg/inline` | find and place Lucide icons |
| `ppt render DECK` | render actual pages, check geometry, make a contact sheet |
| `ppt export DECK [--windows-fonts]` | export editable PPTX, image PPTX and PDF |

Use the host's native image tool when available; otherwise see
[image-backends.md](references/image-backends.md). Save generated assets to their planned paths.

## 1. Brief and outline

Create a project under the user's folder with `ppt init`. Continue an existing project when the
user identified it; otherwise choose a new folder without overwriting their work.

Record the request and source paths in `brief.md`. Read supplied materials before writing.
Facts, figures, quotes and product capabilities must be grounded in those materials or confirmed
by the user. Distinguish conceptual illustrations from evidence or actual product screenshots.

Write `outline.md`: each slide's id, purpose, final title/body, data, visual idea and speaker notes.
Mirror ids, titles, types and notes in `deck.json`. Honour an explicit slide count; otherwise let
the story determine length. Keep one main message per slide and move detail to notes.

Use concrete language and short lines suitable for presentation. Shorten copy to preserve the
style's intended hierarchy instead of shrinking all type. Numbers need units, periods and sources.

## 2. Read the full style prompt and make it actionable

Use the requested style, or search the textual catalogue for a style suited to audience, tone,
content density and language. `ppt styles show ID --both` prints the full original and translation.
`ppt styles use ID DECK` copies those two prompt files to `style/`.

Read them in full, including typography, layout, image treatment, slide types and restrictions.
Write `style/notes.md` with:

- palette roles and exact colours;
- installed type families, weights, scale, line spacing and language adaptation;
- the defining motifs, density, whitespace and image treatment;
- a short mapping from defining prompt requirements to concrete implementation choices.

Keep this mapping specific: “oversized ultra-bold headlines” must become a tested font and scale;
“tight asymmetric editorial grid” must affect region sizes and spacing. Matching colours alone
does not establish the style. Preserve the full prompt as the authority when notes omit a detail.
Read [style-library.md](references/style-library.md) for selection and translation guidance.

## 3. Agent-designed composition

Before implementation, write `design-plan.md` using
[composition.md](references/composition.md). Start with the deck's shared visual system, then
design each page from its message and the style's written layout principles.

For each slide decide the first thing the audience should notice, reading order, major regions
and proportions, type scale, image crop, meaningful geometric elements and layer order. Record
useful pixel rectangles on the 1920×1080 canvas. Explain how its composition expresses the
selected style. The Agent invents these arrangements; supplied style descriptions guide their
visual language rather than fixing identical coordinates for every topic.

Choose artwork only where it helps the idea. Charts, tables, processes, timelines and simple
decoration are usually editable shapes. Record required assets in `asset-plan.json`.

## 4. Generate or prepare artwork

Read [assets.md](references/assets.md). Derive each asset prompt from the planned slide role
and the relevant image-style clauses in the full style prompt. Specify subject, medium, palette,
viewpoint, lighting, crop and output aspect ratio. An asset prompt describes its own picture;
the Agent retains responsibility for the slide's overall composition.

Generated artwork is text-free. For calm areas, describe visible surfaces and detail density,
such as “an even pale wall with soft light”, instead of asking for a headline area. Keep slide
copy out of image prompts. Native logos and actual screenshots supplied by the user may keep
their original lettering.

Write prompts to `prompts.md` and jobs to `assets/jobs.json`. Generate only the assets needed;
inspect subject, aspect, texture, unwanted lettering and transparency before placing them.
For recurring characters or products, an existing subject asset can preserve identity across
poses. It does not determine the slide layout.

## 5. Build the actual slides

Read [slide-html.md](references/slide-html.md) before authoring. Set style tokens and shared
components in `theme.css`. Each `slides/sNN.html` contains one 1920×1080 `.slide-canvas` with
absolute pixel placement, live text, native geometry and local images. Use installed fonts,
and run `ppt icons inline DECK/slides` when using icon placeholders.

Implement the design plan, including its identifying type treatment and structural motifs.
The starter CSS supplies mechanics, not a visual design: replace its default sizes, spacing and
colours where the style calls for it. Adapt CJK typography deliberately; test its actual visual
weight instead of assuming `font-weight: 900` supplies a heavier installed face.

Render a representative page early when type or export behaviour is uncertain, then continue
the deck with the resolved system. This is the actual editable page in progress. Keep the plan
current when inspection leads to a better composition.

## 6. Review the rendered result

Run `ppt render DECK`. Fix reported geometry and missing-asset errors. Open the contact sheet
and inspect each `out/png/sNN.png` at full size using [review.md](references/review.md).

Review two things separately: correctness/readability, and whether the full written style has
become visible on the page. Check headline force, proportions, density, whitespace, motif usage,
image treatment and deck rhythm. Passing a geometry script is not an aesthetic pass.

Log actual findings and changes in `render-review.md`, including concrete evidence for the
defining style traits. Fix affected slides and re-render. Do not claim a review you did not perform.

## 7. Export and deliver

`ppt export DECK` exports editable PPTX, image PPTX and PDF with notes. All outputs originate
from the Agent-authored slides. `--mode image` selects image PPTX and PDF as the default outputs;
it uses the same design and rendering workflow.

Inspect export structure and, when a presentation renderer is available, the exported PPTX
itself. Check type weight, line breaks, shapes and proportions after conversion. Font remapping
can change the design; use `--windows-fonts` when appropriate and disclose unverified rendering.

Deliver links, slide count, chosen style and any remaining limitations or facts needing review.
Image PPTX/PDF preserve the rendered appearance; editable text depends on installed fonts.

## Revisions

Update copy, plan and the affected HTML, then render and export. For added slides, design a new
composition using the same written style system. For restyling, keep the content and reconsider
the layouts against the new prompt in a new folder unless the user requested an overwrite.

## Supporting guidance

| File | Read when |
| --- | --- |
| [style-library.md](references/style-library.md) | choosing and interpreting a style |
| [composition.md](references/composition.md) | designing the deck and each page |
| [assets.md](references/assets.md) | planning or prompting artwork |
| [slide-html.md](references/slide-html.md) | implementing slides |
| [review.md](references/review.md) | inspecting renders and exports |
| [image-backends.md](references/image-backends.md) | setting up image generation |
