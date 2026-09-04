# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A collection of authored Claude Code **agent skills**. For the `skills` plugin there is no source
code, no build, no test runner, no dependencies — every artifact is markdown that gets loaded into
an agent's context. The "product" is agent behaviour, so the only meaningful verification is
behavioural (see Testing).

The one exception is `context-watch/`, a second plugin vendored from
[troglodyte/context-watch-plugin](https://github.com/troglodyte/context-watch-plugin). It ships
python (a `UserPromptSubmit` guard hook and two tools) with a real unittest suite:

```
cd context-watch && python3 -m unittest discover -s tests
```

Upstream is the source of truth for it. Fix things there and re-vendor; a fix made only here will
be overwritten the next time this copy is refreshed.

## Layout

The repo is both a plugin and its own marketplace, and the marketplace lists two plugins:

```
.claude-plugin/
  marketplace.json   # marketplace "trog-skills": plugin "skills" (source ".")
                     # plus plugin "context-watch" (source "./context-watch")
  plugin.json        # the "skills" plugin manifest — bump version here on release
skills/
  <skill-name>/
    SKILL.md         # required — frontmatter + the skill body
    *.md             # optional reference files, loaded only on demand
    TESTING.md       # optional — behavioural test record for that skill
context-watch/       # the second plugin, vendored — its own .claude-plugin/plugin.json,
                     # skills/check/, hooks/, tools/, tests/
```

`context-watch` is a separate plugin rather than another directory under `skills/` because
installing it registers a hook that runs on every turn. Folding it into `skills` would force that
on anyone who wanted only the markdown skills.

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
/plugin install context-watch@trog-skills     # optional, adds the per-turn guard hook
```

One plugin ships every *skill*. That was a deliberate call over plugin-per-skill: nothing under
`skills/` is worth installing in isolation yet, and the split would cost a nested `plugin.json`
plus a marketplace entry per skill. `context-watch` is the exception, and the reason is the hook,
not the skill — see Layout. Revisit the rest if someone actually wants one skill without the others.

Symlinking a single skill into `~/.claude/skills/<name>` still works and is the faster loop while
iterating on one skill. Current state worth knowing (verified 2026-09-03):

- **The plugin is installed from GitHub, not from this checkout.** `skills@trog-skills` resolves to
  `~/.claude/plugins/cache/trog-skills/skills/0.3.0`, cloned from `troglodyte/skills`. Every
  `skills:<name>` entry in the skill list is that frozen 0.3.0 snapshot — editing this repo does
  **not** change it until a release is tagged, pushed, and the plugin updated. As of 0.3.0 the cache
  and `main` are byte-identical, so the distinction is currently invisible; it stops being invisible
  the moment anything lands on `main`.
- `design-patterns` is *also* installed by symlink at `~/.claude/skills/design-patterns`, now
  pointing at `/Users/michael.harris/code/skills/skills/design-patterns` — the **main checkout**, so
  it tracks `main` and survives worktree cleanup. It was repointed from a byte-identical copy in
  `code/utils-folder`. This means design-patterns appears twice in the skill list: the live symlink
  and the plugin's 0.3.0 copy. That redundancy is the price of the fast edit loop; delete the symlink
  if the duplicate ever causes trouble.
- `deploy`, `markdown`, `explain-it-to-me` and `run-script-handoff` have **no symlink** — they reach
  the agent only through the plugin cache. Edits here are not live for them.
- `deploy`'s baseline test is recorded but the GREEN arm has never been run — see
  `deploy/TESTING.md` before trusting it.
- `~/.claude/skills/pr-review` is a symlink into a **git worktree**
  (`.claude/worktrees/npm-aws-codeartifact-migration-ba3733/skills/pr-review`, branch
  `claude/code-review-skill-6ad4fd`). That skill is not on `main` and the symlink breaks if the
  worktree is removed. Land the branch, then repoint at the main checkout.
- `~/.claude/skills/nasa-coding-standards` is a symlink to the **main checkout**
  (`/Users/michael.harris/code/skills/skills/nasa-coding-standards`), repointed there when the
  branch landed in `edbfa75`, so it tracks `main` and survives worktree cleanup. It is not in the
  0.3.0 plugin cache, so that symlink is the only path reaching the agent until a release is cut —
  the plugin ships nothing for it yet. Its behavioural record is unusually complete and unusually
  unflattering: read `nasa-coding-standards/TESTING.md` before trusting any claim about it, in
  particular the confound section and the two rules that score 0/6.
- `improve-codebase-architecture/` at the repo root is an empty untracked stub, outside `skills/` and
  therefore not shipped; the installed skill of that name comes from `~/.agents/skills/`.
- `context-watch` is installed from its own marketplace
  (`context-watch@context-watch`, cached under `~/.claude/plugins/cache/context-watch/`), **not**
  from this repo's copy. Editing `context-watch/` here changes nothing in a running session until
  that install is repointed at `trog-skills`.

`design-patterns` is additionally reinforced by a "Design dialog" section in `~/.claude/CLAUDE.md`.
That section was deliberately kept after testing — see `design-patterns/TESTING.md` before removing it.

## Testing a skill

There is nothing to run for the skills under `skills/` (`context-watch`'s python is the exception,
and its unittest suite is above). A skill is tested by dispatching general-purpose subagents at a fixture and
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
