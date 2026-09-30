"""End-to-end tests for skill-atlas, run against a synthetic HOME.

The point of these is the machine this repo was written on is not the machine
these run on. A census tool that only works on the author's box is not a tool,
so every test here builds a throwaway tree, points `~` at it, and exercises the
real pipeline. A hardcoded home directory fails these tests rather than silently
measuring the wrong filesystem.
"""
import contextlib, io, json, os, shutil, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas import config, content, dataset, scan, tables  # noqa: E402
from atlas.taxonomy import Taxonomy  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_cli():
    """Import the root atlas.py as a module.

    It cannot be imported as `atlas`: the package directory shadows it on
    sys.path, and the command functions live in the script, not the package.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("atlas_cli", os.path.join(REPO, "atlas.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def skill_md(name, desc="A synthetic skill used only by the test suite.", body="Do a thing.\n"):
    return f"---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\n{body}"


def make_tree(home, *, skills=(), vault=(), agents=(), settings=None, plugin=None):
    """Build a synthetic ~/.claude and return its path."""
    claude = os.path.join(home, ".claude")
    for sub in ("skills", "skill-vault", "agents", "plugins/cache"):
        os.makedirs(os.path.join(claude, sub), exist_ok=True)
    for name, body in (x if isinstance(x, tuple) else (x, None) for x in skills):
        d = os.path.join(claude, "skills", name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(skill_md(name, body=body or "Synthetic body.\n"))
    for coll, name in vault:
        d = os.path.join(claude, "skill-vault", coll, name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(skill_md(name))
    for name in agents:
        with open(os.path.join(claude, "agents", f"{name}.md"), "w", encoding="utf-8") as f:
            f.write(skill_md(name))
    if plugin:
        for name in plugin:
            d = os.path.join(claude, "plugins/cache", "marketplace", "plug", "1.0.0", name)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(skill_md(name))
    if settings is not None:
        with open(os.path.join(claude, "settings.json"), "w", encoding="utf-8") as f:
            json.dump(settings, f)
    return claude


class Sandbox(unittest.TestCase):
    """Redirects HOME and every output path into a temp dir."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="atlas-test-")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self._home = os.environ.get("HOME")
        os.environ["HOME"] = self.home
        self._saved = {k: getattr(config, k) for k in (
            "DATA_DIR", "RUNS_DIR", "DIST_DIR", "SKILLS_JSON", "ROUTER_JSON",
            "REPORT_JSON", "KEYS_JSON", "OUT_HTML")}
        config.DATA_DIR = os.path.join(self.tmp, "data")
        config.RUNS_DIR = os.path.join(config.DATA_DIR, "runs")
        config.DIST_DIR = os.path.join(self.tmp, "dist")
        config.SKILLS_JSON = os.path.join(config.DATA_DIR, "skills.json")
        config.ROUTER_JSON = os.path.join(config.DATA_DIR, "router-index.json")
        config.REPORT_JSON = os.path.join(config.DATA_DIR, "report-data.json")
        config.KEYS_JSON = os.path.join(config.DATA_DIR, "skill-keys.json")
        config.OUT_HTML = os.path.join(config.DIST_DIR, "skill-atlas.html")

    def tearDown(self):
        if self._home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._home
        for k, v in self._saved.items():
            setattr(config, k, v)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pipeline(self, quiet=True):
        """Run the real command functions against the sandbox paths.

        Output is swallowed by default so a test run reads as a test run; pass
        quiet=False inside your own redirect_stdout to assert on what it said.
        """
        if not quiet:
            return _load_cli().cmd_all([])
        with contextlib.redirect_stdout(io.StringIO()):
            return _load_cli().cmd_all([])

    def metrics(self):
        with open(config.REPORT_JSON, encoding="utf-8") as f:
            return json.load(f)["metrics"]

    def run_all(self):
        """The real CLI as a separate process, for the entry point itself."""
        env = dict(os.environ, HOME=self.home)
        return subprocess.run([sys.executable, os.path.join(REPO, "atlas.py"), "all"],
                              capture_output=True, text=True, env=env, cwd=self.tmp)


