#!/usr/bin/env python3
"""Skill Atlas — a re-runnable census of the Claude Code skill ecosystem.

  atlas.py scan      walk the roots, parse frontmatter, score        -> data/skills.json
  atlas.py reach     ask the skill-router for reachability truth     -> data/router-index.json
  atlas.py build     assemble the dataset + snapshot the run         -> data/report-data.json
  atlas.py render    compose template + content + data               -> dist/skill-atlas.html
  atlas.py all       scan -> reach -> build -> render
  atlas.py diff      explain what moved between the last two runs
  atlas.py doctor    report classification drift and stale narrative

Python 3 stdlib only, plus the `node` already on this machine for the router stage.
"""
import json, os, subprocess, sys
import collections
import re

from atlas import config, dataset, diffs, render as render_mod, scan as scan_mod
from atlas.taxonomy import Taxonomy

# One definition of "large enough that uniformity is a defect", shared with the
# `flat_family_*` metrics so doctor and the report can never disagree.
FLAT_FAMILY_MIN = dataset.FLAT_FAMILY_MIN


def cmd_scan(argv):
    scan_mod.run()
    return 0


def cmd_reach(argv):
    config.ensure_dirs()
    mjs = os.path.join(config.PROJECT, "bin", "router_index.mjs")
    sys.stdout.flush()  # node writes unbuffered; keep the stage log in real order
    r = subprocess.run(["node", mjs, config.ROUTER_JSON])
    return r.returncode


def cmd_build(argv):
    try:
        p = dataset.build(strict="--force" not in argv)
    except dataset.StaleIndexError as e:
        print(f"build: {e}", file=sys.stderr)
        return 1
    m = p["metrics"]
    print(f"build: {m['total']:,} skills, {len(p['nodes'])} category nodes, "
          f"{os.path.getsize(config.REPORT_JSON):,} B")
    print(f"  listing {m['listing_tok']:,} tok/session over {m['listing_entries']} entries")
    print(f"  grades  {m['grade_a']} A · {m['grade_b']} B · {m['grade_c']} C · {m['grade_d']} D")
    _publish_grafana()
    return 0


def _publish_grafana():
    """Optional, non-fatal: push the run history to Postgres for Grafana.

    Only fires when a connection is actually configured ($ATLAS_PG_DSN or an
    untracked grafana/db.env) -- on a machine without the dashboard DB this is a
    silent no-op, so `build` stays standalone. A publish failure is a warning,
    never a build failure: the report is the source of truth, Grafana is a mirror.
    """
    if not (os.environ.get("ATLAS_PG_DSN")
            or os.path.exists(os.path.join(config.PROJECT, "grafana", "db.env"))):
        return
    try:
        sys.path.insert(0, os.path.join(config.PROJECT, "bin"))
        import load_grafana
        load_grafana.main()
    except Exception as e:  # a mirror that fails must not break the build
        print(f"  grafana publish skipped: {e}", file=sys.stderr)


def cmd_render(argv):
    return render_mod.render(strict_content="--lax" not in argv)


def cmd_all(argv):
    for fn in (cmd_scan, cmd_reach, cmd_build):
        rc = fn(argv)
        if rc:
            return rc
    # a stale-narrative warning is information, not a build failure
    render_mod.render(strict_content=False)
    return 0


def cmd_diff(argv):
    args = [a for a in argv if not a.startswith("-")]
    return diffs.report(*(args[:2] or [None, None]))


