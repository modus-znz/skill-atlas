"""Assemble the report dataset: category tree, short-key skill rows, node rollups.

Emits data/report-data.json and snapshots it into data/runs/<timestamp>/ so
`atlas diff` can explain what moved between any two runs.
"""
import json, os, shutil, time

from . import config
from .reach import LABELS
from .taxonomy import Taxonomy


class StaleIndexError(RuntimeError):
    pass


def load_router(strict=True):
    """Load reachability ground truth, refusing a router index older than the scan.

    build.py used to consume this file blind. A stale index silently produces wrong
    reachability numbers with no signal at all, so the check is a hard gate.
    """
    if not os.path.exists(config.ROUTER_JSON):
        raise StaleIndexError(
            "data/router-index.json is missing. Run: node bin/router_index.mjs data/router-index.json")
    if strict and os.path.exists(config.SKILLS_JSON):
        if os.path.getmtime(config.ROUTER_JSON) < os.path.getmtime(config.SKILLS_JSON):
            raise StaleIndexError(
                "data/router-index.json is older than data/skills.json -- reachability "
                "would be computed from a stale index. Re-run `atlas reach`.")
    with open(config.ROUTER_JSON, encoding="utf-8") as f:
        return json.load(f)


def resolve_shadows(ri):
    """Split shadow events into genuine ones and phantoms.

    A phantom is a skill shadowing *itself* through a symlink -- skill-vault's
    agent-skills/.opencode/skills is a tracked self-symlink, and 25 skills appeared
    to shadow themselves through it. Those are not capability losses.
    """
    winners = {w["id"]: w["path"] for w in ri["winners"]}
    genuine, phantom = set(), set()
    for e in ri["shadowed"]:
        w = winners.get(e["id"], "")
        target = phantom if w and os.path.realpath(w) == os.path.realpath(e["path"]) else genuine
        target.add(os.path.realpath(e["path"]))
    return genuine, phantom


