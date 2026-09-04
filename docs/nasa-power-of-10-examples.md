# Power of 10 in TypeScript — before and after

Worked examples for the seven rules that survive the port to TypeScript and Node, one rule at a
time.

This file is for people. It lives outside `skills/` deliberately, so it never loads into an
agent's context — the agent reads
[`SKILL.md`](../skills/nasa-coding-standards/SKILL.md) and
[`rules.md`](../skills/nasa-coding-standards/rules.md) instead.

Comments marked `// BAD` and `// FIXED` are annotations for this document — they are not in the
real source.

**On provenance, precisely.** Four of the "before" blocks are lifted from the test fixture
(`skills/nasa-coding-standards/make-fixture.sh`): the `failure-path`, `bounded-loop`,
`resolvable-dispatch` and `no-suppressed-diagnostics` cases. The `bounded-recursion`,
`bounded-memory` and `assert-invariants` "before" blocks are **composed for this document** —
they are the shape agents produced under test, not code that exists in the fixture. Some are
lightly reformatted for width.

The "after" blocks are **written for this document.** Several match what agents produced closely,
but the rep directories were not preserved (see
[`TESTING.md`](../skills/nasa-coding-standards/TESTING.md)), so no block here can be traced to a
specific run — and for `resolvable-dispatch` and `no-suppressed-diagnostics` no agent ever
produced a passing fix at all, because both scored 0/6. Treat every "after" as a worked answer,
not as evidence.

Where agents got a rule wrong, the wrong version is shown too. That one *is* drawn from a
recorded run, and it is the more useful thing to recognise.

## Why seven and not ten

| Rule | Original (C) | Status |
| --- | --- | --- |
| 1 | No recursion, no `goto`/`setjmp` | Ported as `bounded-recursion` |
| 2 | Every loop has a provable upper bound | Ported as `bounded-loop` |
| 3 | No dynamic allocation after init | Ported as `bounded-memory` |
| 4 | Functions fit on one printed page | Deferred — the repo already enforces ~30 lines |
| 5 | Two assertions per function minimum | Ported as `assert-invariants`, without the quota |
| 6 | Data declared at smallest scope | Deferred — already lint-enforced |
| 7 | Check every return value | Ported as `failure-path` |
| 8 | Restrict the preprocessor | **Dropped** — TypeScript has no preprocessor |
| 9 | No function pointers; one level of dereference | Ported as `resolvable-dispatch` |
| 10 | Compile pedantically, zero warnings | Ported as `no-suppressed-diagnostics` |

Rule 8 is the only outright drop. Its invariant — *the source you read is the source that
compiles* — has no analogue worth enforcing here, and inventing one would have been easy and
dishonest.

## `failure-path` — check every failure path

The strongest survivor, and the widest. In a Node service this covers unchecked `Response`
objects, floating promises, empty `catch` blocks, unread child-process exit codes, and missing
`'error'` listeners.

Two things make it the highest-value rule in the set. **`fetch` does not throw on 4xx or 5xx** —
it resolves, so the failure surfaces later and somewhere else, as a confusing parse error far from
its cause. And **an unhandled `'error'` event takes the process down.**

### Before

```ts
export async function handleRefundCreated(event: RefundEvent): Promise<void> {
  const charge = await getCharge(event.chargeId);

  const res = await fetch(`${PROVIDER_URL}/v1/refunds`, {
    method: 'POST',
    headers: { authorization: `Bearer ${PROVIDER_KEY}`, 'content-type': 'application/json' },
    body: JSON.stringify({ charge: charge.id, amount: charge.amount }),
  });
  // BAD: res.ok is never read. fetch resolves on 402/500, so the next line
  // parses the provider's error body as if it were a refund.
  const refund = (await res.json()) as ProviderRefund;

  // BAD: not awaited. Returns a promise nobody holds, so a rejected audit
  // write becomes an unhandled rejection after this handler reported success.
  recordAudit({
    refundId: refund.id,
    chargeId: event.chargeId,
    amount: refund.amount,
    metadata: flattenMetadata(event.metadata ?? {}),
  });
}
```

Two defects, and they fail differently. The unchecked `res` means a declined refund parses as
`{ error: … }` and `refund.id` becomes `undefined` in the audit record — a silent data-integrity
bug. The un-awaited `recordAudit` means a rejected audit write becomes an unhandled rejection
after the handler has already reported success.

### After

