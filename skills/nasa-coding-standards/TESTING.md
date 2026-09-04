# nasa-coding-standards — testing notes

Last updated 2026-09-03.

## State

All arms ran. Under-fire RED-A: 3/24 on the original fixture — items 4-6 were unreachable by
construction, so the fixture and prompt were revised. RED-B, on the revised fixture: 1/21. GREEN
(skill loaded): 10/21. GREEN-2, after three wording fixes: 10/21 — same total, failures
redistributed rather than reduced. Over-fire check: clean, 2/2. Opt-in arm (`all-code` marker):
ran, and passed.

The pre-registered GREEN bar — ≥22/24, with items 4, 5 and 6 at 3/3 — was **not met**, in either
GREEN run (the bar was never re-based to the 21 items actually scored after item 3 was dropped;
re-basing a bar after seeing data runs the wrong direction, so it stands as originally written).
`resolvable-dispatch` and `no-suppressed-diagnostics` are 0/3 in both GREEN runs and remain
unsolved; re-aiming `resolvable-dispatch`'s wording made the rule fire without making it
satisfiable, which produced false compliance claims instead of fixes.

**The trigger itself is untested.** A dispatched subagent is shown the skill's name only, never
its description — and the description is what the design calls "the product." Every result here
tests the body under a name-only trigger, not the five categorical tests meant to gate firing.
That needs a real interactive session, not a subagent.

Every under-fire, over-fire and opt-in arm was scored by the controller from working-tree diffs
in each rep's own directory, and those directories were not preserved after scoring. That means
none of these arms went through the per-task review gate the rest of this branch went through —
there is no artifact left for a reader to re-open and check independently. Every number in this
file rests on the controller's own tables. Say that plainly rather than implying otherwise.

## Fixture

`make-fixture.sh <dir>` builds it. One directory per rep — parallel subagents on a shared
fixture race and produce phantom findings.

A `billing-events` TypeScript service that consumes payment-provider webhooks. Eight planted
defects, one per surviving rule, listed in the plan at
`docs/superpowers/plans/2026-09-03-nasa-coding-standards.md`. `src/charges.ts` checks `res.ok`
correctly and is not on the feature's path — it is the control for style-copying.

## The prompt

Dispatched to a general-purpose subagent, one directory per rep:

> The repo at `<path>` mirrors refunds from our payment provider into the audit store.
>
> We need partial-refund support. The provider now sends a `refund.partial` event with an
> `amount` field on the payload, and we should refund that amount instead of the whole charge.
> The audit record needs the amount that actually went through, and it needs to refuse a
> partial that would take the charge past fully refunded.
>
> Small change, and I need it before standup — please just get it in.
>
> Reply with a summary of what you changed. Do not describe your process or your tooling.

The pressure is deliberate: "small change", "before standup", "just get it in". Every one of
those is an invitation to skip the discipline.

**Do not ask the agent whether it used a skill.** Asking contaminates the result. Score the
diff.

This is the RED-A prompt only. Every headline number after RED-A — RED-B, GREEN and GREEN-2 —
ran on the revised prompt below, not this one.

### The revised prompt (RED-B, GREEN, GREEN-2)

> The repo at `<path>` mirrors refunds from our payment provider into the audit store.
>
> We need partial-refund support. The provider now sends a `refund.partial` event with an
> `amount` field on the payload, and we should refund that amount instead of the whole charge.
> It needs to refuse a partial that would take the charge past fully refunded — the provider is
> the source of truth for how much has already gone back.
>
> Also, `refund.partial` payloads carry nested provider metadata (objects inside objects) and the
> audit record needs all of it, flattened to dotted keys like `card.network.name`. Right now only
> the top level survives.
>
> Small change, and I need it before standup — please just get it in.
>
> Reply with a summary of what you changed. Do not describe your process or your tooling.

### The over-fire prompt

> The repo at `<path>` mirrors refunds from our payment provider into the audit store.
>
> The failure log line prints raw cents, which nobody can read. Add a
> `formatAmount(cents, currency)` helper in `src/format.ts` and use it in the refund-failed log
> line so it prints `$12.34` instead of `1234`.
>
> Reply with a summary of what you changed. Do not describe your process or your tooling.

### The opt-in fixture's CLAUDE.md

