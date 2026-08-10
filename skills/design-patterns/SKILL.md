---
name: design-patterns
description: Use when about to write code that has a structural choice - a new class, module, or service; another variant of something that already exists; adding a branch to an existing if/elif chain, switch, or type dispatch; a constructor or config object that keeps growing; or untangling coupled code. Applies even when the change is described as mechanical, routine, copy-paste, or the same shape as what is already there. Also use when asked how to structure something, which pattern fits, or whether a pattern is warranted at all.
---

# Design Patterns

**A conversation, not a lookup.** Get the shape of the code decided *with* your partner rather than assumed. The most common correct outcome is "no pattern - write the direct version."

**REQUIRED BACKGROUND:** superpowers:brainstorming decides *what* to build; this skill covers *how to shape it*.

## The Dialog

Not a gate. It costs one message, and can come before the code or alongside it. What it can't be is a footnote after the fact - by then the choice was made alone. When the change is urgent and the direct version is clearly right, write it *and* have the conversation in the same message.

**Name the axis of change.** What is expected to vary, and is that real or speculative? A pattern buys flexibility along one axis and charges indirection for it. No nameable axis, no pattern.

**State the null hypothesis.** What does the direct version look like - a function, a switch, a struct? Every option has to beat it.

**Offer options,** in this order: the axis in one sentence; the direct version, always first; one or two patterned alternatives with what each buys and costs; your recommendation; the question you need answered.

**Leave the choice open.** End with that question.

If the direct version wins, say so and write it. That's a success, not a failure.

See `patterns.md` for the symptom → pattern table.

## When Not to Reach for a Pattern

- **One implementation, no second planned.** The second one teaches you the real axis.
- **The variance is speculative.** "We might swap this later" is a guess. The direct version is cheaper to change than the wrong abstraction.
- **Only one implementor.** An interface with a single user is indirection with no payoff.
- **The language already provides it.** Iterator, Command, Strategy, and Observer are closures, function values, and iteration protocols in most modern languages. Reach for the feature, not the class diagram.
- **The codebase has an idiom.** A lone Visitor among plain functions costs more than it buys.

## Guidelines

- **Keep cyclomatic complexity low.** Branches per unit is the cheapest early signal that an axis of change is real. But a pattern redistributes complexity, it doesn't delete it - fewer paths through each unit, not fewer paths overall. Chasing the metric is its own kind of over-engineering.
- **Composition over inheritance** - where Decorator, Strategy, and Adapter get their flexibility.
- **Program to an interface** - once there are two implementations to abstract over.
- **Patterns are consequences of SOLID, not substitutes.** If a pattern makes a class do more, or callers know more, it's the wrong one.

## Rationalizations

| Excuse | Reality |
|---|---|
| "It's mechanical - same shape as the others" | The Nth copy is the trigger. Sameness is the finding, not a reason to skip. |
| "It's just one more branch" | Every branch was. The dialog costs a message; the fifth copy costs a bug. |
| "There's a standup / incident / deadline" | One message, and the likely answer is the direct version. |
| "I'll flag the refactor at the end" | A footnote after the diff isn't a dialog. The choice was already made. |
| "They asked me to just add it" | Add it - and name the axis. Asking for quick isn't asking you to decide the shape. |

## Red Flags

- Shipping a structural change with the axis never named.
- Adding the Nth branch and calling it mechanical.
- Deferring the structural point to a closing paragraph after the diff.
- Recommending a shape without leaving the choice open.
- One option offered instead of the direct version plus alternatives.
- "More extensible" with no named thing that will extend.
- An interface, factory, or manager with exactly one user.

**All of these: name the axis, start from the direct version, leave the choice open.**
