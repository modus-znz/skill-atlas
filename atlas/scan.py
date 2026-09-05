"""Walk the skill roots, parse frontmatter, measure bundles.

Produces data/skills.json. This is the only module that touches the filesystem
outside the project, and it reads frontmatter and stat() metadata only -- it never
copies the contents of a secret, key, or environment file it happens to walk past.
"""
import json, os, re, subprocess, time

from . import config


def parse_frontmatter(text):
    """Minimal YAML-frontmatter reader: flat keys plus indented continuation lines."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw, body = text[3:end], text[end + 4:]
    fm, key = {}, None
    for line in raw.split("\n"):
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fm[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")) and fm.get(key) is not None:
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, body


def dirstats(d, skip, now):
    """Files, bytes, first-level subdirs, and newest/oldest mtime for one bundle."""
    nfiles = nbytes = 0
    subs, newest, oldest = set(), 0.0, now
    for r, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in skip]
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
            nbytes += st.st_size
            nfiles += 1
            newest = max(newest, st.st_mtime)
            oldest = min(oldest, st.st_mtime)
    return nfiles, nbytes, sorted(subs), newest, oldest


def version_key(v):
    """Semver sorts above content-hash directories, so the newest release wins."""
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", v)
    return (1, int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0, 0)


def slugify(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower().strip('"')).strip("-")


def _git(d, *args):
    try:
        return subprocess.run(["git", "-C", d, *args], capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def collect(cfg, now):
    """Walk every root once, deduping on realpath so symlink cycles cannot double-count."""
    skip = cfg["skip_dirs"]
    rows, seen = [], set()
    for spec in cfg["roots"]:
        source, root = spec["source"], spec["path"]
        if not os.path.isdir(root):
            continue
        for r, dirs, files in os.walk(root, followlinks=spec.get("follow_symlinks", False)):
            dirs[:] = [x for x in dirs if x not in skip]
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
            fm, body = parse_frontmatter(text)
            nf, nb, subs, newest, _ = dirstats(r, skip, now)
            rel = os.path.relpath(r, root)
            seg = rel.split(os.sep)
            name = (fm.get("name") or os.path.basename(r)).strip('"')
            marketplace = plugin = pver = ""
            if source == "plugin" and len(seg) >= 3:
                marketplace, plugin, pver = seg[0], seg[1], seg[2]
            desc = re.sub(r"\s+", " ", fm.get("description", "")).strip()
            # The session listing concatenates when_to_use into the description, which is
            # why adding that field is a tax on every other skill in the listing. Model it.
            wtu = re.sub(r"\s+", " ", fm.get("when_to_use", "")).strip()
            listing_text = f"{desc} - {wtu}" if wtu else desc
            rows.append({
                "name": name, "dir": os.path.basename(r), "source": source,
                "relpath": rel, "realpath": real,
                "group": seg[0] if rel != "." else "",
                "marketplace": marketplace, "plugin": plugin, "pver": pver,
                "collection": seg[0] if source == "vault" else "",
                "subgroup": seg[1] if source == "vault" and len(seg) > 2 else "",
                "desc": desc[:600], "desc_len": len(desc),
                "when_to_use_len": len(wtu),
                "listing_chars": len(listing_text),
                "skill_chars": len(text), "body_chars": len(body),
                "bundle_files": nf, "bundle_bytes": nb, "subdirs": subs,
                "fm_keys": sorted(fm.keys()),
                "dmi": fm.get("disable-model-invocation", ""),
                "allowed_tools": fm.get("allowed-tools", "") or fm.get("allowedTools", ""),
                "license": fm.get("license", ""), "version": fm.get("version", ""),
                "mtime": newest, "age_days": round((now - newest) / 86400, 1),
            })
    return rows


def dedupe_plugin_versions(rows):
    """Keep one row per (marketplace, plugin, skill); older cached versions stay flagged."""
    best, counts = {}, {}
    for i, s in enumerate(rows):
        if s["source"] != "plugin":
            s["is_latest"], s["dup_copies"] = True, 1
            continue
        k = (s["marketplace"], s["plugin"], s["name"])
        counts[k] = counts.get(k, 0) + 1
        rank = (version_key(s["pver"]), s["mtime"])
        if k not in best or rank > best[k][0]:
            best[k] = (rank, i)
    for _, i in best.values():
        rows[i]["is_latest"] = True
    for s in rows:
        if s["source"] == "plugin":
            s.setdefault("is_latest", False)
            s["dup_copies"] = counts[(s["marketplace"], s["plugin"], s["name"])]
    return rows


def mark_collisions(rows):
    byname = {}
    for s in rows:
        if s["source"] == "plugin" and not s["is_latest"]:
            continue
        byname.setdefault(s["name"], []).append(s)
    for s in rows:
        n = len(byname.get(s["name"], []))
        s["collides"], s["collision_n"] = n > 1, n
    return rows


LISTING_CAP = 1536  # per-entry description cap applied by the listing allocator


def token_estimates(rows, cpt):
    for s in rows:
        entry_chars = len(s["name"]) + 4 + min(s.get("listing_chars", s["desc_len"]), LISTING_CAP)
        s["listing_tok"] = round(entry_chars / cpt)
        s["listing_chars_billed"] = entry_chars
        s["load_tok"] = round(s["skill_chars"] / cpt)
        s["router_id"] = slugify(s["name"])
    return rows


def vault_provenance(cfg):
    vault = next((r["path"] for r in cfg["roots"] if r["source"] == "vault"), None)
    prov = {}
    if not vault or not os.path.isdir(vault):
        return prov
    for c in sorted(os.listdir(vault)):
        d = os.path.join(vault, c)
        if not os.path.isdir(d):
            continue
        prov[c] = {
            "remote": _git(d, "remote", "get-url", "origin"),
            "last_commit": _git(d, "log", "-1", "--format=%cs"),
            "subject": _git(d, "log", "-1", "--format=%s")[:120],
            "commits": _git(d, "rev-list", "--count", "HEAD"),
        }
    return prov


def run():
    cfg = config.roots()
    now = time.time()
    config.ensure_dirs()
    rows = collect(cfg, now)
    rows = dedupe_plugin_versions(rows)
    rows = mark_collisions(rows)
    rows = token_estimates(rows, cfg["chars_per_token"])

    from .reach import classify
    settings = json.load(open(cfg["settings"], encoding="utf-8"))
    classify(rows, settings)

    from .score import score_all
    score_all(rows, config.rubric())

    out = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "generated_epoch": now,
        "skills": rows,
        "provenance": vault_provenance(cfg),
        "overrides_n": len(settings.get("skillOverrides", {})),
        "enabled_plugins": settings.get("enabledPlugins", {}),
    }
    with open(config.SKILLS_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f)
    latest = [s for s in rows if s["is_latest"]]
    print(f"scan: {len(rows)} SKILL.md files -> {len(latest)} distinct skills")
    for src in ("active", "vault", "plugin"):
        n = sum(1 for s in latest if s["source"] == src)
        print(f"  {src:8s} {n:4d}")
    return out
