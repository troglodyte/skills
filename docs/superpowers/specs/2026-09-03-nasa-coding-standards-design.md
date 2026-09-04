# NASA coding standards skill — design

## Purpose

Bring NASA/JPL "Power of 10" discipline to the TypeScript and Node code this team writes,
without handing out C advice wearing a TypeScript hat.

The value is concentrated in four ideas rather than ten rules: bound everything (loops, memory,
recursion depth), check every failure path, keep dispatch statically resolvable, and suppress no
diagnostics.
Exactly one of the original ten does not survive the port and is dropped explicitly, with the
reason recorded.

## Scope decision: two skills, not three

The original request named three candidate skills — the ported rule list, the criticality
mindset, and a review-time audit.
The rule list and the mindset are one skill, because both fire at the same moment (about to
write code) and shipping them separately would put two skills with overlapping descriptions
in competition for one trigger.
The mindset is the rationale behind the rules, not a peer of them.

This follows the split already used by `design-patterns`: posture in `SKILL.md`, catalog in a
sibling file loaded on demand.

The audit skill is genuinely separate — it fires on review, not on authoring, and fails in a
different way (a review skill fails by flagging noise; an authoring skill fails by staying
silent).
It is out of scope for this spec and specified in **Follow-on work** below.

## Decisions

| Question | Decision |
| --- | --- |
| Which standard | Power of 10, opinionatedly ported to TS/Node, plus the criticality posture |
| When it fires | Five categorical tests on the code being written, plus an opt-in marker that promotes a whole repo |
| What it does | Writes to the standard silently, then discloses one bullet per rule it changed code under. No dialog, no permission-asking |
| Where the rules live | `rules.md`, loaded on demand; the audit skill will read the same file |
| Build order | Authoring skill first, audit skill second |

Rejected: an always-on mode with no signal list (guaranteed to over-fire), explicit-invocation-only
(never brings the discipline on its own, which is a reference doc rather than a skill), a hard
gate before "done" (turns small changes into compliance ceremony), and silent discipline with no
output block (behaviourally untestable).

## The port

### Adjudication criterion

A rule ports when its **invariant survives the death of its mechanism**.
The mechanism is whatever C-specific device the original prescribes; the invariant is the
property that device was buying.

This test does real work.
Rule 3's mechanism (no `malloc` after init) is meaningless under garbage collection, but its
invariant — resource use is derivable from the source, not from the input — survives intact.
By contrast, a tempting reframing of rule 3 as "avoid allocation churn to reduce GC pauses"
*fails* the test: it borrows the determinism rationale while enforcing something no tool can
check, and Holzmann's own design constraint was that every rule be mechanically checkable.

Rules 1, 2 and 3 are a triad — bounded control flow, bounded iteration, bounded memory — and
the property they jointly buy is static provability of resource use.
Rule 2 states it outright: a checking tool must be able to prove statically that a preset upper
bound cannot be exceeded.
Preserving that grouping matters, because a reader who sees the three together understands why
each one is there.

Every rule below is recorded as **Original → Port → What did not survive**, including the rules
that port cleanly.
The uniform format is deliberate: an earlier draft quarantined the reinterpreted rules into a
separate "our additions" section, which was wrong twice over.
It implied the remaining rules ported cleanly when none of them do, and a section labelled as
ours reads to an agent as negotiable, binding weakest exactly where we most want compliance.

### Rules

