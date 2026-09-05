"""Reachability: can the model actually get to this skill, and by what route?

Six states, driven by ~/.claude/settings.json:
  listed        active skill in the session listing (costs tokens every session)
  hidden        active but user-invocable-only -- reachable by /name or skill_search
  vault         skill-vault; zero listing cost, reachable only via the skill-router MCP
  plugin-on     plugin explicitly enabled in enabledPlugins
  plugin-off    plugin explicitly disabled
  plugin-unset  plugin present in the cache but named nowhere in settings
"""
LABELS = {
    "listed": "Listed", "hidden": "Hidden (/name)", "vault": "Vault (MCP)",
    "plugin-on": "Plugin on", "plugin-off": "Plugin off", "plugin-unset": "Plugin unset",
}


def classify(rows, settings):
    overrides = settings.get("skillOverrides", {})
    enabled = settings.get("enabledPlugins", {})
    for s in rows:
        if s["source"] == "active":
            ov = overrides.get(s["dir"]) or overrides.get(s["name"])
            s["hidden"] = ov == "user-invocable-only"
            s["reach"] = "hidden" if s["hidden"] else "listed"
        elif s["source"] == "vault":
            s["hidden"], s["reach"] = True, "vault"
        else:
            # enabledPlugins keys may be bare or "name@marketplace"
            en = enabled.get(s["plugin"])
            if en is None:
                en = next((v for k, v in enabled.items()
                           if k.split("@")[0] == s["plugin"]), None)
            s["hidden"] = en is not True
            s["reach"] = ("plugin-on" if en is True
                          else "plugin-off" if en is False else "plugin-unset")
        s["reach_label"] = LABELS[s["reach"]]
    return rows
