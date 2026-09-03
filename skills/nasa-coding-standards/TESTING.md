# nasa-coding-standards — testing notes

Last updated 2026-09-03.

## State

**Pre-registration only. No arm has run.** Everything below the `## Pre-registration` heading
was written before the fixture was dispatched to anything and before `SKILL.md` existed. Nothing
in it may be edited after an arm runs — corrections go in `## History` as a dated row.

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

## History

| Change | Result |
|---|---|
| Pre-registration written, before fixture dispatch and before the skill existed | — |

## Open questions

None recorded yet. Fill in after the arms run.
