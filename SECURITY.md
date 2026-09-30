# Security policy

## Reporting a vulnerability

Use **GitHub's private vulnerability reporting** on this repository:
*Security* → *Report a vulnerability*. Please do not open a public issue for
anything exploitable.

> The maintainer has to enable private reporting in *Settings → Code security →
> Security advisories* for that link to open a submission form. If it is off, the
> page will say so rather than silently failing — in that case open an issue that
> describes the class of problem with the exploit details redacted, and ask for a
> private channel.

This is a single-maintainer project with no support SLA. If a report is valid you
will be credited in the fix unless you would rather not be.

There is deliberately no email address here. This file has never carried one,
because an address that is never monitored is worse than no address at all: it
turns a report into a silent loss. If a monitored channel is added later, it will
be added here and nowhere else.

## What this tool reads

`atlas scan` walks the roots in `config/roots.json` and reads skill and agent files
to measure them. It is a local, read-only tool: it has no network client, no
database of its own, and no authentication surface, because it is not a service and
there is nothing to authenticate to.

The default roots are inside your home directory. The census needs **no environment
variables and no credentials** — every path comes from `config/roots.json`, and a
missing `settings.json` is treated as an empty configuration rather than an error.

## The real risk: publishing the report

The rendered report is a single self-contained HTML file, and that is deliberate —
it is mailable, openable offline, and publishable as an artifact. It is also a
description of your environment. Before you publish one, know what is in it:

- **Skill names and descriptions.** Enough to fingerprint which skills, plugins and
  vault collections you run, and therefore a good deal about your tooling.
- **Category and family names.** Your `config/taxonomy.json` is a description of how
  you have organised your work, and it renders as-is.
- **Bundle shape.** File counts, sizes and directory layout per skill, which is
  enough to recognise a specific installation.
- **Run history.** Diff and trend views carry timestamps and score movement across
  runs, which is a low-bandwidth way to infer when you were reworking things.

Absolute filesystem paths are *not* in the report: identity is stored by realpath
in `data/skill-keys.json`, and that sidecar is written to disk precisely so the
paths stay out of the rendered page. That protection applies to
`dist/skill-atlas.html` only. `data/skills.json` and the sidecar both contain
absolute paths, so publish `dist/`, not `data/`.

If any of that is not yours to publish, do not publish the file. Generate a report
against a throwaway `HOME` instead: point the config at a directory of synthetic
skills and render from there.

## The optional Grafana mirror

`atlas.py build` will publish run history to Postgres when `ATLAS_PG_DSN` is set,
and is a silent no-op when it is not. If you enable it:

- Keep the DSN out of the repo. `grafana/db.env` and `grafana/*.pw` are gitignored
  for this, and `ATLAS_PG_DSN` in your shell is better still.
- `bin/load_grafana.py` reads `psycopg2`, which honours `~/.pgpass` for a password it
  is not given. Nothing in this repository manages that file; if you rely on it, it
  is your own `0600` file to maintain.
- The HTML report is the source of truth; the database is a mirror. A publish failure
  is reported as a warning and never fails the build, so a broken mirror cannot
  corrupt a census.

## The router stage

The optional router stage executes a JavaScript file — the `skill-router` index
builder — at a path you configure. That is code execution by design, from a path in
your own config file. Treat `router_lib` as a trust decision: point it at code you
have read. The stage is skipped entirely, with a note, when the path is absent.

## Out of scope

Do not expose a rendered report to an untrusted network expecting it to be safe, and
do not treat the report as a system of record for anything. It is a snapshot of one
scan of one filesystem, and it goes stale the moment the filesystem does.
