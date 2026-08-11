---
name: repo-work-summary
description: Produce a markdown briefing that explains what work was done in a repository — high-level narrative, the details worth knowing, gotchas, plus Mermaid diagrams, tables, and charts where they earn their place. Use this skill whenever the user wants to come up to speed on code changes, including requests like "catch me up on this repo", "what changed while I was out", "summarize this branch or PR", "explain the last 20 commits", "what did we ship last sprint", "write a handoff doc for this work", or "review what's on this branch" — and any other request to understand, review, or document a body of work in a git repo, even if the user never says the word "summary".
---

# Repo Work Summary

Turn a body of git history into a briefing someone can read in a few minutes and actually understand what happened, why, and what to watch out for.

The failure mode to avoid: a reworded commit log. Commit messages describe intent at the moment of writing; they miss what was actually changed, what got abandoned halfway, and what will bite the reader later. **Read the diff, not just the log.** The value of this briefing is the stuff a reader couldn't get from `git log` themselves.

## Step 1: Resolve the scope

Figure out precisely which commits are in scope before gathering anything. Ask if genuinely ambiguous, but prefer inferring from context and stating your assumption in the output.

| User says | Scope |
|---|---|
| "this branch" / "this PR" | `git merge-base HEAD <base>..HEAD` — commits unique to the branch |
| "last N commits" | `HEAD~N..HEAD` |
| "since Friday" / "last 2 weeks" | `--since=<date>` |
| "what changed while I was out" | `--since` their last activity; if unknown, ask or default to 2 weeks |
| "catch me up on this repo" (fresh clone, no timeframe) | Recent meaningful history — last ~30 commits or 2 weeks, whichever is smaller; say which you chose |

Determine the base branch rather than assuming `main`: check `git symbolic-ref refs/remotes/origin/HEAD`, then fall back to whichever of `main`/`master`/`develop` exists.

If the scope turns out to be enormous (hundreds of commits, thousands of changed lines), don't silently truncate. Summarize the shape of it, then go deep on the parts that matter most and say explicitly what you skimmed.

## Step 2: Gather evidence

Run `scripts/collect.sh` to pull the standard evidence set in one pass:

```bash
bash scripts/collect.sh <base-ref> <head-ref>       # range mode
bash scripts/collect.sh --since "2 weeks ago"        # time mode
```

It writes a set of files to a temp directory and prints the path: commit log with stats, `diff --stat`, changed-file list, per-area churn, merge commits, and the full diff (capped). Read the summaries first, then read the actual diff for the files that matter.

Then go beyond the mechanical collection, because this is where the real insight comes from:

- **Read the substantive diffs in full.** Prioritize by churn and by importance: entry points, core modules, schema/migration files, config, CI, dependency manifests. Skim generated files, lockfiles, and vendored code.
- **Follow the "why".** Linked issue/PR numbers in commit messages, comments added alongside changes, and revert commits all explain motivation the log alone doesn't.
- **Check for tests.** Did behavior change without test changes? That's worth flagging.
- **Look for loose ends**: new `TODO`/`FIXME`/`XXX` markers, commented-out code, `skip`ped tests, stubbed functions, hardcoded values that look temporary.
- **Look for anything operationally sticky**: new env vars, new dependencies, DB migrations, changed API shapes or defaults, renamed public functions, changed build steps. These are what break the reader's afternoon.

If a repo-specific detail can't be determined from what's in the repo, say so rather than guessing. Fabricated confidence is worse than an acknowledged gap.

## Step 3: Choose a depth

Match the depth to what they asked for. When unclear, default to Standard.

- **Quick** (~1 page) — the narrative, a changed-areas table, top gotchas. No diagrams unless one is genuinely clarifying. For "just tell me what happened."
- **Standard** (2–4 pages) — the full template below. The default.
- **Deep** — Standard plus per-change-set detail, file-level walkthroughs of the important modules, and review-grade observations (correctness concerns, edge cases, design questions). For reviewing someone else's work or writing a real handoff.

Offer the adjacent depth at the end of the document: "Want me to go deeper on the auth refactor?" is more useful than padding.

## Step 4: Write the document

Structure to follow. Drop sections that would be empty rather than writing "N/A" — an empty section is noise, and noise is what makes people stop reading these.

