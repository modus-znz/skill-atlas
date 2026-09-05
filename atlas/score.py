"""The published 100-point rubric, driven entirely by config/rubric.json.

Six dimensions: reachability (25), description quality (25), bundle depth (15),
body weight (15), freshness (10), hygiene (10). Every threshold is config, so the
rubric can be retuned without touching code -- and a retune is visible in git.
"""
from . import config


def _desc_points(n, r):
    if n == 0:
        return r["empty"]
    if n < r["thin_max"]:
        return r["thin"]
    if n <= r["good_max"]:
        return r["good"]
    if n <= r["long_max"]:
        return r["long"]
    return r["bloated"]


def _body_points(n, r):
    if n < r["thin_max"]:
        return r["thin"]
    if n <= r["good_max"]:
        return r["good"]
    if n <= r["long_max"]:
        return r["long"]
    return r["bloated"]


def _fresh_points(age, r):
    for limit, pts in r["tiers"]:
        if age <= limit:
            return pts
    return r["stale"]


def score_one(s, rub, depth_subdirs):
    p = {}
    p["reach"] = rub["reach"].get(s["reach"], rub["reach"]["_default"])
    p["desc"] = _desc_points(s["desc_len"], rub["desc"])

    d = rub["depth"]
    n_depth = len([x for x in s["subdirs"] if x in depth_subdirs])
    p["depth"] = min(d["max"], d["base"] + n_depth * d["per_subdir"]) \
        if s["bundle_files"] > 1 else d["stub"]

    p["body"] = _body_points(s["body_chars"], rub["body"])
    p["fresh"] = _fresh_points(s["age_days"], rub["fresh"])

    h = rub["hygiene"]
    hyg = h["base"]
    if s.get("dup_copies", 1) > 1:
        hyg -= min(h["dup_penalty_max"], s["dup_copies"])
    if s["collides"]:
        hyg -= h["collision_penalty"]
    p["hygiene"] = max(0, hyg)

    s["score_parts"] = p
    return sum(p.values())


def grade_for(score, thresholds):
    for g in ("A", "B", "C", "D"):
        if score >= thresholds[g]:
            return g
    return "E"


def score_all(rows, rub):
    depth_subdirs = set(config.roots()["depth_subdirs"])
    for s in rows:
        s["score"] = score_one(s, rub, depth_subdirs)
        s["grade"] = grade_for(s["score"], rub["grades"])
    return rows
