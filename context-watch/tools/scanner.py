#!/usr/bin/env python3
"""Inspect what sits at position zero of every turn.

CLAUDE.md is re-read on every turn, so its cost is size x turn count.
An 8.6k-token CLAUDE.md in a 2793-message session is ~24M tokens.
"""

import json
import os
import re
from pathlib import Path

CHARS_PER_TOKEN = 4.0
ADVISE_AT = 3000
FLAG_AT = 6000


def est_tokens(path):
    try:
        return int(Path(path).stat().st_size / CHARS_PER_TOKEN)
    except OSError:
        return 0


def _verdict(tokens):
    if tokens >= FLAG_AT:
        return "flag"
    if tokens >= ADVISE_AT:
        return "advise"
    return "ok"


def _is_file(path):
    """Path.is_file() lets PermissionError escape on Python < 3.13, whose
    ignored-errno list omits EACCES. One unsearchable directory anywhere on
    the walk must not crash the scan."""
    try:
        return path.is_file()
    except OSError:
        return False


def _is_dir(path):
    try:
        return path.is_dir()
    except OSError:
        return False


def scan_claude_md(cwd):
    """Every CLAUDE.md from cwd up to the filesystem root, plus the global one.

    cwd is resolved first: Path("a/b").parents stops at ".", so a relative
    cwd would silently walk only part of the way and under-report.
    """
    try:
        cwd = Path(cwd).resolve()
    except OSError:
        return []
    if not _is_dir(cwd):
        return []
    out = []
    seen = set()
    for d in [cwd] + list(cwd.parents):
        f = d / "CLAUDE.md"
        if _is_file(f) and str(f) not in seen:
            seen.add(str(f))
            t = est_tokens(f)
            out.append({"path": str(f), "est_tokens": t, "verdict": _verdict(t)})
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    g = ((Path(cfg) if cfg else Path.home() / ".claude") / "CLAUDE.md").resolve()
    if _is_file(g) and str(g) not in seen:
        t = est_tokens(g)
        out.append({"path": str(g), "est_tokens": t, "verdict": _verdict(t)})
    return out


def used_names(projects_dir):
    """Skill and MCP-server names actually invoked across the corpus.

    Substring pre-filter before json.loads: only a small fraction of lines
    mention either, and full parsing of ~900MB is not worth the wait.
    """
    skills, mcp = set(), set()
    root = Path(projects_dir)
    if not _is_dir(root):
        return {"skills": skills, "mcp": mcp}
    for f in root.rglob("*.jsonl"):
        try:
            fh = open(str(f), "r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"Skill"' not in line and "mcp__" not in line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                msg = rec.get("message")
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for b in content:
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    name = b.get("name") or ""
                    if name == "Skill":
                        inp = b.get("input")
                        if isinstance(inp, dict) and inp.get("skill"):
                            skills.add(str(inp["skill"]).split(":")[-1])
                    elif name.startswith("mcp__"):
                        mcp.add(_mcp_stem(name))
    return {"skills": skills, "mcp": mcp}


def _mcp_stem(name):
    """Server name out of an MCP tool name.

    The plugin convention doubles the server name
    (mcp__plugin_playwright_playwright__browser_click), a bare server does
    not (mcp__ide__getDiagnostics). Undoing the doubling unconditionally
    would truncate any plain server name containing an underscore, so only
    strip a half that genuinely repeats.
    """
    body = name[len("mcp__"):] if name.startswith("mcp__") else name
    plugin = body.startswith("plugin_")
    if plugin:
        body = body[len("plugin_"):]
    stem = body.split("__")[0]
    if plugin:
        half = len(stem) // 2
        if len(stem) % 2 == 1 and stem[half] == "_" and stem[:half] == stem[half + 1:]:
            return stem[:half]
    return stem


def _est_listing_cost(skill_dir):
    """A skill costs name + description in the listing; the body loads on demand.

    The description is frequently a folded multi-line YAML scalar, so it runs
    until the next top-level key. Matching only to end-of-line would capture
    the first line and silently undercount the very number this reports.
    """
    f = Path(skill_dir) / "SKILL.md"
    try:
        txt = f.read_text(errors="replace")
    except OSError:
        return 0
    m = re.search(r"^---\n(.*?)\n---", txt, re.S)
    desc = ""
    if m:
        d = re.search(r"^description:\s*(.*?)(?=\n\S|\Z)", m.group(1), re.M | re.S)
        desc = " ".join(d.group(1).split()) if d else ""
    return int((len(Path(skill_dir).name) + len(desc)) / CHARS_PER_TOKEN)


def scan_unused(skills_dir, projects_dir):
    skills_dir = Path(skills_dir)
    if not _is_dir(skills_dir):
        return {"unused_skills": [], "est_recoverable": 0}
    used = used_names(projects_dir)["skills"]
    unused, total = [], 0
    for d in sorted(skills_dir.iterdir()):
        # Matched on bare directory name, so a personal skill sharing a name
        # with an invoked plugin skill reads as used. That biases toward
        # under-reporting waste, which is the safe direction for an advisory.
        if not _is_file(d / "SKILL.md") or d.name in used:
            continue
        cost = _est_listing_cost(d)
        total += cost
        unused.append({"name": d.name, "est_tokens": cost})
    return {"unused_skills": unused, "est_recoverable": total}