class TestForeignHome(Sandbox):
    def test_full_pipeline_runs_on_an_empty_home(self):
        self.assertEqual(self.pipeline(), 0)
        self.assertTrue(os.path.exists(config.OUT_HTML))

    def test_cli_entry_point_succeeds_in_a_subprocess(self):
        r = self.run_all()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("render:", r.stdout)

    def test_pipeline_measures_the_synthetic_tree(self):
        make_tree(self.home, skills=[("alpha", "Body one.\n"), ("beta", "Body two.\n")],
                  vault=[("coll", "gamma")], agents=["engineering-sre"])
        self.assertEqual(self.pipeline(), 0)
        m = self.metrics()
        self.assertEqual(m["active"], 2)
        self.assertEqual(m["vault"], 1)
        self.assertEqual(m["agents"], 1)
        self.assertEqual(m["total_units"], 4)

    def test_no_hardcoded_home_in_the_source(self):
        """The CI check for this, as a test, so a local run catches it too."""
        bad = []
        for root, dirs, files in os.walk(REPO):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "data", "dist")]
            for fn in files:
                if not fn.endswith((".py", ".mjs")):
                    continue
                p = os.path.join(root, fn)
                # config.py is where paths are resolved; this file holds the
                # needles as search data, so neither counts as a hardcoded path.
                if p.endswith(os.path.join("atlas", "config.py")) or p == __file__:
                    continue
                txt = open(p, encoding="utf-8", errors="replace").read()
                for needle in ("/home/", "C:\\Users", ".claude/skills"):
                    if needle in txt:
                        bad.append(f"{os.path.relpath(p, REPO)}: {needle}")
        self.assertEqual(bad, [], "hardcoded path outside config.py")


