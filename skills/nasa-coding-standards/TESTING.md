# nasa-coding-standards — testing notes

Last updated 2026-09-03.

## State

**Baseline (RED) run and recorded, twice. The skill does not exist yet.** Everything under
`## Pre-registration` was written before any arm was dispatched and before `SKILL.md` existed,
and is unedited. Nothing in it may be revised after an arm runs — corrections go in `## History`
as a dated row, and the fixture revision below is recorded rather than folded in silently.

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

**1 of 21.** All three reps modified `reconcile.ts` and `metadata.ts`, so the revision worked:
every item is now reached, and every ❌ is a decision the agent made rather than a file it never
opened.

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

## History

| Change | Result |
|---|---|
| Pre-registration written, before fixture dispatch and before the skill existed | — |
| Under-fire RED-A, 3 reps, no skill, original fixture | 3/24; items 4-6 unreached |
| Fixture + prompt revised so `bounded-*` is reachable; item 3 dropped as prompted | — |
| Under-fire RED-B, 3 reps, no skill, revised fixture | **1/21** |

## Open questions

None recorded yet. Fill in after the arms run.
