import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import scanner


class TestClaudeMdScan(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def test_est_tokens_is_chars_over_four(self):
        f = self.tmp / "CLAUDE.md"
        f.write_text("x" * 400)
        self.assertEqual(scanner.est_tokens(f), 100)

    def test_verdicts_by_size(self):
        small = self.tmp / "a" / "CLAUDE.md"
        small.parent.mkdir()
        small.write_text("x" * 400)            # 100 tokens
        big = self.tmp / "a" / "b" / "CLAUDE.md"
        big.parent.mkdir()
        big.write_text("x" * 40000)            # 10000 tokens
        found = {r["path"]: r["verdict"] for r in scanner.scan_claude_md(big.parent)}
        self.assertEqual(found[str(small)], "ok")
        self.assertEqual(found[str(big)], "flag")

    def test_advise_band(self):
        mid = self.tmp / "c" / "CLAUDE.md"
        mid.parent.mkdir()
        mid.write_text("x" * 16000)            # 4000 tokens
        found = {r["path"]: r["verdict"] for r in scanner.scan_claude_md(mid.parent)}
        self.assertEqual(found[str(mid)], "advise")

    def test_missing_dir_returns_empty(self):
        self.assertEqual(scanner.scan_claude_md(self.tmp / "nope"), [])

    def test_relative_cwd_still_walks_to_root(self):
        import os as _os
        nested = self.tmp / "x" / "y"
        nested.mkdir(parents=True)
        (self.tmp / "CLAUDE.md").write_text("z" * 400)
        prev = _os.getcwd()
        _os.chdir(str(nested))
        try:
            found = [r["path"] for r in scanner.scan_claude_md(".")]
        finally:
            _os.chdir(prev)
        self.assertIn(str(self.tmp / "CLAUDE.md"), found)

    def test_unsearchable_directory_does_not_raise(self):
        import os as _os
        locked = self.tmp / "locked"
        locked.mkdir()
        (locked / "CLAUDE.md").write_text("q" * 400)
        _os.chmod(str(locked), 0o000)
        try:
            scanner.scan_claude_md(self.tmp)  # must not raise
        finally:
            _os.chmod(str(locked), 0o755)

    def test_verdict_boundaries(self):
        cases = ((2999, "ok"), (3000, "advise"), (5999, "advise"),
                 (6000, "flag"), (6001, "flag"))
        for tokens, expected in cases:
            with self.subTest(tokens=tokens):
                self.assertEqual(scanner._verdict(tokens), expected)


class TestUsageScan(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.projects = self.tmp / "projects" / "-proj"
        self.projects.mkdir(parents=True)
        (self.projects / "s.jsonl").write_text("\n".join([
            '{"type":"assistant","message":{"content":[{"type":"tool_use",'
            '"name":"Skill","input":{"skill":"refactor"}}]}}',
            '{"type":"assistant","message":{"content":[{"type":"tool_use",'
            '"name":"mcp__plugin_playwright_playwright__browser_click","input":{}}]}}',
            'garbage line',
        ]))
        self.skills = self.tmp / "skills"
        for name, desc in (("refactor", "used one"), ("dormant", "never used")):
            d = self.skills / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(
                "---\nname: {}\ndescription: {}\n---\nbody\n".format(name, desc))

    def test_used_names_extracted(self):
        u = scanner.used_names(self.tmp / "projects")
        self.assertIn("refactor", u["skills"])
        self.assertIn("playwright", u["mcp"])

    def test_unused_skill_identified(self):
        r = scanner.scan_unused(self.skills, self.tmp / "projects")
        names = [s["name"] for s in r["unused_skills"]]
        self.assertEqual(names, ["dormant"])
        self.assertNotIn("refactor", names)

    def test_recoverable_is_listing_cost_only(self):
        r = scanner.scan_unused(self.skills, self.tmp / "projects")
        # name + description only; the body never loads unless invoked
        self.assertGreater(r["est_recoverable"], 0)
        self.assertLess(r["est_recoverable"], 50)

    def test_missing_dirs_are_safe(self):
        r = scanner.scan_unused(self.tmp / "nope", self.tmp / "also-nope")
        self.assertEqual(r["unused_skills"], [])

    def test_mcp_stem_handles_plugin_and_bare_names(self):
        cases = (
            ("mcp__plugin_playwright_playwright__browser_click", "playwright"),
            ("mcp__plugin_neo4j-memory_neo4j-memory__memory_add", "neo4j-memory"),
            ("mcp__ide__getDiagnostics", "ide"),
            ("mcp__my_server__do_thing", "my_server"),
        )
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(scanner._mcp_stem(name), expected)

    def test_multiline_description_is_measured_in_full(self):
        d = self.tmp / "folded"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\nname: folded\ndescription:\n"
            "  first line of the description\n"
            "  second line of the description\n"
            "metadata: x\n---\nbody\n")
        one_line = self.tmp / "flat"
        one_line.mkdir(parents=True)
        (one_line / "SKILL.md").write_text(
            "---\nname: flat\ndescription: first line of the description\n---\nbody\n")
        self.assertGreater(scanner._est_listing_cost(d),
                           scanner._est_listing_cost(one_line))


if __name__ == "__main__":
    unittest.main()