```ts
async function postRefund(chargeId: string, amount: number): Promise<ProviderRefund> {
  const res = await fetch(`${PROVIDER_URL}/v1/refunds`, {
    method: 'POST',
    headers: { authorization: `Bearer ${PROVIDER_KEY}`, 'content-type': 'application/json' },
    body: JSON.stringify({ charge: chargeId, amount }),
  });

  // FIXED: status checked before the body is trusted, and the failure path
  // throws rather than logging and continuing.
  if (!res.ok) {
    throw new ProviderError(`refund POST failed for ${chargeId}: ${res.status}`);
  }

  return (await res.json()) as ProviderRefund;
}

export async function handleRefundCreated(event: RefundEvent): Promise<void> {
  const charge = await getCharge(event.chargeId);
  const refund = await postRefund(charge.id, charge.amount);

  // FIXED: awaited, so a failed audit write fails the handler.
  await recordAudit({
    refundId: refund.id,
    chargeId: event.chargeId,
    amount: refund.amount,
    metadata: flattenMetadata(event.metadata ?? {}),
  });
}
```

**This rule cannot be relaxed.** It already contains its own one-line minimum: a `.catch()` with a
comment *is* checking the failure path, because the decision to discard the error has been made and
recorded. There is nothing left to trade away.

```ts
// This IS compliance, not an exemption: the error is caught and the decision to
// discard it is written down. Even `.catch(noop)` qualifies when a comment
// records the decision — what fails the rule is a catch with no reason given,
// because then nobody can tell a choice from an oversight.
// Audit is best-effort; a failed write must not fail the refund. Alerted on via the
// audit service's own error rate, not from here.
void recordAudit(entry).catch((err) => log.warn({ err }, 'audit write dropped'));
```

### What testing showed

`res.ok` went from **0 of 6** to **6 of 6** — the most reliable single effect measured. Worth
knowing why it was 0: five of six agents *extracted the `fetch` into a new helper they wrote
themselves* and still did not add the check. Refactoring the exact line does not surface the
omission.

The floating promise is weaker, at 3 of 6. One agent fixed `res.ok` in a function it had just
written while leaving the un-awaited call three lines below.

## `bounded-loop` — every loop has a stated ceiling

Applies when a loop's termination depends on a value not computed inside the function. Iterating
an in-memory collection already satisfies the rule — the bound is its length. Cursor pagination,
retry loops, and queue polling do not.

Two parts are always required: a cap, and **defined behaviour when the cap is reached**. The
second is the one that gets skipped, and skipping it converts an unbounded loop into a silently
truncated result, which is worse.

A timeout is the third part wherever the loop body can hang — which for a network loop is always,
though it usually belongs on the call rather than on the loop. The example below caps iterations
only, and assumes `fetchRefundPage` carries its own `AbortSignal.timeout`. Bounding the count
without bounding the wait leaves the loop hangable on a single slow page.

### Before

```ts
export async function countRefunds(chargeId: string): Promise<number> {
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
    // BAD: the loop's termination is decided by the provider's response, not
    // by anything computed in this function. No cap, no timeout, no exit.
    hasMore = page.has_more;
  }

  return refunds.length;
}
```

`hasMore` comes off the wire. A provider bug that always returns `has_more: true`, or a cursor
that fails to advance, spins this forever inside a request handler.

### After

```ts
// src/config.ts
// Note the parse guard. `Number(process.env.X ?? 50)` is the tempting one-liner
// and it is a trap: a non-numeric value yields NaN, `pages > NaN` is always
// false, and the cap silently becomes no cap at all.
const configured = Number(process.env.MAX_REFUND_PAGES);
export const MAX_REFUND_PAGES = Number.isInteger(configured) && configured > 0
  ? configured
  : 50;
```

```ts
export async function countRefunds(chargeId: string): Promise<number> {
  let total = 0;
  let cursor = '';
  let hasMore = true;
  let pages = 0;

  while (hasMore) {
    // FIXED: a cap, and defined behaviour when it is reached. The throw is the
    // part that gets skipped — breaking here instead would silently return a
    // truncated total, which is worse than looping.
    if (++pages > MAX_REFUND_PAGES) {
      throw new ReconcileError(
        `charge ${chargeId} exceeded ${MAX_REFUND_PAGES} refund pages`,
      );
    }

    const page = await fetchRefundPage(chargeId, cursor);
    total += page.data.length;
    cursor = page.next ?? '';
    hasMore = page.has_more;
  }

  return total;
}
```