class TestOptionalInputs(Sandbox):
    def test_missing_settings_is_empty_not_an_error(self):
        make_tree(self.home, skills=["alpha"])
        self.assertEqual(self.pipeline(), 0)
        m = self.metrics()
        self.assertEqual(m["listed"], 1, "with no settings every active skill is listed")

    def test_settings_hiding_a_skill(self):
        make_tree(self.home, skills=["alpha", "beta"],
                  settings={"skillOverrides": {"beta": "user-invocable-only"}})
        self.assertEqual(self.pipeline(), 0)
        m = self.metrics()
        self.assertEqual(m["listed"], 1)
        self.assertEqual(m["hidden"], 1)

    def test_absent_router_is_skipped_and_reports_unknown_not_zero(self):
        make_tree(self.home, skills=["alpha"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(self.pipeline(quiet=False), 0)
        out = buf.getvalue()
        self.assertIn("skipped: no skill-router", out)
        self.assertIn("NOT measured", out)
        m = self.metrics()
        # The load-bearing distinction: unmeasured must not read as zero.
        for key in ("router_ids", "phantom_shadows", "router_aliases"):
            self.assertIsNone(m[key], f"{key} should be None, not {m[key]!r}")

    def test_a_stale_router_index_is_refused(self):
        """An index older than the scan is a lie, not a fallback.

        The stub index is structurally valid, so the mtime gate is the only
        thing under test: a regression shows up as this assertion failing
        rather than as a KeyError from somewhere downstream.
        """
        make_tree(self.home, skills=["alpha"])
        os.makedirs(os.path.dirname(config.ROUTER_JSON), exist_ok=True)
        with open(config.ROUTER_JSON, "w", encoding="utf-8") as f:
            json.dump({"winners": [], "shadowed": [], "size": 0, "aliases": {}}, f)
        cli = _load_cli()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.cmd_scan([]), 0)  # writes skills.json
        # Age the index explicitly rather than relying on write order: on a
        # coarse filesystem clock the two writes land in the same tick, which
        # would make this test pass or fail depending on the machine.
        old = os.path.getmtime(config.SKILLS_JSON) - 60
        os.utime(config.ROUTER_JSON, (old, old))
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cli.cmd_build([])
        self.assertEqual(rc, 1, "build must fail closed on a stale index")

    def test_force_overrides_the_staleness_gate(self):
        make_tree(self.home, skills=["alpha"])
        os.makedirs(os.path.dirname(config.ROUTER_JSON), exist_ok=True)
        with open(config.ROUTER_JSON, "w", encoding="utf-8") as f:
            json.dump({"winners": [], "shadowed": [], "size": 0, "aliases": {}}, f)
        cli = _load_cli()
        with contextlib.redirect_stdout(io.StringIO()):
            cli.cmd_scan([])
            old = os.path.getmtime(config.SKILLS_JSON) - 60
            os.utime(config.ROUTER_JSON, (old, old))
            rc = cli.cmd_build(["--force"])
        self.assertEqual(rc, 0, "--force is the documented escape hatch")


class TestTaxonomy(unittest.TestCase):
    def test_family_as_a_bare_list(self):
        t = Taxonomy({"families": {"A": ["alpha"]}, "unclassified": "Unclassified"})
        self.assertEqual(t.family("alpha"), "A")

    def test_family_as_a_spec_object(self):
        t = Taxonomy({"families": {"A": {"_about": "x", "members": ["alpha"]}},
                      "unclassified": "Unclassified"})
        self.assertEqual(t.family("alpha"), "A")

    def test_spec_keys_are_not_treated_as_members(self):
        """Iterating a dict as a list would file skills named 'members'."""
        t = Taxonomy({"families": {"A": {"_about": "x", "members": ["alpha"]}},
                      "unclassified": "Unclassified"})
        for name in ("members", "_about"):
            self.assertEqual(t.family(name), "Unclassified")

    def test_unmatched_falls_through_to_unclassified(self):
        t = Taxonomy({"families": {"A": ["alpha"]}, "unclassified": "Unclassified"})
        self.assertEqual(t.family("nowhere"), "Unclassified")

    def test_prefix_rule_beats_the_member_list(self):
        t = Taxonomy({"families": {"A": ["alpha"]},
                      "prefix_rules": [{"pattern": "^x-", "family": "X"}],
                      "unclassified": "Unclassified"})
        self.assertEqual(t.family("x-anything"), "X")

    def test_shipped_taxonomy_is_a_starter_with_no_members(self):
        t = Taxonomy(config.taxonomy())
        self.assertEqual(t.lookup, {},
                         "the shipped taxonomy must not describe one machine's inventory")
        self.assertTrue(len(t.families) >= 5, "starter should still name usable families")

    def test_stale_entries_detected(self):
        t = Taxonomy({"families": {"A": ["gone"]}, "unclassified": "Unclassified"})
        rows = [{"name": "here", "source": "active", "is_latest": True}]
        self.assertEqual(t.stale_entries(rows), ["gone"])


class TestContent(unittest.TestCase):
    def test_unknown_slot_is_left_visible(self):
        body, missing = content.interpolate("x {{ metrics.nope }}", {})
        self.assertEqual(missing, ["metrics.nope"])
        self.assertIn("?nope", body)

    def test_known_slot_is_interpolated(self):
        body, missing = content.interpolate("{{ metrics.total }}", {"total": 7})
        self.assertEqual(missing, [])
        self.assertEqual(body, "7")

    def test_integers_get_thousands_separators(self):
        body, _ = content.interpolate("{{ metrics.total }}", {"total": 20750})
        self.assertEqual(body, "20,750")

    def test_none_renders_visibly_rather_than_blank(self):
        body, missing = content.interpolate("{{ metrics.router_ids }}", {"router_ids": None})
        self.assertEqual(missing, [], "None is a known key, not a missing one")
        self.assertIn("None", body)

    def test_broken_assertion_is_detected(self):
        fm = {"assert": {"listed": 5, "missing_key": 1}}
        broken = content.check_assertions(fm, {"listed": 9})
        self.assertEqual([k for k, _, _ in broken], ["listed", "missing_key"])

    def test_holding_assertion_is_not_reported(self):
        self.assertEqual(content.check_assertions({"assert": {"listed": 5}}, {"listed": 5}), [])

    def test_shipped_fragments_declare_no_hand_typed_counts(self):
        """The claim the report makes about itself, enforced."""
        for cid, frag in content.load_all().items():
            self.assertNotIn("assert", frag["fm"],
                             f"{frag['file']} asserts a hand-typed figure; interpolate it instead")


class TestScan(Sandbox):
    def test_flat_root_requires_a_name_field(self):
        make_tree(self.home, agents=["real-agent"])
        with open(os.path.join(self.home, ".claude", "agents", "README.md"), "w") as f:
            f.write("just a note, no frontmatter\n")
        cfg = config.roots()
        rows = scan.collect(cfg, 0)
        names = {r["name"] for r in rows}
        self.assertIn("real-agent", names)
        self.assertNotIn("README", names)

    def test_description_is_optional_but_recorded(self):
        make_tree(self.home, skills=["nodesc"])
        with open(os.path.join(self.home, ".claude", "skills", "nodesc", "SKILL.md"), "w") as f:
            f.write("---\nname: nodesc\n---\n\nbody only\n")
        cfg = config.roots()
        rows = scan.collect(cfg, 0)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("desc", ""), "")

    def test_symlink_cycle_does_not_double_count(self):
        make_tree(self.home, vault=[("coll", "one")])
        vault = os.path.join(self.home, ".claude", "skill-vault")
        os.symlink(os.path.join(vault, "coll"), os.path.join(vault, "coll", "loop"))
        cfg = config.roots()
        rows = scan.collect(cfg, 0)
        self.assertEqual(len({r["name"] for r in rows}), 1)


    def test_doctor_is_clean_without_the_optional_router(self):
        """A reader who does not use skill-router must still get a green doctor.

        A check that cannot go green is a check people learn to ignore.
        """
        make_tree(self.home, skills=["alpha"])
        cli = _load_cli()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(cli.cmd_all([]), 0)
            rc = cli.cmd_doctor([])
        out = buf.getvalue()
        self.assertEqual(rc, 0, out)
        self.assertIn("not installed, so not measured", out)
        self.assertNotIn("DESYNCED", out)
        # The notices counter is shared by several checks, and each now counts
        # itself. The stale-narrative summary used to print the grand total under
        # its own label, so an unrelated notice read as a stale fragment. Assert
        # the two numbers agree: 0 stale fragments, and 2 notices total -- the
        # router skip and the one skill this test's empty taxonomy leaves
        # unclassified.
        self.assertIn("content fragments with stale assertions: 0", out)
        self.assertIn("doctor: 0 problem(s), 2 notice(s)", out)

    def test_doctor_fails_when_a_router_is_present_but_unindexed(self):
        make_tree(self.home, skills=["alpha"])
        lib = os.path.join(self.home, ".claude", "mcp-servers", "skill-router")
        os.makedirs(lib)
        with open(os.path.join(lib, "lib.mjs"), "w") as f:
            f.write("// stub\n")
        cli = _load_cli()
        with contextlib.redirect_stdout(io.StringIO()):
            cli.cmd_all([])
            rc = cli.cmd_doctor([])
        self.assertEqual(rc, 1, "an installed router with no index is a real gap")


