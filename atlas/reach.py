"""Reachability: can the model actually get to this skill, and by what route?

Six states, driven by ~/.claude/settings.json:
  listed        active skill in the session listing (costs tokens every session)
  hidden        active but user-invocable-only -- reachable by /name or skill_search
  vault         skill-vault; zero listing cost, reachable only via the skill-router MCP
  plugin-on     plugin explicitly enabled in enabledPlugins
  plugin-off    plugin explicitly disabled
  plugin-unset  plugin present in the cache but named nowhere in settings
  agent         resident subagent, dispatched by Agent(subagent_type:) -- billed
                into the system prompt every session, but from a roster that is
                allocated separately from the skill listing budget
"""
LABELS = {
    "listed": "Listed", "hidden": "Hidden (/name)", "vault": "Vault (MCP)",
    "plugin-on": "Plugin on", "plugin-off": "Plugin off", "plugin-unset": "Plugin unset",
    "agent": "Agent (dispatch)",
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
        elif s["source"] == "agent":
            # Always dispatchable and always billed, so not "hidden" in the sense
            # the other states use -- but reached through Agent(subagent_type:),
            # never through the skill listing or skill_load. Its own state, or the
            # else-branch below would read settings.enabledPlugins for a plugin
            # named "" and file every agent as plugin-unset.
            s["hidden"], s["reach"] = False, "agent"
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
