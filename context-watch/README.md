# context-watch

Warns when a Claude Code session enters the expensive population, and provides
a deliberate compaction procedure plus a preamble-bloat scanner.

## Why

Measured across 5,713 sessions: 0.8% of sessions account for 73.8% of all
cache-read tokens. Sessions that ever exceed 60k context account for 98.3%.
Cost is concentrated in a rare tail, so detection has to be automatic.

The guard hook that watches for this runs on every turn, so it has to be
cheap: measured at 50ms against a 16.5MB real transcript. The preamble
scanner is a secondary check — on the corpus that motivated it, unused
skills account for only ~569 tokens, which is why it exists to keep the
answer honest as setups change rather than because it currently finds much.

## Install

The plugin lives at `context-watch/` inside the repo, so the marketplace is the
outer repo and the plugin is selected from within it:

    /plugin marketplace add troglodyte/context-watch-plugin
    /plugin install context-watch@context-watch

This copy is also vendored into the `trog-skills` marketplace, where the same
plugin is installed as:

    /plugin marketplace add troglodyte/skills
    /plugin install context-watch@trog-skills

`troglodyte/context-watch-plugin` is upstream; changes belong there first.

## Usage

When the guard warns, or a session feels long or expensive, run
`/context-watch:check`. It measures where context is going, scans `CLAUDE.md` and
installed skills for bloat, and walks through choosing between `/clear`,
`/compact`, and dispatching a subagent — then, if compacting, what to keep
and what to drop.

## Configuration

- `CONTEXT_WATCH_THRESHOLDS` — comma-separated context sizes. Default `60000,150000`.
- `CONTEXT_WATCH_STATE_DIR` — where one-shot state lives. Default `~/.claude/.context-watch/`.

## Tests

    python3 -m unittest discover -s tests -v
