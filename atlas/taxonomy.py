"""Category classification for the active library.

The original build.py fell through to `return "Design aesthetics"`, so every skill
added after it was written would have been silently misfiled there. Here the
fallthrough is an explicit `Unclassified` bucket that `atlas doctor` reports on --
drift surfaces instead of quietly corrupting the category tree.
"""
import os, re

from . import config


class Taxonomy:
    def __init__(self, cfg=None):
        cfg = cfg or config.taxonomy()
        self.unclassified = cfg.get("unclassified", "Unclassified")
        self.prefix_rules = [(re.compile(r["pattern"]), r["family"])
                             for r in cfg.get("prefix_rules", [])]
        self.families = cfg.get("families", {})
        self.lookup = {}
        for fam, names in self.families.items():
            for n in names:
                self.lookup[n] = fam

    def family(self, name):
        n = name.strip('"')
        for rx, fam in self.prefix_rules:
            if rx.match(n):
                return fam
        return self.lookup.get(n, self.unclassified)

    def treepath(self, s):
        """Full category path for one skill, all levels down."""
        if s["source"] == "active":
            return ["Active library", self.family(s["name"])]
        if s["source"] == "agent":
            # Domain comes from the slug's own prefix (engineering-sre ->
            # Engineering) rather than a hand-kept list in taxonomy.json. The
            # roster is renamed and re-populated by the `agency` tool, so a config
            # list would rot on the next `agency add`; deriving it means a new
            # domain files itself and `doctor` never sees an unclassified agent.
            dom = s["name"].split("-")[0] if "-" in s["name"] else "other"
            return ["Agent roster", dom.capitalize()]
        if s["source"] == "vault":
            seg = s["relpath"].split(os.sep)
            mid = [x for x in seg[1:-1] if x not in ("skills", "plugins")]
            return ["Skill vault", s["collection"]] + mid[:2]
        return ["Plugin cache", s["plugin"]]

    def unclassified_names(self, rows):
        return sorted({s["name"] for s in rows
                       if s["source"] == "active" and s.get("is_latest", True)
                       and self.family(s["name"]) == self.unclassified})

    def stale_entries(self, rows):
        """Taxonomy names that no longer exist on disk -- config rot, reported not fixed."""
        live = {s["name"] for s in rows if s.get("is_latest", True)}
        return sorted(n for n in self.lookup if n not in live)
