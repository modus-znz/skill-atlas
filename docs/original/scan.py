import json, os, re, sys

HOME = "/home/ghost"
ROOTS = [
    ("active", f"{HOME}/.claude/skills"),
    ("vault", f"{HOME}/.claude/skill-vault"),
    ("plugin", f"{HOME}/.claude/plugins/cache"),
]

def parse_fm(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1: return {}, text
    raw = text[3:end]
    body = text[end+4:]
    fm = {}
    key = None
    for line in raw.split("\n"):
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1); fm[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")) and fm.get(key) is not None:
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, body

def dirstats(d):
    nfiles = 0; nbytes = 0; subs = set()
    for r, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules")]
        rel = os.path.relpath(r, d)
        if rel != ".": subs.add(rel.split(os.sep)[0])
        for f in files:
            p = os.path.join(r, f)
            if os.path.islink(p): continue
            try: nbytes += os.path.getsize(p); nfiles += 1
            except OSError: pass
    return nfiles, nbytes, sorted(subs)

out = []
seen = set()
for source, root in ROOTS:
    if not os.path.isdir(root): continue
    for r, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules")]
        if "SKILL.md" not in files: continue
        p = os.path.join(r, "SKILL.md")
        real = os.path.realpath(p)
        if real in seen: continue
        seen.add(real)
        try: text = open(p, encoding="utf-8", errors="replace").read()
        except OSError: continue
        fm, body = parse_fm(text)
        nf, nb, subs = dirstats(r)
        rel = os.path.relpath(r, root)
        out.append({
            "name": fm.get("name") or os.path.basename(r),
            "dir": os.path.basename(r),
            "source": source,
            "relpath": rel,
            "group": rel.split(os.sep)[0] if rel != "." else "",
            "desc": re.sub(r"\s+", " ", fm.get("description", ""))[:600],
            "skill_chars": len(text),
            "body_chars": len(body),
            "bundle_files": nf,
            "bundle_bytes": nb,
            "subdirs": subs,
            "fm_keys": sorted(fm.keys()),
            "disable_model_invocation": fm.get("disable-model-invocation", ""),
            "allowed_tools": fm.get("allowed-tools", "") or fm.get("allowedTools", ""),
            "license": fm.get("license", ""),
            "version": fm.get("version", ""),
        })
print(json.dumps(out))
