# skills

Claude Code agent skills, packaged as a plugin.

## Install

```
/plugin marketplace add troglodyte/skills
/plugin install skills@trog-skills
```

## What's in it

| Skill | Fires when |
|---|---|
| `deploy` | The user says "deploy", "land this", or "ship it" about finished work on a branch. Runs the whole landing sequence — merge, version bump, changelog, annotated tag, `--follow-tags` push, branch and worktree cleanup — and ships the branch **unmodified**. |
| `design-patterns` | You're about to write code with a structural choice — a new module, another variant of something that exists, one more branch in a type dispatch, a config object that keeps growing. Runs a short dialog to name the axis of change and settle the shape, starting from the direct version. |
| `explain-it-to-me` | Someone needs to come up to speed on a body of git work — "catch me up on this repo", "what changed while I was out", "summarize this branch", "write a handoff doc". Reads the diff rather than rewording the log, and adds Mermaid diagrams and tables where they earn their place. |
| `markdown` | You're producing or fixing a `.md` file that renders somewhere else — READMEs, docs pages, specs, changelogs, ADRs, PR descriptions. A design spec for Markdown that survives the destination renderer, since most Markdown defects are invisible in the source. |
| `run-script-handoff` | You're about to hand a human a command to run in their own terminal and paste back. Covers the task slug, `run/<slug>.sh`, colored output helpers, and the `tee` + clipboard invocation line. |

Each skill is a directory under `skills/`, and its `SKILL.md` frontmatter `name` must match that
directory name — a mismatch means Claude never loads the skill.
