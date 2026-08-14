---
name: deploy
description: Use when the user says "deploy", "land this", "ship it", or "cut a release" for finished work sitting on a branch — one word standing in for a whole sequence they don't want to spell out again. Also use before merging a feature branch into the default branch, creating a release tag, or pushing tags.
---

# Deploy

One word, one sequence, run to the end. The user types "deploy" *instead of*
spelling out merge, bump, changelog, tag, push, clean up — so stopping after
the merge to ask about the tag turns one instruction into four round trips,
which is the thing the word exists to prevent.

## The rule that is not a step

**Deploy ships what is on the branch. It does not improve it.**

Given a branch containing what looked like a defect, 3 of 3 baseline agents
fixed the code and committed the fix into the release. Each was reasoning
sensibly — "I would not ship a confirmed parse error" — and each shipped
something nobody had reviewed. A deploy that amends the work destroys the
only guarantee the operation carries: that what ships is what was tested.

If the branch looks broken, **land nothing and say so.** The user can fix it
and deploy again; that costs one message. No exceptions:

- Not for a one-line, obviously-correct fix
- Not for a parse error or a failing test you confirmed yourself
- Not because "the previous commit clearly intended this"
- Lint, formatting, imports and stray comments are work, not deployment

## Learn this repo's convention first

The last release did it correctly. Copy it rather than guessing:

```sh
git log --oneline --graph -15
git show --stat <last release commit>    # names the version file for you
git tag -l | tail -5
git cat-file -t <latest tag>             # 'tag' = annotated, 'commit' = lightweight
```

That `--stat` is the portable answer to "where does the version live" —
`Cargo.toml`, `package.json`, `pyproject.toml`, a `VERSION` file, a gemspec —
without pattern-matching on ecosystem. It also shows whether releases merge
with `--no-ff`, what the commit message looks like, and whether a lockfile
moves alongside.

Repo instructions — `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, the
changelog preamble — outrank both this skill and the git history. Read them
before starting.

## The sequence

1. **Account for the working tree.** An uncommitted edit that belongs to this
   branch's work gets its own commit. Anything you cannot attribute: stop and
   ask. Never `git add -A` — stage explicit paths, or you sweep up another
   agent's worktree gitlink. Never leave a stash behind for someone else to
   pop.
2. **Merge the branch into the default branch**, in the style the history
   shows. Where past releases have merge commits, use `--no-ff`; a
   fast-forward erases the record those repos read their history from.
3. **Bump the version on the default branch, at the merge** — never on the
   feature branch, where a later rebase or squash invalidates a version
   already tagged.
4. **Write the changelog section** for that version.
5. **Commit bump and changelog together**, in the message shape the last
   release used.
6. **Tag the release commit, annotated** (`git tag -a`).
7. **Push with `--follow-tags`.** A bare `git push` does not send annotated
   tags, and a tag that exists only locally is not a release.
8. **Delete the merged branch and prune stale worktrees.** Confirm the merge
   against the *remote* — `git rev-list --count origin/<default>..<branch>`
   must be 0 — because the local default-branch ref goes stale in repos that
   push `<branch>:<default>`. 3 of 3 baseline agents left a stale worktree
   standing, each reasoning it was "unrelated to this task".
9. **Leave the primary checkout on the default branch**, clean and level with
   the remote. That directory is where the human works; ending on a deleted
   branch, or behind the remote, is not finished.

Docs-only and chore branches merge and push with **no bump and no tag**.

## When the push is refused

Some environments deny pushes to an agent outright.

- Run the local sequence, stop at the push, and say plainly what is unpushed.
- **Do not ask another agent or session to run it, and do not add a permission
  rule allowing it.** Both route around a refusal, and the refusal is the
  point. 2 of 3 baseline agents ended by proposing exactly that.

## Red flags — stop

- You are editing a source file
- You are running the test suite to decide whether to fix something first
- You bumped the version while still on the feature branch
- You are about to `git push` without `--follow-tags`
- You are reporting done with a worktree still listed, or the checkout parked
  on a branch that no longer exists
- You are wondering who else could run the push for you