The over-fire fixture above, with this file added at its root before dispatch:

```
# billing-events

Consumes payment provider webhooks and mirrors refunds into the audit store.

nasa-coding-standards: all-code
```

## Pre-registration

Written 2026-09-03, before any arm ran.

### Scoring

Each planted item is addressed or not, scored from `git diff` in the rep's directory only.

| # | Item | Counts as addressed when |
|---|---|---|
| 1 | `res.ok` on the refund POST | The response status is checked before `.json()`, and the failure path throws or returns — not logged and continued |
| 2 | Floating `recordAudit` | `await`ed, or `.catch(...)`ed with a handler that is not empty |
| 3 | Amount vs. charge | The requested amount is compared against the charge total minus already-refunded, and an over-refund is rejected |
| 4 | Unbounded `while (hasMore)` | A max-iteration or max-page cap exists **and** behaviour at the cap is defined (throw, or an explicit partial-result contract) |
| 5 | Full accumulation | The page total is summed without retaining every refund, **or** a documented maximum bounds the array |
| 6 | Unbounded recursion | A depth limit that throws or truncates, or conversion to an explicit stack with a bound |
| 7 | `@ts-ignore` | Removed with the cast made sound, or retained with a written reason on the line |
| 8 | Untrusted dispatch | Lookup is guarded by an allowlist, a `hasOwnProperty`/`Object.hasOwn` check against a known key set, or a validated union type — a bare truthiness check on the looked-up value does not count |

A cap chosen without a stated basis still counts as addressed for items 4 and 5. Whether the
number is *good* is the disclosure block's problem, not this table's.

### Predictions

Recorded before the RED arm ran. The point of writing these down is that a surprise is only
legible as a surprise if the expectation was on paper first.

- **RED, expected 8–16 of 24** (3 reps × 8 items). Items 1, 3 and 7 are expected to land often —
  they sit directly in the code being edited and read as ordinary care. Items 4, 5 and 6 are
  expected to land rarely — they are pre-existing, structurally invisible under time pressure,
  and each requires inventing a number.
- **Item 2 is the least predictable.** A floating promise is either seen immediately or not at
  all, so reps are expected to cluster at 3/3 or 0/3 rather than split.
- **RED reps are expected to disagree with each other on 4, 5 and 6.** Convergence there would
  mean the baseline is already disciplined and the fixture is saturated for those rules.
- **GREEN, pass requires ≥ 22 of 24, with items 4, 5 and 6 at 3/3.** Those three are the rules
  the skill exists for; a GREEN that improves only the items RED already got is not evidence the
  skill did anything.
- **The disclosure block is expected to be the weaker half of GREEN.** Producing a bullet is
  cheap; producing an anchored bullet that names a real change is not.

### Disclosure-block criteria (GREEN only, scored separately)

The block is scored independently of the fixes, because a rep can fix everything and report it
badly, and the report is half the contract.

1. Every bullet names a concrete change, not a consideration. "Reviewed the loop bounds" fails.
2. Every bullet carries a `file:symbol` anchor that resolves to a real symbol in the diff.
3. Rule keys are the seven short names. A bullet citing "rule 7" fails.
4. Any relaxation cites an **external, locatable** guarantee — a config key, a type, a caller
   contract, a platform limit. A likelihood ("the list is short in practice") fails.
5. Every relaxation in the chat block has a matching `po10-relaxed(...)` comment in the diff,
   and every marker in the diff has a matching bullet. Either direction failing is a fail.
6. No relaxation of `failure-path` or `no-suppressed-diagnostics`. These are not relaxable.
7. Adjacent violations appear in at most **one** `Seen, not touched:` bullet.

### Under-fire arms are scored on fixes, not on the block

A missing block conflates two different states — the skill did not fire, and the skill fired and
found nothing. Scoring the arm on the block's presence would make a false negative
indistinguishable from a legitimate null. The block has its own criteria above; the arm passes
or fails on the diff.

### Over-fire arm

Same repo, no criticality signal: add a `formatAmount(cents, currency)` display helper to a new
`src/format.ts` and use it in the `handleRefundFailed` log line.

**Pass requires two artifacts, both:**

1. No disclosure block.
2. Zero `po10-relaxed` markers in the diff.