```markdown
# What changed in <repo> — <scope description>

**Scope:** <exact range or date window> · <N> commits · <N> files · +<X>/-<Y> lines
**Contributors:** <who>
**Read time:** ~<N> min

## The short version
Three to five sentences. What was the goal of this work, what got done, and
what state is it in now. Someone who reads only this paragraph should be able
to hold a conversation about it.

## Themes
The work grouped by intent, not by commit order — usually 2–5 themes, each a
few sentences. This is the main body. Reference concrete files and functions so
the reader can jump straight to the code.

## What changed where
<table: area/module | what happened | files touched | why it matters>

## Details worth knowing
The non-obvious things. Design decisions and their tradeoffs, behavior changes
that aren't visible from the API surface, patterns newly introduced that the
reader should follow, deliberate deviations from how the codebase used to work.

## Watch out for
Breaking changes, new env vars or config, migrations to run, new dependencies,
changed defaults, anything that will surprise someone pulling this branch.
Lead with the highest-consequence item.

## Loose ends
Unfinished work, TODOs added, skipped or missing tests, known-broken paths,
things clearly intended as follow-ups.

## If you're picking this up
Where to start reading, what to run to verify it works, what's likely next.
```

Then apply judgment: if the work is one tight feature, themes may collapse into one section; if it's a mixed bag of unrelated commits, say so plainly ("this is maintenance week, not a coherent project") rather than manufacturing a narrative.

## Diagrams, tables, charts

Use them where they carry information text carries badly, and skip them otherwise. A wrong or decorative diagram costs the reader more than no diagram — they'll try to make sense of it.

Diagrams go in Mermaid so they render in GitHub, VS Code, and most markdown viewers.

| When the work is about... | Reach for |
|---|---|
| A request/data path through several components | `flowchart LR` |
| Interaction between services, client/server, async steps | `sequenceDiagram` |
| Schema or model changes | `erDiagram` |
| Status/lifecycle logic (order states, job states, auth states) | `stateDiagram-v2` |
| Module or dependency restructuring | `flowchart` with subgraphs, before/after side by side |
| Sequenced or overlapping work over time | `gantt` or `timeline` |

For a before/after refactor, two small diagrams beat one cluttered one. Mark new or changed nodes distinctly — a `:::new` class, or bold labels — so the reader sees the delta at a glance instead of diffing two pictures by eye.

**Tables** are the workhorse: changed areas, before/after behavior, new config vars and their defaults, dependency additions with versions and reasons, API surface changes. Prefer a table any time the content is 3+ items with 2+ dimensions.

**Charts** — only when quantity is actually the point (churn by module across a sprint, commit volume over time). Render as a Mermaid `xychart-beta` or `pie`, or as a plain table with inline bars (`████░░`, which renders everywhere and never breaks). Don't chart 4 numbers; a sentence beats a chart at that size.

Keep Mermaid syntax conservative: quote labels containing punctuation, avoid parentheses and `<br>` in node text, and prefer plain node shapes. Fancy syntax is where Mermaid breaks silently — read `references/diagram-patterns.md` before writing a diagram for tested snippets of each type and the specific things that break parsing.

## Output

Write to a file — these documents get shared, re-read, and committed:

- Default path: `<repo-root>/docs/summaries/YYYY-MM-DD-<slug>.md`, or wherever the repo already keeps notes if such a place exists.
- If the repo has no obvious home for it and the user hasn't said, write to the repo root as `WORK-SUMMARY-<slug>.md` and mention they may want to move or gitignore it.
- Then give a 2–3 sentence verbal summary in the conversation and the file path. Don't paste the whole document back into chat.

## Worked example

**Input:** "Catch me up on the payments branch, I've been out two weeks."

**Approach:** resolve `origin/main...payments`, collect evidence, notice 60% of churn is in `billing/` plus a new `migrations/0043_add_idempotency_keys.py`, read those diffs closely, spot that the retry path changed behavior without a corresponding test, notice `STRIPE_WEBHOOK_SECRET` is newly required.

**Output shape:** narrative naming the goal (idempotent payment retries); themes for the idempotency layer, webhook handling, and incidental cleanup; a `sequenceDiagram` of the new retry/webhook flow since the ordering is the whole point; a table of changed areas; "Watch out for" leading with the migration and the new required env var; loose ends noting the untested retry path and two TODOs about partial refunds.

That output is useful because the reader learns the migration and the env var — the two things that would have cost them an hour — in the first thirty seconds.
