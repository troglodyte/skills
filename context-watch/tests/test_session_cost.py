import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import session_cost as sc


class TestTranscriptPath(unittest.TestCase):
    def test_plain_path(self):
        p = sc.transcript_path("abc", "/home/u/code/proj", projects_dir="/P")
        self.assertEqual(p, Path("/P/-home-u-code-proj/abc.jsonl"))

    def test_dotted_directory_doubles_the_dash(self):
        # The separator and the leading dot both convert, hence "--claude".
        p = sc.transcript_path(
            "s1", "/home/u/code/proj/.claude/worktrees/x", projects_dir="/P"
        )
        self.assertEqual(
            p, Path("/P/-home-u-code-proj--claude-worktrees-x/s1.jsonl")
        )

    def test_leading_dot_directory(self):
        p = sc.transcript_path("s2", "/home/u/.hidden-dir/obs", projects_dir="/P")
        self.assertEqual(p, Path("/P/-home-u--hidden-dir-obs/s2.jsonl"))

    def test_default_projects_dir_honours_env(self):
        os.environ["CLAUDE_CONFIG_DIR"] = "/custom"
        try:
            self.assertEqual(sc.default_projects_dir(), Path("/custom/projects"))
        finally:
            del os.environ["CLAUDE_CONFIG_DIR"]


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestSessionMetrics(unittest.TestCase):
    def test_basic_metrics(self):
        m = sc.session_metrics(FIXTURES / "basic.jsonl")
        self.assertEqual(m["n_messages"], 3)
        self.assertEqual(m["context"], 9000)      # latest, not max
        self.assertEqual(m["cumulative"], 15000)  # 1000 + 5000 + 9000
        self.assertEqual(m["n_tool_calls"], 1)
        self.assertEqual(m["malformed"], 0)

    def test_quirks_do_not_crash(self):
        m = sc.session_metrics(FIXTURES / "quirks.jsonl")
        self.assertEqual(m["malformed"], 1)       # the one bad line
        self.assertEqual(m["n_messages"], 3)      # 3 assistant records
        self.assertEqual(m["context"], 300)

    def test_missing_file_returns_zeros(self):
        m = sc.session_metrics(FIXTURES / "does-not-exist.jsonl")
        self.assertEqual(m["n_messages"], 0)
        self.assertEqual(m["context"], 0)


class TestReadClassification(unittest.TestCase):
    def setUp(self):
        self.r = sc.classify_reads(FIXTURES / "reads.jsonl")

    def test_bucket_counts(self):
        # /a.py first, /b.py first, /n.ipynb first
        self.assertEqual(self.r["cold"], 3)
        # /a.py after Edit, /n.ipynb after NotebookEdit (notebook_path fallback)
        self.assertEqual(self.r["after_edit"], 2)
        self.assertEqual(self.r["new_range"], 1)   # /b.py lines 100-110
        self.assertEqual(self.r["redundant"], 1)   # /b.py lines 1-10 again

    def test_re_read_after_edit_is_not_redundant(self):
        """The regression that produced a false 81% redundancy figure."""
        self.assertEqual(self.r["after_edit"], 2)
        self.assertNotEqual(self.r["redundant"], 2)

    def test_distinct_files(self):
        self.assertEqual(self.r["distinct_files"], 3)

    def test_tokens_attributed_per_bucket(self):
        # each tool_result body is 4 chars -> 1 token at chars/4
        self.assertEqual(self.r["est_tokens"]["redundant"], 1)
        self.assertEqual(self.r["est_tokens"]["cold"], 3)


class TestReport(unittest.TestCase):
    def test_report_merges_metrics_and_reads(self):
        r = sc.report(FIXTURES / "reads.jsonl")
        self.assertIn("context", r)
        self.assertIn("reads", r)
        self.assertEqual(r["reads"]["redundant"], 1)

    def test_report_on_missing_file_is_safe(self):
        r = sc.report(FIXTURES / "nope.jsonl")
        self.assertEqual(r["context"], 0)
        self.assertEqual(r["reads"]["total"], 0)


class TestHuman(unittest.TestCase):
    def test_below_thousand_is_plain(self):
        self.assertEqual(sc.human(0), "0")
        self.assertEqual(sc.human(999), "999")

    def test_unit_boundaries(self):
        self.assertEqual(sc.human(1000), "1.0k")
        self.assertEqual(sc.human(1_000_000), "1.0M")
        self.assertEqual(sc.human(1_000_000_000), "1.0B")

    def test_rounding_does_not_overflow_the_unit(self):
        self.assertEqual(sc.human(999_999), "1.0M")
        self.assertEqual(sc.human(999_999_999), "1.0B")

    def test_just_below_rollover_keeps_smaller_unit(self):
        self.assertEqual(sc.human(999_499), "999.5k")


if __name__ == "__main__":
    unittest.main()