| # | Original (C) | Port (TS/Node) | What did not survive |
| --- | --- | --- | --- |
| 1 | Simple control flow; no `goto`, `setjmp`, or recursion, so control flow is provably simple | Recursion is permitted over structures whose depth is bounded by data you control. Depth arriving across a trust boundary carries a counter that throws, or becomes an explicit stack | `goto`/`setjmp` have no JS equivalent. The blanket recursion ban: tree and AST work makes recursion idiomatic, and a rule that gets ignored teaches that the whole set is negotiable |
| 2 | Every loop has a statically provable upper bound | Iterating an in-memory collection already satisfies this — the bound is its length. Loops gated on external state carry a max-iteration cap, a timeout, and defined behaviour at the cap | Nothing. This rule ports most directly of the ten |
| 3 | No dynamic allocation after initialization, so memory use is statically derivable | Every buffer, collection, queue and cache has a maximum readable from code or config. No unbounded slurping of a stream, response, or query result; caches have eviction | Allocator defects, fragmentation, and pause predictability are meaningless under GC. The static-bound invariant is the whole of what carries over |
| 4 | Functions fit on a single printed page | Defer to the repo's existing ~30-line limit | Nothing, but it is already enforced elsewhere, so it appears in `rules.md` only and is absent from `SKILL.md` |
| 5 | Minimum two assertions per function | Assert what types cannot: Zod at IO boundaries, invariants such as non-empty or sums-to-100 or tenant ownership, `never` in exhaustive switches | The density quota. TS types discharge much of what C assertions were compensating for, and a quota would manufacture noise |
| 6 | Data declared at the smallest possible scope | Defer to existing `const` and block-scope conventions | Nothing, but already lint-enforced; `rules.md` only |
| 7 | Check every non-void return value; validate every parameter | No floating promises; `res.ok` checked, since `fetch` does not throw on 4xx/5xx; no empty `catch`; `allSettled` rejections inspected; child-process exit codes read; an `'error'` listener on every stream and EventEmitter | Nothing. Strongest survivor, and the `'error'` listener clause is the highest-value single item for a Node service — an unhandled `'error'` event takes the process down |
| 8 | Preprocessor use restricted to includes and simple macros | **None.** | The invariant — the source you read is the source that compiles — has no analogue worth enforcing here, since TS has no preprocessor |
| 9 | No more than one level of dereferencing; no function pointers, so the call graph is statically resolvable | No `eval` or `new Function`; no dispatch on untrusted string keys (`handlers[payload.type]`) without an allowlist | The dereference-level restriction, and the ban on function values, which are idiomatic JS. The call-graph invariant survives and covers a real vulnerability class |
| 10 | Compile with all warnings at the most pedantic setting; run static analysis | `strict`, `noUncheckedIndexedAccess`, zero `@ts-ignore` or `eslint-disable` without a written reason, `tsc --noEmit` clean | Nothing |

Rule 8 is the only rule dropped outright, and it is dropped because its invariant does not matter
in this domain — not because no analogue could be invented.

## Files

```text
skills/nasa-coding-standards/
  SKILL.md      # posture + disclosure contract, ~700 words, loaded every time
  rules.md      # ported table with TS examples; dropped rules and why
  TESTING.md    # behavioural record
```

`SKILL.md` cross-references `design-patterns` the way `design-patterns` cross-references
`brainstorming`.
Both skills may legitimately fire on the same code: `design-patterns` decides what shape the
code takes, this one decides what happens when it fails.

## Trigger description

The description is the product, since it is all the agent sees before deciding to load.

It is built as **five categorical tests** rather than a long list of specific signals.
An enumeration of a dozen signals gets matched loosely — the agent pattern-matches the shape of
the list instead of checking membership — whereas each clause below is a question with an answer.

```text
Use when the code being written or modified does any of five things: moves money (payments,
refunds, billing, credits); changes who can access what (authentication, authorization,
permissions, tokens, secrets, signature verification); does something that cannot be taken back
(deletes or migrates data, sends customer-facing messages, writes to a third party, changes
production infrastructure); crosses a trust boundary (parses, validates, or buffers input from
outside the process — webhooks, uploads, third-party responses, queue payloads); or loops or
waits on external state (retries, polling, pagination, streaming, scheduled jobs, queue
consumers). Also use when the repository's CLAUDE.md declares `nasa-coding-standards: all-code`,
which promotes every change in that repo.
```

The opt-in is a literal marker string rather than a judgment call, because "is this repo
safety-critical?" answered by vibes will drift, while a string either matches or it does not.

No negative clause ("not for routine UI") is included.
An earlier draft had one; it was removed because a payment form is UI, and the clause risked
talking the agent out of firing on a checkout flow.
The five tests are therefore required to exclude by construction — no test answers yes, do not
fire — and the over-fire arm has to prove that rather than assume it.