def cmd_doctor(argv):
    """Two verdicts, never conflated.

    PROBLEMS are drift the pipeline cannot render around -- an unclassified
    skill has no home in the tree, a stale taxonomy entry describes a skill
    that is gone, a stale router index makes reachability a lie. These fail.

    NOTICES are things a human should see but that are not defects. Stale
    narrative is the standing example: a paragraph written on 2026-09-04 that
    describes that day's census is CORRECT about the past, and the report
    already badges it inline. Failing the build on it would turn every
    historical passage into a permanent error and train everyone to ignore
    the exit code.
    """
    problems, notices = 0, 0
    if not os.path.exists(config.SKILLS_JSON):
        print("doctor: no scan yet. Run `atlas.py scan`.")
        return 1
    scan = json.load(open(config.SKILLS_JSON, encoding="utf-8"))
    rows = [s for s in scan["skills"] if s.get("is_latest")]
    tax = Taxonomy()

    print("PROBLEMS (fail the build)")
    un = tax.unclassified_names(rows)
    print(f"  unclassified active skills: {len(un)}")
    for n in un:
        print(f"    ? {n}")
    problems += len(un)

    stale = tax.stale_entries(rows)
    print(f"  taxonomy entries no longer on disk: {len(stale)}")
    for n in stale:
        print(f"    x {n}")
    problems += len(stale)

    if os.path.exists(config.ROUTER_JSON):
        fresh = os.path.getmtime(config.ROUTER_JSON) >= os.path.getmtime(config.SKILLS_JSON)
        print(f"  router index: {'fresh' if fresh else 'STALE - re-run `atlas.py reach`'}")
        problems += 0 if fresh else 1
    else:
        print("  router index: MISSING - run `atlas.py reach`")
        problems += 1

    # The identity sidecar is a derived file with a consumer (diffs) and no
    # loud failure mode: absent, the diff silently falls back to the lossy
    # name+source+path key. That is the same shape as the router index that sat
    # stale forever, so it gets the same existence-and-alignment gate.
    if os.path.exists(config.KEYS_JSON) and os.path.exists(config.REPORT_JSON):
        nk = len(json.load(open(config.KEYS_JSON, encoding="utf-8"))["keys"])
        ns = len(json.load(open(config.REPORT_JSON, encoding="utf-8"))["skills"])
        ok = nk == ns
        print(f"  identity sidecar: {nk} keys vs {ns} skills - "
              f"{'aligned' if ok else 'MISALIGNED - re-run `atlas.py build`'}")
        problems += 0 if ok else 1
    elif os.path.exists(config.REPORT_JSON):
        print("  identity sidecar: MISSING - diffs fall back to the lossy key; "
              "re-run `atlas.py build`")
        problems += 1

    # The ledger ribbon in health.html summarises the findings below it. It is
    # authored prose, so nothing forces it to agree with the `st-` classes it
    # describes -- and a summary that drifts from its own list is exactly the
    # defect the status pills were added to fix, one layer up. Counted, not trusted.
    _hp = os.path.join(config.CONTENT_DIR, "health.html")
    if os.path.exists(_hp):
        _h = open(_hp, encoding="utf-8").read()
        _tag = collections.Counter(re.findall(r'<div class="find sev-\w+ st-(\w+)"', _h))
        _rib = re.search(r'<p class="ledger">.*?</p>', _h, re.S)
        _said = {("decl" if "decision" in lbl else lbl): int(n)
                 for n, lbl in re.findall(r'>(\d+) ([a-z ]+)<', _rib.group(0))} if _rib else {}
        _real = {k: v for k, v in _tag.items()}
        _ok = _rib is not None and _said == _real
        print(f"  ledger ribbon: says {_said or 'NOTHING'} vs tagged {_real} - "
              f"{'agrees' if _ok else 'DESYNCED - update the ribbon in content/health.html'}")
        problems += 0 if _ok else 1

    print("\nNOTICES (informational; do not fail the build)")
    if os.path.exists(config.REPORT_JSON):
        from atlas import content as content_mod
        metrics = json.load(open(config.REPORT_JSON, encoding="utf-8"))["metrics"]
        for cid, frag in content_mod.load_all().items():
            broken = content_mod.check_assertions(frag["fm"], metrics)
            if broken:
                notices += 1
                print(f"  stale narrative: {frag['file']}")
                for k, w, n in broken:
                    print(f"    ! {k}: written as {w}, now {n}")
        print(f"  content fragments with stale assertions: {notices}"
              f"{' (each renders a badge in the report)' if notices else ''}")
    else:
        print("  no report built yet; narrative not checked")

    # A rubric that returns the SAME score for every member of a large family has
    # stopped measuring that family -- it cannot rank within it, so the grade is
    # noise dressed as signal. Design aesthetics is the standing case: 62 skills,
    # every one at 81, because five dimensions saturate and `depth` is uniform at
    # base (>1 file, no qualifying subdir). This is a NOTICE and deliberately does
    # not touch the weights: retuning the rubric would break comparability with the
    # 2026-09-04 baseline that every `atlas.py diff` is measured against.
    fams = collections.defaultdict(list)
    for s in (r for r in rows if r["source"] == "active"):
        fams[tax.family(s["name"])].append(s["score"])
    flat = [(f, v) for f, v in fams.items()
            if len(v) >= FLAT_FAMILY_MIN and max(v) == min(v)]
    for f, v in sorted(flat, key=lambda kv: -len(kv[1])):
        notices += 1
        print(f"  rubric blind spot: {f} -- {len(v)} skills, all scoring {v[0]:.0f}; "
              f"the rubric cannot rank inside this family")
    print(f"  families with zero score variance (n>={FLAT_FAMILY_MIN}): {len(flat)}")

    print(f"\ndoctor: {problems} problem(s), {notices} notice(s)")
    return 1 if problems else 0


COMMANDS = {"scan": cmd_scan, "reach": cmd_reach, "build": cmd_build,
            "render": cmd_render, "all": cmd_all, "diff": cmd_diff, "doctor": cmd_doctor}


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd not in COMMANDS:
        print(f"unknown command: {cmd}\n{__doc__}", file=sys.stderr)
        return 2
    return COMMANDS[cmd](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
