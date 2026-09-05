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


BUILDERS = {"vault_collections": vault_collections, "plugins": plugins}


def build_all(payload):
    return {k: fn(payload) for k, fn in BUILDERS.items()}
