---
name: check
description: Use when a session feels long or expensive, when the context-watch guard warns, or when asked to reduce context/token usage - diagnoses what is consuming context and applies a deliberate compaction procedure
---

# Context Check

Diagnose what is consuming this session's context, then act on it.

## Step 1: Measure

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/tools/session_cost.py" --session-id "${CLAUDE_SESSION_ID}" --cwd "$(pwd)"
```

If the session id is unavailable, find the newest transcript for this directory:

```bash
BASE="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
DIR="$BASE/projects/$(pwd | sed 's/[\/.]/-/g')"
LATEST=$(ls -t "$DIR"/*.jsonl 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
  python3 "${CLAUDE_PLUGIN_ROOT}/tools/session_cost.py" --transcript "$LATEST"
else
  echo "No transcript yet for this directory."
fi
```

## Step 2: Scan the preamble

```bash
BASE="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
python3 -c "
import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/tools')
import scanner, os
base = '$BASE'
for r in scanner.scan_claude_md(os.getcwd()):
    print('%-8s %6d  %s' % (r['verdict'], r['est_tokens'], r['path']))
u = scanner.scan_unused(base + '/skills', base + '/projects')
print('unused skills: %d (~%d tokens)' % (len(u['unused_skills']), u['est_recoverable']))
"
```

`CLAUDE.md` sits at position zero and is re-read every turn, so its cost is
size x turn count. Anything flagged is the first thing to trim.

## Step 3: Choose the cheapest action that fits

The governing relation is **cost ~= context size x remaining turns**. Content
entering context early is multiplied by every turn after it.

- **Next task is independent of this one -> `/clear`.** Drops context to zero.
  Compaction would preserve a summary that is not needed. This is the
  highest-leverage habit.
- **Same task, history is long -> `/compact <instructions>`.** Always
  instructed; never leave it to auto-compact.
- **About to explore broadly -> dispatch a subagent.** Reads land in the
  subagent's context and die there; only the conclusion returns. This flattens
  the growth curve instead of trimming after the fact.

## Step 4: If compacting, say what to keep

Preserve what cannot be re-derived:

- decisions and their rationale
- constraints found empirically ("fzf needs `--filter`; fails without a TTY")
- current task state: what is done, what remains
- corrections, so a wrong path is not retried

Drop aggressively, starting with file contents. Re-reading files costs about
0.04% of billed tokens, so discarding bodies and re-reading on demand is very
nearly free. Keep the paths, discard the text. Also drop tool output already
acted upon, and abandoned approaches beyond a one-line note of what failed.

This is deliberately the opposite of what auto-compact tends to preserve.
