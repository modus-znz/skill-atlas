"""Rollup tables generated from the dataset, for slots prose cannot keep honest.

These two tables were the last hand-typed numbers in the report, and they were the
worst offenders: the vault table listed seven collections and silently omitted the
largest one in the library, because it was typed before that collection existed.
A table whose row SET goes stale is worse than a table whose cells do -- a wrong
number invites a second look, a missing row does not.

Deliberately not a generic table engine: a function per table, columns spelled out. A
config-driven renderer would be more code and less readable for no new power.
"""
import collections, json, os

from . import config


def _pct_pill(part, whole):
    """Reachability pill. Thresholds match the report's traffic-light convention:
    near-total is fine, a majority is a warning, a minority is a real finding."""
    pct = round(100 * part / whole) if whole else 0
    cls = "p-ok" if pct >= 98 else "p-warn" if pct >= 50 else "p-bad"
    return f'<span class="pill {cls}">{part:,} · {pct}%</span>'


def _depth2(payload, top):
    return sorted(((k.split(" / ", 1)[1], a) for k, a in payload["nodes"].items()
                   if a["depth"] == 2 and a["path"][0] == top),
                  key=lambda x: -x[1]["ld"])


def vault_collections(payload):
    """Vault load weight per collection, heaviest first.

    `Reachable` counts skills addressable by BARE name: a collection whose names
    collide with an earlier root needs a qualified id for the losers. Since the
    namespacing fix none of them are lost -- this column is friction, not loss,
    which is why a low percentage is a warning rather than an error.
    """
    out = []
    for name, a in _depth2(payload, "Skill vault"):
        reach = a["n"] - a["sh"]
        out.append(
            f'<tr><td>{name}</td><td class="n">{a["n"]:,}</td>'
            f'<td class="n">{_pct_pill(reach, a["n"])}</td>'
            f'<td class="n">{a["ld"]:,}</td>'
            f'<td class="n">{round(a["ld"] / a["n"]):,}</td>'
            f'<td class="n">{a["bb"] / 1048576:.2f} MB</td>'
            f'<td class="n">{a["avg"]}</td></tr>')
    return "".join(out)


PLUGIN_STATE = {"plugin-on": ("p-ok", "On"), "plugin-off": ("p-mute", "Off"),
                "plugin-unset": ("p-info", "Unset")}


def plugins(payload):
    """Plugin cache: skills, cached copies, listing cost, on/off/unset.

    `Versions cached` is the largest copy count among the plugin's skills -- the
    cache keeps every version it ever fetched, so one plugin can hold seven copies
    of a single skill. Only the newest is indexed; the rest are disk with no reach.
    """
    copies = {}
    for s in payload["skills"]:
        if s["s"] == "plugin":
            copies[s["p"][1]] = max(copies.get(s["p"][1], 1), s.get("dp", 1))
    out = []
    for name, a in sorted(_depth2(payload, "Plugin cache"), key=lambda x: (
            0 if "plugin-on" in x[1]["reach"] else 1, -x[1]["n"])):
        state = max(a["reach"], key=a["reach"].get)
        cls, label = PLUGIN_STATE.get(state, ("p-mute", state))
        extra = ""
        nv = copies.get(name, 1)
        if nv > 1:
            extra = f' · <span class="pill p-bad">{nv} copies</span>'
        out.append(
            f'<tr><td>{name}</td><td class="n">{a["n"]}</td><td class="n">{nv}</td>'
            f'<td class="n">{a["lt"]:,}</td>'
            f'<td><span class="pill {cls}">{label}</span>{extra}</td></tr>')
    return "".join(out)


def active_families(payload):
    """Per-family density for the active library, thinnest first.

    `Spread` is the point that a per-skill table cannot make: a family whose best
    and worst skill score the same is a family the rubric has stopped measuring.
    Computed from the skill rows rather than the category nodes, because the nodes
    carry an average and an average hides exactly that.
    """
    fams = {}
    for s in payload["skills"]:
        if s["s"] != "active":
            continue
        f = s["p"][1] if len(s["p"]) > 1 else "?"
        d = fams.setdefault(f, {"sc": [], "listed": 0, "ld": 0, "g": {}})
        d["sc"].append(s["sc"])
        d["listed"] += 1 if s["r"] == "listed" else 0
        d["ld"] += s["ld"]
        d["g"][s["g"]] = d["g"].get(s["g"], 0) + 1
    out = []
    for f, d in sorted(fams.items(), key=lambda kv: (len(kv[1]["sc"]), kv[0])):
        sc, n = d["sc"], len(d["sc"])
        spread = max(sc) - min(sc)
        cls = "p-bad" if spread == 0 and n >= 10 else "p-ok" if spread >= 10 else "p-warn"
        mix = " · ".join(f"{v}{k}" for k, v in sorted(d["g"].items()))
        out.append(
            f'<tr><td><b>{f}</b></td><td class="n">{n}</td>'
            f'<td class="n">{d["listed"]}</td>'
            f'<td class="n">{sum(sc)/n:.1f}</td>'
            f'<td class="n">{min(sc):.0f}&ndash;{max(sc):.0f}</td>'
            f'<td class="n"><span class="pill {cls}">{spread:.0f}</span></td>'
            f'<td class="n">{mix}</td>'
            f'<td class="n">{round(d["ld"]/n):,}</td></tr>')
    return "".join(out)


