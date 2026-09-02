# skills

Claude Code agent skills, packaged as plugins. The repo is its own marketplace, `trog-skills`,
and ships two plugins: `skills` (markdown-only agent skills) and `context-watch` (a skill plus a
guard hook and its python tools).

## Install

```
/plugin marketplace add troglodyte/skills
/plugin install skills@trog-skills
/plugin install context-watch@trog-skills   # optional, installs a per-turn guard hook
```

## What's in `skills`

| Skill | Fires when |
|---|---|
| `deploy` | The user says "deploy", "land this", or "ship it" about finished work on a branch. Runs the whole landing sequence — merge, version bump, changelog, annotated tag, `--follow-tags` push, branch and worktree cleanup — and ships the branch **unmodified**. |
| `design-patterns` | You're about to write code with a structural choice — a new module, another variant of something that exists, one more branch in a type dispatch, a config object that keeps growing. Runs a short dialog to name the axis of change and settle the shape, starting from the direct version. |
| `explain-it-to-me` | Someone needs to come up to speed on a body of git work — "catch me up on this repo", "what changed while I was out", "summarize this branch", "write a handoff doc". Reads the diff rather than rewording the log, and adds Mermaid diagrams and tables where they earn their place. |
| `markdown` | You're producing or fixing a `.md` file that renders somewhere else — READMEs, docs pages, specs, changelogs, ADRs, PR descriptions. A design spec for Markdown that survives the destination renderer, since most Markdown defects are invisible in the source. |
| `run-script-handoff` | You're about to hand a human a command to run in their own terminal and paste back. Covers the task slug, `run/<slug>.sh`, colored output helpers, and the `tee` + clipboard invocation line. |

Each skill is a directory under `skills/`, and its `SKILL.md` frontmatter `name` must match that
directory name — a mismatch means Claude never loads the skill.

## What's in `context-watch`

Vendored from [troglodyte/context-watch-plugin](https://github.com/troglodyte/context-watch-plugin),
which remains its upstream home. Unlike the `skills` plugin it is not markdown-only — installing it
registers a `UserPromptSubmit` guard hook that runs on **every turn**, which is why it is a separate
plugin you opt into rather than another directory under `skills/`.

| Piece | What it does |
|---|---|
| `context-watch:check` skill | Fires when a session feels long or expensive, when the guard warns, or when asked to cut context. Measures where the context actually went, scans `CLAUDE.md` and installed skills for preamble bloat, then walks through `/clear` vs `/compact` vs dispatching a subagent. |
| `hooks/guard.py` | Watches each turn for the context sizes that concentrate cost (defaults 60k and 150k, set by `CONTEXT_WATCH_THRESHOLDS`) and warns once per threshold. Measured at 50ms against a 16.5MB transcript. |
| `tools/session_cost.py`, `tools/scanner.py` | The measurement behind the skill: per-session cost accounting and the preamble-bloat scanner. |

Its python is tested the ordinary way, unlike the markdown skills:

```
cd context-watch && python3 -m unittest discover -s tests
```