Between the two available failure modes, mild under-firing is preferred.
A skill that stays quiet when it should have spoken loses one opportunity; a skill that lectures
on a formatting helper gets uninstalled.

## Disclosure contract

### Rule keys

The block refers to rules by short name, never by number.
With rule 8 dropped and rules 4 and 6 deferred to existing repo conventions, the numbering is a
lookup burden on the reader for no benefit.

`bounded-recursion` (1), `bounded-loop` (2), `bounded-memory` (3), `assert-invariants` (5),
`failure-path` (7), `resolvable-dispatch` (9), `no-suppressed-diagnostics` (10).

### What earns a bullet

One bullet per rule under which the agent **changed code**, or relaxed the rule.
A rule that was considered and already satisfied earns nothing — "strict was already on" is not a
finding.

There is no numeric cap.
An earlier draft capped the block at five bullets; that was the wrong instrument.
A count scales with verbosity rather than with the problem, and an agent holding seven findings
under a cap of five will merge them into one bullet, destroying the per-rule traceability the
block exists to provide.
The "did something" filter does the anti-lecture work instead: nothing merely considered can pad
the block, and on a trivial change there is nothing to report by construction.

Format: `<rule-name> → <what changed> (<file:symbol>)`.

The `file:symbol` anchor is required.
An unanchored claim is the cheapest thing for an agent to produce and the hardest for a reviewer
to falsify, particularly across a multi-file change.

### Relaxations

Format: `Relaxed: <rule-name> — <guarantee> (<where it lives>)`.

The guarantee must be **external and locatable** — a config key, a type, a caller contract, or a
platform limit — never an assessment of likelihood.
"The loop is short in practice" is precisely the rationalization the skill exists to prevent.
Requiring a location is what separates the two: an agent invents a plausible guarantee as readily
as a plausible likelihood, but one that must name where it lives is checkable by the next reader,
and an agent forced to name it will notice when there is nothing to name.

`failure-path` and `no-suppressed-diagnostics` are **not relaxable**.
Both already contain their own compliant minimum: `.catch(noop)` with a comment *is* checking the
failure path — the decision to discard it has been made and recorded — and `@ts-ignore` with a
written reason *is* rule 10.
A relaxation of either is a request to skip the one-line version of compliance, not a design
tradeoff.

`bounded-loop` and `bounded-memory` remain relaxable, because compliance there requires a real
decision — what is the number? — and a non-relaxable rule whose compliance is expensive invites
silent non-compliance instead.

### Relaxations live in the code

Every relaxation is written as a grep-able comment at the site:

```text
// po10-relaxed(bounded-loop): bound enforced by queue.maxBatch (config/queue.ts)
```

The comment **is** the relaxation; a relaxation without one is a violation.
The chat bullet is that comment copied out, so there is one source and no drift.

An earlier draft applied this only to "permanent" relaxations.
That was unworkable: permanence is undecidable at write time, and any judgment call whose cheaper
branch is "skip it" gets resolved toward skipping.

On modifying code that carries a marker, the guarantee is a claim to re-verify, not a fact.

Applied rules need no comment — a cap constant is its own evidence — except where the constant's
value is not self-evident, in which case its reason goes inline.

### Scope

Rules apply to any function the agent modifies: you own it once you touch it.
Violations elsewhere are not fixed, and are reported in at most **one** `Seen, not touched:`
bullet for the whole change — not one per violation, which would reopen the lecture channel the
rest of this contract closes.

Without this line, agents will both silently fix adjacent code and silently ignore it,
unpredictably.

### Applicability must be structural

Making relaxation harder pushes the agent's cheapest exit toward deciding a rule *did not apply*,
and non-applicable rules are never mentioned — so that judgment is invisible and unfalsifiable.

`SKILL.md` therefore states a structural test for each rule, checkable against the code rather
than a matter of opinion.
For example: `bounded-loop` applies when a loop's termination depends on a value not computed
inside the function; `failure-path` applies to any call returning a Promise or an exit code.

### Silence

If no rule produced a change, emit no block at all.
This makes the block's presence the evidence that the skill fired.

## Test plan

Baseline before skill, per this repo's doctrine.
Predictions and pass criteria are pre-registered in `TESTING.md` before any arm runs, so a
result cannot be read into after the fact.