def agent_domains(payload):
    """The resident agent roster, rolled up by domain.

    No score column, and that is the point: agents are censused, not graded. What
    matters about them is what the session PAYS -- the roster is billed into the
    system prefix on every request from an allocation separate to the skill
    listing, so it is measured beside that listing and never added into it.
    """
    doms = {}
    for s in payload["skills"]:
        if s["s"] != "agent":
            continue
        d = doms.setdefault(s["p"][1] if len(s["p"]) > 1 else "Other",
                            {"n": 0, "lt": 0, "ld": 0, "bb": 0, "ag": []})
        d["n"] += 1
        d["lt"] += s["lt"]
        d["ld"] += s["ld"]
        d["bb"] += s["bb"]
        d["ag"].append(s["ag"])
    out = []
    for f, d in sorted(doms.items(), key=lambda kv: -kv[1]["n"]):
        out.append(
            f'<tr><td><b>{f}</b></td><td class="n">{d["n"]}</td>'
            f'<td class="n">{d["lt"]:,}</td>'
            f'<td class="n">{round(d["lt"] / d["n"]):,}</td>'
            f'<td class="n">{d["ld"]:,}</td>'
            f'<td class="n">{round(d["bb"] / 1024):,} KB</td>'
            f'<td class="n">{round(sum(d["ag"]) / len(d["ag"]))}</td></tr>')
    return "".join(out)


def heaviest_loads(payload, n=10):
    """The n skills whose bodies cost the most to load, heaviest first.

    Load size is a property of the file, not of the tree it sits in, so this is
    per-skill rather than per-family: a progressive-disclosure split can move a
    skill out of the top ten entirely, which is exactly the change such a table
    exists to make visible. Ranking on the load figure alone rather than on
    listing cost -- a huge skill nobody reaches is not a problem, and a
    frequently-reached one is worth splitting whichever way its bytes fall.
    """
    rows = sorted(payload["skills"], key=lambda s: -s["ld"])[:n]
    out = []
    for s in rows:
        scope = {"active": "active", "vault": "vault",
                 "plugin": "plugin", "agent": "agent"}.get(s["s"], s["s"])
        copies = s.get("dp", 1)
        note = []
        if copies > 1:
            note.append(f'<span class="pill p-bad">{copies} cached copies</span>')
        if s["s"] == "active" and s["r"] == "hidden":
            note.append("hidden")
        elif s["s"] == "plugin":
            note.append(f"plugin &middot; {s['r']}")
        elif s["s"] == "vault":
            note.append("vault &middot; search only")
        out.append(
            f'<tr><td class="n">{s["ld"]:,}</td><td><code>{s["n"]}</code></td>'
            f'<td>{scope}</td><td>{" ".join(note) or "&mdash;"}</td></tr>')
    return "".join(out)


def rubric_weights(payload=None):
    """The scoring bands, read from config/rubric.json rather than restated here.

    A rubric table written by hand is a snapshot of a config file that can be edited
    without anyone noticing the prose is now describing different numbers -- and a
    report that documents a rubric it does not use is worse than one that documents
    none. The rationale for each dimension lives in the content fragment; the numbers
    can only come from the file that is actually loaded at score time.
    """
    r = json.load(open(os.path.join(config.CONFIG_DIR, "rubric.json"), encoding="utf-8"))
    reach, desc, depth, body, fresh, hyg = (r["reach"], r["desc"], r["depth"],
                                           r["body"], r["fresh"], r["hygiene"])
    rows = [
        ("Reachability", reach["listed"],
         " · ".join(f"{k} {v}" for k, v in reach.items() if not k.startswith("_"))),
        ("Description quality", desc["good"],
         f"0 chars &rarr; {desc['empty']} &middot; &lt;{desc['thin_max']} &rarr; {desc['thin']}"
         f" &middot; {desc['thin_max']}&ndash;{desc['good_max']} &rarr; {desc['good']}"
         f" &middot; {desc['good_max'] + 1}&ndash;{desc['long_max']} &rarr; {desc['long']}"
         f" &middot; &gt;{desc['long_max']} &rarr; {desc['bloated']}"),
        ("Bundle depth", depth["max"],
         f"{depth['base']} base + {depth['per_subdir']} per support dir, capped at "
         f"{depth['max']} &middot; single-file bundle &rarr; {depth['stub']}"),
        ("Body weight", body["good"],
         f"&lt;{body['thin_max']} &rarr; {body['thin']} &middot; {body['thin_max']}"
         f"&ndash;{body['good_max']:,} &rarr; {body['good']} &middot; {body['good_max']:,}"
         f"&ndash;{body['long_max']:,} &rarr; {body['long']} &middot; &gt;{body['long_max']:,}"
         f" &rarr; {body['bloated']}"),
        ("Freshness", fresh["tiers"][0][1],
         " &middot; ".join(f"&le;{d} d &rarr; {p}" for d, p in fresh["tiers"])
         + f" &middot; older &rarr; {fresh['stale']}"),
        ("Hygiene", hyg["base"],
         f"{hyg['base']} base &middot; &minus;1 per duplicate copy "
         f"(max &minus;{hyg['dup_penalty_max']}) &middot; &minus;{hyg['collision_penalty']}"
         f" if the name collides"),
    ]
    return "".join(
        f'<tr><td class="n">{pts}</td><td><b>{name}</b></td><td>{bands}</td></tr>'
        for name, pts, bands in rows)


BUILDERS = {"vault_collections": vault_collections, "plugins": plugins,
            "active_families": active_families, "agent_domains": agent_domains,
            "heaviest_loads": heaviest_loads, "rubric_weights": rubric_weights}


def build_all(payload):
    return {k: fn(payload) for k, fn in BUILDERS.items()}
