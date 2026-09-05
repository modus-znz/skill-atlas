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

from atlas import config, dataset, diffs, render as render_mod, scan as scan_mod
from atlas.taxonomy import Taxonomy


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
    return 0


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