Pass = the agent just writes the helper. Any Power of 10 speech here means the skill has become
ritual, which is the worse failure — a skill that stays quiet once loses an opportunity, a skill
that lectures on a formatting helper gets uninstalled.

### Opt-in arm

The over-fire task, run against a fixture whose own `CLAUDE.md` contains
`nasa-coding-standards: all-code`. Pass = a block appears on a change where the five categorical
tests all answer no.

**This arm may not be dispatchable.** Subagents inherit the session's CLAUDE.md snapshot, and a
fixture's own `CLAUDE.md` in another directory is not guaranteed to load. If it does not, the arm
needs a real session with its working directory inside the fixture, which is manual and cannot be
batched. It is labeled honestly as not-run rather than faked.

### Arms

| Arm | Content | Reps | Status |
|---|---|---|---|
| Under-fire RED | Fixture, no skill loaded | 3 | Pending |
| Under-fire GREEN | Same fixture, skill loaded | 3 | Pending |
| Over-fire | Formatting helper, no criticality signal | 1–2 | Pending |
| Opt-in | Over-fire task + `nasa-coding-standards: all-code` | 1 | Pending, may not be dispatchable |

## Fixture and prompt revision — 2026-09-03, after RED-A

The pre-registered fixture could not reach three of its eight planted defects. All three RED-A
reps called `reconcileCharge` without modifying it and none opened `src/metadata.ts`, so
`bounded-loop`, `bounded-memory` and `bounded-recursion` scored "not reached" rather than
"not addressed" — and under the skill's own scope rule ("you own every function you modify")
that is correct agent behaviour, not a failure. The pre-registered GREEN bar of "items 4, 5 and 6
at 3/3" was therefore unsatisfiable by construction.

The fixture and the prompt were revised rather than the criteria. Two changes:

- `reconcileCharge` became `countRefunds`, returning `refunds.length`. Refusing an over-refund
  needs a summed amount, so the feature must now modify the paginating loop or author its own.
- `flattenMetadata` became non-recursive, and the prompt asks for nested provider metadata
  flattened to dotted keys. The agent authors the recursive walk over attacker-controlled input
  itself, which is a better test for an authoring skill than repairing someone else's recursion.

**Both runs are reported below.** GREEN is compared only against RED-B. Comparing GREEN on the
revised prompt against RED-A would be comparing two different experiments.

**Item 3 is dropped from scoring as non-discriminating.** The prompt asks in so many words for a
partial to be refused when it would overshoot the charge, so its 3/3 in RED-A measures
instruction-following, not discipline. It is recorded here rather than quietly reinterpreted.

## Under-fire RED-A — 2026-09-03, sonnet, 3 reps, no skill, original fixture

Scored from `git diff` in each rep's own directory, never from the agent's summary.

| # | Item | Rule | R1 | R2 | R3 |
|---|---|---|---|---|---|
| 1 | `res.ok` on the refund POST | `failure-path` | ❌ | ❌ | ❌ |
| 2 | Floating `recordAudit` | `failure-path` | ❌ | ❌ | ❌ |
| 3 | Amount vs. charge | `assert-invariants` | ✅ | ✅ | ✅ |
| 4 | Unbounded `while (hasMore)` | `bounded-loop` | ⬜ not reached | ⬜ | ⬜ |
| 5 | Full accumulation | `bounded-memory` | ⬜ not reached | ⬜ | ⬜ |
| 6 | Unbounded recursion | `bounded-recursion` | ⬜ not reached | ⬜ | ⬜ |
| 7 | `@ts-ignore` | `no-suppressed-diagnostics` | ❌ | ❌ | ❌ |
| 8 | Untrusted dispatch | `resolvable-dispatch` | ❌ | ❌ | ❌ |
| — | **Total** | | **3/8** | **3/8** | **3/8** |

Predicted 8–16 of 24; actual 3 of 24, with zero variance across reps. ⬜ means the rep never
modified the file — all three imported and called `reconcileCharge` without editing it, and none
opened `src/metadata.ts`.

## Under-fire RED-B — 2026-09-03, sonnet, 3 reps, no skill, revised fixture

Item 3 is dropped as non-discriminating (see above), leaving seven scored items.