### Fixture

A mundane TS/Node service that happens to move money: a refund webhook handler.
Deliberately not framed as safety-critical — no aerospace framing, no "critical" in a filename
— because a fixture that looks important gets carefulness for free and stops discriminating.

The task prompt is an ordinary feature request ("add partial-refund support") carrying
skip-pressure ("small change, before standup").

Eight planted opportunities, each mapping to one surviving rule:

| Planted defect | Rule |
| --- | --- |
| `fetch` to the payment provider, `res.ok` never checked | 7 |
| `while (hasMore)` cursor loop over refunds, no cap, no timeout | 2 |
| Entire refund list accumulated into an array | 3 |
| Fire-and-forget audit-log promise, floating | 7 |
| Pre-existing `@ts-ignore` on the webhook payload type | 10 |
| Recursive walk of attacker-controlled nested `metadata` | 1 |
| Refund amount never checked against the original charge | 5 |
| `handlers[payload.type]` dispatch on an untrusted string key, no allowlist | 9 |

### Scoring

Scored from the produced diff only, never by asking the agent what it used — asking
contaminates the result.
Each planted item is addressed or not.

The under-fire arms are scored on the presence of the specific expected fixes, **not** on whether
a block appeared.
"No block" conflates two different states — the skill did not fire, and the skill fired and found
nothing — so a false negative would otherwise be indistinguishable from a legitimate null.

The disclosure block is scored separately: whether each bullet names a concrete change, carries a
`file:symbol` anchor, and uses short rule names; and whether any relaxation cites a locatable
external guarantee rather than a likelihood.

The over-fire arm passes only on **two** artifacts: no block, and zero `po10-relaxed` markers in
the diff.

### Arms

| Arm | Content | Reps | Status |
| --- | --- | --- | --- |
| Under-fire RED | Fixture, no skill loaded | 3 | Runs first, before the skill is written |
| Under-fire GREEN | Same fixture, skill loaded | 3 | Pending — requires the skill to exist |
| Over-fire | Display-formatting helper in the same repo, no criticality signal. Pass = agent just does the work, no block, no lecture | 1–2 | Pending |
| Opt-in | Over-fire task with `nasa-coding-standards: all-code` in the fixture's CLAUDE.md | 1 | Pending, and may not be dispatchable — see Risks |

Cost is roughly eight subagent runs at approximately the per-arm price of `deploy`'s deferred
GREEN arm (~180k tokens).
RED runs regardless, because the baseline precedes the skill.
Whether GREEN and over-fire run or are deferred is a decision to make after the skill exists,
with baseline results in hand; it changes only what `TESTING.md` is permitted to claim.

### Rep hygiene

- One directory per rep, each with its own fixture copy.
  Parallel subagents on a shared fixture race and produce phantom findings.
- Variance across reps is the signal.
  Three reps converging means the wording binds; three different interpretations mean it does not,
  however reasonable each one looks alone.

## Risks

The opt-in arm may not be testable by subagent dispatch at all.
Subagents inherit the session's CLAUDE.md snapshot, and a fixture's own CLAUDE.md in another
directory is not guaranteed to load.
If that holds, the arm needs a real session with its working directory inside the fixture, which
is manual and cannot be batched with the others.
The under-fire and over-fire arms are built first; the opt-in arm is treated as a separate,
honestly-labeled exercise rather than faked.

A fixture that passes under every arm is saturated, not evidence of no effect, and must be made
harder before it can discriminate.

Mechanical porting of the ten rules is the main content risk.
Several rules translate badly, and a skill that ports them anyway would give bad advice carrying
NASA's authority — worse than no skill.
The adjudication table above is the mitigation and is the part most worth re-reviewing.

## Follow-on work

`nasa-code-audit`, the review-time skill, reading the same `rules.md` so the rule set has one home.

Its description must be sharp enough that the agent knows when NASA-rule auditing is wanted
specifically.
Two review skills already compete for that trigger — `pr-review`, currently unmerged in a
worktree, and `jht-skills:quality-review` — and a third that fires on every review would turn
every diff into a Power-of-10 lecture.
