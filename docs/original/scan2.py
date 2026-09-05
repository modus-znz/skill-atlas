#!/usr/bin/env python3
"""Enriched skill census: dedupe cached plugin versions, add staleness, score by rubric."""
import json, os, re, subprocess, time

HOME = "/home/ghost"
ROOTS = [("active", f"{HOME}/.claude/skills"),
         ("vault",  f"{HOME}/.claude/skill-vault"),
         ("plugin", f"{HOME}/.claude/plugins/cache")]
NOW = time.time()

# ---------- settings: which active skills are hidden from the session listing ----------
raw = open(f"{HOME}/.claude/settings.json", encoding="utf-8").read()
cfg = json.loads(raw)
overrides = cfg.get("skillOverrides", {})
enabled_plugins = cfg.get("enabledPlugins", {})

def parse_fm(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    rawfm, body = text[3:end], text[end + 4:]
    fm, key = {}, None
    for line in rawfm.split("\n"):
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1); fm[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")) and fm.get(key) is not None:
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, body

def dirstats(d):
    nfiles = nbytes = 0; subs = set(); newest = 0.0; oldest = NOW
    for r, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "__pycache__")]
        rel = os.path.relpath(r, d)
        if rel != ".":
            subs.add(rel.split(os.sep)[0])
        for f in files:
            p = os.path.join(r, f)
            if os.path.islink(p):
                continue
            try:
                st = os.stat(p)
            except OSError:
                continue
            nbytes += st.st_size; nfiles += 1
            newest = max(newest, st.st_mtime); oldest = min(oldest, st.st_mtime)
    return nfiles, nbytes, sorted(subs), newest, oldest

def vkey(v):
    """Sort key: semver tuple wins; hash dirs fall back to (-1,) so semver ranks higher."""
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", v)
    return (1, int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0, 0)

rows, seen = [], set()
for source, root in ROOTS:
    if not os.path.isdir(root):
        continue
    # followlinks: the four *-with-strix skills are symlinks into ~/.agents/skills/.
    # Claude Code resolves them, so they are live skills; the realpath `seen` set below
    # still prevents a symlink loop from double-counting anything.
    for r, dirs, files in os.walk(root, followlinks=(source == "active")):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "__pycache__")]
        if "SKILL.md" not in files:
            continue
        p = os.path.join(r, "SKILL.md")
        real = os.path.realpath(p)
        if real in seen:
            continue
        seen.add(real)
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        fm, body = parse_fm(text)
        nf, nb, subs, newest, oldest = dirstats(r)
        rel = os.path.relpath(r, root)
        seg = rel.split(os.sep)
        name = fm.get("name") or os.path.basename(r)

        marketplace = plugin = pver = ""
        if source == "plugin" and len(seg) >= 3:
            marketplace, plugin, pver = seg[0], seg[1], seg[2]
        group = seg[0] if rel != "." else ""

        desc = re.sub(r"\s+", " ", fm.get("description", "")).strip()
        rows.append({
            "name": name, "dir": os.path.basename(r), "source": source,
            "relpath": rel, "group": group,
            "marketplace": marketplace, "plugin": plugin, "pver": pver,
            "collection": seg[0] if source == "vault" else "",
            "subgroup": seg[1] if source == "vault" and len(seg) > 2 else "",
            "desc": desc[:600], "desc_len": len(desc),
            "skill_chars": len(text), "body_chars": len(body),
            "bundle_files": nf, "bundle_bytes": nb, "subdirs": subs,
            "fm_keys": sorted(fm.keys()),
            "dmi": fm.get("disable-model-invocation", ""),
            "allowed_tools": fm.get("allowed-tools", "") or fm.get("allowedTools", ""),
            "license": fm.get("license", ""), "version": fm.get("version", ""),
            "mtime": newest, "age_days": round((NOW - newest) / 86400, 1),
        })

# ---------- dedupe plugin cache: keep newest version per (plugin, skill name) ----------
best = {}
for i, s in enumerate(rows):
    if s["source"] != "plugin":
        s["is_latest"] = True; s["dup_copies"] = 1; continue
    k = (s["marketplace"], s["plugin"], s["name"])
    cur = best.get(k)
    rank = (vkey(s["pver"]), s["mtime"])
    if cur is None or rank > cur[0]:
        best[k] = (rank, i)
counts = {}
for s in rows:
    if s["source"] == "plugin":
        k = (s["marketplace"], s["plugin"], s["name"])
        counts[k] = counts.get(k, 0) + 1
for k, (_, i) in best.items():
    rows[i]["is_latest"] = True
for s in rows:
    if s["source"] == "plugin":
        k = (s["marketplace"], s["plugin"], s["name"])
        s.setdefault("is_latest", False)
        s["dup_copies"] = counts[k]

# ---------- reachability ----------
for s in rows:
    if s["source"] == "active":
        ov = overrides.get(s["dir"]) or overrides.get(s["name"])
        s["hidden"] = ov == "user-invocable-only"
        s["reach"] = "hidden" if s["hidden"] else "listed"
    elif s["source"] == "vault":
        s["hidden"] = True; s["reach"] = "vault"
    else:
        en = enabled_plugins.get(s["plugin"]) or next(
            (v for k, v in enabled_plugins.items() if k.split("@")[0] == s["plugin"]), None)
        s["hidden"] = en is not True
        s["reach"] = "plugin-on" if en is True else ("plugin-off" if en is False else "plugin-unset")

# ---------- name collisions across the whole library ----------
byname = {}
for s in rows:
    if s["source"] == "plugin" and not s["is_latest"]:
        continue
    byname.setdefault(s["name"], []).append(s)
for s in rows:
    n = len(byname.get(s["name"], []))
    s["collides"] = n > 1
    s["collision_n"] = n

