# Image backends

`ppt imagegen` turns artwork prompt files into PNGs through whichever backend the
machine has. Check with `ppt imagegen check`.

## Contents

1. Native host tools
2. Codex CLI bridge (default)
3. OpenAI and Gemini APIs
4. Jobs and results
5. Troubleshooting

## 1. Native host tools

If the agent running this skill has its own image tool (for example Codex's built-in `image_gen`),
use it directly: the planned artwork prompts, one call per asset, then copy each result to the path in the plan. Keep the batch and
review discipline from `SKILL.md`. The bridge exists for hosts without image generation, such as
Claude Code.

## 2. Codex CLI bridge (default)

For each job the bridge runs, headlessly:

```text
codex exec --json --skip-git-repo-check --ephemeral --ignore-user-config -s read-only
           -c model_reasoning_effort="low" -C <tmp> [-i ref1 -i ref2 …]   < relay prompt
```

The relay prompt tells Codex to call its built-in image tool exactly once with the given prompt
verbatim, passing the attached images as references, with the requested shape (and transparency).
Codex saves the result under `$CODEX_HOME/generated_images/<thread-id>/`; the bridge copies the
newest file to the job's `out` path. It uses the user's ChatGPT login (no API key) and counts
against their ChatGPT image allowance.

- Binary discovery: `PPT_STUDIO_CODEX`, then the Codex CLI bundled in `ChatGPT.app` / `Codex.app`,
  then `codex` on `PATH`. A broken shim on `PATH` is skipped automatically.
- `--ignore-user-config` keeps the user's MCP servers and plugins from starting on every call;
  set `PPT_STUDIO_CODEX_USER_CONFIG=1` to use their config (for example a custom provider).
- `--ephemeral` keeps these relay sessions out of the user's Codex history. Generated originals stay
  in `$CODEX_HOME/generated_images`; `PPT_STUDIO_CODEX_CLEANUP=1` deletes each one after copying.
- Extra flags: `PPT_STUDIO_CODEX_ARGS="…"`.
- Typical results: about 45–75 s per image; 16:9 returns 1672×941, 1:1 about 1254×1254,
  2:3 1024×1536; transparent requests return RGBA PNGs.

## 3. OpenAI and Gemini APIs

Used automatically when Codex is unavailable and a key is set, or forced with
`--backend openai|gemini` / `PPT_STUDIO_IMAGE_BACKEND`.

| Backend | Key | Model (override) | Notes |
| --- | --- | --- | --- |
| openai | `OPENAI_API_KEY` (`OPENAI_BASE_URL` for proxies) | `gpt-image-2` (`PPT_STUDIO_OPENAI_MODEL`) | references go through `/images/edits`; sizes per aspect, e.g. 16:9 → 2048×1152; `PPT_STUDIO_OPENAI_QUALITY` (default high) |
| gemini | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | `gemini-3-pro-image-preview` (`PPT_STUDIO_GEMINI_MODEL`) | aspect via `imageConfig`; `PPT_STUDIO_GEMINI_SIZE` (default 2K); transparency emulated with a green key removed locally |

These two paths are implemented against the public APIs but were not exercised on the machine
where the skill was built; test with `ppt imagegen gen --prompt "…" --out /tmp/x.png --dry-run`
first, then one real image.

## 4. Jobs and results

```bash
ppt imagegen batch assets/jobs.json                 # all missing artwork, 4 at a time
ppt imagegen batch assets/jobs.json --only hero,desk # a subset
ppt imagegen batch assets/jobs.json --force --only s07-street   # regenerate one
ppt imagegen gen --prompt-file prompts.md#hero --out assets/hero.png --aspect 16:9
```

- Paths in a jobs file resolve against the deck root.
- `prompt_file` may point into a multi-prompt file with `file.md#section` (`## section`).
- Each job: `id`, `out`, `prompt_file` or `prompt`, optional `refs`, `aspect` (default 16:9),
  `transparent`, `kind` (`asset`, also the default; prompts are linted for text-artifact
  phrasing), `timeout`. `defaults` apply to every job.
- Optional `refs` / `--ref` inputs are existing subject assets for identity or image editing.
  They are not style boards or whole-slide layouts. Inspect local inputs before using them.
- Results accumulate in `<jobs>.results.json` (size, alpha, seconds, errors, warnings).
- Semantics are all-settled: every job runs; failures are listed at the end. Transient failures
  retry once automatically; refusals and config errors do not.
- Concurrency: `--concurrency N` or `PPT_STUDIO_CONCURRENCY` (default 4). Timeout per image:
  `PPT_STUDIO_TIMEOUT` (default 900 s).

## 5. Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `Codex CLI not found` | install the Codex CLI or ChatGPT desktop app, or set `PPT_STUDIO_CODEX` |
| `codex produced no image … agent: …` | read the agent text: not logged in (`codex login`), quota or rate limit (wait, lower concurrency), or a refusal |
| `[refused]` | the prompt tripped a policy; remove real people's names, brands, trademarks or sensitive content; retry that job once |
| hangs at start | the CLI waits for stdin; the bridge closes it — if you call `codex exec` yourself, redirect `< /dev/null` |
| wrong aspect returned | expected occasionally; crop with `object-fit` or `ppt img fit`, regenerate only if the crop loses the subject |
| transparency missing | `ppt img key SRC -o OUT` (flat background), then `ppt img trim` |
| many timeouts | lower concurrency to 2; check network |
