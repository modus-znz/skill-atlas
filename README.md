<div align="center">

# skill-atlas

**A re-runnable census of the Claude Code skill ecosystem: what is installed, what the model can actually reach, and what it costs per session.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB.svg)](atlas/config.py)
[![Deps](https://img.shields.io/badge/dependencies-stdlib%20only-success.svg)](atlas/config.py)
[![Rubric](https://img.shields.io/badge/rubric-100%20points%2C%20in%20config-informational.svg)](config/rubric.json)
[![Status: active](https://img.shields.io/badge/status-active-informational.svg)](#limitations)

`modus-znz/skill-atlas` · Python · MIT

</div>

---

## Contents

- [The problem](#the-problem)
- [What it does](#what-it-does)
- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [Usage](#usage)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment and operations](#deployment-and-operations)
- [Design decisions and trade-offs](#design-decisions-and-trade-offs)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## The problem

A skill library grows by accretion. Something gets installed, a plugin cache
fills up, a vault is copied in from somewhere, and a few months later nobody can
answer basic questions about it. Which of these 2,000 directories does the
model actually see? How many tokens does the session listing bill every single
conversation? Which entries are shadowed by a duplicate that a realpath
comparison would resolve and a name comparison would not? Which plugin is
present in the cache but named nowhere in settings, so it is neither on nor off?

Answering those by hand means walking several directory trees and reading
`settings.json`, and the answer is stale the moment anything changes. The
ecosystem does not need a report once. It needs a census that can be re-run and
diffed, where every number in the narrative is computed in one place so the
prose and the data cannot disagree.

## What it does

| Capability | Notes |
|---|---|
| Filesystem census | Walks active skills, the vault, the plugin cache and the agent roster; parses frontmatter with a minimal reader |
| Reachability classification | Six states derived from `settings.json`, not guessed from directory names |
| 100-point rubric | Reachability, description quality, bundle depth, body weight, freshness, hygiene — every threshold in `config/rubric.json` |
| Cost accounting | Listing tokens billed per session, versus tokens a visibility change would avoid |
| Category tree | Taxonomy-built tree with per-node aggregates, so averages are statements about a *category* |
| Shadow resolution | Duplicate detection by realpath, so a shadowed entry is distinguished from a genuine one |
| Run-to-run diffs | Added, removed, regraded, re-reached skills, plus every metric that moved |
| Self-diagnosis | `doctor` reports rubric drift and narrative that has gone stale |
| Single-file HTML report | One `dist/skill-atlas.html`, no server, no build step |
| Optional Grafana mirror | Pushes run history to Postgres when a DSN is configured; silent no-op otherwise |

## Quickstart

Python 3 standard library only. `node` is needed for the `reach` stage, because
that stage asks the skill-router itself rather than reimplementing its index.

```bash
git clone https://github.com/modus-znz/skill-atlas.git
cd skill-atlas

# Point the census at your own machine first — this is the only step required.
$EDITOR config/roots.json

python3 atlas.py all      # scan -> reach -> build -> render
open dist/skill-atlas.html
```

`config/roots.json` is the single source of what gets walked. Nothing in the
code hardcodes a path.

## Architecture

Four stages, each writing one file, so a stage can be re-run alone and a
failure is attributable:

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

Every run is snapshotted into `data/runs/`, which is what makes `diff` and
`doctor` possible.

### Components

| Component | Responsibility | Knows about |
|---|---|---|
| `atlas.py` | Stage dispatch, KPI output, the Grafana mirror | The stages, not their internals |
| `atlas/config.py` | Path and config resolution. Nothing else holds a path. | `config/*.json` |
| `atlas/scan.py` | Walks roots, parses frontmatter, measures bundles | The filesystem, and nothing else in the project |
| `atlas/reach.py` | Six-state reachability from `settings.json` | The settings schema |
| `atlas/score.py` | Applies the rubric to one skill | `config/rubric.json` only |
| `atlas/taxonomy.py` | Builds the category path for a skill | `config/taxonomy.json` |
| `atlas/dataset.py` | Assembles the payload, computes every metric | All of the above |
| `atlas/tables.py` | Tabulation for the report | The payload |
| `atlas/diffs.py` | Compares two runs | Run snapshots |
| `atlas/render.py` | Composes template + content + data | The template |
| `atlas/content.py` | The narrative | The metrics |
| `bin/router_index.mjs` | Asks skill-router for reachability truth | The router library |

## Usage

```bash
$ python3 atlas.py

Skill Atlas — a re-runnable census of the Claude Code skill ecosystem.

  atlas.py scan      walk the roots, parse frontmatter, score        -> data/skills.json
  atlas.py reach     ask the skill-router for reachability truth     -> data/router-index.json
  atlas.py build     assemble the dataset + snapshot the run         -> data/report-data.json
  atlas.py render    compose template + content + data               -> dist/skill-atlas.html
  atlas.py all       scan -> reach -> build -> render
  atlas.py diff      explain what moved between the last two runs
  atlas.py doctor    report classification drift and stale narrative

Python 3 stdlib only, plus the `node` already on this machine for the router stage.
```

Run stages individually when debugging, and note the two that have real state
preconditions:

```bash
$ python3 atlas.py doctor
doctor: no scan yet. Run `atlas.py scan`.

$ python3 atlas.py diff
diff: need two runs, have 0. Run `atlas all` again later.
```

A successful `build` prints the counts that the report's narrative then quotes
(illustrative figures — yours will differ):

```
build: 431 skills, 62 category nodes, 96,218 B
  listing 2,940 tok/session over 24 entries
  grades  38 A · 211 B · 96 C · 12 D
```

`diff` compares the last two snapshots by default, and takes explicit
timestamps to compare any pair:

```bash
python3 atlas.py diff                        # last two runs
python3 atlas.py diff 2026-03-02 2026-03-19  # any two stored run ids
```

## Configuration

Three JSON files under `config/`. No environment variables, no CLI flags worth
remembering.

| File | Holds |
|---|---|
| `config/roots.json` | The four scan roots, skip dirs, depth subdirs, chars-per-token, listing budget |
| `config/rubric.json` | The 100-point rubric: every threshold and weight |
| `config/taxonomy.json` | The category tree and how a skill's path is derived |

The rubric is worth reading, because it is the argument the report is making:

| Dimension | Points | Rationale encoded in the weights |
|---|---|---|
| Reachability | 25 | An unreachable skill scores nothing regardless of quality |
| Description quality | 25 | 60–400 characters is the useful band; over 700 is penalised as bloated |
| Bundle depth | 15 | 5 points per real subdirectory (`references`, `scripts`, `assets`, `examples`, `templates`) |
| Body weight | 15 | 400–12,000 characters; thin and bloated are both wrong |
| Freshness | 10 | Under 60 days scores full, over 300 scores 2 |
| Hygiene | 10 | Penalty for duplicate copies and name collisions |

Grades are A ≥ 82, B ≥ 70, C ≥ 58, D ≥ 45.

Two constants in `config/roots.json` are worth knowing about:
`chars_per_token: 3.6` converts description characters into listing tokens, and
`listing_budget_chars: 24000` is `skillListingBudgetFraction` 0.04 of a 600k
context window.

## Testing

```bash
python3 -m unittest discover -s tests
python3 atlas.py doctor
```

The suite builds a throwaway `~` in a temp directory, points the real CLI at it,
and runs the whole pipeline. That is the case that matters for a census tool: the
machine it was written on is not the machine it runs on, so every test that can
express "a stranger clones this" does. Covered: a foreign `HOME`, absent
`settings.json`, an absent router, a stale router index, `doctor` staying green
without the optional router, both taxonomy family shapes, symlink cycles,
generated tables, and content interpolation.

`doctor` covers the failure mode unit tests cannot: a confidently wrong number in
a sentence. It checks that the rubric still discriminates, that narrative
assertions still hold, that the identity sidecar is index-aligned, and that the
ledger ribbon in `health.html` still agrees with the status tags below it.

## Deployment and operations

```bash
python3 atlas.py all && python3 -m http.server -d dist 8080
```

| Concern | How it is handled |
|---|---|
| Output | One `dist/skill-atlas.html`. No server, no CDN, no build step. |
| Idempotence | Each stage overwrites its own file. Re-running is the normal operation. |
| Snapshots | Every build appends to `data/runs/`, which is what `diff` reads. Prune when it grows. |
| Grafana mirror | Fires only if `ATLAS_PG_DSN` is set or `grafana/db.env` exists. A failure is a warning, never a build failure. |
| Cost of a run | One filesystem walk plus one `node` subprocess. `scan` never reads file *contents* beyond frontmatter and `stat()`. |

The mirror is a mirror. The report is the source of truth, and a failing publish
must never be able to break a build — so it is wrapped and reported as skipped.

## Design decisions and trade-offs

| Decision | Chosen | Rejected | Cost accepted |
|---|---|---|---|
| Every metric in one function | `dataset.metrics()` is the only place a number is computed | Computing metrics at render time | One large function, but prose and data cannot disagree — the point of the whole tool |
| Rubric in config, not code | `config/rubric.json` | Hardcoded thresholds | A retune is a config change, visible in git, with no code review |
| Identity by realpath | A `skill-keys.json` sidecar, index-aligned with the payload | `name\|source\|treepath` | The sidecar must stay index-aligned or diffs go wrong; a lossy key drops rows from every diff |
| One keyspace per diff pair | Both sides indexed with realpath when *both* carry it, else both with the lossy key | Per-payload key selection | A pre-sidecar run still diffs, at the cost of three ambiguous rows |
| Agents censused, not scored | Agent rows count toward totals and cost but carry no grade | Scoring them like skills | The payload needs a `None` grade, and every aggregate must filter to scored rows |
| Reachability from the router | Ask skill-router, do not reimplement it | Reimplementing the index in Python | A `node` dependency for one stage |
| Frontmatter read, contents not | Parse frontmatter and `stat()` only | Reading files to measure quality | Bundle weight is bytes, not comprehension — which is the honest claim anyway |
| Grafana optional | Fires only when configured; failures are warnings | Making the dashboard mandatory | A mirror can silently be stale, so the report is always the primary artefact |

### Why identity is a sidecar

`name|source` collapses a large share of rows as soon as two collections vendor
the same skill name, and name-plus-treepath still collapses some. A diff keyed on
either *silently drops skills it should be reporting*, which is the worst
possible failure for a change-tracking tool. Realpath is exact, so identity is
stored in `data/skill-keys.json`, index-aligned with the payload — which also
keeps absolute paths off the rendered page, which matters when that page is
published as a single-file artifact.

## Limitations

- **`score.py` is covered indirectly.** The suite asserts the pipeline, the
  taxonomy, the tables and content interpolation, but the per-dimension scoring
  arithmetic is exercised through whole-skill runs rather than as unit-level
  threshold fixtures. A change to `config/rubric.json` shifts every score
  silently and no test objects.
- **The census is per-machine.** `config/roots.json` points at one `~`. There is
  no aggregation across hosts, and no way to compare a second machine without
  merging the snapshots by hand.
- **`reach` needs `node` and a working skill-router.** Without it, `build`
  refuses in strict mode rather than guessing reachability. Use `build --force`
  to accept a stale index, which the run then records.
- **Bytes are not comprehension.** Bundle weight is `stat()` size. A large
  bundle of generated files scores as depth it has not earned.
- **Frontmatter parsing is minimal.** Flat keys and indented continuation lines.
  A list-valued or nested frontmatter field is read as a string, so a skill
  declaring structured metadata may be scored on a misread of it.
- **No reverse index.** The report answers "what is in this category", not "which
  skills reference this file".
- **Age is file mtime.** A bundle that was never edited since installation looks
  stale regardless of whether it is abandoned.

## Roadmap

- [ ] **Next** — per-dimension fixtures for `score.py`, so each rubric band is
      asserted at its threshold rather than only through whole-skill runs.
- [ ] **Next** — `doctor` gains a check for *narrative* numbers that no longer
      exist in `metrics()`, not just numbers that have gone stale.
- [ ] **Later** — merge two machines' runs into one census, keyed by
      `(host, realpath)`.
- [ ] **Later** — a reverse index for cross-skill file references.
- **Probably not** — scraping skill *content* to score quality. Reading the
  files this tool walks past is exactly the behaviour that makes a census tool
  unsafe to point at a real machine.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version:

1. Open an issue before anything larger than a bug fix, especially for rubric
   changes.
2. A rubric change is a config change plus a note in the commit message saying
   what the new threshold is for. Retuning the scoring silently invalidates
   comparison with every previous run.
3. Never make a stage read file *contents*. `scan` reads frontmatter and
   `stat()`; keeping it that way is what makes the tool safe to point at a real
   machine.
4. If you add a number the narrative can quote, compute it in
   `dataset.metrics()`. One place, so prose and data cannot drift.

## License

MIT — see [LICENSE](LICENSE).