def build(strict=True):
    with open(config.SKILLS_JSON, encoding="utf-8") as f:
        scan = json.load(f)
    rows = [s for s in scan["skills"] if s.get("is_latest")]
    ri = load_router(strict=strict)
    genuine, phantom = resolve_shadows(ri)
    tax = Taxonomy()

    skills = []
    for s in rows:
        p = tax.treepath(s)
        skills.append({
            "n": s["name"], "s": s["source"], "p": p,
            "d": s["desc"][:230], "dl": s["desc_len"],
            "sc": s["score"], "g": s["grade"], "r": s["reach"],
            "rl": LABELS.get(s["reach"], s["reach"]),
            "lt": s["listing_tok"], "ld": s["load_tok"],
            "bf": s["bundle_files"], "bb": s["bundle_bytes"], "ag": s["age_days"],
            "dm": bool(s["dmi"] and s["dmi"].lower().startswith("t")),
            "co": s["collision_n"] if s["collides"] else 0,
            "dp": s.get("dup_copies", 1), "sp": s["score_parts"],
            "sh": s["realpath"] in genuine,
            "rid": s.get("router_id", ""),
            "sd": [x for x in s["subdirs"] if x in config.roots()["depth_subdirs"]],
        })

    nodes = {}
    for sk in skills:
        for i in range(1, len(sk["p"]) + 1):
            key = " / ".join(sk["p"][:i])
            a = nodes.setdefault(key, {"path": sk["p"][:i], "depth": i, "n": 0, "sc": 0,
                                       "lt": 0, "ld": 0, "bb": 0, "sh": 0,
                                       "reach": {}, "grades": {}})
            a["n"] += 1
            a["sc"] += sk["sc"]
            a["lt"] += sk["lt"]
            a["ld"] += sk["ld"]
            a["bb"] += sk["bb"]
            a["sh"] += 1 if sk["sh"] else 0
            a["reach"][sk["r"]] = a["reach"].get(sk["r"], 0) + 1
            a["grades"][sk["g"]] = a["grades"].get(sk["g"], 0) + 1
    for a in nodes.values():
        a["avg"] = round(a["sc"] / a["n"], 1)
        del a["sc"]

    payload = {
        "generated": scan["generated"],
        "generated_epoch": scan.get("generated_epoch", time.time()),
        "skills": skills,
        "nodes": dict(sorted(nodes.items())),
        "provenance": scan["provenance"],
        "metrics": metrics(scan, skills, genuine, phantom, ri, tax, rows),
    }
    config.ensure_dirs()
    with open(config.REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    snapshot(payload)
    return payload


def metrics(scan, skills, genuine, phantom, ri, tax, rows):
    """Every number the narrative is allowed to quote, computed in exactly one place."""
    by = lambda src: [s for s in skills if s["s"] == src]
    reach = {}
    for s in skills:
        reach[s["r"]] = reach.get(s["r"], 0) + 1
    grades = {}
    for s in skills:
        grades[s["g"]] = grades.get(s["g"], 0) + 1
    listed = [s for s in skills if s["r"] == "listed"]
    rc = config.roots()
    budget_tok = round(rc.get("listing_budget_chars", 24000) / rc["chars_per_token"])
    vault_bytes = sum(s["bb"] for s in by("vault"))
    plugin_bytes = sum(s["bb"] for s in by("plugin"))
    return {
        "generated": scan["generated"],
        "files_scanned": len(scan["skills"]),
        "total": len(skills),
        "stale_copies": len(scan["skills"]) - len(skills),
        "active": len(by("active")),
        "vault": len(by("vault")),
        "plugin": len(by("plugin")),
        "listed": reach.get("listed", 0),
        "hidden": reach.get("hidden", 0),
        "plugin_on": reach.get("plugin-on", 0),
        "plugin_off": reach.get("plugin-off", 0),
        "plugin_unset": reach.get("plugin-unset", 0),
        # The session listing bills active-listed AND enabled-plugin skills alike.
        "listing_tok": sum(s["lt"] for s in skills if s["r"] in ("listed", "plugin-on")),
        "listing_tok_active": sum(s["lt"] for s in listed),
        "listing_tok_plugin": sum(s["lt"] for s in skills if s["r"] == "plugin-on"),
        "listing_entries": len([s for s in skills if s["r"] in ("listed", "plugin-on")]),
        "listing_budget_tok": budget_tok,
        "listing_headroom_tok": budget_tok - sum(
            s["lt"] for s in skills if s["r"] in ("listed", "plugin-on")),
        "listing_over_budget": int(sum(
            s["lt"] for s in skills if s["r"] in ("listed", "plugin-on")) > budget_tok),
        "load_tok_total": sum(s["ld"] for s in skills),
        "grade_a": grades.get("A", 0), "grade_b": grades.get("B", 0),
        "grade_c": grades.get("C", 0), "grade_d": grades.get("D", 0),
        "grade_e": grades.get("E", 0),
        "median_grade": sorted(grades.items(), key=lambda x: -x[1])[0][0] if grades else "-",
        "avg_score": round(sum(s["sc"] for s in skills) / len(skills), 1) if skills else 0,
        "shadowed": len(genuine),
        "phantom_shadows": len(phantom),
        "router_ids": ri["size"],
        "router_aliases": ri.get("aliases", 0),
        "unclassified": len(tax.unclassified_names(rows)),
        "stale_taxonomy": len(tax.stale_entries(rows)),
        "vault_mb": round(vault_bytes / 1e6),
        "plugin_mb": round(plugin_bytes / 1e6),
        "collections": len(scan["provenance"]),
    }


def snapshot(payload):
    ts = time.strftime("%Y%m%d-%H%M%S")
    d = os.path.join(config.RUNS_DIR, ts)
    os.makedirs(d, exist_ok=True)
    shutil.copy2(config.REPORT_JSON, os.path.join(d, "report-data.json"))
    return d


def runs():
    if not os.path.isdir(config.RUNS_DIR):
        return []
    return sorted(d for d in os.listdir(config.RUNS_DIR)
                  if os.path.isfile(os.path.join(config.RUNS_DIR, d, "report-data.json")))


def load_run(ts):
    with open(os.path.join(config.RUNS_DIR, ts, "report-data.json"), encoding="utf-8") as f:
        return json.load(f)
