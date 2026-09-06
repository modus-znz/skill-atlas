# Skill Atlas → Grafana

A live trend view of the atlas run history. The static HTML report is a snapshot;
this turns the 20+ timestamped runs under `data/runs/` into time-series panels —
grade mix drifting, token cost climbing, the agent-listing line appearing at the
exact run the fourth scan root landed.

Grafana is the mirror, never the source of truth: the report and `data/runs/` are
authoritative, and a publish failure never breaks `atlas.py build`.

## What's here

| File | Role |
|---|---|
| `schema.sql` | The `atlas.runs` table (JSONB metrics) + two roles: `grafana_ro` (read-only, Grafana's) and `atlas_writer` (the loader's). Idempotent. |
| `provisioning/datasources/skill-atlas.yaml` | Postgres datasource `skill-atlas-pg`. Password comes from `$SKILL_ATLAS_RO_PASSWORD` at startup — **no secret in this file**. |
| `provisioning/dashboards/skill-atlas.yaml` | Dashboard provider; loads the JSON below from disk (repo is source of truth, UI edits are not persisted). |
| `dashboards/skill-atlas-trends.json` | The dashboard: 5 stat panels + token cost, headroom, grade mix, census-by-root over time. |
| `db.env` | **Untracked (gitignored).** The loader's `atlas_writer` DSN. |

The loader is `../bin/load_grafana.py`, and `atlas.py build` calls it automatically
when a connection is configured (else silent no-op).

## Live instance

- **URL:** <http://localhost:3300> — dashboard **Skill Atlas → Trends** (uid `skill-atlas-trends`), folder *Skill Atlas*.
- Grafana v13.2.1, Debian package, bound to `127.0.0.1`. Admin credential is in `/etc/grafana/grafana.ini` (`admin_password`) and mirrored to `~/Desktop/CREDENTIALS.md`.
- Datasource reads as `grafana_ro`; the data is refreshed on every `atlas.py build`, or manually with `python3 bin/load_grafana.py`.

## Reproduce on a fresh box

```bash
# 1. database + schema + roles (passwords are yours to choose)
sudo -u postgres createdb skill_atlas
sudo -u postgres psql -d skill_atlas \
  -v grafana_pw="$(openssl rand -hex 16)" \
  -v writer_pw="$(openssl rand -hex 16)" \
  -f grafana/schema.sql
#   -> capture both passwords; put the writer one in grafana/db.env:
#      ATLAS_PG_DSN=postgresql://atlas_writer:<writer_pw>@127.0.0.1:5432/skill_atlas
chmod 600 grafana/db.env

# 2. backfill every run on disk
python3 bin/load_grafana.py

# 3. install provisioning + dashboard, and the read-only password via a systemd
#    drop-in (keeps the secret out of the tracked provisioning yaml)
sudo install -o root -g grafana -m 640 grafana/provisioning/datasources/skill-atlas.yaml /etc/grafana/provisioning/datasources/
sudo install -o root -g grafana -m 640 grafana/provisioning/dashboards/skill-atlas.yaml  /etc/grafana/provisioning/dashboards/
sudo install -d -o root -g grafana -m 750 /var/lib/grafana/dashboards/skill-atlas
sudo install -o root -g grafana -m 640 grafana/dashboards/skill-atlas-trends.json /var/lib/grafana/dashboards/skill-atlas/
sudo install -d -m 755 /etc/systemd/system/grafana-server.service.d
printf '[Service]\nEnvironment=SKILL_ATLAS_RO_PASSWORD=<grafana_pw>\n' | sudo -A tee /etc/systemd/system/grafana-server.service.d/skill-atlas.conf >/dev/null
sudo chmod 600 /etc/systemd/system/grafana-server.service.d/skill-atlas.conf

sudo systemctl daemon-reload && sudo -A systemctl restart grafana-server
```

## Why these choices

- **JSONB, not 66 columns** — the atlas adds and drops metrics between runs (the
  `agent_*` family appeared only at run 21). A typed schema would need a migration
  each time; JSONB extraction (`(metrics->>'listing_tok')::float`) costs nothing here.
- **Two roles** — Grafana reads with a credential that *cannot write*, so a
  compromised dashboard can't rewrite history. Only the loader holds `atlas_writer`.
- **Secret via env var, not the yaml** — the tracked datasource file carries
  `${SKILL_ATLAS_RO_PASSWORD}`; the value lives only in the systemd drop-in and
  `CREDENTIALS.md`. Nothing secret is committed.
