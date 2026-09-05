"""Assemble the report dataset: category tree, short-key skill rows, node rollups.

Emits data/report-data.json and snapshots it into data/runs/<timestamp>/ so
`atlas diff` can explain what moved between any two runs.
"""
import collections, json, os, shutil, time

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


def qualified_ids(ri):
    """realpath -> the router's own qualified id (`financial-services/dcf-model`).

    scan.py used to synthesise this as slugify(name), which is the BARE slug and
    therefore NOT unique -- 72 names shared one value across 100 rows, so anything
    keyed on it silently collapsed duplicate skills into a single row. The router
    already computes the unique id in buildIndex(); this joins it in rather than
    guessing. Plugin-cache rows are absent by design (isExcludedPluginPath), and
    get "" -- they are not router-addressable, and inventing an id would relapse
    into the same fiction.
    """
    out = {}
    for e in ri["winners"] + ri["shadowed"]:
        out[os.path.realpath(e["path"])] = e.get("qualified_id", "")
    return out


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
    qual = qualified_ids(ri)
    tax = Taxonomy()

    skills = []
    keys = []  # realpath per row, index-aligned with skills[]
    for s in rows:
        p = tax.treepath(s)
        keys.append(s["realpath"])
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
            "rid": qual.get(s["realpath"], ""),
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
    # Identity lives in a sidecar, not in the payload. `name|source` collapses 92
    # of 2,075 rows (seven vault collections ship an `xlsx-author`), and even
    # name+treepath still collapses 3 -- a diff keyed on either silently drops
    # skills it should be reporting. realpath is exact, and holding it outside
    # report-data.json keeps ~100 KB of paths off the rendered page.
    with open(config.KEYS_JSON, "w", encoding="utf-8") as f:
        json.dump({"generated": payload["generated"], "keys": keys}, f,
                  separators=(",", ":"))
    snapshot(payload)
    return payload


