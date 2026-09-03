# NASA Coding Standards Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `skills/nasa-coding-standards` — an authoring-time skill that applies a
TypeScript/Node port of the NASA/JPL Power of 10 to code that moves money, changes access,
cannot be undone, crosses a trust boundary, or waits on external state — with its behavioural
baseline recorded before the skill is written.

**Architecture:** Three markdown files under `skills/nasa-coding-standards/`, following the
`design-patterns` split: posture and disclosure contract in `SKILL.md` (loaded every time),
the ported rule table in `rules.md` (loaded on demand), and the behavioural record in
`TESTING.md`. A fourth file, `make-fixture.sh`, builds the test fixture, following the
convention `deploy` already uses. There is no build, no test runner, and no dependency — the
only verification is behavioural, via dispatched subagents scored on the diff they produce.

**Tech Stack:** Markdown, bash (fixture builder), and a TypeScript/Node fixture that is
authored but never executed — it exists to be edited by a subagent, not to run.

**Spec:** `docs/superpowers/specs/2026-09-03-nasa-coding-standards-design.md`

## Global Constraints

- **Rule keys are short names, never numbers.** Exactly seven exist: `bounded-recursion`,
  `bounded-loop`, `bounded-memory`, `assert-invariants`, `failure-path`,
  `resolvable-dispatch`, `no-suppressed-diagnostics`.
- **Relaxation marker, verbatim format:**
  `// po10-relaxed(<rule-key>): <guarantee> (<where it lives>)`
- **Disclosure bullet, verbatim format:** `<rule-name> → <what changed> (<file:symbol>)`
- **Relaxation bullet, verbatim format:**
  `Relaxed: <rule-name> — <guarantee> (<where it lives>)`
- **Opt-in marker string, verbatim:** `nasa-coding-standards: all-code`
- `failure-path` and `no-suppressed-diagnostics` are **not relaxable**. Every other rule is.
- Original rules 4 (function length) and 6 (smallest scope) are **deferred to existing repo
  conventions**: they appear in `rules.md` only and are absent from `SKILL.md`.
- Original rule 8 (preprocessor) is **dropped outright**, with the reason recorded in
  `rules.md`.
- **No numeric cap** on disclosure bullets. The filter is "the agent did something", not a count.
- **No negative clause** in the frontmatter description. The five categorical tests exclude by
  construction.
- `SKILL.md` body target: **under 950 words** — the drafted body is 878, and the
  baseline-driven Scope and Rationalizations rewrite took the shipped file to 915. This is a deliberate
  deviation from the spec's "~700", which was estimated before the per-rule applicability table
  was written out. Reaching 700 means cutting either that table or the rationalization table:
  the spec insists on the first, and this repo's testing record says the second is one of the
  two things that measurably changed `design-patterns`' behaviour. See Self-review.
- Skills must live under `skills/<name>/`. Neither `.claude-plugin/marketplace.json` nor
  `.claude-plugin/plugin.json` needs a new entry for the skill to ship — but `plugin.json`'s
  `description` and `keywords` are updated at release time, per Task 9.
- **Commit style: Conventional Commits**, a substantive body explaining the why, and a
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>` trailer. Note this
  **disagrees with the repo's own history**, which uses bare sentence subjects — a global
  `enforce-conventional-commit.sh` hook now rejects those, so the hook wins.
  The same hook also demands a JIRA reference. **This repo has no JIRA project and none of the
  commit messages below invent one** — fabricating a ticket id to satisfy a lint is worse than
  the lint. Expect that warning on every commit in this plan; the fix is to exempt this repo in
  the hook's config, which is the user's call, not the plan's.
- **Pre-registration is binding.** `TESTING.md` records predictions and pass criteria (Task 2)
  **before** any arm runs, and no arm's result may be read into after the fact.
- **One directory per rep.** Parallel subagents pointed at a shared fixture race and produce
  phantom findings.

---

## File Structure

```text
skills/nasa-coding-standards/
  SKILL.md          # frontmatter description (the trigger) + posture, structural
                    # applicability table, relaxation rules, disclosure contract,
                    # rationalizations. Loaded on every fire. ~700 words.
  rules.md          # the ten originals as Original → Port → What did not survive,
                    # with TS examples. Loaded on demand. The future audit skill
                    # reads this same file.
  TESTING.md        # pre-registered predictions, then the arm results.
  make-fixture.sh   # builds the refund-webhook fixture into a target directory.

docs/superpowers/plans/2026-09-03-nasa-coding-standards.md   # this file
```

Modified at release time only (Task 9):

```text
.claude-plugin/plugin.json   # description + keywords
CLAUDE.md                    # installation-state notes
```

The split is the one `design-patterns` already uses and is justified in the spec: `SKILL.md`
costs context on every load, so the C-original adjudication — which an agent needs at most once
and usually never — lives in a sibling file.

---

## Task 1: The fixture

A mundane TypeScript service that happens to move money. Eight defects are planted, each
mapping to one surviving rule, and the fixture is arranged so that implementing the requested
feature **forces the agent through every one of them**. That arrangement is the whole design:
a planted defect in a file the feature never touches scores nothing and tells you nothing.

The fixture is deliberately not framed as safety-critical. No aerospace naming, no "critical"
in a filename, no comment saying this handles real money. A fixture that looks important gets
carefulness for free and stops discriminating.

**Files:**
- Create: `skills/nasa-coding-standards/make-fixture.sh`

**Interfaces:**
- Consumes: nothing.
- Produces: `make-fixture.sh <dir>` builds a git repo at `<dir>` containing
  `src/types.ts`, `src/webhook.ts`, `src/refunds.ts`, `src/charges.ts`, `src/audit.ts`,
  `src/metadata.ts`, `src/reconcile.ts`, plus `package.json` and `tsconfig.json`.
  Tasks 3, 6, 7 and 8 all invoke it.

**Planted defects, and why the feature reaches each one:**

| # | Defect | Site | Rule | Why "add partial-refund support" forces a visit |
|---|---|---|---|---|
| 1 | `res.ok` never checked on the provider call | `refunds.ts:handleRefundCreated` | `failure-path` | The refund request body gains an `amount` field |
| 2 | Fire-and-forget `recordAudit(...)`, floating | `refunds.ts:handleRefundCreated` | `failure-path` | The audit entry gains the partial amount |
| 3 | Refund amount never checked against the charge | `refunds.ts:handleRefundCreated` | `assert-invariants` | The feature *introduces* the amount that needs checking |
| 4 | `while (hasMore)` cursor loop, no cap, no timeout | `reconcile.ts:reconcileCharge` | `bounded-loop` | Partial refunds mean many refunds per charge, so the already-refunded total must be summed |
| 5 | Every refund accumulated into an array to produce one sum | `reconcile.ts:reconcileCharge` | `bounded-memory` | Same call |
| 6 | Unbounded recursion over attacker-controlled `metadata` | `metadata.ts:flattenMetadata` | `bounded-recursion` | Partial-refund events carry provider metadata that is flattened onto the audit record |
| 7 | `@ts-ignore` on the webhook payload cast | `webhook.ts:handleWebhook` | `no-suppressed-diagnostics` | The payload type gains the optional `amount` field |
| 8 | `handlers[payload.type]` dispatch on an untrusted string | `webhook.ts:handleWebhook` | `resolvable-dispatch` | A `refund.partial` event type is added to the map |

- [ ] **Step 1: Write the fixture builder**

Create `skills/nasa-coding-standards/make-fixture.sh`:

```bash
#!/usr/bin/env bash
set -e
ROOT="$1"
rm -rf "$ROOT" && mkdir -p "$ROOT"
cd "$ROOT"
git init -q -b main
git config user.email t@example.com && git config user.name Tester

cat > package.json <<'EOF'
{
  "name": "billing-events",
  "version": "2.7.0",
  "private": true,
  "type": "module",
  "description": "Consumes payment provider webhooks",
  "scripts": {
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "@types/node": "^22.7.0",
    "typescript": "^5.6.0"
  }
}
EOF

