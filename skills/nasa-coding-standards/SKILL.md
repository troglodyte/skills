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
| `resolvable-dispatch` | You add to, or read from, a lookup whose key comes from outside the process — adding an entry to one counts | If the lookup is typed `Record<string, …>`, convert it to a `satisfies`-checked map with a rejecting default before adding your key. Never `eval` |
| `no-suppressed-diagnostics` | The change adds or touches `@ts-ignore`, `@ts-expect-error`, `eslint-disable` or `any` | Remove it, or a written reason on the same line. `tsc --noEmit` clean |

Two carry more weight than the rest in Node. **`fetch` does not throw on 4xx or 5xx** — it
resolves, and the failure surfaces later, somewhere else. An unhandled `'error'` event **takes
the process down**.

C originals, the adjudication, and the two rules deferred to repo convention: `rules.md`.

## Scope

You own every function you modify, and every module-level value it reads. **Introducing the
problem is not the test — touching the code is.** Extracting a bad call into a new helper, or
rewriting a function around its existing shape, makes it yours.

Violations in code you did not modify are not fixed and not enumerated — report them in
**one** `Seen, not touched:` bullet for the whole change.

## Relaxing a rule

`failure-path` and `no-suppressed-diagnostics` **cannot be relaxed.** Each already contains its
own one-line minimum: `.catch(noop)` with a comment *is* checking the failure path, and
`@ts-ignore` with a written reason *is* `no-suppressed-diagnostics`. There is nothing left to trade.

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
- failure-path → checked res.ok and threw ImportError (src/importer.ts:fetchManifest)
- bounded-memory → streamed rows instead of buffering the result set (src/importer.ts:loadRows)
- Relaxed: bounded-loop — page count bounded by api.maxPages (src/settings.ts)
- Seen, not touched: parser.ts walks nested groups without a depth cap
```

The `file:symbol` anchor is required — an unanchored claim is the cheapest thing to write and
the hardest to falsify. A bullet asserts that **your change** made the rule hold. Adding an
entry to a structure that was already unsafe is not compliance; describing it as though the
structure were already safe is worse.

**If no rule produced a change, emit no block.** Silence is correct on a change these rules do
not touch.

## Rationalizations

| Excuse | Reality |
|---|---|
| "It was already there — I didn't introduce it" | You modified the function. Introducing it is not the test; touching it is. |
| "I only extracted the call, I didn't change it" | The extracted call is a function you wrote. It gets the check. |
| "I only added one key to the dispatch table" | The key arrives off the wire. Adding to an unguarded lookup is the moment to guard it. |
| "I kept the same shape the old code had" | You rewrote it. A rewrite inherits the rule, not the exemption. |
| "The provider always returns 200" | `res.ok` is one line. Either name where that guarantee lives, or check it. |
| "The list is never that long" | A likelihood, not a bound. Column two already decided. |
| "Small change, before standup" | The fixes are one line each. Skipping them is not what saves the time. |