# A family smaller than this can be legitimately uniform by chance; above it, a
# zero spread means the rubric has stopped discriminating inside that family.
# Lives here so `atlas.py doctor` and the metrics that content asserts on cannot
# disagree about where the line sits.
FLAT_FAMILY_MIN = 10


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

    # Listing tokens for a set of reachability states. The cost panel tabulates
    # both what the listing bills and what visibility discipline avoids, so both
    # halves have to be measured -- a table where only the paid rows update
    # reads as current while quietly serving last month's savings figure.
    def lt(*states):
        return sum(s["lt"] for s in skills if s["r"] in states)

    # One entry per installed plugin -> the state its skills report. A plugin's
    # skills all share a state, so `max` is just picking that shared value.
    plugin_dirs = {}
    for s_ in skills:
        if s_["s"] == "plugin":
            plugin_dirs[s_["p"][1]] = s_["r"]

    def ld(*states):
        return sum(s["ld"] for s in skills if s["r"] in states)

    # Mean quality score per reachability scope. The overview's scope table is a
    # present-tense claim about the library as it stands, so every one of its
    # cells is measured -- hand-typed cells there were the same defect as the
    # cost table: a header saying "at a glance" over last month's numbers.
    def avg(*states):
        xs = [s["sc"] for s in skills if s["r"] in states]
        return round(sum(xs) / len(xs), 1) if xs else 0

    billed = lt("listed", "plugin-on")
    bloat_max = config.rubric()["desc"]["long_max"]
    bloated = [s_ for s_ in skills if s_["dl"] > bloat_max]
    # "Avoided" means tokens a listing CANDIDATE is not spending: active skills
    # hidden by skillOverrides, and plugin skills switched off or left unset.
    # The vault is excluded on purpose -- it is not a candidate at any setting,
    # so folding it in would inflate the saving with tokens no configuration
    # change could ever have spent. Its hypothetical is reported on its own.
    AVOIDABLE = ("hidden", "plugin-off", "plugin-unset")
    avoided = lt(*AVOIDABLE)
    rc = config.roots()
    budget_tok = round(rc.get("listing_budget_chars", 24000) / rc["chars_per_token"])
    vault_bytes = sum(s["bb"] for s in by("vault"))
    plugin_bytes = sum(s["bb"] for s in by("plugin"))
    _fam = collections.defaultdict(list)
    for _s in skills:
        if _s["s"] == "active":
            _fam[_s["p"][1] if len(_s["p"]) > 1 else "?"].append(_s["sc"])
    _flatf = [(len(v), v[0]) for v in _fam.values()
              if len(v) >= FLAT_FAMILY_MIN and max(v) == min(v)]
    _flat = max(_flatf) if _flatf else (0, 0)

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
        # Descriptions the rubric penalises as "bloated" (> rubric.desc.long_max),
        # split by whether that length is actually PAID for. The length penalty is
        # calibrated for the session listing, but applied uniformly -- so a vault
        # or disabled-plugin skill loses 13 points for characters no session ever
        # bills, while those same characters help skill_search (scoreItem weights a
        # description hit 1.5). Measured here so the finding cannot drift.
        # Skills whose frontmatter yields no description at all. These are not
        # merely low-scoring: the router falls back to the first non-heading body
        # line, which for a file with NO frontmatter block is the literal text
        # "description: ..." -- so search indexes the label instead of the prose
        # and the defect hides behind a plausible-looking result. Guard metric:
        # anything but 0 means a malformed import landed.
        "desc_missing": len([s_ for s_ in skills if s_["dl"] == 0]),
        "desc_bloated": len(bloated),
        "desc_bloated_billed": len([s_ for s_ in bloated if s_["r"] in ("listed", "plugin-on")]),
        "listing_tok": billed,
        "listing_tok_active": lt("listed"),
        "listing_tok_plugin": lt("plugin-on"),
        "listing_entries": len([s for s in skills if s["r"] in ("listed", "plugin-on")]),
        "listing_budget_tok": budget_tok,
        "listing_headroom_tok": budget_tok - billed,
        "listing_over_budget": int(billed > budget_tok),
        # What hiding, disabling and vaulting keep out of every session prefix.
        # Vault is always 0 by construction; it is emitted anyway so the panel
        # never hardcodes even a constant.
        "listing_tok_hidden": lt("hidden"),
        "listing_tok_plugin_off": lt("plugin-off"),
        "listing_tok_plugin_unset": lt("plugin-unset"),
        "listing_tok_vault": lt("vault"),  # hypothetical: never actually billed
        "listing_avoided_tok": avoided,
        "listing_avoided_n": len([s for s in skills if s["r"] in AVOIDABLE]),
        "listing_all_on_tok": billed + avoided,
        "listing_avoided_ratio": round(avoided / billed, 1) if billed else 0,
        "load_tok_total": sum(s["ld"] for s in skills),
        "load_tok_vault": ld("vault"),
        # Installed plugins, and how many are enabled -- counted from the cache's
        # own directory set, not from settings.json, so a plugin that is enabled
        # but no longer cached cannot inflate the "installed" figure.
        "plugin_installed": len(plugin_dirs),
        "plugin_on_installed": len([d for d, st in plugin_dirs.items() if st == "plugin-on"]),
        # D-graded skills that are actually billed in the listing. The health
        # panel claims the worst skills cost nothing because they sit in the
        # vault; that only stays true while this reads 0, so it is measured
        # rather than asserted in prose.
        "grade_d_billed": len([s for s in skills
                               if s["g"] == "D" and s["r"] in ("listed", "plugin-on")]),
        "active_max_age_days": max([s["ag"] for s in skills if s["s"] == "active"], default=0),
        "score_listed": avg("listed"),
        "score_hidden": avg("hidden"),
        "score_vault": avg("vault"),
        "score_plugin_on": avg("plugin-on"),
        "score_plugin_off": avg("plugin-off"),
        "score_plugin_unset": avg("plugin-unset"),
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
        # The largest active family whose members all score identically -- the
        # rubric's own blind spot, surfaced as a number so the prose describing
        # it in content/families.html carries an assertion and cannot drift
        # silently when a 63rd aesthetic skill lands. 0 = no such family.
        "flat_family_n": _flat[0],
        "flat_family_score": _flat[1],
        "collections": len(scan["provenance"]),
    }


def snapshot(payload):
    ts = time.strftime("%Y%m%d-%H%M%S")
    d = os.path.join(config.RUNS_DIR, ts)
    os.makedirs(d, exist_ok=True)
    shutil.copy2(config.REPORT_JSON, os.path.join(d, "report-data.json"))
    if os.path.exists(config.KEYS_JSON):
        shutil.copy2(config.KEYS_JSON, os.path.join(d, "skill-keys.json"))
    return d


def runs():
    if not os.path.isdir(config.RUNS_DIR):
        return []
    return sorted(d for d in os.listdir(config.RUNS_DIR)
                  if os.path.isfile(os.path.join(config.RUNS_DIR, d, "report-data.json")))


def load_run(ts):
    d = os.path.join(config.RUNS_DIR, ts)
    with open(os.path.join(d, "report-data.json"), encoding="utf-8") as f:
        payload = json.load(f)
    kp = os.path.join(d, "skill-keys.json")
    if os.path.exists(kp):
        with open(kp, encoding="utf-8") as f:
            ks = json.load(f).get("keys", [])
        # Only trust the sidecar if it still lines up; a hand-edited run should
        # degrade to the fallback key rather than mispair every row after the edit.
        if len(ks) == len(payload["skills"]):
            payload["_keys"] = ks
    return payload
