-- Skill Atlas -> Grafana schema objects. Run against the skill_atlas database:
--   createdb skill_atlas   (installer does this, guarded)
--   psql -d skill_atlas -v grafana_pw=... -f grafana/schema.sql
--
-- Metrics live in a single JSONB column, not 66 typed columns, on purpose: the
-- atlas gains and loses numeric metrics between runs (the agent_* family appeared
-- only at run 21), so a typed schema would need a migration every time a metric is
-- added. Grafana's Postgres datasource extracts what it needs with
-- (metrics->>'listing_tok')::numeric, so nothing is lost by keeping it flexible.

CREATE SCHEMA IF NOT EXISTS atlas;

CREATE TABLE IF NOT EXISTS atlas.runs (
    ts          timestamptz PRIMARY KEY,   -- run timestamp, parsed from the dir name
    run_id      text NOT NULL,             -- e.g. 20260906-032533; human-readable key
    generated   text,                      -- the ISO string the atlas emitted
    metrics     jsonb NOT NULL             -- all numeric metrics, verbatim
);
CREATE INDEX IF NOT EXISTS runs_ts_idx ON atlas.runs (ts);

-- Read-only role for Grafana; password passed via -v grafana_pw so it never lands
-- in this tracked file. The \gexec pattern keeps it idempotent AND in plain SQL,
-- where psql :var substitution works -- a $$ DO block would swallow the :var as
-- literal text and fail. First line creates the role only if absent; second resets
-- the password whether it was just created or already there.
SELECT 'CREATE ROLE grafana_ro LOGIN PASSWORD ' || quote_literal(:'grafana_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'grafana_ro')
\gexec
SELECT 'ALTER ROLE grafana_ro LOGIN PASSWORD ' || quote_literal(:'grafana_pw')
\gexec

GRANT CONNECT ON DATABASE skill_atlas TO grafana_ro;
GRANT USAGE ON SCHEMA atlas TO grafana_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA atlas TO grafana_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA atlas GRANT SELECT ON TABLES TO grafana_ro;

-- Writer role for the loader (bin/load_grafana.py). Separate from grafana_ro so the
-- dashboard credential stays strictly read-only -- a compromised Grafana cannot
-- rewrite history. Password via -v writer_pw, same no-secrets-in-git rule.
SELECT 'CREATE ROLE atlas_writer LOGIN PASSWORD ' || quote_literal(:'writer_pw')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'atlas_writer')
\gexec
SELECT 'ALTER ROLE atlas_writer PASSWORD ' || quote_literal(:'writer_pw')
\gexec
GRANT CONNECT ON DATABASE skill_atlas TO atlas_writer;
GRANT USAGE ON SCHEMA atlas TO atlas_writer;
GRANT SELECT, INSERT, UPDATE ON atlas.runs TO atlas_writer;
