"""Compare two runs and explain what moved. This is what makes the census a trend."""
from . import dataset


def _index(payload, sidecar):
    """Map identity -> row. With `sidecar` true the key is the skill's realpath
    (exact); otherwise name+source+treepath, which is lossy -- three vault rows
    collide -- and exists only so a run recorded before the sidecar still diffs.

    The scheme is chosen ONCE PER PAIR by _index_pair, never per payload: the
    two keyspaces are disjoint, so mixing them makes every key mismatch and the
    diff reports "everything added, everything removed" as though it were a real
    finding. Degrading both sides together loses three rows; degrading one side
    loses the entire comparison."""
    ks = payload.get("_keys") if sidecar else None
    out = {}
    for i, row in enumerate(payload["skills"]):
        k = ks[i] if ks else row["n"] + "|" + row["s"] + "|" + "/".join(row["p"])
        out[k] = row
    return out


def _index_pair(a, b):
    """Index both sides in one keyspace -- the exact one only if BOTH carry it."""
    sidecar = bool(a.get("_keys")) and bool(b.get("_keys"))
    return _index(a, sidecar), _index(b, sidecar)


def diff(a_ts, b_ts):
    a, b = dataset.load_run(a_ts), dataset.load_run(b_ts)
    ai, bi = _index_pair(a, b)
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
    ai, bi = _index_pair(dataset.load_run(a_ts), dataset.load_run(b_ts))
    print(f"diff {d['from']} -> {d['to']}")
    print(f"  added {len(d['added'])}  removed {len(d['removed'])}  "
          f"regraded {len(d['regraded'])}  reachability changed {len(d['rereach'])}")
    for label, rows in (("added", d["added"]), ("removed", d["removed"])):
        for k in rows[:limit]:
            r = (bi if label == "added" else ai)[k]
            print(f"  {label:8s} {r['s']:7s} {r['n']}")
        if len(rows) > limit:
            print(f"  {label:8s} … and {len(rows) - limit} more")
    # `added`/`removed` above announce their own truncation; these two did not,
    # so a 34-row regrade printed 20 lines under a header saying 34 and the
    # missing 14 looked like they had not moved. Same tail, same promise.
    for label, rows in (("grade", d["regraded"]), ("reach", d["rereach"])):
        for k, x, y in rows[:limit]:
            print(f"  {label:8s} {bi[k]['n']}: {x} -> {y}")
        if len(rows) > limit:
            print(f"  {label:8s} … and {len(rows) - limit} more")
    if d["metrics"]:
        print("  metrics:")
        for k, (x, y) in d["metrics"].items():
            print(f"    {k:22s} {x} -> {y}")
    return 0