The cap lives in `config.ts` rather than inline, which matters for the relaxation rule below: a
config key is a locatable guarantee, a magic number in a loop body is not.

### Relaxing it

`bounded-loop` *can* be relaxed, because compliance requires a real decision — what is the
number? — and a rule whose compliance is expensive invites silent non-compliance instead.

A relaxation is a grep-able comment at the site, and the comment **is** the relaxation. One
without a comment is a violation.

```ts
// The marker names the rule, the guarantee, and where the guarantee lives.
// Drop the parenthetical and it stops being checkable by the next reader.
// po10-relaxed(bounded-loop): page count bounded by provider max_pages (src/config.ts)
while (hasMore) {
```

The guarantee must be **external and locatable** — a config key, a type, a caller contract, a
platform limit. Never a likelihood. "The loop is short in practice" is exactly the reasoning the
rule exists to prevent, and being unable to name where the guarantee lives is itself the answer.

### What testing showed

0 of 3 at baseline, 3 of 3 after. But no agent has ever written a `po10-relaxed` comment in any
of the six skill-loaded runs, so the relaxation half of this is untested in practice.

## `bounded-memory` — every collection has a maximum

Rule 3's C mechanism, "no `malloc` after initialization", is meaningless under garbage collection.
Its invariant survives intact: **resource use is derivable from the source, not from the input.**

Applies when a collection, buffer, queue, or cache grows by an amount the source does not fix.
Caches need eviction; streams need streaming rather than slurping.

### Before

```ts
// BAD: unbounded. Its size is the provider's refund count, which is input,
// not something this source fixes.
const refunds: ProviderRefund[] = [];

while (hasMore) {
  const page = await fetchRefundPage(chargeId, cursor);
  // BAD: every refund is retained to compute one number.
  refunds.push(...page.data);
  cursor = page.next ?? '';
  hasMore = page.has_more;
}

return refunds.reduce((sum, r) => sum + r.amount, 0);
```

Every refund the provider has ever recorded is held in memory to produce one number.

### After

```ts
// FIXED: one accumulator instead of a growing array. Memory is now fixed by
// the source regardless of how many refunds exist.
let total = 0;

while (hasMore) {
  const page = await fetchRefundPage(chargeId, cursor);
  for (const refund of page.data) {
    total += refund.amount;
  }
  cursor = page.next ?? '';
  hasMore = page.has_more;
}

return total;
```

### What testing showed

This is the only rule whose **score** got worse under the skill: 1 of 3, then 0 of 3 on a re-run.
Every agent
capped the page count and then accumulated all the pages anyway, before reducing.

Bounding the loop appears to discharge the felt obligation to bound the memory, even though they
are separate rules and the same function violates one while satisfying the other. If you take one
practical thing from this file, take that: **after you cap a loop, look again at what the loop
accumulates.**

## `bounded-recursion` — depth that crosses a trust boundary carries a counter

The C original bans recursion outright. That does not survive: tree and AST work makes recursion
idiomatic, and a rule that gets ignored teaches that the whole set is negotiable.

What survives is narrower and enforceable. Recursion is fine over structures whose depth is bounded
by data you control. Depth arriving from outside the process carries a counter that throws, or
becomes an explicit stack.

### Before

```ts
export function flattenMetadata(
  input: Record<string, unknown>,
  prefix = '',
): Record<string, string> {
  const out: Record<string, string> = {};

  for (const [key, value] of Object.entries(input)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === 'object') {
      // BAD: recurses to whatever depth the payload chooses. No counter, no
      // ceiling, and the depth crossed a trust boundary to get here.
      Object.assign(out, flattenMetadata(value as Record<string, unknown>, path));
    } else {
      out[path] = String(value);
    }
  }

  return out;
}
```

`input` is webhook metadata. A payload nested ten thousand deep is a stack overflow, and it costs
the sender nothing to construct.

### After

```ts
const MAX_METADATA_DEPTH = 8; // rules.md uses 8; any stated, locatable number qualifies

export function flattenMetadata(
  input: Record<string, unknown>,
  prefix = '',
  depth = 0,
): Record<string, string> {
  // FIXED: depth counter that throws. The bound is checked on entry, so it
  // holds no matter which call site recurses.
  if (depth > MAX_METADATA_DEPTH) {
    throw new PayloadError(`metadata nested deeper than ${MAX_METADATA_DEPTH}`);
  }

  const out: Record<string, string> = {};

  for (const [key, value] of Object.entries(input)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (isPlainObject(value)) {
      Object.assign(out, flattenMetadata(value, path, depth + 1));
    } else {
      out[path] = String(value);
    }
  }

  return out;
}

// FIXED: excludes arrays, which the before block's bare typeof check let
// through. Without
// this, arrays recurse by index and an attacker inflates the output width as
// well as its depth.
function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
```

