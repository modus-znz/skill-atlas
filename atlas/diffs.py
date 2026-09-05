"""Compare two runs and explain what moved. This is what makes the census a trend."""
from . import dataset


def _index(payload):
    return {s["n"] + "|" + s["s"]: s for s in payload["skills"]}


def diff(a_ts, b_ts):
    a, b = dataset.load_run(a_ts), dataset.load_run(b_ts)
    ai, bi = _index(a), _index(b)
    added = sorted(set(bi) - set(ai))
    removed = sorted(set(ai) - set(bi))
    regraded = [(k, ai[k]["g"], bi[k]["g"]) for k in sorted(set(ai) & set(bi))
                if ai[k]["g"] != bi[k]["g"]]
    rereach = [(k, ai[k]["r"], bi[k]["r"]) for k in sorted(set(ai) & set(bi))
               if ai[k]["r"] != bi[k]["r"]]
    am, bm = a.get("metrics", {}), b.get("metrics", {})
    moved = {k: (am[k], bm[k]) for k in sorted(bm)
             if k in am and isinstance(bm[k], (int, float)) and am[k] != bm[k]}
    return {"from": a_ts, "to": b_ts, "added": added, "removed": removed,
            "regraded": regraded, "rereach": rereach, "metrics": moved}


def report(a_ts=None, b_ts=None, limit=20):
    rs = dataset.runs()
    if len(rs) < 2:
        print(f"diff: need two runs, have {len(rs)}. Run `atlas all` again later.")
        return 0
    a_ts = a_ts or rs[-2]
    b_ts = b_ts or rs[-1]
    d = diff(a_ts, b_ts)
    print(f"diff {d['from']} -> {d['to']}")
    print(f"  added {len(d['added'])}  removed {len(d['removed'])}  "
          f"regraded {len(d['regraded'])}  reachability changed {len(d['rereach'])}")
    for label, rows in (("added", d["added"]), ("removed", d["removed"])):
        for k in rows[:limit]:
            n, s = k.rsplit("|", 1)
            print(f"  {label:8s} {s:7s} {n}")
        if len(rows) > limit:
            print(f"  {label:8s} … and {len(rows) - limit} more")
    for k, x, y in d["regraded"][:limit]:
        print(f"  grade    {k.rsplit('|',1)[0]}: {x} -> {y}")
    for k, x, y in d["rereach"][:limit]:
        print(f"  reach    {k.rsplit('|',1)[0]}: {x} -> {y}")
    if d["metrics"]:
        print("  metrics:")
        for k, (x, y) in d["metrics"].items():
            print(f"    {k:22s} {x} -> {y}")
    return 0
