# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A collection of authored Claude Code **agent skills**. There is no source code, no build, no test
runner, no dependencies — every artifact is markdown that gets loaded into an agent's context. The
"product" is agent behaviour, so the only meaningful verification is behavioural (see Testing).

## Layout

The repo is both a plugin and its own single-plugin marketplace:

```
.claude-plugin/
  marketplace.json   # marketplace "trog-skills", one plugin, source "."
  plugin.json        # the plugin manifest — bump version here on release
skills/
  <skill-name>/
    SKILL.md         # required — frontmatter + the skill body
    *.md             # optional reference files, loaded only on demand
    TESTING.md       # optional — behavioural test record for that skill
```

Skills **must** live under `skills/` — that is where Claude Code looks inside a plugin. Adding a
skill is just a new directory there; neither manifest needs editing (the plugin ships all of them,
deliberately — see the note under Installation).

`SKILL.md` frontmatter needs `name` (matching the directory) and `description`. **The description is
the trigger** — it is what the agent sees before deciding to load the skill, so it carries the
"Use when …" conditions and is the part most worth testing. Body length counts against context on
every load; reference material that isn't always needed belongs in a sibling file
(`design-patterns/patterns.md` is the example — the symptom→pattern catalog split out of SKILL.md to
cut it from 1412 to ~750 words).

Follow `superpowers:writing-skills` when creating or editing a skill.

## Installation

The intended path is the plugin marketplace:

```
/plugin marketplace add troglodyte/skills     # or a local path while developing
/plugin install skills@trog-skills
```

One plugin ships every skill. That was a deliberate call over plugin-per-skill: nothing here is
worth installing in isolation yet, and the split would cost a nested `plugin.json` plus a
marketplace entry per skill. Revisit if someone actually wants one skill without the others.

Symlinking a single skill into `~/.claude/skills/<name>` still works and is the faster loop while
iterating on one skill. Current state worth knowing:

- `design-patterns` is installed by symlink, but it points at
  `/home/trog/code/utils-folder/skills/design-patterns` (byte-identical copy, different repo). This
  repo is the newer home; editing here does **not** change the installed skill until that symlink is
  repointed or the plugin is installed.
- `run-script-handoff` is not installed anywhere yet.
- `improve-codebase-architecture/` at the repo root is an empty untracked stub, outside `skills/` and
  therefore not shipped; the installed skill of that name comes from `~/.agents/skills/`.

`design-patterns` is additionally reinforced by a "Design dialog" section in `~/.claude/CLAUDE.md`.
That section was deliberately kept after testing — see `design-patterns/TESTING.md` before removing it.

## Testing a skill

There is nothing to run. A skill is tested by dispatching general-purpose subagents at a fixture and
scoring **the shape of the reply**, never by asking the agent whether it used the skill (that
contaminates the result). `design-patterns/TESTING.md` is the worked example and the template:
fixture, prompt, explicit pass criteria, history table, open questions.

Two halves, both required:

- **Under-fire test** — a fixture that should trigger the skill, run ~3 reps, with the prompt loaded
  with pressure to skip ("it's mechanical", "before standup"). Score against written criteria.
- **Over-fire check** — an adjacent task the skill should *not* touch. Pass = the agent just does the
  work. A skill that fires on everything has become ritual, which is the worse failure.

Hard-won gotchas:

- Give every rep its own directory with its own fixture copy. Parallel subagents on one file race and
  report phantom findings.
- Subagents inherit the **session's** CLAUDE.md snapshot, not the file on disk. Editing CLAUDE.md
  mid-session does nothing for subagents spawned afterward — start a fresh session.
- Variance across reps is the signal. Three reps converging means the wording binds; three different
  interpretations means it doesn't, however reasonable each one looks alone.
- A null result from a fixture that passes under every arm is not evidence of no effect — it means
  the fixture is saturated and needs to be made harder before it can discriminate.

Record results in the skill's `TESTING.md` history table, including changes that *didn't* hold.

## Note on run-script-handoff

Its conventions (`run/<slug>.sh`, `tools/colors.sh`, `scripts-history/`, the `tee`/`pbcopy`
invocation line) describe the **target** repos the skill is used in. Nothing in this repo follows or
needs that layout.
