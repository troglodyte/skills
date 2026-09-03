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