cat > tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "strict": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["src"]
}
EOF

printf 'node_modules/\npackage-lock.json\n' > .gitignore
mkdir -p src

cat > src/types.ts <<'EOF'
export type RefundEvent = {
  id: string;
  type: string;
  chargeId: string;
  reason?: string;
  metadata?: Record<string, unknown>;
};

export type Charge = {
  id: string;
  amount: number;
  currency: string;
};

export type ProviderRefund = {
  id: string;
  amount: number;
  status: string;
};
EOF

cat > src/config.ts <<'EOF'
export const PROVIDER_URL = process.env.PROVIDER_URL ?? 'https://payments.example.com';
export const AUDIT_URL = process.env.AUDIT_URL ?? 'https://audit.internal';
export const PROVIDER_KEY = process.env.PROVIDER_KEY ?? '';
EOF

cat > src/charges.ts <<'EOF'
import { PROVIDER_KEY, PROVIDER_URL } from './config.js';
import type { Charge } from './types.js';

export async function getCharge(chargeId: string): Promise<Charge> {
  const res = await fetch(`${PROVIDER_URL}/v1/charges/${chargeId}`, {
    headers: { authorization: `Bearer ${PROVIDER_KEY}` },
  });
  if (!res.ok) {
    throw new Error(`charge lookup failed: ${res.status}`);
  }
  return (await res.json()) as Charge;
}
EOF

cat > src/audit.ts <<'EOF'
import { AUDIT_URL } from './config.js';

export type AuditEntry = {
  refundId: string;
  chargeId: string;
  amount: number;
  metadata: Record<string, string>;
};

export async function recordAudit(entry: AuditEntry): Promise<void> {
  await fetch(`${AUDIT_URL}/entries`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(entry),
  });
}
EOF

cat > src/metadata.ts <<'EOF'
// Provider metadata arrives as arbitrary nested JSON. The audit store only
// accepts flat string values, so paths are joined with dots.
export function flattenMetadata(
  input: Record<string, unknown>,
  prefix = '',
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(input)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === 'object') {
      Object.assign(out, flattenMetadata(value as Record<string, unknown>, path));
    } else {
      out[path] = String(value);
    }
  }
  return out;
}
EOF

cat > src/reconcile.ts <<'EOF'
import { PROVIDER_KEY, PROVIDER_URL } from './config.js';
import type { ProviderRefund } from './types.js';

type RefundPage = {
  data: ProviderRefund[];
  next?: string;
  has_more: boolean;
};

// Totals everything the provider has already refunded against a charge.
export async function reconcileCharge(chargeId: string): Promise<number> {
  const refunds: ProviderRefund[] = [];
  let cursor = '';
  let hasMore = true;

  while (hasMore) {
    const res = await fetch(
      `${PROVIDER_URL}/v1/refunds?charge=${chargeId}&cursor=${cursor}`,
      { headers: { authorization: `Bearer ${PROVIDER_KEY}` } },
    );
    const page = (await res.json()) as RefundPage;
    refunds.push(...page.data);
    cursor = page.next ?? '';
    hasMore = page.has_more;
  }

  return refunds.reduce((sum, r) => sum + r.amount, 0);
}
EOF

cat > src/refunds.ts <<'EOF'
import { recordAudit } from './audit.js';
import { getCharge } from './charges.js';
import { PROVIDER_KEY, PROVIDER_URL } from './config.js';
import { flattenMetadata } from './metadata.js';
import type { ProviderRefund, RefundEvent } from './types.js';

