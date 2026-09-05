# Skill Atlas

A re-runnable census of the Claude Code skill ecosystem on this machine — every
`SKILL.md` across the active library, the skill vault, and the plugin cache — scored,
categorised, costed, and rendered to a single self-contained HTML report.

It began life as a one-off 584 KB artifact whose generator lived in an ephemeral `/tmp`
scratchpad. This is that pipeline rescued, de-hardcoded, and given the one thing it
lacked: a way to re-run without the report quietly starting to lie.

## Usage

```bash
python3 atlas.py all        # scan -> reach -> build -> render
python3 atlas.py doctor     # problems (exit 1) vs notices (exit 0)
python3 atlas.py diff       # what moved since the previous run
open dist/skill-atlas.html
```

Individual stages: `scan`, `reach`, `build`, `render`.

Requirements: Python 3 stdlib only, plus `node` for the one router stage.
No packages to install.

## How it works

```
scan    walk 3 roots, parse frontmatter, dedupe, score   -> data/skills.json
reach   ask skill-router/lib.mjs who wins each bare name -> data/router-index.json
build   category tree + rollups + metrics + snapshot     -> data/report-data.json
                                                         +  data/skill-keys.json
render  template + content/ + data                       -> dist/skill-atlas.html
```

## The measured/authored seam

The report is two layers, and keeping them apart is the whole point.

**Measured** — everything under `data/`, regenerated on every run. Never hand-edited.

**Authored** — `content/*.html`, the nine findings and the analysis. Hand-written, and
kept honest by two mechanisms:

```html
---
id: overview
asserted_on: 2026-09-04
assert: {vault: 693, active: 149}
---
<p>The real number is <b>{{ metrics.total }} distinct skills</b>…</p>
```

- `{{ metrics.x }}` is interpolated at render time. A number written this way **cannot**
  drift, because the number is not stored in the prose.
- `assert:` names the facts a passage *depends on*. Each is re-checked against the fresh
  scan; a mismatch renders an inline "written 2026-09-04, when vault was 693, now 1,819"
  badge and warns at build time.

The original template carried `<s>4,210</s> 4,312` typed by hand — a correction someone
had to *notice* and edit in. That is exactly the step that stops happening. Here the KPI
strikethroughs are derived from the previous run in `data/runs/`, and stale analysis
announces itself.

## Drift surfaces instead of hiding

The original `family()` classifier fell through to `return "Design aesthetics"`, so every
skill added after it was written would have been silently misfiled. Here the fallthrough
is an explicit `Unclassified` bucket that `atlas.py doctor` reports and exits non-zero on.
The curated name lists live in `config/taxonomy.json` — config, not code, so a
reclassification shows up in `git diff`.

`atlas.py build` also refuses to run when `data/router-index.json` is older than
`data/skills.json`. Nothing wrote that file before (the old `verify.mjs` only printed), so
it went stale silently while reachability numbers were computed from it anyway.

## Configuration

| File | Holds |
|---|---|
| `config/roots.json` | scan roots, skip lists, token ratio, listing budget |
| `config/rubric.json` | the 100-point weights and A/B/C/D thresholds |
| `config/taxonomy.json` | curated family name-sets + the `Unclassified` bucket |
| `config/kpis.json` | which metrics appear in the KPI strip |

## Privacy

`data/` and `dist/` are gitignored. The dataset embeds descriptions of ~1,800 vault
skills (source-available, redistribution-restricted) and `settings.json`-derived
configuration. Only the generator, template, and hand-written content are tracked.
The scanner reads frontmatter and `stat()` metadata only — it never copies the contents
of a secret, key, or environment file it walks past.

## Not a goal: reproducing 951

The published artifact counted 951 distinct skills on 2026-09-04. This pipeline currently
reports 2,075 — the vault grew 693 → 1,819. A fresh scan *should* differ; `atlas.py diff`
exists to explain the delta. Success is "renders, and the change is accounted for", never
"byte-matches the artifact".

## Two things worth knowing

**`doctor` separates problems from notices.** A problem is drift the pipeline
cannot render around — an unclassified skill has no home in the tree, a stale
taxonomy entry names a skill that is gone, a stale router index makes
reachability a lie. Those exit 1. A *notice* is stale narrative: a paragraph
written on 2026-09-04 describing that day's census is correct about the past,
and the report already badges it inline. Failing the build on it would make
every historical passage a permanent error and train everyone to ignore the
exit code, so notices report and exit 0.

**Skill identity lives outside the payload.** `name|source` collapses 92 of
2,075 rows — seven vault collections each ship an `xlsx-author` — and even
name-plus-treepath still collapses three. So `build` writes an index-aligned
`data/skill-keys.json` of realpaths beside `report-data.json`, and `snapshot`
copies it into each run. `atlas.py diff` keys on it and is therefore exact;
runs recorded without it fall back to the lossy key so they still diff at all.
Keeping ~100 KB of absolute paths out of `report-data.json` also keeps them off
the rendered page, which matters because that page embeds vault descriptions
already (see Privacy).
