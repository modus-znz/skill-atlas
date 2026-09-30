# Architecture

Skill Atlas is a four-stage pipeline that turns a filesystem walk into a single
self-contained HTML report. Each stage writes exactly one file, reads only what
the previous stage wrote, and can be re-run alone — which is what makes a failure
attributable to a stage rather than to "the tool".

## The shape, in one paragraph

`scan` walks the four configured roots, parses each bundle's frontmatter with a
minimal reader, and measures it with `stat()`. `reach` asks the skill-router for
its own index rather than reimplementing it, and classifies each bundle into one
of six reachability states using `settings.json`. `build` scores every bundle
against the rubric, resolves the taxonomy path, resolves shadowed duplicates by
realpath, assembles the payload, and computes every metric the narrative is
allowed to quote — in one function. `render` composes a template with the
narrative and the payload into a single HTML file. Every build is snapshotted so
`diff` and `doctor` can compare runs.

```
  config/roots.json ─┐
  config/rubric.json├─► scan ──► data/skills.json        (one row per bundle)
  config/taxonomy.json│
                     └─► reach ──► data/router-index.json (router's own truth)
                              │
                              ▼
                         build ──► data/report-data.json   (payload + metrics)
                                 └─► data/skill-keys.json   (identity sidecar)
                              │
                              ▼
                        render ──► dist/skill-atlas.html   (one file, no server)
```

## Layers and boundaries

| Layer | Owns | Must not know about |
|---|---|---|
| `atlas.py` | Stage dispatch, KPI printing, the optional Grafana mirror | What a stage does internally |
| `atlas/config.py` | Every path and every config file | Anything but `config/*.json` |
| `atlas/scan.py` | The filesystem walk, frontmatter, bundle measurement | The rubric, the taxonomy, the renderer |
| `atlas/reach.py` | The six-state classification | Where a bundle lives on disk |
| `atlas/score.py` | Applying the rubric to one bundle | How the rubric is stored |
| `atlas/taxonomy.py` | Deriving a category path | Scoring |
| `atlas/dataset.py` | Payload assembly, shadow resolution, **all metrics** | Rendering or narrative |
| `atlas/tables.py` | Tabulation | Where the numbers came from |
| `atlas/diffs.py` | Comparing two run snapshots | How a snapshot was made |
| `atlas/render.py` | Composing template + content + data | How metrics are computed |
| `atlas/content.py` | The narrative prose | The filesystem |

The load-bearing boundary is **one function owns every number**
(`dataset.metrics()`). The report is a data visualisation with prose attached,
and its characteristic failure is a sentence that quotes a figure the data no
longer supports. Splitting metric computation across modules makes that failure
likely; centralising it makes it structurally hard.

## State

| Path | Role | Lifetime |
|---|---|---|
| `data/skills.json` | One row per bundle found by `scan` | Overwritten each scan |
| `data/router-index.json` | The skill-router's own index | Overwritten each `reach` |
| `data/report-data.json` | The rendered payload plus metrics | Overwritten each `build` |
| `data/skill-keys.json` | Realpath per row, index-aligned with the payload | Overwritten each `build` |
| `data/runs/<timestamp>/` | Full snapshot per build | Append-only; the input to `diff` |
| `dist/skill-atlas.html` | The report | Overwritten each `render` |

Nothing here is precious. Every file is a derived artefact except the
snapshots, and the snapshots are only interesting as a trend. Deleting `data/`
loses history, not capability.

## Key decisions

### Decision: every metric computed in exactly one function

**Context.** The report contains prose that quotes numbers. A census that quotes
a number from anywhere other than its own data will eventually quote a stale
one, and a stale number in a confident sentence is worse than no number.

**Chosen.** `dataset.metrics()` is the only place a number is produced. Content
and tables read the payload; they never recompute.

**Rejected.** Computing at render time, which is the obvious place to reach for.

**Cost accepted.** One long function with a wide signature. The compensating
control is that it is *one* function, so there is exactly one place to look, and
`doctor` exists to cross-check the narrative against it.

### Decision: the rubric lives in config

**Context.** The scoring is an editorial position — that 60–400 characters is a
good description and over 700 is bloated. That position will be revised.

**Chosen.** `config/rubric.json` holds every threshold and weight. `score.py`
reads it and contains no numbers.

**Rejected.** Hardcoded thresholds in `score.py`.

**Cost accepted.** A retune is a config diff rather than a code change, which
means it can be made casually. The rubric header notes that scores were ported
verbatim from a predecessor specifically to preserve comparability with the
stored baseline, and any retune invalidates that. This is why CI asserts the
weights still sum to 100.

### Decision: identity is a realpath sidecar

**Context.** A diff needs a stable key per skill. `name|source` collapses a large
share of rows as soon as two collections vendor the same skill name, and
name-plus-treepath still collapses some. A lossy key makes the diff *silently
drop skills it should be reporting*.

**Chosen.** `realpath`, written to `data/skill-keys.json` as a list index-aligned
with `payload["skills"]`. Held outside the payload so the rendered page does not
carry about 100 KB of filesystem paths.

**Rejected.** Composite name keys inside the payload, for simplicity.

**Cost accepted.** An invariant that is not self-enforcing: the sidecar and the
payload must stay the same length and in the same order. A mismatch produces a
diff that is wrong rather than an error.