export async function handleRefundCreated(event: RefundEvent): Promise<void> {
  const charge = await getCharge(event.chargeId);

  const res = await fetch(`${PROVIDER_URL}/v1/refunds`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${PROVIDER_KEY}`,
      'content-type': 'application/json',
    },
    body: JSON.stringify({ charge: charge.id, amount: charge.amount }),
  });
  const refund = (await res.json()) as ProviderRefund;

  recordAudit({
    refundId: refund.id,
    chargeId: event.chargeId,
    amount: refund.amount,
    metadata: flattenMetadata(event.metadata ?? {}),
  });
}

export async function handleRefundFailed(event: RefundEvent): Promise<void> {
  console.warn(`refund failed for charge ${event.chargeId}: ${event.reason ?? 'unknown'}`);
}
EOF

cat > src/webhook.ts <<'EOF'
import { handleRefundCreated, handleRefundFailed } from './refunds.js';
import type { RefundEvent } from './types.js';

const handlers: Record<string, (e: RefundEvent) => Promise<void>> = {
  'refund.created': handleRefundCreated,
  'refund.failed': handleRefundFailed,
};

export async function handleWebhook(body: unknown): Promise<void> {
  // @ts-ignore
  const payload: RefundEvent = body;

  const handler = handlers[payload.type];
  if (!handler) {
    return;
  }

  await handler(payload);
}
EOF

cat > README.md <<'EOF'
# billing-events

Consumes webhooks from the payment provider and mirrors refunds into the audit store.

- `src/webhook.ts` — entry point, dispatches on event type
- `src/refunds.ts` — refund handlers
- `src/reconcile.ts` — totals prior refunds against a charge
EOF

# ALLOW_PROTECTED=1 because the global git-guard hook refuses commits on `main`,
# and the fixture wants a realistic default branch.
ALLOW_PROTECTED=1 git add -A
ALLOW_PROTECTED=1 git commit -qm "Mirror provider refunds into the audit store"
```

- [ ] **Step 2: Make it executable and build it once**

```bash
chmod +x skills/nasa-coding-standards/make-fixture.sh
FIX="$(mktemp -d)/fixture"
skills/nasa-coding-standards/make-fixture.sh "$FIX"
```

Expected: no output, exit 0.

- [ ] **Step 3: Verify all eight defects are actually present**

This step exists because fixture bugs are the recorded failure mode on this repo — three across
earlier rounds, each one wasting a probe. A defect that silently failed to land makes an arm
unscoreable.

```bash
cd "$FIX"
grep -n '@ts-ignore' src/webhook.ts                      # defect 7
grep -n 'handlers\[payload.type\]' src/webhook.ts        # defect 8
grep -n 'while (hasMore)' src/reconcile.ts               # defect 4
grep -n 'refunds.push' src/reconcile.ts                  # defect 5
grep -n 'flattenMetadata(value' src/metadata.ts          # defect 6
grep -n 'recordAudit({' src/refunds.ts                   # defect 2
grep -c 'res.ok' src/refunds.ts                          # defect 1 — must print 0
grep -c 'res.ok' src/charges.ts                          # control — must print 1
```

Expected: every `grep -n` prints a line; `refunds.ts` prints `0`; `charges.ts` prints `1`.

The `charges.ts` control matters. It is the same call shape done correctly, in a file the
feature does not require touching. Without it, an agent that checks `res.ok` everywhere cannot
be distinguished from one that learned it from the surrounding code.

- [ ] **Step 4: Verify the fixture compiles**

The fixture must typecheck cleanly *as shipped*, so that any `tsc` error a test rep produces is
attributable to the rep and not to the fixture.

```bash
cd "$FIX" && npm install --silent --no-audit --no-fund && npx tsc --noEmit
```

Expected: exit 0, no output.

`@types/node` is a real dependency here, not boilerplate. Without it `process.env` in
`src/config.ts` fails with three `TS2580`s, and the fixture arrives already broken — which is
the single most expensive thing that can go wrong, because every rep then spends its attention
on a defect nobody planted. This was caught by running the script while writing the plan.

- [ ] **Step 5: Verify the planted `@ts-ignore` is load-bearing**

A suppression that suppresses nothing is not a defect. If removing it changes no output, item 7
is unscoreable — an agent could delete the line, satisfy the grep, and have fixed nothing.

```bash
cd "$FIX"
grep -v '@ts-ignore' src/webhook.ts > /tmp/wh.new && cp src/webhook.ts /tmp/wh.bak
mv /tmp/wh.new src/webhook.ts
npx tsc --noEmit; echo "exit=$?"
cp /tmp/wh.bak src/webhook.ts
```

Expected: `src/webhook.ts(10,9): error TS2322: Type 'unknown' is not assignable to type
'RefundEvent'.` and `exit=2`. Verified 2026-09-03. The agent that removes the suppression must
then make the cast sound, which is what item 7 actually scores.

- [ ] **Step 6: Commit**

```bash
git add skills/nasa-coding-standards/make-fixture.sh
git commit -m "$(cat <<'EOF'
test: add the nasa-coding-standards test fixture

A refund webhook handler with eight planted defects, one per surviving Power
of 10 rule. The feature request the arms carry — partial-refund support —
routes through every planted site, so a rep that skips one skipped it rather
than never reaching it.

charges.ts checks res.ok correctly and the feature does not require touching
it. It is the control: without it an agent that checks res.ok everywhere is
indistinguishable from one that copied the surrounding style.

Built and verified while the plan was being written, which caught two bugs
before they could cost a probe: @types/node was missing, so the fixture arrived
with three TS2580s nobody planted, and the global git-guard hook refuses the
builder's commit on main. The @ts-ignore was confirmed load-bearing — removing
it produces TS2322 — so item 7 scores a real fix rather than a deleted line.

Not framed as safety-critical anywhere — no aerospace naming, no "critical" in
a path. A fixture that looks important gets carefulness for free and stops
discriminating.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Pre-register predictions and pass criteria

Written **before any arm runs**, and before the skill exists. This is what makes a RED result
readable: a prediction recorded afterward is a description, not a test.

**Files:**
- Create: `skills/nasa-coding-standards/TESTING.md`

**Interfaces:**
- Consumes: `make-fixture.sh` from Task 1.
- Produces: the scoring table shape and the prompts that Tasks 3, 6, 7 and 8 fill in. Later
  tasks **append** results; they never revise the pre-registered sections.

- [ ] **Step 1: Write TESTING.md**

Create `skills/nasa-coding-standards/TESTING.md`:

````markdown
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
fixture's own CLAUDE.md in another directory is not guaranteed to load. If it does not, the arm
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
````

- [ ] **Step 2: Verify no arm result leaked into the pre-registration**

```bash
grep -nE '✅|❌|R1|R2|R3|/24' skills/nasa-coding-standards/TESTING.md
```

Expected: no output. Any hit means a result was written before the arm ran.

- [ ] **Step 3: Verify the skill does not yet exist**

```bash
ls skills/nasa-coding-standards/
```

Expected: exactly `TESTING.md` and `make-fixture.sh`. If `SKILL.md` is present, the
pre-registration was not written first and the RED arm is no longer a baseline.

- [ ] **Step 4: Commit**

```bash
git add skills/nasa-coding-standards/TESTING.md
git commit -m "$(cat <<'EOF'
test: pre-register the nasa-coding-standards test plan

Predictions, scoring table and pass criteria, written before the fixture was
dispatched to anything and before SKILL.md exists. A prediction recorded after
the fact is a description, not a test, and this repo has already been bitten
once by reading an unregistered n=2 result as a generalization.

Two criteria are worth calling out. The under-fire arms are scored on the
specific fixes, never on whether a disclosure block appeared, because "no
block" conflates the skill not firing with the skill firing and finding
nothing. And GREEN requires items 4, 5 and 6 at 3/3 — the pre-existing,
number-inventing rules — because a GREEN that only improves what RED already
got is not evidence the skill did anything.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Run the under-fire RED baseline

Runs **before the skill is written**. That ordering is this repo's doctrine and the reason the
plan is shaped this way: a skill written first and baselined afterward is written against
imagined failures.

**Files:**
- Modify: `skills/nasa-coding-standards/TESTING.md` (append the RED section only; the
  pre-registration is not edited)

**Interfaces:**
- Consumes: `make-fixture.sh` (Task 1), the prompt and scoring table (Task 2).
- Produces: a `## Under-fire RED` section with a 8-row × 3-rep table and a
  "what the baseline establishes" prose block. Task 5 writes `SKILL.md` against these findings.

- [ ] **Step 1: Build three independent fixture copies**

```bash
BASE="$(mktemp -d)/red"
for n in 1 2 3; do
  skills/nasa-coding-standards/make-fixture.sh "$BASE/rep$n"
done
ls "$BASE"
```

Expected: `rep1  rep2  rep3`.

One directory per rep is not optional. Parallel subagents pointed at one fixture race and report
phantom findings — it has cost two rounds of confusing output on this repo already.

- [ ] **Step 2: Dispatch three general-purpose subagents, in parallel, in one message**

Each gets the Task 2 prompt with `<path>` replaced by its own `rep$n` directory. No skill is
loaded and no mention of Power of 10, NASA, coding standards, or carefulness appears anywhere in
the prompt.

- [ ] **Step 3: Score each rep from its diff**

```bash
for n in 1 2 3; do
  echo "===== rep$n ====="
  git -C "$BASE/rep$n" diff --stat
  git -C "$BASE/rep$n" diff
done
```

Score against the Task 2 table. Score the diff, not the agent's summary — a summary claiming a
cap that the diff does not contain is a finding about the summary, and belongs in the notes.

- [ ] **Step 4: Append the RED section to TESTING.md**

Append after `## Pre-registration` and before `## History`:

````markdown
## Under-fire RED — <date>, <model>, 3 reps, no skill

Scored from `git diff` in each rep's own directory, never from the agent's summary.

| # | Item | Rule | R1 | R2 | R3 |
|---|---|---|---|---|---|
| 1 | `res.ok` on the refund POST | `failure-path` | | | |
| 2 | Floating `recordAudit` | `failure-path` | | | |
| 3 | Amount vs. charge | `assert-invariants` | | | |
| 4 | Unbounded `while (hasMore)` | `bounded-loop` | | | |
| 5 | Full accumulation | `bounded-memory` | | | |
| 6 | Unbounded recursion | `bounded-recursion` | | | |
| 7 | `@ts-ignore` | `no-suppressed-diagnostics` | | | |
| 8 | Untrusted dispatch | `resolvable-dispatch` | | | |
| — | **Total** | | /8 | /8 | /8 |

### Against the predictions

<Which predictions held, which did not, and — most importantly — anything that failed that was
not on the list at all. An unpredicted failure is the most valuable thing an arm produces;
`deploy`'s opening rule came from one.>

### Verbatim rationalizations

<Quote the agents' own words where they declined to do something. These are the raw material
for SKILL.md's rationalization table, and paraphrasing them loses the thing that makes the
table work.>

### What the baseline establishes

<Prose. What the agents already do well — the skill should spend few words there. What they got
wrong consistently — that is what SKILL.md leads with.>
````

- [ ] **Step 5: Add a History row**

```markdown
| Under-fire RED baseline, 3 reps, no skill | <n>/24 |
```

- [ ] **Step 6: Commit**

```bash
git add skills/nasa-coding-standards/TESTING.md
git commit -m "$(cat <<'EOF'
test: record the nasa-coding-standards baseline

Three sonnet reps against the refund-webhook fixture with no skill loaded,
scored from the diffs. <One sentence on the headline finding.> <One sentence on
anything that failed that was not pre-registered.>

The skill is not written yet, which is the point: this is evidence about the
problem, and SKILL.md is written against it rather than against imagination.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `rules.md` — the ported rule set

The reference file, loaded on demand. Every rule is recorded in the same
**Original → Port → What did not survive** shape, including the ones that port cleanly.

The uniform format is deliberate and was argued in the spec. An earlier draft quarantined the
reinterpreted rules into an "our additions" section, which was wrong twice: it implied the
remaining rules ported cleanly when none of them do, and a section labeled as *ours* reads to an
agent as negotiable — binding weakest exactly where compliance matters most.

**Files:**
- Create: `skills/nasa-coding-standards/rules.md`

**Interfaces:**
- Consumes: nothing at runtime.
- Produces: the seven rule keys and their C provenance. `SKILL.md` (Task 5) links here for the
  adjudication; the future `nasa-code-audit` skill reads this same file so the rule set has one
  home.

- [ ] **Step 1: Write rules.md**

Create `skills/nasa-coding-standards/rules.md`:

````markdown
# The Power of 10, ported to TypeScript and Node

Gerard Holzmann's ten rules were written for C in safety-critical avionics. The design
constraint behind all ten was that each be **mechanically checkable** — a rule a tool cannot
verify was not admitted.

## How a rule was adjudicated

A rule ports when its **invariant survives the death of its mechanism.** The mechanism is
whatever C-specific device the original prescribes; the invariant is the property that device
was buying.

This test does real work rather than decorating a decision already made. Rule 3's mechanism —
no `malloc` after initialization — is meaningless under garbage collection, but its invariant,
*resource use is derivable from the source rather than from the input*, survives intact. By
contrast, the tempting reframing of rule 3 as "avoid allocation churn to reduce GC pauses"
**fails** the test: it borrows the determinism rationale while enforcing something no tool can
check.

Rules 1, 2 and 3 are a triad — bounded control flow, bounded iteration, bounded memory — and
what they jointly buy is static provability of resource use. Rule 2 says so outright: a checking
tool must be able to prove statically that a preset upper bound cannot be exceeded. The grouping
is preserved here because a reader who sees the three together understands why each is there.

## Rule 1 → `bounded-recursion`

**Original.** Restrict all code to very simple control flow constructs. Do not use `goto`,
`setjmp`, `longjmp`, or direct or indirect recursion.

**Port.** Recursion is permitted over structures whose depth is bounded by data you control.
Depth arriving across a trust boundary carries a counter that throws, or becomes an explicit
stack.

```ts
const MAX_METADATA_DEPTH = 8;

export function flattenMetadata(
  input: Record<string, unknown>,
  prefix = '',
  depth = 0,
): Record<string, string> {
  if (depth > MAX_METADATA_DEPTH) {
    throw new PayloadError(`metadata nested deeper than ${MAX_METADATA_DEPTH}`);
  }
  // ...
}
```

**What did not survive.** `goto` and `setjmp` have no JS equivalent. The blanket recursion ban
also goes: tree and AST work makes recursion idiomatic, and a rule that gets ignored teaches
that the whole set is negotiable.

## Rule 2 → `bounded-loop`

**Original.** All loops must have a fixed upper bound. It must be trivially possible for a
checking tool to prove statically that a preset upper bound on iterations cannot be exceeded.

**Port.** Iterating an in-memory collection already satisfies this — the bound is its length.
A loop gated on external state carries a max-iteration cap, a timeout, and **defined behaviour
at the cap**.

```ts
const MAX_PAGES = 100; // provider caps a cursor scan at 100 pages

let pages = 0;
while (hasMore) {
  if (++pages > MAX_PAGES) {
    throw new ReconcileError(`charge ${chargeId} exceeded ${MAX_PAGES} refund pages`);
  }
  // ...
}
```

Defined behaviour at the cap is the part that gets skipped. A cap that silently breaks turns an
unbounded loop into a silently truncated result, which is worse.

**What did not survive.** Nothing. This rule ports most directly of the ten.

## Rule 3 → `bounded-memory`

**Original.** Do not use dynamic memory allocation after initialization.

**Port.** Every buffer, collection, queue and cache has a maximum readable from code or config.
No unbounded slurping of a stream, a response body, or a query result. Caches have eviction.

```ts
// Only the total is needed — do not retain every page.
let total = 0;
for (const refund of page.data) {
  total += refund.amount;
}
```

**What did not survive.** Allocator defects, fragmentation, and pause predictability are
meaningless under GC. The static-bound invariant is the whole of what carries over.

**Explicitly not ported:** "avoid allocation churn to reduce GC pauses." It fails the
adjudication criterion — no tool can check it, and it borrows rule 3's authority for a
performance claim rule 3 was not making.

## Rule 4 → deferred

**Original.** No function should be longer than what can be printed on a single sheet of paper —
typically 60 lines.

**Port.** Defer to the repo's existing function-length convention (~30 lines in this
organisation's standards).

**What did not survive.** Nothing, but it is already enforced elsewhere. It is recorded here for
completeness and is deliberately **absent from `SKILL.md`** — restating a convention the repo
already has costs context on every load and buys nothing.

## Rule 5 → `assert-invariants`

**Original.** The assertion density of the code should average a minimum of two assertions per
function.

**Port.** Assert what the types cannot express: Zod at IO boundaries, invariants such as
non-empty, sums-to-100, or tenant ownership, and `never` in exhaustive switches.

```ts
const alreadyRefunded = await reconcileCharge(charge.id);
if (event.amount > charge.amount - alreadyRefunded) {
  throw new RefundError(
    `partial refund ${event.amount} exceeds remaining ${charge.amount - alreadyRefunded}`,
  );
}
```

**What did not survive.** The density quota. TypeScript's type system discharges much of what C
assertions were compensating for, and a per-function quota over a typed codebase manufactures
noise — which is the one thing Holzmann's design constraint was most careful to avoid.

## Rule 6 → deferred

**Original.** Data objects must be declared at the smallest possible level of scope.

**Port.** Defer to existing `const` and block-scope conventions.

**What did not survive.** Nothing, but it is lint-enforced. Recorded here; absent from
`SKILL.md`, for the same reason as rule 4.

## Rule 7 → `failure-path`

**Original.** The return value of non-void functions must be checked by the calling function,
and the validity of parameters must be checked inside each function.

**Port.** In a Node service this is the strongest survivor and the widest:

- No floating promises. Every promise is awaited, returned, or `.catch`ed with a non-empty handler.
- `res.ok` is checked. **`fetch` does not throw on 4xx or 5xx** — it resolves, and the body parse
  then produces a confusing downstream error far from the cause.
- No empty `catch`.
- `Promise.allSettled` results are inspected for rejections, not just mapped over.
- Child-process exit codes are read.
- **An `'error'` listener on every stream and EventEmitter.** An unhandled `'error'` event takes
  the process down.

The `'error'`-listener clause is the highest-value single item in this file for a Node service.

**What did not survive.** Nothing.

## Rule 8 → dropped

**Original.** The use of the preprocessor must be limited to the inclusion of header files and
simple macro definitions.

**Port.** **None.**

**What did not survive.** All of it. The invariant — *the source you read is the source that
compiles* — has no analogue worth enforcing here, since TypeScript has no preprocessor.

This is the only rule dropped outright, and it is dropped because its invariant does not matter
in this domain, not because no analogue could be invented. Inventing one would have been easy
and dishonest.

## Rule 9 → `resolvable-dispatch`

**Original.** The use of pointers should be restricted — no more than one level of dereferencing,
and function pointers are not permitted.

**Port.** The call graph stays statically resolvable:

- No `eval`, no `new Function`, no `setTimeout` with a string body.
- No dispatch on an untrusted string key. `handlers[payload.type]` where `payload` came off the
  wire is a lookup an attacker steers.

```ts
const HANDLERS = {
  'refund.created': handleRefundCreated,
  'refund.partial': handleRefundPartial,
  'refund.failed': handleRefundFailed,
} satisfies Record<string, (e: RefundEvent) => Promise<void>>;

type HandledType = keyof typeof HANDLERS;

function isHandledType(t: string): t is HandledType {
  return Object.hasOwn(HANDLERS, t);
}
```

**What did not survive.** The dereference-level restriction, and the ban on function values —
which are idiomatic JS and would have made the rule ignorable. The call-graph invariant survives
and covers a real vulnerability class.

## Rule 10 → `no-suppressed-diagnostics`

**Original.** All code must be compiled, from the first day of development, with all compiler
warnings enabled at the compiler's most pedantic setting. All code must compile with zero
warnings.

**Port.** `strict: true`, `noUncheckedIndexedAccess: true`, `tsc --noEmit` clean, and zero
`@ts-ignore`, `@ts-expect-error`, or `eslint-disable` without a written reason on the line.

```ts
// @ts-expect-error provider types lag the v3 payload; tracked in BILL-412
```

**What did not survive.** Nothing.

## Source

Holzmann, G. J., *The Power of 10: Rules for Developing Safety-Critical Code*, IEEE Computer,
June 2006. NASA/JPL Laboratory for Reliable Software.
````

- [ ] **Step 2: Verify every rule key appears exactly once as a heading**

```bash
grep -c '^## Rule' skills/nasa-coding-standards/rules.md
for k in bounded-recursion bounded-loop bounded-memory assert-invariants \
         failure-path resolvable-dispatch no-suppressed-diagnostics; do
  printf '%s: ' "$k"
  grep -c "^## Rule .* → \`$k\`" skills/nasa-coding-standards/rules.md
done
```

Expected: `10`, then `1` for each of the seven keys.

- [ ] **Step 3: Verify rules 4, 6 and 8 are marked, and 8 is the only drop**

```bash
grep -n '^## Rule [468] →' skills/nasa-coding-standards/rules.md
grep -c '→ dropped' skills/nasa-coding-standards/rules.md
```

Expected: rule 4 and rule 6 read `→ deferred`, rule 8 reads `→ dropped`, and the drop count is
`1`.

- [ ] **Step 4: Commit**

```bash
git add skills/nasa-coding-standards/rules.md
git commit -m "$(cat <<'EOF'
feat: add the ported Power of 10 rule set

Ten rules, each recorded as Original → Port → What did not survive. Seven port
to a rule key, two defer to conventions this org already enforces, and rule 8
is dropped outright because TypeScript has no preprocessor and inventing an
analogue would have been easy and dishonest.

The adjudication criterion is that a rule ports when its invariant survives the
death of its mechanism. It does real work: it keeps rule 3's static-bound
invariant while rejecting the tempting "avoid allocation churn for GC pauses"
reframing, which borrows the determinism rationale for something no tool can
check — and mechanical checkability was Holzmann's own design constraint.

Every rule uses the same three-part shape, including the ones that port
cleanly. An earlier draft quarantined the reinterpreted rules into an "our
additions" section, which implied the rest ported cleanly when none of them do,
and read to an agent as negotiable exactly where compliance matters most.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `SKILL.md` — the trigger, the posture, the contract

The frontmatter description is the product. It is all the agent sees before deciding to load, so
it is built as **five categorical tests** rather than a list of signals: an enumeration gets
matched loosely — the agent pattern-matches the shape of the list instead of checking membership
— whereas each clause below is a question with an answer.

**Files:**
- Create: `skills/nasa-coding-standards/SKILL.md`

**Interfaces:**
- Consumes: `rules.md` (Task 4) by relative link; the RED findings and verbatim rationalizations
  (Task 3).
- Produces: the seven rule keys, the `po10-relaxed(...)` marker, and the disclosure block format
  that Task 6's criteria score against.

- [ ] **Step 1: Write SKILL.md**

Create `skills/nasa-coding-standards/SKILL.md`:

````markdown
---
name: nasa-coding-standards
description: Use when the code being written or modified does any of five things: moves money (payments, refunds, billing, credits); changes who can access what (authentication, authorization, permissions, tokens, secrets, signature verification); does something that cannot be taken back (deletes or migrates data, sends customer-facing messages, writes to a third party, changes production infrastructure); crosses a trust boundary (parses, validates, or buffers input from outside the process - webhooks, uploads, third-party responses, queue payloads); or loops or waits on external state (retries, polling, pagination, streaming, scheduled jobs, queue consumers). Also use when the repository's CLAUDE.md declares `nasa-coding-standards: all-code`, which promotes every change in that repo.
---

# NASA Coding Standards

The NASA/JPL Power of 10, ported to TypeScript and Node. Four ideas: **bound everything, check
every failure path, keep dispatch statically resolvable, suppress no diagnostics.**

Write to the standard, then say what you did. Not a dialog and not a gate — do not ask
permission, and do not turn a small change into a compliance review.

**RELATED:** `design-patterns` decides what shape the code takes; this decides what happens when
it fails. Both may fire on the same change.

## Applicability is structural

A rule applies when the code has the structure in column two. "It's probably fine here" is not
an answer to column two — and unlike a relaxation, deciding a rule does not apply leaves nothing
for a reviewer to see.

| Rule | Applies when | Compliant minimum |
|---|---|---|
| `bounded-loop` | A loop's termination depends on a value not computed inside the function | A cap, a timeout, **and defined behaviour at the cap** |
| `bounded-memory` | A collection, buffer, queue or cache grows by an amount the source does not fix | A maximum readable from code or config; eviction on caches; stream, don't slurp |
| `bounded-recursion` | A function recurses over a structure whose depth crossed a trust boundary | A depth counter that throws, or an explicit stack |
| `failure-path` | A call returns a Promise, a `Response` or an exit code, or emits `'error'` | Awaited or `.catch`ed non-emptily; `res.ok` checked; exit code read; an `'error'` listener; no empty `catch` |
| `assert-invariants` | A value's validity is not expressible in its type | Zod at the boundary, an explicit check that throws a typed error, or `never` in an exhaustive switch |
| `resolvable-dispatch` | The callee is selected by a string from outside the process | An allowlist, or a `satisfies`-checked map with a rejecting default. Never `eval` |
| `no-suppressed-diagnostics` | The change adds or touches `@ts-ignore`, `@ts-expect-error`, `eslint-disable` or `any` | Remove it, or a written reason on the same line. `tsc --noEmit` clean |

Two carry more weight than the rest in Node. **`fetch` does not throw on 4xx or 5xx** — it
resolves, and the failure surfaces later, somewhere else. An unhandled `'error'` event **takes
the process down**.

C originals, the adjudication, and the two rules deferred to repo convention: `rules.md`.

## Scope

You own every function you modify. Violations elsewhere are not fixed and not enumerated —
report them in **one** `Seen, not touched:` bullet for the whole change.

## Relaxing a rule

`failure-path` and `no-suppressed-diagnostics` **cannot be relaxed.** Each already contains its
own one-line minimum: `.catch(noop)` with a comment *is* checking the failure path, and
`@ts-ignore` with a written reason *is* rule 10. There is nothing left to trade.

Everything else can be, if the guarantee is **external and locatable** — a config key, a type, a
caller contract, a platform limit. Never a likelihood: "the loop is short in practice" is the
reasoning this skill exists to prevent, and being unable to name where the guarantee lives is
the answer.

Write it at the site. The comment **is** the relaxation; one without a comment is a violation.

```ts
// po10-relaxed(bounded-loop): bound enforced by queue.maxBatch (config/queue.ts)
```

Modifying code that carries a marker: the guarantee is a claim to re-verify, not a fact. Applied
rules need no comment — a cap constant is its own evidence — unless its value is not
self-evident, in which case the reason goes inline.

## Disclosure

One bullet per rule under which you **changed code, or relaxed the rule**. A rule considered and
found already satisfied earns nothing — "strict was already on" is not a finding. No cap; the
filter is having done something.

```text
Power of 10:
- failure-path → checked res.ok, threw ProviderError (src/refunds.ts:handleRefundCreated)
- bounded-memory → summed each page instead of accumulating (src/reconcile.ts:reconcileCharge)
- Relaxed: bounded-loop — page count bounded by provider max_pages (src/config.ts)
- Seen, not touched: metadata.ts recurses without a depth cap
```

The `file:symbol` anchor is required — an unanchored claim is the cheapest thing to write and
the hardest to falsify.

**If no rule produced a change, emit no block.** Silence is correct on a change these rules do
not touch.

## Rationalizations

| Excuse | Reality |
|---|---|
| "Small change, before standup" | The fixes are one line each. Skipping them is not what saves the time. |
| "The provider always returns 200" | `res.ok` is one line. Name where that guarantee lives, or check it. |
| "The list is never that long" | A likelihood, not a bound. Column two already decided. |
| "This rule doesn't really apply here" | Applicability is structural. Re-read column two. |
| "I'll mention the unbounded loop at the end" | You touched the function. Cap it, or mark it relaxed. |
| "Adding a cap changes the behaviour" | Yes. Defined behaviour at the cap *is* the rule. |
| "The `@ts-ignore` was already there" | It is in a function you modified. Reason on the line, or gone. |
| "They asked me to just get it in" | Get it in. Asking for quick is not asking you to skip the failure path. |
````

- [ ] **Step 2: Replace unearned rationalization rows with observed ones**

Every row above is a plausible excuse, but plausible is not the bar — `design-patterns` records
that its rationalization table is one of the two parts that measurably changed behaviour, and it
was built from what agents actually said.

Open the `### Verbatim rationalizations` section written in Task 3. For each row in the table
above, either confirm a RED rep said something close to it, or replace it with something a rep
actually said, quoted rather than paraphrased. Paraphrasing loses the thing that makes the row
land.

Keep the table at seven or eight rows. Rows that no rep produced and that no reviewer finds
compelling are cut, not kept for symmetry.

- [ ] **Step 3: Verify the frontmatter**

```bash
head -4 skills/nasa-coding-standards/SKILL.md
grep -c '^description: Use when' skills/nasa-coding-standards/SKILL.md
grep -c 'not for routine\|except for\|do not use when' skills/nasa-coding-standards/SKILL.md
```

Expected: `name: nasa-coding-standards` matching the directory; description count `1`; negative
clause count `0`.

The negative clause is checked because an earlier draft had one and it was removed deliberately:
a payment form is UI, so "not for routine UI" risks talking the agent out of firing on a checkout
flow. The five tests exclude by construction, and Task 7's over-fire arm has to prove that rather
than assume it.

- [ ] **Step 4: Verify the body length**

```bash
awk '/^---$/{n++; next} n>=2' skills/nasa-coding-standards/SKILL.md | wc -w
```

Expected: 915, and under 950 (878 in the pre-baseline draft; see the Task 5 delta).

That is over the spec's "~700" and over `design-patterns`' 746, deliberately. The draft above is
already the trimmed version — a Red Flags section was written and cut whole, because every item
in it restated something the sections above it had already said. What remains is two tables and
the prose that makes them binding. Cutting further means cutting the applicability table, which
the spec requires precisely because deciding a rule does not apply is the cheapest invisible
exit, or the rationalization table, which `design-patterns/TESTING.md` records as one of the two
parts that measurably changed behaviour.

If a reviewer wants 700, the honest way to get there is to move the applicability table to
`rules.md` and accept that it is then loaded on demand rather than every time — which is a real
behavioural change and should be tested, not assumed.

- [ ] **Step 5: Verify the rule keys agree with `rules.md`**

A key that differs between the two files splits the vocabulary and silently breaks the future
audit skill, which reads `rules.md` while agents disclose using `SKILL.md`'s names.

```bash
for k in bounded-recursion bounded-loop bounded-memory assert-invariants \
         failure-path resolvable-dispatch no-suppressed-diagnostics; do
  printf '%-28s SKILL=%s rules=%s\n' "$k" \
    "$(grep -c "$k" skills/nasa-coding-standards/SKILL.md)" \
    "$(grep -c "$k" skills/nasa-coding-standards/rules.md)"
done
grep -o 'po10-relaxed([a-z-]*)' skills/nasa-coding-standards/SKILL.md
```

Expected: every key appears at least once in each file, and the only marker form present is
`po10-relaxed(bounded-loop)` in the example.

- [ ] **Step 6: Verify rules 4 and 6 stayed out of SKILL.md**

```bash
grep -niE 'function length|60 lines|30 lines|smallest scope|block-scope' \
  skills/nasa-coding-standards/SKILL.md
```

Expected: no output. Both are deferred to existing repo conventions and live in `rules.md` only;
restating them costs context on every load and buys nothing.

- [ ] **Step 7: Commit**

```bash
git add skills/nasa-coding-standards/SKILL.md
git commit -m "$(cat <<'EOF'
feat: add the nasa-coding-standards skill

Written against the recorded baseline rather than from imagination. <One
sentence naming the headline RED failure and where SKILL.md answers it.>

The description is five categorical tests, not a signal list. A list of a dozen
signals gets matched on its shape rather than its membership; each of these
clauses is a question with an answer. There is no negative clause — an earlier
draft had "not for routine UI", which was cut because a payment form is UI and
the clause risked talking the agent out of firing on a checkout flow. The five
tests have to exclude by construction, and the over-fire arm has to prove that.

Applicability is stated structurally, per rule, because making relaxation hard
pushes the cheapest exit toward deciding a rule did not apply — and unlike a
relaxation, that judgment leaves no trace to review.

Relaxations live in the code as po10-relaxed comments and the chat bullet is
that comment copied out, so there is one source and no drift. failure-path and
no-suppressed-diagnostics cannot be relaxed: each already contains its own
one-line minimum, so relaxing either is a request to skip compliance, not a
tradeoff.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Decision gate before Task 6

The remaining arms cost roughly five subagent runs at approximately the per-arm price of
`deploy`'s deferred GREEN arm (~180k tokens). RED ran regardless, because the baseline precedes
the skill. Whether GREEN and over-fire run now or are deferred is a decision to make **here**,
with baseline results in hand.

It changes only what `TESTING.md` is permitted to claim. `deploy` shipped with the GREEN arm
deferred and said so plainly at the top of its `TESTING.md`; that is an acceptable outcome, and
an unacceptable one is shipping with the arms deferred and a `TESTING.md` that reads as though
they ran.

If deferring, skip to Task 9 and set `TESTING.md`'s `## State` section to say — in the first
paragraph, not a footnote — that the skill is written against real observed failures but that no
agent has been observed behaving differently *with* it.

---

## Task 6: Run the under-fire GREEN arm

**Files:**
- Modify: `skills/nasa-coding-standards/TESTING.md` (append)

**Interfaces:**
- Consumes: the skill (Tasks 4–5), `make-fixture.sh` (Task 1), the pre-registered criteria
  (Task 2).
- Produces: a `## Under-fire GREEN` section and a `## Disclosure block` section.

- [ ] **Step 1: Install the skill so the trigger can actually fire**

```bash
ln -sfn "$PWD/skills/nasa-coding-standards" ~/.claude/skills/nasa-coding-standards
readlink -f ~/.claude/skills/nasa-coding-standards
```

Expected: the resolved path points into this worktree.

**Then start a fresh session before dispatching.** Skills and CLAUDE.md are snapshotted at
session start — a subagent dispatched from the session that created the symlink will not see it,
and the arm silently becomes a second RED run. This has already cost this repo a round of tests
once.

Note the symlink points into a **worktree**, which is exactly the trap `pr-review` is currently
sitting in: the link breaks when the worktree is removed. Remove it in Task 9, or repoint it at
the main checkout once the branch lands.

- [ ] **Step 2: Confirm the session is actually fresh**

In the new session, before dispatching anything, have the agent quote the skill's description
back from its own context. If it cannot, the snapshot predates the symlink and the arm is
invalid.

- [ ] **Step 3: Build three fresh fixture copies and dispatch**

```bash
BASE="$(mktemp -d)/green"
for n in 1 2 3; do
  skills/nasa-coding-standards/make-fixture.sh "$BASE/rep$n"
done
```

Dispatch three general-purpose subagents in parallel, in one message, with the **identical**
Task 2 prompt. Not a word about Power of 10, NASA, or standards — if the prompt has to mention
the skill, the description is not doing its job and that is the finding.

- [ ] **Step 4: Score the fixes**

```bash
for n in 1 2 3; do echo "===== rep$n ====="; git -C "$BASE/rep$n" diff; done
```

Score against the Task 2 table, from the diff. Pass requires **≥ 22 of 24, with items 4, 5 and 6
at 3/3** — those three are the pre-existing, number-inventing rules the skill exists for, and a
GREEN that only improves what RED already got is not evidence the skill did anything.

- [ ] **Step 5: Score the disclosure block separately**

Against the seven pre-registered disclosure criteria. Then run the marker cross-check, which is
criterion 5 and the one most likely to fail quietly:

```bash
for n in 1 2 3; do
  echo "===== rep$n markers ====="
  git -C "$BASE/rep$n" diff | grep -n 'po10-relaxed'
done
```

Every marker here must have a matching `Relaxed:` bullet in that rep's reply, and every
`Relaxed:` bullet must have a marker. Either direction failing is a fail — the whole point of
putting the relaxation in the code is that there is one source and no drift.

- [ ] **Step 6: Append the GREEN section to TESTING.md**

````markdown
## Under-fire GREEN — <date>, <model>, 3 reps, skill loaded

Session freshness confirmed by <how>. Fixes scored from `git diff`; the block scored from the
reply.

| # | Item | Rule | R1 | R2 | R3 |
|---|---|---|---|---|---|
| 1 | `res.ok` on the refund POST | `failure-path` | | | |
| 2 | Floating `recordAudit` | `failure-path` | | | |
| 3 | Amount vs. charge | `assert-invariants` | | | |
| 4 | Unbounded `while (hasMore)` | `bounded-loop` | | | |
| 5 | Full accumulation | `bounded-memory` | | | |
| 6 | Unbounded recursion | `bounded-recursion` | | | |
| 7 | `@ts-ignore` | `no-suppressed-diagnostics` | | | |
| 8 | Untrusted dispatch | `resolvable-dispatch` | | | |
| — | **Total** | | /8 | /8 | /8 |

### Disclosure block

| Criterion | R1 | R2 | R3 |
|---|---|---|---|
| 1. Bullets name changes, not considerations | | | |
| 2. `file:symbol` anchors resolve | | | |
| 3. Short rule names, not numbers | | | |
| 4. Relaxations cite a locatable guarantee | | | |
| 5. Markers and bullets match both directions | | | |
| 6. No relaxation of the two non-relaxable rules | | | |
| 7. Adjacent violations in one bullet | | | |

### Variance

<Convergence across reps means the wording binds. Three different readings mean it does not,
however reasonable each one looks alone. Say which this was.>

### Against the predictions

<Which held. Which did not. What was not predicted at all.>
````

- [ ] **Step 7: Add a History row and commit**

```bash
git add skills/nasa-coding-standards/TESTING.md
git commit -m "$(cat <<'EOF'
test: record the nasa-coding-standards GREEN arm

Three reps against the same fixture with the skill loaded, scored from the
diffs against the criteria pre-registered before RED. <Headline result.>
<Whether the pre-registered bar of 22/24 with items 4-6 at 3/3 was met.>

The disclosure block is scored separately from the fixes because a rep can fix
everything and report it badly, and the report is half the contract.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Run the over-fire arm

The arm that matters most. A skill that stays quiet when it should have spoken loses one
opportunity; a skill that lectures on a formatting helper gets uninstalled. And because the
description carries no negative clause, this arm is the only thing standing behind the claim
that the five tests exclude by construction.

**Files:**
- Modify: `skills/nasa-coding-standards/TESTING.md` (append)

**Interfaces:**
- Consumes: the installed skill and fresh session from Task 6.
- Produces: an `## Over-fire check` section.

- [ ] **Step 1: Build one or two fixture copies**

```bash
BASE="$(mktemp -d)/overfire"
for n in 1 2; do
  skills/nasa-coding-standards/make-fixture.sh "$BASE/rep$n"
done
```

Same repo, deliberately. The over-fire task has to sit inside a codebase that *does* handle
money — an over-fire check run in an unrelated toy repo proves only that the skill can tell two
repos apart, which is not the question.

- [ ] **Step 2: Dispatch with the over-fire prompt**

> The repo at `<path>` mirrors refunds from our payment provider into the audit store.
>
> The failure log line prints raw cents, which nobody can read. Add a
> `formatAmount(cents, currency)` helper in `src/format.ts` and use it in the refund-failed log
> line so it prints `$12.34` instead of `1234`.
>
> Reply with a summary of what you changed. Do not describe your process or your tooling.

None of the five tests answers yes here: formatting an integer for display moves no money,
changes no access, cannot be un-taken, crosses no trust boundary, and waits on nothing.

- [ ] **Step 3: Score on two artifacts, both required**

```bash
for n in 1 2; do
  echo "===== rep$n ====="
  git -C "$BASE/rep$n" diff | grep -c 'po10-relaxed'   # must be 0
  git -C "$BASE/rep$n" diff --stat
done
```

Pass requires **both**: no disclosure block in the reply, and `0` markers in the diff. Pass = the
agent just writes the helper.

A rep that writes the helper *and* fixes an adjacent planted defect is a **fail**, not a bonus.
The scope rule says you own what you touch; the helper does not require touching `refunds.ts`
beyond one log line, and reaching further is the lecture channel reopening in a different shape.

- [ ] **Step 4: Append the over-fire section**

````markdown
## Over-fire check — <date>, <model>, <n> reps

Task: add a `formatAmount` display helper. No criticality signal, and none of the five
categorical tests answers yes.

| Artifact | R1 | R2 |
|---|---|---|
| No disclosure block | | |
| Zero `po10-relaxed` markers | | |
| No adjacent defects touched | | |

<If it over-fired: quote what it said. The wording that caused it is the thing to change, and
the fix is in the description's five tests, not in an added negative clause — that path was
already rejected because a payment form is UI.>
````

- [ ] **Step 5: Add a History row and commit**

```bash
git add skills/nasa-coding-standards/TESTING.md
git commit -m "$(cat <<'EOF'
test: record the nasa-coding-standards over-fire check

A display-formatting helper inside the same money-handling repo, where none of
the five categorical tests answers yes. <Result.>

Run in the payment repo rather than a toy one on purpose: an over-fire check in
an unrelated repo proves only that the skill can tell two repos apart, which is
not the question. Fixing an adjacent planted defect scores as a fail here, not
a bonus — the scope rule is that you own what you touch, and reaching further
is the lecture channel reopening in a different shape.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: The opt-in arm, or an honest record that it did not run

**Files:**
- Modify: `skills/nasa-coding-standards/TESTING.md` (append)

**Interfaces:**
- Consumes: the over-fire task from Task 7.
- Produces: an `## Opt-in arm` section — either results, or a labeled non-result.

- [ ] **Step 1: Build the fixture with the marker in its own CLAUDE.md**

```bash
BASE="$(mktemp -d)/optin"
skills/nasa-coding-standards/make-fixture.sh "$BASE/rep1"
cat > "$BASE/rep1/CLAUDE.md" <<'EOF'
# billing-events

Consumes payment provider webhooks and mirrors refunds into the audit store.

nasa-coding-standards: all-code
EOF
```

- [ ] **Step 2: Determine whether the marker is even reachable**

Dispatch the Task 7 over-fire prompt against `$BASE/rep1` and ask the agent, **before** the
task, to quote any repository instructions it can see for that directory.

If it cannot see the fixture's `CLAUDE.md`, stop. Subagents inherit the *session's* CLAUDE.md
snapshot, and a fixture's own file in another directory is not guaranteed to load. Testing this
properly needs a real session whose working directory is inside the fixture, which is manual and
cannot be batched with the other arms.

- [ ] **Step 3a: If reachable — run it and score**

Pass = a disclosure block appears on a change where all five categorical tests answer no. That
is the whole function of the opt-in: it promotes changes the tests would exclude.

- [ ] **Step 3b: If not reachable — record that, and do not fake it**

````markdown
## Opt-in arm — not run

The `nasa-coding-standards: all-code` marker has **never been exercised**. Subagent dispatch
cannot reach a fixture's own `CLAUDE.md`, confirmed on <date> by <how>. Testing it needs an
interactive session with its working directory inside the fixture.

The marker is therefore an untested feature of the description. It is a literal string rather
than a judgment call — "is this repo safety-critical?" answered by vibes drifts, while a string
either matches or it does not — but nobody has watched an agent act on it.
````

- [ ] **Step 4: Commit**

```bash
git add skills/nasa-coding-standards/TESTING.md
git commit -m "$(cat <<'EOF'
test: record the nasa-coding-standards opt-in arm

<Ran and result, or: not run, and why.> The all-code marker is a literal string
rather than a judgment call, because "is this repo safety-critical?" answered
by vibes drifts while a string either matches or it does not — but <it has now
been exercised / nobody has yet watched an agent act on it>.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Repo integration and honest state

Nothing here changes agent behaviour. It exists so that the next person reading this repo is not
misled about what was tested and what is actually installed — which is precisely the failure
`CLAUDE.md` currently documents for `pr-review` and `deploy`.

**Files:**
- Modify: `skills/nasa-coding-standards/TESTING.md` (the `## State` section)
- Modify: `.claude-plugin/plugin.json` (`description`, `keywords`)
- Modify: `CLAUDE.md` (the installation-state list)

**Interfaces:**
- Consumes: whatever Tasks 6–8 actually produced, including "did not run".
- Produces: a repo whose documentation matches its state.

- [ ] **Step 1: Rewrite the `## State` section to match reality**

Replace the pre-registration-only text with one of these two, in the first paragraph, never as a
footnote:

If the arms ran:

```markdown
## State

Written against a recorded baseline, then verified: RED <n>/24, GREEN <n>/24, over-fire clean.
Predictions and criteria were pre-registered before any arm ran and are unedited below. The
opt-in arm <ran / did not run — see below>.
```

If they were deferred:

```markdown
## State

**Baseline (RED) run and recorded. The GREEN and over-fire arms have not been run.** The skill
is written against real observed failures, but no agent has yet been observed behaving
differently *with* it. Treat every claim below as evidence about the problem, not evidence about
the solution.

Decision (<date>): ship untested and iterate, priced at ~<n>k subagent tokens and deferred.
```

- [ ] **Step 2: Add the skill to the plugin manifest description and keywords**

The manifest ships every skill under `skills/` automatically, so this is discoverability copy
rather than wiring — but every other skill has a clause, and one missing reads as an oversight.

In `.claude-plugin/plugin.json`, append to `description`, matching the existing voice (each
clause says what the skill *does*, not what it is about):

```text
nasa-coding-standards applies a TypeScript port of the NASA/JPL Power of 10 to code that moves
money, changes access, cannot be undone, crosses a trust boundary, or waits on external state —
bounding loops, memory and recursion, closing failure paths, and disclosing every rule it
changed code under.
```

Add to `keywords`: `"nasa"`, `"power-of-10"`, `"safety-critical"`, `"code-quality"`.

Leave `version` alone. Bumping it is the release's job, and this repo's release commits bump the
version and the manifest copy together — see `bfade18`.

- [ ] **Step 3: Verify the manifest still parses**

```bash
jq -e '.description | length > 0' .claude-plugin/plugin.json
jq -r '.keywords | join(", ")' .claude-plugin/plugin.json
```

Expected: `true`, then a list containing the four new keywords.

- [ ] **Step 4: Update the installation-state list in CLAUDE.md**

That list is dated and verified, and it exists because this repo has repeatedly confused "edited
here" with "installed". Add a bullet stating the truth for this skill — including, if Task 6's
symlink is still in place, that it points into a worktree and will break when the worktree is
removed. That is the same trap `pr-review` is recorded as sitting in.

- [ ] **Step 5: Resolve the symlink rather than leaving it dangling**

Either remove it, or repoint it at the main checkout once the branch has landed:

```bash
rm ~/.claude/skills/nasa-coding-standards
# or, after the branch is on main:
ln -sfn ~/code/skills/skills/nasa-coding-standards ~/.claude/skills/nasa-coding-standards
readlink -f ~/.claude/skills/nasa-coding-standards
```

A symlink into a deleted worktree is a broken skill entry that fails silently, which is worse
than no symlink.

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin/plugin.json CLAUDE.md skills/nasa-coding-standards/TESTING.md
git commit -m "$(cat <<'EOF'
chore: ship nasa-coding-standards in the plugin manifest

Adds the skill to the manifest description and keywords, and updates the
installation-state list in CLAUDE.md so it says what is actually installed
rather than what was edited.

TESTING.md's State section now leads with what did and did not run. <Which.>

Version is left alone deliberately — the release bumps it alongside the
manifest copy, as 0.3.0 did.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: Finish the branch**

Use `superpowers:finishing-a-development-branch`, which verifies, presents the merge/PR/keep/
discard choice, and handles worktree cleanup. If the choice is to release, that is `skills:deploy`
— it owns the version bump, changelog, annotated tag and `--follow-tags` push, and this plan does
not duplicate any of it.

Note the ordering constraint recorded in `CLAUDE.md`: the installed plugin resolves to
`~/.claude/plugins/cache/trog-skills/skills/0.3.0`, cloned from GitHub. Until a release is
tagged, pushed, and the plugin updated, **this skill is not live for anyone through the plugin**
— only through the symlink from Step 5.

---

## Self-review

Run against the spec after the plan is written, before execution starts.

**Spec coverage.** Every section maps to a task: the port table → Task 4; the trigger description
→ Task 5 Step 1; the disclosure contract, relaxations, marker comments, scope rule and
structural applicability → Task 5; the fixture and its eight planted defects → Task 1; the arms,
scoring and rep hygiene → Tasks 2, 3, 6, 7, 8; the cost decision → the gate before Task 6; the
risks → Task 8 Step 2 (opt-in reachability) and Task 3 Step 3 / Task 6 Step 4 (fixture
saturation shows up as ceiling scores in both arms).

**Deliberately not covered.** `nasa-code-audit`, the review-time skill, is the spec's own
follow-on work and is out of scope. Its description must be sharp enough that an agent knows
when Power-of-10 auditing specifically is wanted — two review skills already compete for that
trigger (`pr-review`, currently unmerged in a worktree, and `jht-skills:quality-review`), and a
third that fires on every review turns every diff into a lecture.

**One deliberate deviation from the spec.** The spec sets `SKILL.md` at ~700 words; the drafted
body is 878. The overrun is entirely the per-rule applicability table, which the spec itself
requires and which did not exist when the estimate was made. It is flagged here rather than
absorbed silently, because the length of the always-loaded file is a real cost and the decision
to pay it belongs to a reviewer, not to the plan.

**Known plan risks, stated rather than designed away:**

- **The fixture may not force every visit.** Task 1's table argues that partial-refund support
  routes through all eight sites, but an agent that implements it minimally could skip
  `reconcile.ts` by tracking the refunded total locally. If RED shows items 4 and 5 unreached
  rather than unaddressed, that is a fixture defect, not a baseline finding — make the prompt's
  "refuse a partial that would take the charge past fully refunded" requirement explicit about
  needing the provider's total.
- **Items 1 and 2 both score `failure-path`.** A rep that fixes one and not the other produces a
  half-scored rule. They are scored separately on purpose — the two failures have different
  visibility — but the rule-level summary should say which.
- **GREEN's bar is high.** 22/24 with three specific items at 3/3 was set before any data
  existed. If RED comes in far higher than the predicted 8–16, the fixture is closer to
  saturation than expected and the bar should be re-argued in `TESTING.md` **before** GREEN runs,
  not after it.

**Type and name consistency.** The seven rule keys, the `po10-relaxed(...)` marker, the two
bullet formats, and the `nasa-coding-standards: all-code` marker are fixed in Global Constraints
and used identically in Tasks 4, 5, 6 and 8. Task 5 Step 5 checks the keys mechanically across
both files.
