# Original generator (archived 2026-09-05)

The scripts that produced the published Skill Atlas artifact on 2026-09-04. They lived
only in a Claude session's `/tmp` scratchpad and were rescued before that directory was
lost. Superseded by the `atlas/` package; kept for provenance and for the scoring rubric's
audit trail.

Known defects, all fixed in the rewrite:

- `build.py` hardcodes `BASE` to the /tmp scratchpad; `scan*.py` hardcode `HOME`;
  `measure.py` carries its own plugin-path dict. Three copies of configuration in code.
- `build.py`'s `family()` falls through to `return "Design aesthetics"`, silently
  misfiling every skill added after it was written.
- `verify.mjs` only *prints*. Nothing wrote `router-index.json`, so it went stale while
  `build.py` kept reading it.
- `scan2.py` simulates skill-router shadowing by replicating `buildIndex` in Python; the
  simulation breaks same-source ties on `os.walk` order, which is not node's readdir
  order. The rewrite reads the router's own index instead.
- `scan2.py`'s `followlinks` branch exists for the four `*-with-strix` skills, deleted
  from disk 2026-09-05. Dead code.

The rendered artifact and its intermediate JSON are deliberately NOT tracked — they embed
vault skill descriptions under redistribution restrictions. They remain in `data/_rescue/`
on this machine only.