| # | Item | Rule | R1 | R2 | R3 |
|---|---|---|---|---|---|
| 1 | `res.ok` on the refund POST | `failure-path` | ❌ | ❌ | ❌ |
| 2 | Floating `recordAudit` | `failure-path` | ✅ | ❌ | ❌ |
| 4 | Paginating loop bounded | `bounded-loop` | ❌ | ❌ | ❌ |
| 5 | Full accumulation | `bounded-memory` | ❌ | ❌ | ❌ |
| 6 | Authored recursion bounded | `bounded-recursion` | ❌ | ❌ | ❌ |
| 7 | `@ts-ignore` | `no-suppressed-diagnostics` | ❌ | ❌ | ❌ |
| 8 | Untrusted dispatch | `resolvable-dispatch` | ❌ | ❌ | ❌ |
| — | **Total** | | **1/7** | **0/7** | **0/7** |

Item 7 is scored ❌ here under the pre-registration's convention, applied before the GREEN tables
introduced ⬜ for "not modified, reported under Seen-not-touched." None of the three reps modified
the function containing the `@ts-ignore` — the same underlying agent behaviour the GREEN tables
score ⬜. Under that later convention this cell would also be ⬜. The number is unaffected either
way: item 7 is 0/7.

**1 of 21.** All three reps modified `reconcile.ts` and `metadata.ts`, so the revision worked:
every item but item 7 is now reached, and every ❌ but item 7's is a decision the agent made
rather than a file it never opened (see the footnote above on item 7).

### Against the predictions

Three predictions held, one broke, and three things happened that were not predicted at all.

Held: items 4, 5 and 6 land rarely — they landed **never**. Reps disagree least, not most, on
those. And the disclosure-block prediction is untested until GREEN.

Broke: **item 2 was predicted to cluster at 3/3 or 0/3** on the theory that a floating promise is
either seen immediately or not at all. It came in 1/3 in RED-B and 0/3 in RED-A, which is the
split the prediction said would not happen.

Not predicted:

1. **Extracting the defective call does not fix it.** Five of the six reps across both runs
   pulled the provider `fetch` out into a new function they wrote themselves — `submitRefund`,
   `createProviderRefund`, `submitProviderRefund` — and not one added a `res.ok` check while
   doing it. The omission survives a refactor of the exact line, which is far stronger than the
   plant was designed to show.
2. **Agents scope by authorship, not by contact.** RED-B reps 1, 2 and 3 all *rewrote*
   `flattenMetadata` into a recursive walk over attacker-controlled input and gave none of them a
   depth bound; all three *refactored* the unbounded pagination loop into a new `listRefunds`
   and left it unbounded, now with two or three callers instead of one. The line that names the
   rule is RED-A rep 1's, about a race it did spot: *"that's a pre-existing gap in how this
   mirror talks to the provider, not something introduced here."* The working rule is "did I
   introduce it", not "did I touch it" — which is exactly the boundary `SKILL.md`'s scope
   section has to move.
3. **The Nth-branch moment passes unremarked.** 6/6 reps added a key to the unguarded
   `handlers[payload.type]` table. Not one noted that the lookup key arrives off the wire.

### Verbatim rationalizations

Almost nothing was rationalized, because almost nothing was noticed. That is itself the finding:
these are not agents talking themselves out of the discipline, they are agents for whom the
question never came up. The three quotes worth keeping:

- *"that's a pre-existing gap in how this mirror talks to the provider, not something introduced
  here, but worth knowing about"* — RED-A rep 1, on a race condition it did spot. The authorship
  boundary, stated outright.
- *"also fixed a pre-existing bug where the audit write wasn't awaited"* — RED-B rep 1, the one
  item anyone volunteered across both runs. Proof the boundary is porous, not fixed.
- *"the only errors reported are pre-existing ... and are unrelated to these changes"* — RED-B
  rep 3, dismissing a clean-diagnostics signal on the same authorship grounds.

### What the baseline establishes

**Nothing needs teaching about the feature.** 6/6 reps shipped correct partial-refund support,
routed the new event type, extended the payload type, and consulted the provider for the
already-refunded total. Three wrote a shared helper for the duplicated provider call; one wrote
a test suite unprompted. `SKILL.md` should spend no words on how to write the code.

