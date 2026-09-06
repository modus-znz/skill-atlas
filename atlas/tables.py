"""Rollup tables generated from the dataset, for slots prose cannot keep honest.

These two tables were the last hand-typed numbers in the report, and they were the
worst offenders: the vault table listed seven collections and silently omitted the
largest one in the library, because it was typed before that collection existed.
A table whose row SET goes stale is worse than a table whose cells do -- a wrong
number invites a second look, a missing row does not.

Deliberately not a generic table engine: two tables, two functions, columns spelled
out. A config-driven renderer would be more code and less readable for no new power.
"""

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
    2026-09-04 router fix none of them are lost -- this column is friction, not loss,
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


BUILDERS = {"vault_collections": vault_collections, "plugins": plugins,
            "active_families": active_families, "agent_domains": agent_domains}


def build_all(payload):
    return {k: fn(payload) for k, fn in BUILDERS.items()}
