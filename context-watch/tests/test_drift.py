import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import session_cost as sc

# The plugin lives at context-watch/context-watch/, so context-watch is one level up.
REPO_ROOT = Path(os.environ.get("CONTEXT_WATCH_REPO", ROOT.parent))


@unittest.skipUnless((REPO_ROOT / "tools" / "phase0_mine.py").is_file(),
                     "context-watch checkout not present")
class TestClassifierDrift(unittest.TestCase):
    """The classifier is duplicated on purpose.

    Same repo, but different deployment units: installing the plugin ships
    only context-watch/, so session_cost.py cannot import phase0_mine.py at
    runtime. Ruled by the human partner on 2026-07-31 — plan governs over
    the usual no-duplication rule. The copies are kept honest by asserting
    identical results on one fixture.

    Skips if context-watch is absent. That is correct for a standalone plugin
    checkout, but it means the guard is silent in exactly the case where
    drift would matter most -- if a CI or publish pipeline is ever added
    that tests context-watch/ in isolation, this test must not be the only
    thing standing between the two copies.
    """

    def test_identical_bucket_counts(self):
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import phase0_mine as pm

        fixture = ROOT / "tests" / "fixtures" / "reads.jsonl"
        mine = sc.classify_reads(fixture)
        result = pm.analyse_session(fixture)
        self.assertIsNotNone(result, "phase0_mine returned nothing for the fixture")
        other = result[0]
        for bucket in ("cold", "after_edit", "new_range", "redundant"):
            self.assertEqual(mine[bucket], other["reads_" + bucket],
                             "bucket %s drifted between the two copies" % bucket)
        self.assertEqual(mine["total"], other["reads_total"],
                         "total read count drifted")
        self.assertEqual(mine["distinct_files"], other["distinct_files_read"],
                         "distinct file count drifted")
        self.assertEqual(mine["est_tokens"]["redundant"],
                         other["est_redundant_read_tokens"],
                         "redundant-token estimate drifted")


if __name__ == "__main__":
    unittest.main()
