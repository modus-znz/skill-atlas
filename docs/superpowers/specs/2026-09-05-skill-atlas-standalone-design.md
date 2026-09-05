# Skill Atlas — Standalone System (Design)

**Date:** 2026-09-05
**Status:** Approved
**Supersedes:** the ad-hoc `scan.py` / `scan2.py` / `build.py` chain that lived in an
ephemeral `/tmp` scratchpad and produced the one-off `skill-atlas.html` artifact.

## 1. Problem

The Skill Atlas exists only as a 584 KB rendered HTML artifact. Its generator lived in
another Claude session's `/tmp` scratchpad — one reboot from unreconstructable. Three
structural defects make it unrunnable as-is:

1. **Ephemeral, hardcoded paths.** `build.py` hardcodes `BASE` to the `/tmp` scratchpad;
   `scan.py` / `scan2.py` hardcode `HOME`; `measure.py` carries its own 8-entry plugin
   path dict. Three copies of configuration, all embedded in code.

2. **Measured and authored layers are welded.** ~516 KB of the report is machine-measured
   (`report-data.json`); ~82 KB is hand-written narrative living inside the HTML template
   — nine findings, density verdicts, a 9-row upgrade queue. The template is *already*
   inconsistent with its own data: it carries hand-typed `<s>4,210</s> 4,312` strikethrough
   corrections and "Fixed 2026-09-04" badges describing work done after the scan that
   produced the surrounding numbers. Re-running today yields a report that lies.

3. **Silent classification drift.** `build.py`'s `family()` falls through to
   `return "Design aesthetics"`. Every skill added from now on is silently misfiled there.
   The rot has started: its `SECURITY` set still lists the four `*-with-strix` skills
   deleted 2026-09-05.

Additionally, `build.py` consumes `router-index.json` produced out-of-band. The rescued
`verify.mjs` only *prints* diagnostics — nothing in the chain writes that file, which is
how it went stale without any signal.

## 2. Goals / Non-goals

**Goals.** A re-runnable census of the Claude Code skill ecosystem across three roots that
(a) regenerates all measured data on demand, (b) preserves hand-written analysis as
editable content, (c) makes staleness in that analysis *visible* rather than silent,
(d) surfaces classification drift instead of hiding it, and (e) tracks change over time.

**Non-goals.** A served application, a database, live filtering against a backend, or any
runtime dependency beyond Python 3 stdlib and the `node` already on this machine. The
single-file HTML output is a feature — mailable, openable anywhere, publishable as an
artifact — and is preserved.

**Explicitly not a goal: reproducing 951.** The machine changed on 2026-09-05 (strix
deleted, ~21 S480b vault collections added). A fresh scan *should* differ. Success is
"renders, and `atlas diff` explains the delta", never "byte-matches the artifact".

## 3. Architecture

```
skill-atlas/
  atlas.py                 CLI: scan | reach | build | render | all | diff | doctor
  atlas/
    config.py              loads config/*.json; resolves all paths from project root
    scan.py                walks roots, parses frontmatter, dirstats, dedupes
    reach.py               settings.json -> skillOverrides/enabledPlugins -> reachability
    score.py               rubric -> score_parts {reach,desc,depth,body} + grade
    taxonomy.py            family classification + Unclassified drift reporting
    dataset.py             assembles report-data.json + path-prefix node rollups
    content.py             parses content/*.md frontmatter, interpolation, assertions
    render.py              template + content -> dist/skill-atlas.html
    diffs.py               compares two runs
  bin/router_index.mjs     node stage; imports skill-router lib.mjs, WRITES router-index.json
  config/roots.json        scan roots + home; no path hardcoded in code
  config/taxonomy.json     curated family name-sets (data, not code)
  config/rubric.json       100-pt weights + A/B/C/D thresholds
  content/                 AUTHORED layer, git-tracked, hand-edited
  templates/atlas.html.tpl layout + CSS + JS shell, zero baked prose
  data/                    GITIGNORED: skills.json, router-index.json, report-data.json,
                           runs/<timestamp>/
  dist/                    GITIGNORED: skill-atlas.html
```

**Data flow.** `scan` -> `data/skills.json`; `reach` (node) -> `data/router-index.json`;
`build` (scan + reach + config) -> `data/report-data.json` + `data/runs/<ts>/`;
`render` (report-data + content + template) -> `dist/skill-atlas.html`.

## 4. The measured/authored seam

Narrative moves out of the template into `content/*.md`. Each file carries frontmatter:

```markdown
---
id: shadowing
title: 77 skills were unreachable
asserted_on: 2026-09-04
assert: {unreachable: 0, vault_total: 693}
---
The router keyed skills by bare name, so {{ metrics.shadowed }} copies resolved
to a single winner.
```

Two mechanisms, deliberately distinct:

- **`{{ metrics.* }}` interpolation** — live values substituted at render time. Counts in
  prose can never drift from the data, because they are not stored in the prose.
- **`assert:` claims** — the facts a passage *depends on*. Each is checked against the
  fresh dataset at build time. A mismatch renders an inline badge ("written 2026-09-04,
  when vault_total was 693; now 708") and prints a build warning.

This is the core of the design. It replaces hand-typed strikethrough corrections with a
mechanism, so stale analysis becomes visible instead of silently false.

## 5. Drift and freshness gates

- `family()`'s fallthrough becomes an explicit `Unclassified` bucket. `atlas doctor`
  lists every unclassified skill as an actionable queue.
- `atlas doctor` also flags taxonomy entries naming skills no longer on disk (catching the
  stale strix entries).
- `atlas build` refuses to run when `data/router-index.json` is older than
  `data/skills.json`, rather than computing reachability from a stale index in silence.

## 6. Runs and diff

Every build snapshots the dataset to `data/runs/<timestamp>/report-data.json`.
`atlas diff` compares the two most recent runs and reports added/removed skills, grade
movements, reachability changes, and listing-cost delta. This is what converts a one-off
census into a trend instrument.

## 7. Security posture

`data/` and `dist/` are gitignored. The dataset embeds descriptions of ~693 vault skills
flagged source-available-with-redistribution-ban, plus `skillOverrides` / `enabledPlugins`
derived from `~/.claude/settings.json`. Only the generator, template and hand-written
content reach the private remote. The scanner reads frontmatter and directory statistics
only; it never copies credentials, and never emits the contents of any `.env`, `.jks`,
or secret file it encounters.

## 8. Acceptance criteria

1. `python3 atlas.py all` completes from a clean checkout with no `/tmp` dependency.
2. Rendered output is visually indistinguishable in structure from the published artifact.
3. Figures differ from the artifact's 951 only in ways `atlas diff` accounts for.
4. `atlas doctor` reports unclassified skills and stale taxonomy entries, and exits
   non-zero when either is non-empty.
5. No file under `data/` or `dist/` is git-tracked.
