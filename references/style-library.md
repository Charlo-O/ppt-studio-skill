# Style library

160 slide styles, each a YAML-like written design specification for a whole deck.
Read the full text to choose and apply a style. Full catalog by category: `library/INDEX.md`.

## Contents

1. Finding a style
2. Quick picks by deck purpose
3. Judging fit
4. Reading a spec
5. Language adaptation
6. `style/notes.md` template

## 1. Finding a style

```bash
ppt styles categories
ppt styles search 科技 蓝色 商务            # Chinese, English or Japanese words; mood, colour, topic
ppt styles search dark editorial photo --top 5
ppt styles list --category Isometric        # or --theme dark, --imagery character
ppt styles show 47 --meta                   # palette, mood, imagery tags, file paths
ppt styles show 47                          # full original spec   (--zh for the translation)
```

`theme` (light/dark) comes from the spec's background colour; `imagery` tags are keyword hints
(photo, illustration, isometric, 3d, character, collage, watercolor, hand-drawn, texture, glass,
neon, icons, ui). Confirm these hints in the full written prompt.

## 2. Quick picks by deck purpose

| Purpose | Strong candidates |
| --- | --- |
| Business report, review, consulting | 001 Corporate Blue Minimal · 012 Clean Business · 017 Blue & Red Round · 019 Red Square · 034 White Risk Report · 035 Orange Insight Report · 036 Green Strategy Report · 086 Consulting Glass · 033 Black Data Report (dark) |
| Data-heavy, dashboards, KPIs | 095 Corporate Infographic · 093 Retro Infographic · 096 Editorial Infographic · 094 Dark Infographic · 009 SaaS dashboard · 122 Neo Swiss · 113 Block Infographic |
| Pitch, startup, product launch | 042 Green Pitch · 044 Orange Pitch · 004 Neo Gradient · 154 Modern UI · 085 Aurora Glass · 047 Isometric Blue x Yellow |
| Tech, AI, digital transformation | 054 Technology Isometric · 046 Isometric Blue x Red · 048 Isometric Green · 084 Digital Blueprint · 056 Cyber Isometric (dark) · 053 City Isometric (dark) · 119 Diagram Poster (dark line art) |
| Education, training, workshops | 003 Global Education · 050 Learning Isometric · 049 Academic Isometric · 059 Playful Learning · 011 neon multicolor (monochrome workshop) · 141 Conversation Bubble · 083 Speculative Instruction · 082 Industrial Manual |
| Brand, marketing, lifestyle | 025 Soft Brand System · 027 Luxury Brand System · 028 Green Brand System · 155 Brand Guideline · 153 Playful Brand · 126 Lifestyle Magazine · 002 Natural Lifestyle · 006 Organic Editorial |
| Fashion, bold editorial | 005 Dark Editorial · 013 Warm Editorial · 014 Earth Editorial · 015 Neo Editorial · 029 Neon Editorial · 032 Bold Editorial · 142 Modern Fashion · 021 Neo-Brutalist |
| Recruiting, culture, HR | 037 Recruit Blob · 038 Recruit Objects · 039 Recruit Line · 040 Recruit Minimal · 043 Culture Book · 125 Recruitment Magazine |
| Portfolio, design, architecture | 041 Pop Portfolio · 030 Minimal Grid · 007 Modern Minimal · 022 Monochrome Architecture · 023 Monochrome Minimal · 070 Architectural Isometric · 156 Geometric Block |
| Culture, art, history, museums | 061 Neo Museum · 062 Neo Mondrian · 063 Dada Collage · 064 Dada Black · 121 Neo Constructivist · 123 Cinematic Infographic · 124 Architectural Timeline · 127 Art Magazine · 078/079/080 Risograph |
| Nature, sustainability, ESG | 074 Watercolor Botanical · 075 Watercolor Spring · 076 Pastel Naturalist · 036 Green Strategy Report · 028 Green Brand System |
| Concept talks, metaphors, keynotes | 105 Miniature Metaphor · 107 Miniature Idea · 106 Miniature Landscape · 108 Miniature Keyboard · 077 Chromatic Object · 128 Object Editorial · 133 Monochrome Yellow · 134 Monochrome White · 135 Nostalgic Objects |
| Youth, events, campaigns, fun | 143 Flashy Memphis · 144 Color Block · 102 Blue & Yellow Collage · 103 Neon Collage · 101 Blue Collage · 120 Neon Poster · 117 Neon Signboard · 090 Playground Graffiti · 089 Urban Graffiti · 091 Underground Comic · 099 Comic Vibe |
| Characters, kids, storytelling | 149 Bold Mascot · 097 Bauhaus Cartoon · 100 Kawaii Monster · 152 Skate Rulebook · 157 Character Poster · 158 Scandinavian Animal · 159 Playful Creature · 160 Friendly Blob · 098 Naive Zine · 151 Minimal Character |
| Soft UI, product, app | 065 Multi Neumo · 066 Citrus Neumo · 067 Azure Neumo · 068 Neon Neumo · 087 Pastel Glass · 088 Dreamy Glass · 154 Modern UI |
| Humour, nostalgia, internet | 145 Bad PowerPoint · 146 Windows98 UI · 147 WindowsXP UI · 148 Internet Nostalgia · 058 Retro UI · 129–132 Cat series |
| Playbooks, how-to, manuals | 114 Block Playbook · 115 Modular Playbook · 116 Modular Infographic · 081 Yellow Blueprint · 110 Retro Runner · 112 Editorial Runner |