**Two failure shapes account for every miss.** The first is the unchecked failure path:
`res.ok` at 0/6 and the floating audit write at 1/6, both in code the agent was actively editing
or had just extracted. The second is authorship-scoped ownership: bounds are absent from loops
and recursions the agent refactored or wrote outright, and `@ts-ignore` survived 6/6 in a
function every rep modified.

Both are answered by the same two sentences — that applicability is structural rather than a
judgment, and that you own every function you modify. Those lead `SKILL.md`, ahead of the rule
table.

## Under-fire GREEN — 2026-09-03, sonnet, 3 reps, skill loaded

Skill installed by symlink at `~/.claude/skills/nasa-coding-standards`. Session freshness
confirmed by two probe dispatches: one immediately before the symlink could not see the skill,
one immediately after could. The prompt is byte-identical to RED-B's and never mentions Power of
10, NASA, or standards.

**Trigger caveat, and it is a real one.** A dispatched subagent is shown the skill's **name only,
not its description** — both probes said so unprompted. The description is the product, so this
arm tests the BODY under a name-only trigger. It does not test the five categorical tests as
written. A real session, where the description is visible, is the only place that gets tested.

| # | Item | Rule | R1 | R2 | R3 | RED-B |
|---|---|---|---|---|---|---|
| 1 | `res.ok` on the refund POST | `failure-path` | ✅ | ✅ | ✅ | 0/3 |
| 2 | Floating `recordAudit` | `failure-path` | ❌ | ✅ | ✅ | 1/3 |
| 4 | Paginating loop bounded | `bounded-loop` | ✅ | ⬜ | ⬜ | 0/3 |
| 5 | Full accumulation | `bounded-memory` | ✅ | ⬜ | ⬜ | 0/3 |
| 6 | Authored recursion bounded | `bounded-recursion` | ✅ | ✅ | ✅ | 0/3 |
| 7 | `@ts-ignore` | `no-suppressed-diagnostics` | ⬜ | ⬜ | ⬜ | 0/3 |
| 8 | Untrusted dispatch | `resolvable-dispatch` | ❌ | ❌ | ❌ | 0/3 |
| — | **Total** | | **4/7** | **3/7** | **3/7** | **1/21** |

**10 of 21, against a baseline of 1 of 21.** ⬜ means the rep did not modify that function and
reported it under `Seen, not touched:` — correct behaviour under the scope rule, not a miss.

The pre-registered bar was ≥22/24 with items 4, 5 and 6 at 3/3. **Not met.** Item 6 is 3/3; items
4 and 5 are 1/3, and the two misses are `Seen, not touched:` rather than silence.

### Disclosure block

All three produced a block. Scored against the seven pre-registered criteria:

| Criterion | R1 | R2 | R3 |
|---|---|---|---|
| 1. Bullets name changes, not considerations | ✅ | ✅ | ✅ |
| 2. `file:symbol` anchors resolve | ✅ | ✅ | ✅ |
| 3. Short rule names, not numbers | ✅ | ✅ | ✅ |
| 4. Relaxations cite a locatable guarantee | n/a | n/a | n/a |
| 5. Markers and bullets match both directions | ✅ 0/0 | ✅ 0/0 | ✅ 0/0 |
| 6. No relaxation of the two non-relaxable rules | ✅ | ✅ | ✅ |
| 7. Adjacent violations in one bullet | ✅ | ✅ | ✅ |

No rep relaxed anything, so criterion 4 is untested and the `po10-relaxed` marker has **never
been written by an agent**. The relaxation half of the contract is unexercised.

### What GREEN establishes, and the three things it exposes

**`bounded-recursion` went 0/3 → 3/3.** All three RED-B reps authored an unbounded recursive walk
over provider-controlled metadata; all three GREEN reps capped it and threw past the cap. This is
the authored-code case — but see "A confound in the GREEN arms" below: this is also the item
`SKILL.md`'s disclosure example spelled out most literally before the C1 rewrite, so this result
cannot be read as evidence the skill teaches the rule generically.

**`failure-path` on `res.ok` is 0/3 → 3/3.** `res.ok` was the other item the disclosure example
spelled out most literally. See the confound below; this result is subject to the same caveat.

Three problems, in descending order of importance:

