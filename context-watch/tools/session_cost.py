#!/usr/bin/env python3
"""Parse a single live Claude Code session transcript.

Stdlib only, Python 3.8+. Importable by the guard hook and the
context-check skill; also usable as a CLI.
"""

import json
import math
import os
import re
from pathlib import Path

CHARS_PER_TOKEN = 4.0


def default_projects_dir():
    """Honour CLAUDE_CONFIG_DIR so this works against non-default installs."""
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(cfg) if cfg else Path.home() / ".claude"
    return base / "projects"


def transcript_path(session_id, cwd, projects_dir=None):
    """Locate a session transcript from session_id + cwd.

    Claude Code slugifies the absolute cwd by replacing every '/' and '.'
    with '-'. A dotted directory therefore yields a doubled dash, because
    the separator and the dot both convert.
    """
    base = Path(projects_dir) if projects_dir else default_projects_dir()
    slug = re.sub(r"[/.]", "-", str(cwd))
    return base / slug / "{}.jsonl".format(session_id)


def iter_records(path):
    """Yield parsed records, plus a count of unparseable lines.

    Returns (generator, counter_dict). The counter is mutated as the
    generator is consumed, so read it only after full iteration.
    """
    counter = {"malformed": 0}

    def gen():
        try:
            fh = open(str(path), "r", encoding="utf-8", errors="replace")
        except OSError:
            return
        with fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    counter["malformed"] += 1
                    continue
                if isinstance(rec, dict):
                    yield rec

    return gen(), counter


def content_blocks(message):
    """message.content is a block list, or a bare string on older records."""
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def session_metrics(path):
    """Token and activity totals for one session."""
    records, counter = iter_records(path)
    n_messages = n_tool_calls = 0
    context = cumulative = 0
    for rec in records:
        if rec.get("type") != "assistant":
            continue
        message = rec.get("message")
        if not isinstance(message, dict):
            continue
        n_messages += 1
        usage = message.get("usage")
        if isinstance(usage, dict):
            cr = usage.get("cache_read_input_tokens") or 0
            cumulative += cr
            if cr:
                context = cr
        for block in content_blocks(message):
            if block.get("type") == "tool_use":
                n_tool_calls += 1
    return {
        "n_messages": n_messages,
        "n_tool_calls": n_tool_calls,
        "context": context,
        "cumulative": cumulative,
        "malformed": counter["malformed"],
    }


EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
READ_TOOLS = {"Read"}

COLD = "cold"
AFTER_EDIT = "after_edit"
NEW_RANGE = "new_range"
REDUNDANT = "redundant"
BUCKETS = (COLD, AFTER_EDIT, NEW_RANGE, REDUNDANT)


class Ranges:
    """Union of line intervals covered by reads of one file."""

    FULL = (1, math.inf)

    def __init__(self):
        self.spans = []

    def covers(self, span):
        lo, hi = span
        return any(s_lo <= lo and hi <= s_hi for s_lo, s_hi in self.spans)

    def add(self, span):
        self.spans.append(span)
        self.spans.sort()
        merged = []
        for lo, hi in self.spans:
            if merged and lo <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
            else:
                merged.append((lo, hi))
        self.spans = merged


def read_span(tool_input):
    """Map a Read input to a line span. No offset/limit means whole file."""
    if not isinstance(tool_input, dict):
        return Ranges.FULL
    offset, limit = tool_input.get("offset"), tool_input.get("limit")
    if offset is None and limit is None:
        return Ranges.FULL
    try:
        start = int(offset) if offset is not None else 1
        return (start, math.inf) if limit is None else (start, start + int(limit))
    except (TypeError, ValueError):
        return Ranges.FULL


def result_text(block):
    """tool_result content is a string on some versions, a block list on others."""
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return ""


def classify_reads(path):
    """Bucket every Read by edit interleaving and line-span coverage.

    Classifying on file_path alone conflates verification re-reads and
    partial reads with genuine waste, and overstates redundancy roughly
    16x on real transcripts.
    """
    counts = dict.fromkeys(BUCKETS, 0)
    est = dict.fromkeys(BUCKETS, 0)
    seen = {}
    dirty = set()
    pending = {}

    records, _ = iter_records(path)
    for rec in records:
        message = rec.get("message")
        if not isinstance(message, dict):
            continue

        if rec.get("type") == "assistant":
            for block in content_blocks(message):
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name") or "?"
                tool_input = block.get("input")
                fpath = None
                if isinstance(tool_input, dict):
                    # NotebookEdit carries notebook_path, not file_path. Miss it and
                    # a notebook edit never marks the file dirty, so the next read
                    # counts as redundant instead of after_edit -- precisely the
                    # miscount this taxonomy exists to prevent.
                    fpath = tool_input.get("file_path") or tool_input.get("notebook_path")
                bucket = None
                if name in READ_TOOLS and fpath:
                    span = read_span(tool_input)
                    if fpath not in seen:
                        bucket = COLD
                        seen[fpath] = Ranges()
                        seen[fpath].add(span)
                    elif fpath in dirty:
                        bucket = AFTER_EDIT
                        seen[fpath].add(span)
                    elif not seen[fpath].covers(span):
                        bucket = NEW_RANGE
                        seen[fpath].add(span)
                    else:
                        bucket = REDUNDANT
                    counts[bucket] += 1
                    dirty.discard(fpath)
                elif name in EDIT_TOOLS and fpath:
                    dirty.add(fpath)
                if block.get("id"):
                    pending[block["id"]] = bucket

        elif rec.get("type") == "user":
            for block in content_blocks(message):
                if block.get("type") != "tool_result":
                    continue
                bucket = pending.pop(block.get("tool_use_id"), None)
                if bucket:
                    est[bucket] += int(len(result_text(block)) / CHARS_PER_TOKEN)

    out = dict(counts)
    out["est_tokens"] = est
    out["distinct_files"] = len(seen)
    out["total"] = sum(counts.values())
    return out


def report(path):
    """Everything the guard and the skill need, in one pass-pair."""
    out = session_metrics(path)
    out["reads"] = classify_reads(path)
    return out


def human(n):
    # The 0.9995 factor picks the larger unit for values that would round up
    # to 1000.0 in the smaller one, so 999_999 formats as "1.0M", not "1000.0k".
    for unit, size in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if abs(n) >= size * 0.9995:
            return "{:.1f}{}".format(n / size, unit)
    return str(int(n))


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="Report cost metrics for one session.")
    ap.add_argument("--session-id")
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--transcript", help="explicit path; overrides --session-id/--cwd")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.transcript:
        path = Path(args.transcript)
    elif args.session_id:
        path = transcript_path(args.session_id, args.cwd)
    else:
        ap.error("need --transcript or --session-id")

    r = report(path)
    if args.json:
        print(json.dumps(r, indent=2))
        return 0

    print("context now      {:>10}".format(human(r["context"])))
    print("cumulative read  {:>10}".format(human(r["cumulative"])))
    print("messages         {:>10}".format(r["n_messages"]))
    print("tool calls       {:>10}".format(r["n_tool_calls"]))
    print("\nreads")
    for b in BUCKETS:
        print("  {:<12} {:>6}  {:>8}".format(
            b, r["reads"][b], human(r["reads"]["est_tokens"][b])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