The `isPlainObject` guard is not incidental. Without it, arrays recurse by index and produce keys
like `items.0.name` — usually not what the audit store wants, and another way an attacker inflates
the output.

### What testing showed

0 of 3 to 6 of 6 — the cleanest result in the whole test. The baseline denominator is 3, not 6:
the original fixture never routed an agent through this function, so only the revised run
measures it, and `TESTING.md` forbids comparing against the original. Notably, at baseline all
three agents *authored this recursion from scratch* — they were adding nested-object support to
a flat flattener — and none of them bounded what they had just written.

## `assert-invariants` — assert what types cannot express

Rule 5's original demands two assertions per function on average. The quota does not port:
TypeScript discharges much of what C assertions were compensating for, and a per-function quota
over a typed codebase manufactures noise.

What survives is the target. Assert the things the type system cannot say: Zod at IO boundaries,
domain invariants like non-empty or sums-to-100 or tenant ownership, and `never` in exhaustive
switches.

### Before

```ts
export async function handleRefundPartial(event: RefundEvent): Promise<void> {
  const charge = await getCharge(event.chargeId);
  // BAD: the `!` silences the one compile-time hint that `amount` is optional
  // on the wire. Past it, nothing rejects a negative, a NaN, or an amount that
  // overshoots what is left on the charge — and no type can, because `number`
  // is a correct type for all three.
  const refund = await postRefund(charge.id, event.amount!);
  await recordAudit({ refundId: refund.id, chargeId: event.chargeId, amount: refund.amount });
}
```

The `!` is worth dwelling on: it is a `no-suppressed-diagnostics` violation and an
`assert-invariants` violation in one character. The compiler asked the exact right question and
was told to be quiet.

`event.amount` is `number | undefined` off the wire. Nothing here stops a negative amount, a
`NaN`, or a partial refund that takes the charge past fully refunded — and the type system cannot,
because `number` is a perfectly good type for all three.

### After

```ts
export async function handleRefundPartial(event: RefundEvent): Promise<void> {
  const { amount } = event;

  // FIXED (invariant 1): shape the type cannot express — present, finite,
  // positive. Typed error so a caller can tell a malformed payload from a
  // legitimate request that must be refused.
  if (amount === undefined || !Number.isFinite(amount) || amount <= 0) {
    throw new InvalidRefundAmountError(`refund.partial ${event.id} has amount ${amount}`);
  }

  const charge = await getCharge(event.chargeId);
  const alreadyRefunded = await sumRefundedAmount(event.chargeId);

  // FIXED (invariant 2): the domain rule. Refunds never exceed the charge,
  // and the provider's own total is the source of truth, not a local tally.
  if (alreadyRefunded + amount > charge.amount) {
    throw new RefundExceedsChargeError(
      `refund of ${amount} on ${event.chargeId} exceeds remaining ` +
        `${charge.amount - alreadyRefunded}`,
    );
  }

  const refund = await postRefund(charge.id, amount);
  // FIXED: audits refund.amount from the response, not the requested amount —
  // a provider that partially honours the request must not produce an audit
  // row claiming otherwise.
  await recordAudit({ refundId: refund.id, chargeId: event.chargeId, amount: refund.amount });
}
```

Two invariants, both typed errors rather than generic `Error`, so callers can distinguish a
malformed payload from a legitimate request that must be refused.

And note which amount reaches the audit record: `refund.amount` from the provider's response, not
the requested `amount`. A provider that partially honours the request must not produce an audit
row claiming otherwise.

### Exhaustive switches

The other half of this rule, and the cheapest form of it:

```ts
function describe(status: RefundStatus): string {
  switch (status) {
    case 'pending': return 'awaiting the provider';
    case 'succeeded': return 'money returned';
    case 'failed': return 'declined';
    default: {
      // FIXED: adding a variant to RefundStatus now fails the build here,
      // instead of falling through silently at runtime.
      const exhaustive: never = status;
      throw new Error(`unhandled refund status: ${String(exhaustive)}`);
    }
  }
}
```

Adding a variant to `RefundStatus` now fails the build here, rather than silently falling through
at runtime.

## `resolvable-dispatch` — the call graph stays statically resolvable