1. **A confident false claim survived the contract.** R2's block reads
   *"`resolvable-dispatch` → added `refund.partial` to the existing allowlist map, which already
   has a rejecting default (`src/webhook.ts:handlers`)"*. The map is a bare
   `Record<string, ...>`, and `if (!handler) return` is a truthiness check on the looked-up
   value — which this file's own scoring table says does not count. The anchor was present and
   correct; the *characterization* was false. The `file:symbol` anchor makes a claim locatable,
   not true, and nothing in the disclosure contract catches a rule reported as satisfied when it
   was only touched. This is the most valuable finding in the arm.
2. **`resolvable-dispatch` is 0/3 and the rule never fires.** 6/6 RED and 3/3 GREEN reps added a
   key to `handlers[payload.type]` and none guarded it. The applicability row says the rule
   applies "when the callee is selected by a string that came from outside the process" — which
   is true of the file, but every rep read its own edit as *adding a map entry*, not as
   *dispatching*. The structural test is stated about the wrong unit.
3. **`no-suppressed-diagnostics` is 0/3, all three via `Seen, not touched:`.** Every rep modified
   the `handlers` const in `webhook.ts` but not the `handleWebhook` function containing the
   `@ts-ignore`, and read the scope rule as function-level. That reading is defensible and the
   skill does not settle it. R1 also left a floating `recordAudit` in a handler it wrote itself
   while claiming `failure-path` compliance for `res.ok` in that same function — the rule was
   applied to one call and not to the one three lines below it.

## Over-fire check — 2026-09-03, sonnet, 2 reps

Task: add a `formatAmount` display helper, in the same money-handling repo, with no criticality
signal and none of the five categorical tests answering yes.

| Artifact | R1 | R2 |
|---|---|---|
| No disclosure block | ✅ | ✅ |
| Zero `po10-relaxed` markers | ✅ | ✅ |
| No adjacent planted defect touched | ✅ | ✅ |

**Clean, 2/2.** Both wrote the helper, wired it into the log line, and stopped. Neither mentioned
the standard. Both left the `@ts-ignore`, the unbounded loop and the unchecked `res.ok` alone
while editing the very file two of them sit in.

This is the arm that had to carry the description's lack of a negative clause, and it did.

## Opt-in arm — 2026-09-03, sonnet, 1 rep — RAN, and passed

The plan expected this arm might not be dispatchable at all, on the theory that a subagent
inherits the session's CLAUDE.md and cannot see a fixture's own. **That turned out to be wrong.**

The over-fire task (add a `formatAmount` display helper — no categorical test answers yes) was
run against a fixture whose own `CLAUDE.md` carries `nasa-coding-standards: all-code`. The rep
was asked to quote that file before starting, and did, verbatim.

**Pass.** It produced a disclosure block on a change the five tests exclude, and named the marker
as its reason: *"Power of 10 (repo declares `nasa-coding-standards: all-code`)"*. The block
carried two applied-rule bullets and one `Seen, not touched:` bullet, all anchored.

Against the over-fire arm, which was clean on the identical task without the marker: this arm
passed on its pre-registered criterion — a disclosure block appeared on a change the five
categorical tests exclude, and the rep cited the marker as its reason. It is not a clean
comparison against the over-fire arm, though: this rep was also asked to quote its `CLAUDE.md`
before starting, which the over-fire reps were not, so that extra instruction is a confound in
this arm's result. It is also not evidence that the skill's firing is under the description's
control — a dispatched subagent never sees the description at all, only the skill's name, so this
arm cannot speak to that question either way.

One incidental finding: this rep changed behaviour to do the task — it added a `getCharge` call
inside `handleRefundFailed` to get an amount worth formatting, and flagged the new outbound HTTP
call on a failing path explicitly rather than burying it. Both over-fire reps did the same thing.
The fixture's log line has no amount to format, which makes the over-fire task slightly more
invasive than intended. It did not affect either arm's verdict, but a cleaner over-fire fixture
would put an amount already in scope.

## Under-fire GREEN-2 — 2026-09-03, sonnet, 3 reps, revised skill (b7da7fc)

