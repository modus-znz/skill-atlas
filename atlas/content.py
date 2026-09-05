"""The authored layer: hand-written HTML fragments with checked assertions.

Two mechanisms, deliberately distinct:

  {{ metrics.x }}  interpolated at render time. A number written this way cannot
                   drift from the data, because the number is not stored in the prose.

  assert: {k: v}   the facts a passage DEPENDS ON. Each is re-checked against the
                   fresh dataset; a mismatch renders an inline staleness badge and
                   warns at build time.

This replaces the hand-typed `<s>4,210</s> 4,312` strikethrough corrections that were
baked into the original template -- corrections someone had to notice and type, which
is exactly the step that does not happen.
"""
import os, re

from . import config

_ASSERT_ITEM = re.compile(r"([A-Za-z0-9_]+)\s*:\s*([^,}]+)")


def _coerce(v):
    v = v.strip().strip("'\"")
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def parse(text):
    """Split a content fragment into (frontmatter dict, body html)."""
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            raw, body = text[3:end], text[end + 4:]
            for line in raw.split("\n"):
                m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
                if not m:
                    continue
                k, v = m.group(1), m.group(2).strip()
                if k == "assert":
                    fm[k] = {a: _coerce(b) for a, b in _ASSERT_ITEM.findall(v)}
                else:
                    fm[k] = v
    return fm, body.strip()


def load_all():
    out = {}
    if not os.path.isdir(config.CONTENT_DIR):
        return out
    for fn in sorted(os.listdir(config.CONTENT_DIR)):
        if not fn.endswith(".html"):
            continue
        with open(os.path.join(config.CONTENT_DIR, fn), encoding="utf-8") as f:
            fm, body = parse(f.read())
        out[fm.get("id", os.path.splitext(fn)[0])] = {"fm": fm, "body": body, "file": fn}
    return out


def fmt(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


def interpolate(body, metrics, tables=None):
    """Substitute {{ metrics.key }} and {{ table.name }}.

    An unknown key is left visible, not silently blanked -- a blank renders as a
    plausible empty cell, whereas `?key` in red is impossible to ship by accident.
    Tables are whole generated row-sets rather than single values; they exist so a
    table's ROW SET stays as measured as its cells.
    """
    missing = []
    tables = tables or {}

    def sub(m):
        kind, k = m.group(1), m.group(2)
        src = metrics if kind == "metrics" else tables
        if k not in src:
            missing.append(f"{kind}.{k}")
            return f"<span class='pill p-bad'>?{k}</span>"
        return fmt(src[k]) if kind == "metrics" else src[k]

    return re.sub(r"\{\{\s*(metrics|table)\.([A-Za-z0-9_]+)\s*\}\}", sub, body), missing


def check_assertions(fm, metrics):
    """Return [(key, was, now)] for every claim the fresh data no longer supports."""
    broken = []
    for k, was in (fm.get("assert") or {}).items():
        now = metrics.get(k)
        if now is None or now != was:
            broken.append((k, was, now))
    return broken


def staleness_badge(fm, broken):
    if not broken:
        return ""
    when = fm.get("asserted_on", "an earlier scan")
    items = "; ".join(f"<code>{k}</code> was {fmt(w)}, now {fmt(n)}" for k, w, n in broken)
    return (f'<div class="find sev-md" style="margin-bottom:14px">'
            f'<div class="fh"><h3>This section may be out of date</h3>'
            f'<span class="pill p-warn">Stale narrative</span></div>'
            f'<p>Written {when}, when {items}. The prose below has not been revised '
            f'since; the figures above and in the tables are live.</p></div>')