### Decision: one keyspace per diff pair

**Context.** A run recorded before the sidecar existed has no realpath keys. If
one side of a comparison is indexed by realpath and the other by name, the two
keyspaces are disjoint and every key mismatches — the diff reports "everything
added, everything removed" as though it were a finding.

**Chosen.** `_index_pair` picks the scheme once for the pair: exact if *both*
payloads carry the sidecar, lossy if either does not.

**Rejected.** Choosing per payload, which is the natural implementation and
produces exactly the degenerate case above.

**Cost accepted.** Degrading both sides together loses three ambiguous rows.
Degrading one side loses the entire comparison, so the smaller loss was chosen.

### Decision: agents are censused but unscored

**Context.** Agents are resident subagents, dispatched by type. They have real
byte and token cost, so they belong in the census. But they have no
frontmatter-derived description in the same shape as a skill, so the rubric does
not apply to them.

**Chosen.** Agent rows appear in `skills[]` with a `None` score and grade. They
count toward totals, category membership and cost. Every grade aggregate filters
to scored rows only.

**Rejected.** Omitting them from the census, which would understate the true
cost of a machine's configuration.

**Cost accepted.** A nullable grade in the payload, and a discipline in
`metrics()` where the mistake of dividing by `n` instead of `scn` would halve the
average of any category that ever mixes scored and unscored rows.

### Decision: read frontmatter, never contents

**Context.** The tool is pointed at a real machine's `~/.claude`, which contains
settings, credentials-adjacent files and private work.

**Chosen.** `scan` parses frontmatter and reads `stat()` metadata. It never opens
a file for its body. `dirstats` walks with `os.stat` and skips symlinks.

**Rejected.** Reading SKILL.md bodies to measure quality, which would give better
scores.

**Cost accepted.** Bundle "depth" is bytes and subdirectory names, not
comprehension. A large bundle of generated files scores as depth it has not
earned. This is stated in the README's limitations because the alternative is a
tool that is unsafe to point at a real machine.

### Decision: the reach stage asks, it does not guess

**Context.** Reachability is a property of the router's index, not of the
filesystem. A directory existing does not mean a skill is reachable.

**Chosen.** `atlas/reach.py` classifies from `settings.json`, and the
`router_index.json` stage shells out to `bin/router_index.mjs`, which imports the
skill-router's own library.

**Rejected.** Reimplementing the index in Python.

**Cost accepted.** A `node` dependency for one stage, and a `build` that refuses
in strict mode when the index is stale. `--force` accepts a stale index and the
run records that it did.

## The flow, end to end

Running `atlas.py all`:

1. `scan` loads `config/roots.json`, expands `~` in every path, and walks each
   root. Active skills follow symlinks; the vault, plugin cache and agent roster
   do not, because a symlink loop in a cache is a real failure mode.
2. For each bundle it reads the first few KB, extracts frontmatter with
   `parse_frontmatter`, and measures files, bytes, first-level subdirectories and
   newest/oldest mtime with `dirstats`.
3. Only the newest version per skill is kept, with semver sorting above
   content-hash directories so a tagged release beats a hash-named copy.
4. `score.py` applies the rubric, producing a score and a grade band.
5. `reach` runs `node bin/router_index.mjs`, then `classify` maps each row to one
   of six states from `skillOverrides` and `enabledPlugins`.
6. `build` loads both files, filters to latest, resolves shadowed duplicates by
   comparing `os.path.realpath` of the router's winner against the entry's own
   path — a match means the entry is a phantom, not a genuine second copy.
7. The taxonomy assigns each row a category path; `build` walks those paths to
   construct the category tree, accumulating count, tokens, bytes, reach mix and
   the average over *scored* rows only.
8. `metrics()` computes every headline number, `report-data.json` and
   `skill-keys.json` are written, and the run is snapshotted into `data/runs/`.
9. `_publish_grafana` fires only if `ATLAS_PG_DSN` is set or `grafana/db.env`
   exists. Any exception is caught and reported as skipped: a mirror must not be
   able to break a build.
10. `render` composes `templates/atlas.html.tpl` with the narrative and the
    payload into `dist/skill-atlas.html`.

## Known weaknesses

- **`score_one` has no per-dimension fixture.** The suite runs the pipeline
  end-to-end against a synthetic `HOME` and covers the taxonomy, tables,
  interpolation and optional-input handling, but each rubric band is only
  exercised through whole-skill runs. The `keyspaces` invariant is verified for
  the identity sidecar's index alignment, not for scoring keyspaces.
- **The sidecar alignment invariant is silent.** A length or order mismatch
  produces a wrong diff, not an exception.
- **Bundle weight is bytes.** Generated files score as depth.
- **Frontmatter parsing is minimal.** Nested or list-valued fields are read as
  strings, so a skill with structured metadata may be scored on a misread.
- **Freshness is mtime.** A never-edited bundle looks stale whether or not it is
  abandoned, and an actively edited one looks fresh however broken it is.
- **Single machine.** `roots.json` describes one `~`; there is no cross-host
  aggregation.
- **The `scan` walk is the slow part and has no progress output.** On a large
  plugin cache this is a long silent wait, which reads as a hang.