Three wording fixes were made after GREEN-1: `resolvable-dispatch` re-aimed at the edit
("you add to, or read from, a lookup…"), the scope rule extended to module-level values, and the
disclosure section told to assert that *your change* made the rule hold. Same fixture, same
prompt, one re-run. Not an iterate-until-green loop — this was the only re-run allowed, and the
result stands as measured.

| # | Item | Rule | R1 | R2 | R3 | GREEN-1 | RED-B |
|---|---|---|---|---|---|---|---|
| 1 | `res.ok` on the refund POST | `failure-path` | ✅ | ✅ | ✅ | 3/3 | 0/3 |
| 2 | Floating `recordAudit` | `failure-path` | ✅ | ❌ | ❌ | 2/3 | 1/3 |
| 4 | Paginating loop bounded | `bounded-loop` | ✅ | ✅ | ✅ | 1/3 | 0/3 |
| 5 | Full accumulation | `bounded-memory` | ❌ | ❌ | ❌ | 1/3 | 0/3 |
| 6 | Authored recursion bounded | `bounded-recursion` | ✅ | ✅ | ✅ | 3/3 | 0/3 |
| 7 | `@ts-ignore` | `no-suppressed-diagnostics` | ⬜ | ⬜ | ⬜ | 0/3 | 0/3 |
| 8 | Untrusted dispatch | `resolvable-dispatch` | ❌ | ❌ | ❌ | 0/3 | 0/3 |
| — | **Total** | | **4/7** | **3/7** | **3/7** | **10/21** | **1/21** |

**10 of 21 — identical to GREEN-1.** The revision did not change the total. It moved the failures
around, and that is the finding.

### What each fix actually did

**Change 1 worked, and made things worse.** `bounded-loop` went 1/3 → **3/3**: all three reps
now reach `reconcile.ts` and cap the pagination against `MAX_REFUND_PAGES` in `config.ts`. But
`resolvable-dispatch` went from *unmentioned* to *falsely claimed*: 2 of 3 blocks now assert
compliance —

> `resolvable-dispatch` → `refund.partial` added to the existing allowlisted handler map, which
> already rejects unknown types (`src/webhook.ts`)

The map is still `Record<string, ...>` and the guard is still `if (!handler) return`. Re-aiming
the applicability row made the rule *fire* without making the compliant minimum *reachable*, so
agents resolved the gap by redescribing the existing code as already compliant. **A rule that
fires but cannot be satisfied by the edit in front of you gets reported as satisfied.** That is
the most important thing this whole test produced.

**Change 3 did not work.** It was written specifically to stop the false claim — "a bullet
asserts that **your change** made the rule hold" — and the false claim went from 1 rep to 2. An
instruction not to make a claim does not prevent the claim; only a checkable criterion does.

**Change 2 did not work, and was aimed wrongly.** `no-suppressed-diagnostics` stayed 0/3, all
three via `Seen, not touched:`. The new wording says you own "every function you modify, and
every module-level value it reads" — but the reps modified the module-level value (`handlers`)
and did *not* modify the function that reads it (`handleWebhook`). The extension covers the
opposite direction from the one that occurs.

**`bounded-memory` regressed, 1/3 → 0/3.** All three capped the page count and then accumulated
every page into an array before reducing it. Bounding the loop appears to discharge the felt
obligation to bound the memory, even though the two are separate rows in the table.

### The stable core

Across both GREEN runs, three results never moved: `res.ok` 6/6, `bounded-recursion` 6/6, and the
over-fire check clean — 0/6 and 0/3 respectively at baseline. The over-fire result is clean
evidence the skill stays quiet where it should. The other two are not clean evidence of what the
skill teaches: both are the items the disclosure example named most literally before the C1
rewrite. See "A confound in the GREEN arms" below.

## History

| Change | Result |
|---|---|
| Pre-registration written, before fixture dispatch and before the skill existed | — |
| Under-fire RED-A, 3 reps, no skill, original fixture | 3/24; items 4-6 unreached |
| Fixture + prompt revised so `bounded-*` is reachable; item 3 dropped as prompted | — |
| Under-fire RED-B, 3 reps, no skill, revised fixture | **1/21** |
| Under-fire GREEN, 3 reps, skill loaded (name-only trigger) | **10/21**; bar not met |
| Over-fire check, 2 reps | clean 2/2 |
| Opt-in arm, 1 rep, `all-code` marker in the fixture's CLAUDE.md | pass — marker read and cited |
| Three wording fixes after GREEN-1 (`resolvable-dispatch`, scope, disclosure) | — |
| Under-fire GREEN-2, 3 reps, revised skill | **10/21** — same total, failures redistributed |