# ---------- skill-router reachability: replicate lib.mjs buildIndex ----------
# id = slugify(name), one winner per id, precedence active > plugin > vault.
# A shadowed skill is absent from BOTH skill_search results and skill_load, because
# `search` iterates the same winners-only Map — so it is unreachable, not merely ambiguous.
SOURCE_RANK = {"active": 0, "plugin": 1, "vault": 2}

def slugify(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower().strip('"')).strip("-")

router_index = {}
for s in rows:
    if s["source"] == "plugin" and not s["is_latest"]:
        continue
    k = slugify(s["name"])
    cur = router_index.get(k)
    if cur is None or SOURCE_RANK[s["source"]] < SOURCE_RANK[cur["source"]]:
        router_index[k] = s
for s in rows:
    s["router_id"] = slugify(s["name"])
    s["shadowed"] = (s.get("is_latest", True)
                     and router_index.get(s["router_id"]) is not s)

# ---------- token estimates (chars/3.6, the measured ratio for this corpus) ----------
for s in rows:
    s["listing_tok"] = round((len(s["name"]) + s["desc_len"] + 12) / 3.6)
    s["load_tok"] = round(s["skill_chars"] / 3.6)

# ---------- SCORE: published rubric, 0-100 ----------
def score(s):
    parts = {}
    # Reachability (25) - can the model actually get to it?
    parts["reach"] = {"listed": 25, "plugin-on": 23, "hidden": 16,
                      "plugin-unset": 10, "plugin-off": 8, "vault": 12}.get(s["reach"], 10)
    # Description quality (25) - skill_search ranks on this; too short = unfindable,
    # too long = a standing per-session tax when listed.
    d = s["desc_len"]
    parts["desc"] = 4 if d == 0 else 12 if d < 60 else 25 if d <= 400 else 20 if d <= 700 else 12
    # Bundle depth (15) - references/scripts/assets mean real substance, not a stub.
    depth = len([x for x in s["subdirs"] if x in ("references", "scripts", "assets",
                                                  "examples", "templates", "reference")])
    parts["depth"] = min(15, 5 + depth * 5) if s["bundle_files"] > 1 else 3
    # Body weight (15) - a SKILL.md must be loadable without eating the window.
    b = s["body_chars"]
    parts["body"] = 4 if b < 400 else 15 if b <= 12000 else 10 if b <= 25000 else 5
    # Freshness (10)
    a = s["age_days"]
    parts["fresh"] = 10 if a <= 60 else 7 if a <= 150 else 4 if a <= 300 else 2
    # Hygiene (10) - duplicate cached copies and name collisions are real defects.
    h = 10
    if s.get("dup_copies", 1) > 1: h -= min(5, s["dup_copies"])
    if s["collides"]: h -= 3
    parts["hygiene"] = max(0, h)
    s["score_parts"] = parts
    return sum(parts.values())

for s in rows:
    s["score"] = score(s)
    s["grade"] = ("A" if s["score"] >= 82 else "B" if s["score"] >= 70 else
                  "C" if s["score"] >= 58 else "D" if s["score"] >= 45 else "E")

# ---------- vault git provenance ----------
prov = {}
for c in sorted(os.listdir(f"{HOME}/.claude/skill-vault")):
    d = f"{HOME}/.claude/skill-vault/{c}"
    if not os.path.isdir(d):
        continue
    def g(*a):
        try:
            return subprocess.run(["git", "-C", d] + list(a), capture_output=True,
                                  text=True, timeout=10).stdout.strip()
        except Exception:
            return ""
    prov[c] = {"remote": g("remote", "get-url", "origin"),
               "last_commit": g("log", "-1", "--format=%cs"),
               "subject": g("log", "-1", "--format=%s")[:120],
               "commits": g("rev-list", "--count", "HEAD")}

out = {"generated": time.strftime("%Y-%m-%d %H:%M"), "skills": rows, "provenance": prov,
       "overrides_n": len(overrides), "enabled_plugins": enabled_plugins}
with open("/tmp/claude-1000/-home-ghost/7e89efe0-826e-4609-ae6a-3064c3347fb2/scratchpad/skills2.json", "w") as f:
    json.dump(out, f)

# ---------- console summary ----------
tot = len(rows)
latest = [s for s in rows if s.get("is_latest")]
print(f"raw={tot}  after-version-dedupe={len(latest)}")
for src in ("active", "vault", "plugin"):
    a = [s for s in rows if s["source"] == src]
    b = [s for s in latest if s["source"] == src]
    print(f"  {src:8s} raw={len(a):4d}  latest={len(b):4d}")
print("\nplugin distinct-latest per plugin:")
pp = {}
for s in latest:
    if s["source"] == "plugin":
        pp[s["plugin"]] = pp.get(s["plugin"], 0) + 1
for k, v in sorted(pp.items(), key=lambda x: -x[1]):
    print(f"  {k:22s} {v}")
print("\nreach:")
rr = {}
for s in latest:
    rr[s["reach"]] = rr.get(s["reach"], 0) + 1
print(" ", rr)
print("\nrouter index:", len(router_index), "ids  shadowed:",
      sum(1 for s in latest if s["shadowed"]))
for src in ("active", "vault", "plugin"):
    n = sum(1 for s in latest if s["source"] == src)
    w = sum(1 for s in latest if s["source"] == src and not s["shadowed"])
    print(f"  {src:8s} {n:4d} on disk -> {w:4d} reachable by id")
print("\nprovenance:")
for k, v in prov.items():
    print(f"  {k:22s} {v['last_commit'] or '(no git)':12s} {v['commits'] or '-':>5s} commits  {v['remote'][:60]}")
