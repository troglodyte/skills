#!/usr/bin/env python3
"""UserPromptSubmit hook: warn once when a session gets expensive.

Silent below threshold. Fails open on every error path -- a broken guard
must never block a prompt. Hook stdout is injected into the conversation,
so output is rationed to at most one short warning per threshold.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

DEFAULT_THRESHOLDS = [60000, 150000]


def thresholds():
    raw = os.environ.get("CONTEXT_WATCH_THRESHOLDS")
    if not raw:
        return list(DEFAULT_THRESHOLDS)
    try:
        vals = sorted(int(x.strip()) for x in raw.split(",") if x.strip())
        return vals or list(DEFAULT_THRESHOLDS)
    except ValueError:
        return list(DEFAULT_THRESHOLDS)


def state_dir():
    override = os.environ.get("CONTEXT_WATCH_STATE_DIR")
    if override:
        return Path(override)
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(cfg) if cfg else Path.home() / ".claude"
    return base / ".context-watch"


def state_path(session_id):
    safe = "".join(c for c in str(session_id) if c.isalnum() or c in "-_") or "default"
    return state_dir() / "{}.json".format(safe)


def _load_state(session_id):
    """Always returns a dict whose "fired" key is a list of ints.

    A state file can hold anything -- hand-edited, truncated mid-write, or
    valid JSON that is not an object. Normalising here means callers never
    have to defend themselves, and nothing below can raise.
    """
    try:
        state = json.loads(state_path(session_id).read_text())
    except (OSError, ValueError):
        return {"fired": []}
    if not isinstance(state, dict):
        return {"fired": []}
    fired = state.get("fired")
    state["fired"] = [x for x in fired if isinstance(x, int)] if isinstance(fired, list) else []
    return state


def already_fired(session_id, threshold):
    return threshold in _load_state(session_id)["fired"]


def mark_fired(session_id, threshold):
    """Returns True if the firing was durably recorded.

    A False return means the warning must NOT be printed: without durable
    state we would re-warn on every subsequent prompt, which is far worse
    than staying quiet.
    """
    state = _load_state(session_id)
    fired = set(state["fired"])
    fired.add(threshold)
    state["fired"] = sorted(fired)
    try:
        p = state_path(session_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state))
        return True
    except OSError:
        return False


def crossed(context, session_id):
    """Highest threshold this context exceeds that has not yet fired."""
    for t in sorted(thresholds(), reverse=True):
        if context >= t and not already_fired(session_id, t):
            return t
    return None


def format_warning(threshold, rep):
    import session_cost as sc

    if threshold >= 150000:
        advice = ("Strongly consider /clear if the next task is independent, "
                  "or /compact with explicit instructions. Run "
                  "/context-watch:check for a breakdown.")
    else:
        advice = ("Consider /clear at the next task boundary, or offload "
                  "exploration to a subagent. Run /context-watch:check "
                  "for a breakdown.")
    return (
        "[context-watch] Context is {} across {} messages; {} carried so far. "
        "Every further turn re-reads all of it.\n{}"
    ).format(
        sc.human(rep["context"]), rep["n_messages"],
        sc.human(rep["cumulative"]), advice,
    )


def main(stdin_text=None):
    """Always returns 0. Prints at most one warning."""
    try:
        raw = stdin_text if stdin_text is not None else sys.stdin.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return 0

        session_id = payload.get("session_id") or "default"

        # Once every threshold has fired for this session, the guard can
        # never say anything else again -- skip locating and parsing the
        # transcript entirely.
        if all(already_fired(session_id, t) for t in thresholds()):
            return 0

        explicit = payload.get("transcript_path")

        import session_cost as sc

        if explicit:
            path = Path(explicit)
        else:
            path = sc.transcript_path(session_id, payload.get("cwd") or os.getcwd())

        rep = sc.session_metrics(path)
        t = crossed(rep["context"], session_id)
        if t is None:
            return 0
        # Mark every threshold at or below the one that fired. A session that
        # jumps straight past several thresholds in one turn would otherwise
        # emit the milder warnings on later turns, reading as a downgrade
        # immediately after the strong one.
        recorded = False
        for lower in thresholds():
            if lower <= t:
                ok = mark_fired(session_id, lower)
                if lower == t:
                    recorded = ok
        if recorded:
            print(format_warning(t, rep))
        return 0
    except BaseException:
        # BaseException, not Exception: a KeyboardInterrupt delivered mid-parse
        # must still exit 0 with empty stdout. Failing open is the whole
        # contract -- a guard that can break a prompt is worse than no guard.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