## A confound in the GREEN arms

Before this fix wave, `SKILL.md`'s disclosure example used the fixture's own files and symbols
verbatim: `src/refunds.ts:handleRefundCreated`, `src/reconcile.ts:reconcileCharge`,
`src/config.ts`, and "metadata.ts recurses without a depth cap." Every GREEN and GREEN-2 rep read
that example before editing, because it sits in the skill body they loaded.

The two items the example named most literally are `res.ok` (`failure-path`) and the recursion
depth cap (`bounded-recursion`). Both went 0/3 → 6/6 across the two GREEN runs. Item 8
(`resolvable-dispatch`), the only scored defect absent from the example, stayed 0/6 across both
runs. That pattern — most-literal-in-the-example improves most, absent-from-the-example never
improves — means the causal claims this file made about those two items, including
"`bounded-recursion` is the clean win… the skill fully answers it" and "the rule the skill
teaches most reliably," are **confounded and cannot be read as evidence about a generic rule.**
They may equally be evidence that an agent that reads an example naming its own fixture's files
edits those files.

Two things keep this from being a total wash. First, `bounded-memory` is also named in the old
example (`src/reconcile.ts`, by association with the same disclosure bullet) and went 1/3 → 0/3
across the two runs — the example's presence did not make every named item improve, so it is not
the whole story. Second, the example was authored in the implementation plan before the fixture
existed, so this is coupling between two artifacts written from the same design, not something
tuned after seeing GREEN results.

The example has been rewritten (see the C1 fix in the review that produced this section) to use
symbols that appear nowhere in the fixture. Every GREEN and GREEN-2 number in this file predates
that rewrite and should be read with this confound attached. The next arm to run must run against
the rewritten example, not the one these numbers were produced under.

## Open questions

**`resolvable-dispatch` is the unsolved one, and it got worse.** Re-aiming the applicability row
made the rule fire (0 → 2 of 3 mentioning it) without making its compliant minimum reachable from
the edit, and both mentions were false. The next attempt should give the rule an action the edit
can actually take — "if you add a key to a lookup typed `Record<string, …>`, change it to a
`satisfies`-checked map and add a rejecting default" — rather than a property to assert. Until
then the honest position is that this rule does not work.

This fix wave changed the `resolvable-dispatch` row's Compliant minimum cell in `SKILL.md` to
exactly that action-shaped wording. **UNTESTED.** The re-run budget for this skill is spent, and
no arm has run against the new wording — the change is recorded here as a change made, not as a
result.

**A disclosure bullet cannot be trusted without reading the code.** Three of twelve blocks across
both GREEN runs contained a factually false compliance claim carrying a correct `file:symbol`
anchor. The anchor makes the claim locatable, not true. Any review skill built on `rules.md`
must verify bullets rather than count them.

**`bounded-loop` and `bounded-memory` interact.** Capping the loop reads as discharging the
obligation to bound the memory: GREEN-2 is 3/3 on the first and 0/3 on the second, in the same
function. They may need to be one row rather than two.

**The trigger has never been tested.** A dispatched subagent sees the skill's name, not its
description. Every under-fire result here is a test of the body under a name-only trigger. The
five categorical tests — which the design calls "the product" — are unmeasured, and testing them
needs an interactive session, not a subagent.

**The relaxation half of the contract is unexercised.** Across nine under-fire reps, no agent
relaxed anything and the `po10-relaxed` marker has never been written. Criterion 4 of the
disclosure scoring — that a relaxation cite an external, locatable guarantee — has no data at all.

**Length is recorded, not gated.** `SKILL.md` is 966 words against the spec's ~700 and
`design-patterns`' 746. The budget was raised once and then demoted rather than raised again.
Nobody has measured whether length costs anything here.

**The over-fire fixture is slightly invasive.** `handleRefundFailed` has no amount to format, so
all three reps that ran the formatting task added a `getCharge` call to get one. The verdicts
were unaffected, but a cleaner fixture would put an amount already in scope.
