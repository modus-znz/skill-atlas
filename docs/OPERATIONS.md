# Operations

Running the census. The short version: it is a read-only walk of your own
`~/.claude`, it writes only into this repository, and re-running it is the
normal way to use it.

## First run

The census points at one machine, so this step is mandatory:

```bash
$EDITOR config/roots.json
```

Four roots, each with its own symlink policy:

| Source | Default path | Symlinks | Why |
|---|---|---|---|
| `active` | `~/.claude/skills` | followed | Your real skills, possibly linked from elsewhere |
| `vault` | `~/.claude/skill-vault` | not followed | A vendored copy; a loop here is plausible |
| `plugin` | `~/.claude/plugins/cache` | not followed | Content-addressed; symlinks are not identity |
| `agent` | `~/.claude/agents` | not followed | Flat `<slug>.md` files, not skill directories |

Remove a root you do not have. A missing root is skipped, not an error.

Then:

```bash
python3 atlas.py all
open dist/skill-atlas.html
```

## Verify a run

```bash
$ python3 atlas.py doctor     # rubric drift and stale narrative
$ python3 atlas.py            # the CLI itself runs
```

`build` prints the numbers the report then quotes, so compare them against the
headline figures in the HTML (illustrative figures — yours will differ):

```
build: 431 skills, 62 category nodes, 96,218 B
  listing 2,940 tok/session over 24 entries
  grades  38 A · 211 B · 96 C · 12 D
```

A surprising grade distribution is usually a **rubric** problem, not a data
problem — `doctor` exists for exactly this, because a rubric that no longer
discriminates produces a flat distribution that looks like data.

## Common failures

| Symptom | Likely cause | Action |
|---|---|---|
| `build: stale router index` | `data/router-index.json` is older than the skills it describes | `python3 atlas.py reach`, or `build --force` to accept the stale index and record that you did |
| `diff: need two runs, have 0` | Fewer than two snapshots in `data/runs/` | Run `atlas all` again after a real change; a diff between two identical runs is not a trend |
| `node: command not found` on `reach` | `node` is not on `PATH` | The `reach` stage needs it. Skip it and use `build --force` with a hand-made index, or install Node. |
| `doctor: no scan yet` | `scan` has not run | `python3 atlas.py scan` |
| Report is empty or has no categories | `roots.json` points at directories that do not exist | Check the paths with `ls`; a typo'd `~` expands silently |
| Every grade is D | The rubric moved, or the roots point at a cache rather than your active skills | `doctor` first, then confirm the roots are the ones you meant |
| `scan` seems to hang | It is walking a large plugin cache with no progress output | Expected on a cold run over thousands of bundles. Wait; there is no partial output until the stage completes. |
| A skill you installed is missing | Its bundle has no `name:` in frontmatter, or the directory is not one of the four roots | Check the frontmatter; agents are matched by `name:` for the same reason |
| A skill appears twice | Two copies exist and are both latest | The report marks one as a phantom shadow when realpaths resolve; check `dup_copies` |
| `grafana publish skipped: …` | Mirror configured but unreachable | Expected to be non-fatal. The HTML report is unaffected — fix the DSN or remove the config. |
| `FileNotFoundError` in `load_run` | A snapshot directory was pruned | Use timestamps that still exist in `data/runs/` |

## Data and state

| Path | Role | Safe to delete? |
|---|---|---|
| `data/skills.json` | `scan` output | Yes, regenerated |
| `data/router-index.json` | `reach` output | Yes, regenerated — but `build` then needs `--force` |
| `data/report-data.json` | The payload the report embeds | Yes, regenerated |
| `data/skill-keys.json` | Identity sidecar; must stay index-aligned with the payload | Yes — but see below |
| `data/runs/` | One snapshot per build, the input to `diff` | Only if you accept losing the trend |
| `dist/skill-atlas.html` | The report | Yes, regenerated |

**Do not delete `skill-keys.json` on its own while keeping
`report-data.json`.** The sidecar is a list index-aligned with
`payload["skills"]`; if the two disagree in length or order, `diff` reports
wrong results rather than failing. `build` writes both, so regenerate both by
running `build`.

Prune `data/runs/` when it grows. Each snapshot is a full `report-data.json`, so
this is the only directory that accumulates without bound.

## Backups

There is nothing to back up. Every artefact under `data/` and `dist/` is derived
from `config/` plus a filesystem walk, and the source of truth for the census is
the machine it describes. If you want to keep a trend, copy `data/runs/`.

## The optional Grafana mirror

Off unless configured. It publishes run history so the census can be charted
over time.

```bash
psql -f grafana/schema.sql                     # once
printf 'ATLAS_PG_DSN=postgresql://atlas_writer@127.0.0.1:5432/skill_atlas\n' \
  > grafana/db.env
chmod 600 grafana/db.env                        # the writer password goes in ~/.pgpass
python3 atlas.py build                          # publishes if the file exists
```

A publish failure is caught, reported as `grafana publish skipped: …` on stderr,
and **does not fail the build**. That is deliberate: the HTML report is the
source of truth and a mirror must not be able to break it. If you rely on
Grafana, check the exit status and the stderr line rather than assuming success.

## Automation

A weekly cron is the intended cadence, and the snapshot is what makes it useful:

```cron
17 4 * * 1  cd ~/src/skill-atlas && python3 atlas.py all >> ~/Library/Logs/skill-atlas.log 2>&1
```

`atlas all` is idempotent — each stage overwrites its own file — so a cron job
that fires while you are mid-install will just measure whatever is on disk at
that moment. If that matters, the run will be wrong in an interesting way and
worth re-running.

## Safety posture

- **`scan` never reads file bodies.** It parses frontmatter and `stat()`s. It
  walks `~/.claude`, which contains settings and private work, and the point of
  the design is that pointing this at a real machine is safe.
- Symlinks are followed for `active` only, and never for the vault, the plugin
  cache or the agent roster.
- Nothing outside this repository is written. No network access except the
  optional Postgres mirror.
- CI enforces that no path is hardcoded outside `atlas/config.py`, so a stray
  absolute path cannot quietly make the census measure the wrong machine.

## Escalation

Bugs, rubric disagreements, and correction requests: open an issue with the
`build` output and the relevant `config/*.json` excerpt. A rubric change is a
deliberate act — say what the new threshold is for, because it invalidates
comparison with every previous run.