Rule 9 restricts pointers and bans function pointers in C. The dereference limit does not port,
and neither does the ban on function values — they are idiomatic JavaScript, and banning them
would make the rule ignorable.

What survives covers a real vulnerability class: no `eval`, no `new Function`, and no dispatch on
an untrusted string key.

### Before

```ts
const handlers: Record<string, (e: RefundEvent) => Promise<void>> = {
  'refund.created': handleRefundCreated,
  'refund.failed': handleRefundFailed,
};

export async function handleWebhook(body: unknown): Promise<void> {
  // @ts-ignore
  const payload: RefundEvent = body;

  // BAD: payload.type came off the wire and selects which function runs. On a
  // plain object literal the prototype is reachable, so type: "constructor"
  // returns something truthy that passes the guard below and is then called.
  const handler = handlers[payload.type];
  // BAD: truthiness check on the looked-up value, not a membership check on
  // the key. It rejects missing keys; it does not reject dangerous ones.
  if (!handler) {
    return;
  }

  await handler(payload);
}
```

`payload.type` came off the wire and indexes an object. With a plain object literal the prototype
chain is reachable, so `type: "constructor"` yields a truthy value that passes the `if` and is then
called.

### The wrong "after" — recognise this one

Under test, agents produced this and reported the rule as satisfied:

```ts
// BAD: unchanged from the "before" block above. The only edit was adding one
// more key to the map. Nothing about the lookup's safety changed.
const handler = handlers[payload.type];
if (!handler) {
  return;
}
```

with a disclosure bullet reading *"`refund.partial` added to the existing allowlisted handler map,
which already rejects unknown types."*

The map is a bare `Record<string, …>`; it is not an allowlist, and `if (!handler)` is a truthiness
check on the looked-up value, not a membership check on the key. **Adding an entry to a structure
that was already unsafe is not compliance.**

### After

```ts
const HANDLERS = {
  'refund.created': handleRefundCreated,
  'refund.partial': handleRefundPartial,
  'refund.failed': handleRefundFailed,
  // FIXED (1 of 3): `satisfies` type-checks the literal without widening it,
  // so `keyof typeof` below is the exact union of these three keys. Annotating
  // as `Record<string, …>` instead would collapse it back to `string`.
} satisfies Record<string, (e: RefundEvent) => Promise<void>>;

type HandledType = keyof typeof HANDLERS;

// FIXED (2 of 3): checks the KEY, not the value, and does not walk the
// prototype — so "constructor" and "__proto__" are rejected. The type
// predicate is what lets the call below index without a cast.
function isHandledType(t: string): t is HandledType {
  return Object.hasOwn(HANDLERS, t);
}

export async function handleWebhook(body: unknown): Promise<void> {
  const payload = refundEventSchema.parse(body);

  // FIXED (3 of 3): the rejecting branch is explicit and logged, rather than a
  // silent return that hides a misconfigured provider.
  if (!isHandledType(payload.type)) {
    log.warn({ type: payload.type }, 'unhandled webhook type');
    return;
  }

  await HANDLERS[payload.type](payload);
}
```

Three changes carry it. `satisfies` keeps the literal's exact keys so `keyof typeof` is a real
union rather than `string`. `Object.hasOwn` checks the key, not the value, and does not consult
the prototype. And the rejecting branch is explicit and logged, rather than a silent `return`.

### What testing showed

**0 of 6, and the rule the skill made *louder* rather than better.** Re-aiming the applicability
wording
at the edit made the rule *fire* — agents began mentioning it — without making its compliant
minimum reachable from the edit in front of them. Two of three then resolved the gap by
redescribing the existing code as already compliant.

The general lesson is worth more than the rule: **a rule that fires but cannot be satisfied by the
change you are making gets reported as satisfied.** If you are writing guidance of any kind, give
it an action, not a property to assert.

## `no-suppressed-diagnostics` — suppress nothing silently

Rule 10 ports directly: `strict`, `noUncheckedIndexedAccess`, `tsc --noEmit` clean, and no
`@ts-ignore`, `@ts-expect-error`, `eslint-disable`, or `any` without a written reason on the line.

### Before

```ts
export async function handleWebhook(body: unknown): Promise<void> {
  // BAD: no reason given, and it is load-bearing — deleting this line produces
  // TS2322. The suppression is the only thing between an unvalidated webhook
  // body and every field access downstream of it.
  // @ts-ignore
  const payload: RefundEvent = body;

  const handler = handlers[payload.type];
  // ...
}
```

