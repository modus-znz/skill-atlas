"""Path and configuration resolution. Nothing in this project hardcodes a path."""
import json, os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT, "config")
DATA_DIR = os.path.join(PROJECT, "data")
RUNS_DIR = os.path.join(DATA_DIR, "runs")
DIST_DIR = os.path.join(PROJECT, "dist")
CONTENT_DIR = os.path.join(PROJECT, "content")
TEMPLATE = os.path.join(PROJECT, "templates", "atlas.html.tpl")

SKILLS_JSON = os.path.join(DATA_DIR, "skills.json")
ROUTER_JSON = os.path.join(DATA_DIR, "router-index.json")
REPORT_JSON = os.path.join(DATA_DIR, "report-data.json")
OUT_HTML = os.path.join(DIST_DIR, "skill-atlas.html")


def _load(name):
    with open(os.path.join(CONFIG_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def roots():
    """Scan configuration with every ~ expanded."""
    c = _load("roots.json")
    c["settings"] = os.path.expanduser(c["settings"])
    c["router_lib"] = os.path.expanduser(c["router_lib"])
    for r in c["roots"]:
        r["path"] = os.path.expanduser(r["path"])
    return c


def rubric():
    return _load("rubric.json")


def taxonomy():
    return _load("taxonomy.json")


def ensure_dirs():
    for d in (DATA_DIR, RUNS_DIR, DIST_DIR):
        os.makedirs(d, exist_ok=True)
