#!/usr/bin/env python3
"""Publish Skill Atlas run history into Postgres for Grafana.

Reads every data/runs/*/report-data.json and upserts one row per run into
atlas.runs, keyed on the run's timestamp. Idempotent: re-running reloads the
same rows with ON CONFLICT DO UPDATE, so a backfill and an incremental publish
are the same code path.

Connection comes from $ATLAS_PG_DSN, or from grafana/db.env beside this repo
(untracked, chmod 600). The role is atlas_writer -- write access is deliberately
NOT the same credential Grafana reads with.

Called standalone (`python3 bin/load_grafana.py`) for a full backfill, and as an
optional, non-fatal tail of `atlas.py build` so every future run self-publishes.
"""
import glob
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
RUNS = os.path.join(PROJECT, "data", "runs")


def _dsn():
    dsn = os.environ.get("ATLAS_PG_DSN")
    if dsn:
        return dsn
    envf = os.path.join(PROJECT, "grafana", "db.env")
    if os.path.exists(envf):
        for line in open(envf, encoding="utf-8"):
            line = line.strip()
            if line.startswith("ATLAS_PG_DSN="):
                return line.split("=", 1)[1]
    return None


def _rows():
    """Yield (ts, run_id, generated, metrics) for each run on disk."""
    for f in sorted(glob.glob(os.path.join(RUNS, "*", "report-data.json"))):
        run_id = os.path.basename(os.path.dirname(f))
        try:
            ts = datetime.strptime(run_id, "%Y%m%d-%H%M%S")
        except ValueError:
            # a run dir that is not a timestamp is not ours to load
            continue
        d = json.load(open(f, encoding="utf-8"))
        metrics = d.get("metrics", {})
        # keep only the JSON-scalar metrics; nested objects are report-shaping,
        # not time-series signal, and would bloat the row for no query benefit
        metrics = {k: v for k, v in metrics.items()
                   if isinstance(v, (int, float, str, bool)) or v is None}
        yield ts, run_id, d.get("generated"), metrics


def main():
    dsn = _dsn()
    if not dsn:
        print("load_grafana: no ATLAS_PG_DSN and no grafana/db.env -- nothing to do",
              file=sys.stderr)
        return 1
    try:
        import psycopg2
        from psycopg2.extras import Json, execute_values
    except ImportError:
        print("load_grafana: psycopg2 not importable; skipping", file=sys.stderr)
        return 1

    rows = list(_rows())
    if not rows:
        print("load_grafana: no runs found under data/runs", file=sys.stderr)
        return 0

    conn = psycopg2.connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO atlas.runs (ts, run_id, generated, metrics)
                VALUES %s
                ON CONFLICT (ts) DO UPDATE
                  SET run_id = EXCLUDED.run_id,
                      generated = EXCLUDED.generated,
                      metrics = EXCLUDED.metrics
            """, [(ts, rid, gen, Json(m)) for ts, rid, gen, m in rows])
            cur.execute("SELECT count(*), min(ts), max(ts) FROM atlas.runs")
            n, lo, hi = cur.fetchone()
    finally:
        conn.close()
    print(f"load_grafana: upserted {len(rows)} run(s); table now holds {n} "
          f"({lo:%Y-%m-%d %H:%M} -> {hi:%Y-%m-%d %H:%M})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