`@ts-ignore` here is doing real work — removing it produces
`TS2322: Type 'unknown' is not assignable to type 'RefundEvent'`. The suppression is the only thing
standing between an unvalidated webhook body and every downstream field access.

### After — validate, don't suppress

Zod 3 syntax — Zod 4 changed `z.record` to require both a key and a value schema
(`z.record(z.string(), z.unknown())`).

```ts
const refundEventSchema = z.object({
  id: z.string(),
  type: z.string(),
  chargeId: z.string(),
  amount: z.number().finite().positive().optional(),
  reason: z.string().optional(),
  metadata: z.record(z.unknown()).optional(),
});

export async function handleWebhook(body: unknown): Promise<void> {
  // FIXED: no suppression, because there is nothing left to suppress — the
  // value genuinely is a RefundEvent once it survives parse().
  const payload = refundEventSchema.parse(body);
  // ...
}
```

The cast disappears because the value is now genuinely of that type. This also happens to satisfy
`assert-invariants` at the same boundary — Zod at the IO edge is the single highest-leverage line
in a webhook handler.

### After — when you genuinely must suppress

```ts
// FIXED: expect-error rather than ignore, plus a written reason and a ticket.
// @ts-expect-error provider types lag the v3 payload shape; tracked in BILL-412
const legacyField = response.legacy_amount;
```

Prefer `@ts-expect-error` over `@ts-ignore`: it fails the build when the underlying error goes
away, so the suppression cannot outlive its reason.

**This rule cannot be relaxed either.** `@ts-expect-error` with a written reason *is* the rule.
Asking to relax it is asking to skip a one-line version of compliance.

### What testing showed

**0 of 6.** Every agent reported it under `Seen, not touched:` — each had modified the `handlers`
constant in that file but not the function containing the suppression, and read ownership as
function-level. That reading is defensible, which is the problem: the scope boundary between "a
module-level value I edited" and "the function that reads it" was never settled.

## Scope: what you own

Every rule above applies to code you touch, and the boundary that matters in practice is narrower
than people assume.

You own every function you modify — and introducing the problem is not the test, touching the code
is. Extracting a bad call into a new helper makes it yours. Rewriting a function around its
existing shape makes it yours. This is not pedantry: five of six agents under test extracted an
unchecked `fetch` into a helper they wrote themselves and still did not check it.

Violations in code you did not modify are not fixed and not enumerated. They get one line:

```text
Seen, not touched: reconcile.ts paginates without a cap; webhook.ts casts the body via @ts-ignore
```

One bullet for the whole change, not one per violation. Without that limit, agents both silently
fix adjacent code and silently ignore it, unpredictably — and a per-violation list turns every
diff into a lecture.

## Honest summary of what the rules buy

Measured against a baseline of agents doing the same task without the rules:

Denominators differ by rule and are given explicitly, because two fixtures were used: three rules
were only reachable in the revised one, so their baseline is 3 reps rather than 6. Where two
skill-loaded runs disagree, both are shown.

| Rule | Baseline | With rules | Verdict |
| --- | --- | --- | --- |
| `failure-path` (`res.ok`) | 0/6 | 6/6 | Works |
| `bounded-recursion` | 0/3 | 6/6 | Works |
| `bounded-loop` | 0/3 | 1/3 then 3/3 | Works after the rule was re-aimed |
| `failure-path` (floating promise) | 1/6 | 3/6 | Partial |
| `assert-invariants` | — | — | Not measurable; the task asked for it directly |
| `bounded-memory` | 0/3 | 1/3 then 0/3 | Regressed — capping the loop masks it |
| `resolvable-dispatch` | 0/6 | 0/6 | Fails, and produces false compliance claims |
| `no-suppressed-diagnostics` | 0/6 | 0/6 | Fails on a scope ambiguity |

Three caveats on that table, all material. The measurements are confounded — the skill's own
disclosure example named the fixture's files and symbols, so the rules whose examples were most
literal are the rules that improved most. The "with rules" column mixes two runs against two
fixture versions. And these were AI agents, not people; whether the same wording moves a human
reader is untested.

The full record, including what is confounded and what is unresolved, is in
[`TESTING.md`](../skills/nasa-coding-standards/TESTING.md).

## Source

Holzmann, G. J., *The Power of 10: Rules for Developing Safety-Critical Code*, IEEE Computer,
June 2006. NASA/JPL Laboratory for Reliable Software.
