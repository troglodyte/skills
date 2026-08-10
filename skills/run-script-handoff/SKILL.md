---
name: run-script-handoff
description: Conventions for handing the user a shell command or script to run in their own terminal — the task slug, script location and naming under run/, colors.sh output helpers, /tmp path naming, the tee + pbcopy invocation line, and archiving to scripts-history/. Use this whenever you are about to give the user something to run, ask them to execute or paste anything, or write/edit any script under run/ or cicd/ — including one-liners, quick one-offs, and edits to a script that already exists. If your next message would contain a command in a code block for the user to run, use this skill first.
---

# Handing run scripts to the user

The user runs these commands in their own terminal and then pastes the output back into the
conversation. That round trip is the whole point of the conventions below: the script exists so
they don't have to retype anything, and the invocation line exists so the output lands on their
clipboard without a second thought. A handoff that makes them hunt for output, or scroll a wall of
uncolored text, has failed even if the command itself was correct.

## Pick a slug first

One short, task-shaped slug per task, reused everywhere — script name, tmp files, snapshots.

`cog-stg` → `run/cog-stg.sh`, `/tmp/cog-stg.txt`

Terse and human, not a log line. `run/cog-staging.sh`, never
`run/1785860027-tmp_run-cognito-lambda-staging-cutover.sh`. Same for tmp paths:
`/tmp/cog-stg.txt`, never `/tmp/tl-cognito-lambda-staging-cutover-output.txt`. No timestamps, no
`tmp_run` marker — `/run/` is git-ignored, so nothing needs to be disambiguated from real code.

## Write the script

Everything goes in **`run/<slug>.sh`**. Even a single command — the user should always be pasting
one line, and a file can be edited and re-run without a fresh copy-paste. Reuse the same file while
iterating on a task rather than making `-v2` variants.

Source the color helpers so the output is readable, and use them:

```bash
#!/usr/bin/env bash
set -euo pipefail
source tools/colors.sh

step "Fetching current staging config"
aws cognito-idp describe-user-pool --user-pool-id "$POOL_ID" > /tmp/cog-stg-pool.json
ok "Saved pool config"

warn "About to overwrite the client callback URLs"
```

- `step` — cyan section header, one per phase of the script
- `ok` — green, confirms a phase landed
- `warn` — yellow, something the user should read before it scrolls past
- `err` — red, failure paths
- `info` — plain detail

`colors.sh` auto-disables color when piped or when `NO_COLOR` is set, so it's safe under the `tee`
below. Scripts are run from the repo root, so `source tools/colors.sh` resolves as written.

`set -euo pipefail` matters more than usual here: the user is reading the output rather than
checking `$?`, so a silently-skipped step will look like a success.

## The invocation line

Hand over exactly this shape, as one line:

```bash
nvm use && bash run/cog-stg.sh 2>&1 | tee /tmp/cog-stg.txt; pbcopy < /tmp/cog-stg.txt
```

Every piece is load-bearing:

- **`2>&1`** — stderr is usually the interesting half when something breaks. Without it, errors
  reach the terminal but not the file, so the clipboard shows a truncated success story.
- **`tee /tmp/<slug>.txt`** — the user watches it live *and* keeps a copy.
- **`; pbcopy`** — a semicolon, not `&&`. On `&&` the copy is skipped exactly when the run failed,
  which is when the user most needs to paste it back. The full output goes on the clipboard, not a
  tail — truncating hides the earlier step that actually caused the failure.
- **`pbcopy < /tmp/<slug>.txt`** reading the file, not piping into it, so re-copying later is just
  that same fragment again.
- **`nvm use`** for Node projects; drop it where it's irrelevant.

Don't collapse this into `| tee /tmp/cog-stg.txt | pbcopy` — that routes stdout into `pbcopy` and
the user sees a blank terminal while it runs.

## Lifecycle

While iterating on a task, keep editing `run/<slug>.sh`. Once the task is finished or superseded,
move it to `scripts-history/<slug>.sh` as the archive:

```bash
mv run/cog-stg.sh scripts-history/cog-stg.sh
```

`/run/` and `/scripts-history/` are both git-ignored (as is legacy `*tmp_run*.sh`, for old files),
so none of this needs a commit.

## Also applies to

The per-app ops scripts in `cicd/<app>/*.sh` follow the same `colors.sh` conventions, and get the
same `tee`/`pbcopy` invocation line when handed over. They aren't disposable, so they keep their
real names and stay in git — the `run/` naming and archiving rules don't apply to them.

## Before sending

Check the message you're about to send:

- [ ] Command lives in `run/<slug>.sh`, not inline in the chat
- [ ] Slug is short and task-shaped; same slug on every `/tmp` path the script writes
- [ ] Script sources `tools/colors.sh` and actually uses `step`/`ok`/`warn`/`err`
- [ ] `set -euo pipefail` present
- [ ] Invocation line has all of `2>&1`, `tee`, `;`, `pbcopy`
- [ ] Reused the existing script for this task instead of creating a near-duplicate
