#!/usr/bin/env python3
"""Assemble the report dataset: derive the category tree, trim fields, inject into HTML."""
import json, os, re

BASE = "/tmp/claude-1000/-home-ghost/7e89efe0-826e-4609-ae6a-3064c3347fb2/scratchpad"
d = json.load(open(f"{BASE}/skills2.json"))
rows = [s for s in d["skills"] if s.get("is_latest")]

# ---------- family derivation for the 145 active skills ----------
EXPLICIT = {
    "odoo": ("Odoo", r"^odoo-"),
    "remotion": ("Remotion / video", r"^remotion"),
    "stitch": ("Stitch design-gen", r"^stitch"),
}
PROCESS = {"karpathy-guidelines", "token-lean", "claude-router", "graphify", "agent-skills-spec",
           "book-to-skill", "design-skill-registry", "full-output-enforcement", "enhance-prompt",
           "philosophical-brain", "homelab-catalog", "design-md"}
FRONTEND = {"design-taste-frontend", "design-taste-frontend-v1", "high-end-visual-design",
            "apple-design", "minimalist-ui", "industrial-brutalist-ui", "shadcn", "shadcn-ui",
            "react-vite-dashboard", "pick-ui-library", "image-to-code", "imagegen-frontend-web",
            "imagegen-frontend-mobile", "redesign-existing-projects", "mobile-screen",
            "taste-design", "gpt-taste", "brandkit", "prototype"}
MOTION = {"animate", "animation-vocabulary", "find-animation-opportunities", "improve-animations",
          "review-animations", "emil-design-eng"}
VIDEO = {"video-editing", "ffmpeg-usage", "kinocut", "kinocut-repurpose"}
WRITING = {"no-ai-slop", "humanizer", "humanize-dev-artifacts", "storytelling", "lingo", "odt"}
TOOLING = {"antigravity-rules", "antigravity-prompt", "kimi", "agentic"}
SECURITY = {"penetration-testing-with-strix", "managed-pentesting-with-strix",
            "ci-security-scanning-with-strix", "fix-security-vulnerabilities-with-strix"}

def family(s):
    n = s["name"].strip('"')
    for _, (label, pat) in EXPLICIT.items():
        if re.match(pat, n):
            return label
    if n in PROCESS:   return "Process & meta"
    if n in FRONTEND:  return "Frontend & UI craft"
    if n in MOTION:    return "Motion & animation"
    if n in VIDEO:     return "Video production"
    if n in WRITING:   return "Writing & documents"
    if n in TOOLING:   return "Editor & model tooling"
    if n in SECURITY:  return "Security & pentest"
    return "Design aesthetics"

def treepath(s):
    """Full category path, all levels down."""
    if s["source"] == "active":
        return ["Active library", family(s)]
    if s["source"] == "vault":
        seg = s["relpath"].split(os.sep)
        parts = ["Skill vault", s["collection"]]
        mid = [x for x in seg[1:-1] if x not in ("skills", "plugins")]
        parts += mid[:2]
        return parts
    return ["Plugin cache", s["plugin"]]

# ---------- ground-truth shadowing, read from the router's own index ----------
# scan2.py's simulation breaks same-source ties on os.walk order, which does not match
# node's readdir order -- so the winner is taken from the live index instead of guessed.
# A shadow event where winner and loser share a realpath is phantom (the agent-skills
# .opencode/skills self-symlink); those are not capability losses and are excluded.
_ri = json.load(open(f"{BASE}/router-index.json"))
_win = {w["id"]: w["path"] for w in _ri["winners"]}
SHADOWED, PHANTOM = set(), set()
for e in _ri["shadowed"]:
    w = _win.get(e["id"], "")
    (PHANTOM if os.path.realpath(w) == os.path.realpath(e["path"]) else SHADOWED).add(
        os.path.realpath(e["path"]))
print(f"router index {_ri['size']} ids | genuine shadows {len(SHADOWED)} | phantom {len(PHANTOM)}")

ROOT_OF = {"active": f"{os.path.expanduser('~')}/.claude/skills",
           "vault": f"{os.path.expanduser('~')}/.claude/skill-vault",
           "plugin": f"{os.path.expanduser('~')}/.claude/plugins/cache"}

REACH_LABEL = {"listed": "Listed", "hidden": "Hidden (/name)", "vault": "Vault (MCP)",
               "plugin-on": "Plugin on", "plugin-off": "Plugin off", "plugin-unset": "Plugin unset"}

skills = []
for s in rows:
    p = treepath(s)
    skills.append({
        "n": s["name"].strip('"'), "s": s["source"], "p": p,
        "d": s["desc"][:230], "dl": s["desc_len"],
        "sc": s["score"], "g": s["grade"], "r": s["reach"], "rl": REACH_LABEL[s["reach"]],
        "lt": s["listing_tok"], "ld": s["load_tok"], "bf": s["bundle_files"],
        "bb": s["bundle_bytes"], "ag": s["age_days"],
        "dm": bool(s["dmi"] and s["dmi"].lower().startswith("t")),
        "co": s["collision_n"] if s["collides"] else 0,
        "dp": s.get("dup_copies", 1), "sp": s["score_parts"],
        "sh": os.path.realpath(os.path.join(ROOT_OF[s["source"]], s["relpath"], "SKILL.md")) in SHADOWED,
        "rid": s.get("router_id", ""),
        "sd": [x for x in s["subdirs"] if x in ("references", "scripts", "assets", "examples", "templates", "reference")],
    })

# ---------- category rollups, every node in the tree ----------
nodes = {}
for sk in skills:
    for i in range(1, len(sk["p"]) + 1):
        key = " / ".join(sk["p"][:i])
        a = nodes.setdefault(key, {"path": sk["p"][:i], "depth": i, "n": 0, "sc": 0,
                                   "lt": 0, "ld": 0, "bb": 0, "reach": {}, "grades": {}})
        a["n"] += 1; a["sc"] += sk["sc"]; a["lt"] += sk["lt"]; a["ld"] += sk["ld"]; a["bb"] += sk["bb"]
        a["reach"][sk["r"]] = a["reach"].get(sk["r"], 0) + 1
        a["sh"] = a.get("sh", 0) + (1 if sk["sh"] else 0)
        a["grades"][sk["g"]] = a["grades"].get(sk["g"], 0) + 1
for k, a in nodes.items():
    a["avg"] = round(a["sc"] / a["n"], 1)
    del a["sc"]

payload = {
    "generated": d["generated"], "skills": skills,
    "nodes": {k: v for k, v in sorted(nodes.items())},
    "provenance": d["provenance"],
}
open(f"{BASE}/report-data.json", "w").write(json.dumps(payload, separators=(",", ":")))
print("skills:", len(skills), "nodes:", len(nodes),
      "bytes:", os.path.getsize(f"{BASE}/report-data.json"))
fam = {}
for sk in skills:
    if sk["s"] == "active":
        fam[sk["p"][1]] = fam.get(sk["p"][1], 0) + 1
print("active families:", dict(sorted(fam.items(), key=lambda x: -x[1])))
print("shadowed in dataset:", sum(1 for x in skills if x["sh"]))
print("depth3+ nodes:", sum(1 for a in nodes.values() if a["depth"] >= 3))