class TestHealthLedger(unittest.TestCase):
    """The ledger ribbon summarises the findings below it, so it can drift.

    `atlas doctor` checks this. It is duplicated here because every content edit
    is a chance to change the status tags without changing the sentence that
    counts them, and a content edit does not run doctor in CI.
    """

    def test_ribbon_agrees_with_the_status_tags(self):
        import collections, re
        with open(os.path.join(config.CONTENT_DIR, "health.html"), encoding="utf-8") as f:
            h = f.read()
        tags = collections.Counter(re.findall(r'<div class="find sev-\w+ st-(\w+)"', h))
        rib = re.search(r'<p class="ledger">.*?</p>', h, re.S)
        self.assertIsNotNone(rib, "health.html must carry a ledger ribbon")
        said = {("decl" if "decision" in lbl else lbl): int(n)
                for n, lbl in re.findall(r'>(\d+) ([a-z ]+)<', rib.group(0))}
        self.assertEqual(said, dict(tags), "ledger ribbon has drifted from the findings")


class TestTables(unittest.TestCase):
    def test_rubric_weights_come_from_the_shipped_config(self):
        r = json.load(open(os.path.join(REPO, "config", "rubric.json"), encoding="utf-8"))
        out = tables.rubric_weights()
        self.assertIn(str(r["desc"]["good"]), out)
        self.assertIn(f"{r['body']['long_max']:,}", out)

    def test_heaviest_loads_is_ranked_and_bounded(self):
        payload = {"skills": [
            {"n": "small", "s": "active", "r": "listed", "ld": 10, "p": ["Active", "A"]},
            {"n": "big", "s": "active", "r": "hidden", "ld": 900, "p": ["Active", "A"]},
            {"n": "mid", "s": "vault", "r": "vault", "ld": 500, "p": ["Skill vault", "c", "m"]},
        ]}
        out = tables.heaviest_loads(payload, n=2)
        self.assertLess(out.index("big"), out.index("mid"))
        self.assertNotIn("small", out, "n=2 must bound the table")

    def test_heaviest_loads_flags_cached_duplicates(self):
        payload = {"skills": [{"n": "x", "s": "plugin", "r": "plugin-on", "ld": 5,
                               "p": ["Plugin cache", "p"], "dp": 7}]}
        self.assertIn("7 cached copies", tables.heaviest_loads(payload))

    def test_active_families_reports_spread(self):
        payload = {"skills": [
            {"n": "a", "s": "active", "sc": 80, "r": "listed", "ld": 10, "g": "A", "p": ["Active", "F"]},
            {"n": "b", "s": "active", "sc": 40, "r": "listed", "ld": 10, "g": "D", "p": ["Active", "F"]},
        ]}
        out = tables.active_families(payload)
        self.assertIn("40", out)  # the spread figure


if __name__ == "__main__":
    unittest.main()
