# Agent-designed composition

The full style prompt describes a visual language. The Agent applies it to this deck's content.
Use textual reasoning to decide layouts, then inspect the rendered implementation to improve them.

## From style language to visible decisions

Identify the few traits that make the style recognisable beyond its palette. Link each to a
concrete decision and an observation to make during review. For example:

| Prompt requirement | Agent decision | Look for in the actual page |
| --- | --- | --- |
| Oversized, ultra-bold editorial typography | dominant short headline; installed heavy face; tight line spacing | headline leads the page even at contact-sheet size |
| Asymmetric modular layout | unequal regions sized to the argument; strong aligned edges | a deliberate reading order and visual tension |
| Neon blocks and fine rules | editable highlight bands for key phrases; rules divide content | accent colour structures information, not just page numbers |
| Gentle botanical watercolour | soft artwork at selected edges; generous calm central field | organic framing without competing with the message |

These are examples, not defaults. Minimal, dense, playful and editorial styles need different
decisions. Use the chosen prompt's layout descriptions as a vocabulary, not a requirement to
copy one arrangement across all content pages.

## design-plan.md

Write the plan before coding, and update it when a rendered page reveals a better solution.
Keep it short enough to guide implementation rather than duplicate every source file.

```markdown
# Design plan

## Style requirements and implementation
Full prompt: style/prompt.txt; translation: style/prompt.zh.txt
Defining traits → font/scale/geometry/image-treatment decisions.
Language and export adaptations, with any compromise stated explicitly.

## Deck system
Canvas, colour roles, typography roles, alignment grid, recurring motifs and footer treatment.
Sequence rhythm: where a statement, evidence, comparison or visual explanation changes pace.

## s01
Message and desired audience takeaway:
Focal point and reading order:
Composition and reason it suits this content:
Major regions: x, y, width, height in canvas pixels; relative visual weight.
Type: final copy from outline, family, size, weight, line breaks.
Geometry: bands, rules, frames, diagrams; role in conveying meaning.
Artwork: subject, crop, aspect, position and layer; or none needed.
Style traits expressed on this page:
```

For comparisons, make the compared dimensions visually comparable. For a process, make order
and dependencies explicit. For a promotional claim, give the evidence sufficient space to be
read. Decorative symmetry must not obscure the argument.

Preserve shared visual grammar while varying focal scale, region count and rhythm. Repeated
metadata may stay fixed; title placement and layout can vary when the written style calls for it.

## Language and implementation choices

If the chosen font lacks the intended weight or width in Chinese, inspect installed alternatives
and a rendered headline. Shorter wording, line breaks, scale and contrast can retain the style's
force. Do not silently turn a poster headline into an ordinary section heading to fit a default
box. Record unavoidable compromises in style notes and verify the exported appearance.

Use the actual rendered slide as feedback. Evaluate whether the message reads in the intended
order and whether the defining style decisions are visible. Revise the Agent's composition when
they are not; the original written prompt remains available throughout.