## 3. Judging fit

- **Text capacity.** Poster-like styles (149, 157, 133, 134, 136, 139, 024) carry a headline and a
  line or two per slide; they suit keynotes, not dense reports. Infographic and report styles
  (033–036, 093–096, 081, 072) carry tables, charts and many labels.
- **Imagery load.** Isometric, miniature, collage, character and photo styles need subject-specific
  artwork where the content benefits from it. Corporate, Swiss, minimal, neumorphic, UI and infographic styles are
  mostly code-native and generate little. Budget about a minute per image.
- **Room and medium.** Light styles project better in bright rooms; dark styles look premium on
  screens and in video.
- **Language.** Styles built on huge condensed Latin headlines (015, 021, 032, 142, 149) need
  short English or very short Chinese titles; long Chinese titles fit editorial, report and
  isometric styles better.
- **Tone match matters more than topic match.** A finance deck for young users can wear 143; a
  children's charity report may need 036 rather than 160.

## 4. Reading a spec

Specs vary in field names but share these parts. Read all of it once, then translate it:

| Spec section | Becomes |
| --- | --- |
| `Design Style` / `Concept` / `Mood` | the intended tone and defining style traits |
| `Canvas` | always 16:9; keep 1920×1080 |
| `Background`, `Color Palette` | CSS tokens by role: `--bg`, `--surface`, `--ink`, `--ink-2`, `--muted`, `--line`, `--accent`, `--accent-2`… |
| `Typography` (Heading/Body/Numbers/JapaneseHeading) | font roles → installed families (`ppt doctor --fonts`) |
| `Visual Identity`, `Shapes`, `Decorations`, `Graphic Elements` | signature motifs; mostly HTML geometry, sometimes generated |
| `Image Style`, `Photography`, `Illustration`, `Rendering` | the art-direction block of every asset prompt |
| `Layout System`, `Grid`, `Spacing`, `Whitespace` | margins, columns, gaps |
| `Slide Types` (Cover, Contents, …) | composition vocabulary for the Agent to adapt to each message |
| `Components` (Pills, Cards, Tables, Icons…) | shared classes in `theme.css` |
| `Restrictions`, `Avoid`, `Rules` | hard constraints for prompts and HTML |
| `Animation Feel` | ignore (static slides) |

When a spec gives no `Slide Types`, invent suitable compositions from its grid, typography,
spacing and visual identity. See `composition.md`. Keep the full prompt available during
implementation and review; a compressed summary can omit defining details.

## 5. Language adaptation

The specs were written for Japanese decks (`JapaneseHeading`, Mincho, Gothic, English kicker
labels over Japanese titles).

- Gothic / ゴシック → CJK sans: PingFang SC (macOS), Microsoft YaHei (Windows).
- Mincho / 明朝 → CJK serif: Songti SC / STSong (macOS), SimSun (Windows).
- Rounded Gothic / 丸ゴシック → Yuanti SC, Hiragino Maru Gothic ProN; Latin: Arial Rounded MT Bold.
- Handwritten Japanese → Hannotate SC, HanziPen SC, Wawati SC, Kaiti SC, depending on the mood.
- For Japanese decks keep Hiragino Sans / Hiragino Mincho ProN.
- Small English kickers ("CONTENTS", "SECTION 01", "OUR MISSION") are part of many styles; keep
  them short and decorative only when appropriate to a Chinese deck; adapt other labels to
  the deck language.
- CJK titles need more height and less tracking than the Latin display faces in the specs; adjust
  sizes rather than forcing the Latin scale.

## 6. `style/notes.md`

Keep notes concise and traceable to the full prompt:

```markdown
# Style notes — <id / name>
Full source: prompt.txt; translation: prompt.zh.txt
Audience, tone and reason for this style:

## Palette
Colours with functional roles: background, ink, accent, rule, surface.

## Typography
Installed family and weight per role; size and line-height; CJK and Latin treatment.
Observed headline weight after rendering; export limitations if any.

## Defining style requirements → implementation
Requirement from the full prompt → concrete token, shape, type or layout decision.
Record the few defining traits; include more than palette alone.

## Layout language
Grid, asymmetry/symmetry, density, whitespace, focal scale and recurring components.
Per-slide arrangements belong in design-plan.md and follow their content.

## Artwork direction
Relevant medium, palette, light, viewpoint, texture and crop clauses for asset prompts.

## Restrictions and adaptations
Prohibited visual treatments; language adaptations; user overrides and their reasons.
```

Original prompts may mention particular example-slide subjects or layouts. Extract the written
visual principles and adapt them to the actual content. Do not introduce those example subjects
as facts about this deck. Artwork prompts need the image-related clauses; the Agent uses the
complete style specification to design and inspect the whole slide.
