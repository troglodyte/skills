import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
sys.path.insert(0, str(ROOT / "tools"))
import guard


class TestThresholds(unittest.TestCase):
    def test_defaults(self):
        os.environ.pop("CONTEXT_WATCH_THRESHOLDS", None)
        self.assertEqual(guard.thresholds(), [60000, 150000])

    def test_env_override(self):
        os.environ["CONTEXT_WATCH_THRESHOLDS"] = "10,20,30"
        try:
            self.assertEqual(guard.thresholds(), [10, 20, 30])
        finally:
            del os.environ["CONTEXT_WATCH_THRESHOLDS"]

    def test_malformed_env_falls_back_to_defaults(self):
        os.environ["CONTEXT_WATCH_THRESHOLDS"] = "not,numbers"
        try:
            self.assertEqual(guard.thresholds(), [60000, 150000])
        finally:
            del os.environ["CONTEXT_WATCH_THRESHOLDS"]


class TestOneShot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["CONTEXT_WATCH_STATE_DIR"] = self.tmp

    def tearDown(self):
        del os.environ["CONTEXT_WATCH_STATE_DIR"]

    def test_below_threshold_returns_none(self):
        self.assertIsNone(guard.crossed(59_999, "s1"))

    def test_crossing_returns_threshold_once(self):
        self.assertEqual(guard.crossed(60_001, "s1"), 60000)
        guard.mark_fired("s1", 60000)
        self.assertIsNone(guard.crossed(60_001, "s1"))

    def test_escalation_still_fires_after_first(self):
        guard.mark_fired("s2", 60000)
        self.assertEqual(guard.crossed(150_001, "s2"), 150000)

    def test_highest_crossed_threshold_wins(self):
        self.assertEqual(guard.crossed(200_000, "s3"), 150000)

    def test_corrupt_state_treated_as_not_fired(self):
        guard.state_path("s4").parent.mkdir(parents=True, exist_ok=True)
        guard.state_path("s4").write_text("{{{not json")
        self.assertFalse(guard.already_fired("s4", 60000))

    def test_non_dict_state_file_treated_as_not_fired(self):
        for junk in ("[]", '"x"', "42", "null"):
            with self.subTest(junk=junk):
                p = guard.state_path("junk")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(junk)
                self.assertFalse(guard.already_fired("junk", 60000))

    def test_non_list_fired_key_treated_as_not_fired(self):
        p = guard.state_path("badkey")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"fired": "abc"}')
        self.assertFalse(guard.already_fired("badkey", 60000))

    def test_mark_fired_recovers_from_corrupt_state(self):
        p = guard.state_path("recover")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"fired": "abc"}')
        guard.mark_fired("recover", 60000)
        self.assertTrue(guard.already_fired("recover", 60000))


import io
import contextlib


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ["CONTEXT_WATCH_STATE_DIR"] = self.tmp
        self.fixtures = ROOT / "tests" / "fixtures"

    def tearDown(self):
        del os.environ["CONTEXT_WATCH_STATE_DIR"]

    def _run(self, payload):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = guard.main(json.dumps(payload))
        return rc, buf.getvalue()

    def test_silent_below_threshold(self):
        rc, out = self._run({
            "session_id": "s1",
            "transcript_path": str(self.fixtures / "basic.jsonl"),
        })
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_fires_once_above_threshold(self):
        os.environ["CONTEXT_WATCH_THRESHOLDS"] = "5000"
        try:
            payload = {
                "session_id": "s2",
                "transcript_path": str(self.fixtures / "basic.jsonl"),
            }
            rc, first = self._run(payload)
            self.assertEqual(rc, 0)
            self.assertIn("9.0k", first)
            rc, second = self._run(payload)
            self.assertEqual(second, "")
        finally:
            del os.environ["CONTEXT_WATCH_THRESHOLDS"]

    def test_missing_transcript_is_silent(self):
        rc, out = self._run({"session_id": "s3", "cwd": "/nowhere"})
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def test_garbage_stdin_is_silent(self):
        rc, out = self._run_raw("not json at all")
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")

    def _run_raw(self, text):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = guard.main(text)
        return rc, buf.getvalue()

    def test_jumping_past_several_thresholds_warns_only_once(self):
        os.environ["CONTEXT_WATCH_THRESHOLDS"] = "1000,5000"
        try:
            payload = {
                "session_id": "jump",
                "transcript_path": str(self.fixtures / "basic.jsonl"),
            }
            rc, first = self._run(payload)
            self.assertNotEqual(first, "", "expected the escalated warning")
            rc, second = self._run(payload)
            self.assertEqual(second, "", "lower threshold must not fire afterwards")
        finally:
            del os.environ["CONTEXT_WATCH_THRESHOLDS"]

    def test_non_dict_json_payloads_are_silent(self):
        for junk in ("[1,2,3]", "42", "null", '"a string"'):
            with self.subTest(junk=junk):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = guard.main(junk)
                self.assertEqual(rc, 0)
                self.assertEqual(buf.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
