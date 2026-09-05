"""Compose template + content + dataset into the single-file report.

Output stays a self-contained HTML file on purpose: mailable, openable anywhere,
publishable as an artifact. That property is what made the original report useful
and is worth more than live filtering against a backend.
"""
import json, os

from . import config, content, dataset


def _kpi_cards(metrics, prev):
    """Build the KPI strip, deriving strikethrough corrections from the previous run.

    The original template carried `<s>4,210</s> 4,312` typed by hand. Here the old
    value comes from data/runs/, so a correction appears because the number moved --
    not because someone remembered to edit the HTML.
    """
    spec = json.load(open(os.path.join(config.CONFIG_DIR, "kpis.json"), encoding="utf-8"))
    cards = []
    for k in spec:
        key = k["metric"]
        now = metrics.get(key)
        if now is None:
            continue
        val = str(now) if k.get("raw") else content.fmt(now)
        was = (prev or {}).get(key)
        if was is not None and was != now:
            val = f'<s style="opacity:.45">{content.fmt(was) if not k.get("raw") else was}</s> {val}'
        try:
            note = k["note"].format(**{a: content.fmt(b) for a, b in metrics.items()})
        except (KeyError, ValueError):
            note = k["note"]
        cards.append(f'<div class="kpi"><div class="k">{k["label"]}</div>'
                     f'<div class="v num">{val}</div><div class="n">{note}</div></div>')
    return '<div class="kpis">' + "".join(cards) + "</div>"


def render(strict_content=True):
    with open(config.REPORT_JSON, encoding="utf-8") as f:
        payload = json.load(f)
    metrics = payload["metrics"]

    runs = dataset.runs()
    prev = None
    if len(runs) > 1:
        prev = dataset.load_run(runs[-2]).get("metrics")

    tpl = open(config.TEMPLATE, encoding="utf-8").read()
    frags = content.load_all()

    warnings = []
    for cid, frag in frags.items():
        body, missing = content.interpolate(frag["body"], metrics)
        broken = content.check_assertions(frag["fm"], metrics)
        if missing:
            warnings.append(f"{frag['file']}: unknown metric(s) {sorted(set(missing))}")
        if broken:
            warnings.append(f"{frag['file']}: stale assertion(s) " +
                            ", ".join(f"{k} {w}->{n}" for k, w, n in broken))
        body = content.staleness_badge(frag["fm"], broken) + body
        slot = f"<!--CONTENT:{cid}-->"
        if slot not in tpl:
            warnings.append(f"{frag['file']}: no slot {slot} in template")
            continue
        tpl = tpl.replace(slot, body)

    tpl = tpl.replace("<!--KPIS-->", _kpi_cards(metrics, prev))
    tpl = tpl.replace("/*__DATA__*/", json.dumps(payload, separators=(",", ":")))

    leftover = [s for s in ("<!--CONTENT:", "<!--KPIS-->", "/*__DATA__*/") if s in tpl]
    if leftover:
        warnings.append(f"unfilled slots remain: {leftover}")

    config.ensure_dirs()
    with open(config.OUT_HTML, "w", encoding="utf-8") as f:
        f.write(tpl)

    for w in warnings:
        print(f"  warn: {w}")
    print(f"render: {config.OUT_HTML}  {os.path.getsize(config.OUT_HTML):,} B"
          f"  ({len(frags)} content fragments, {len(payload['skills']):,} skills)")
    if warnings and strict_content:
        return 1
    return 0
