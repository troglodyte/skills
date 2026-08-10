# Document structures

Starting points, not molds. Cut any section that has nothing real to say — an empty
"Prerequisites: None" heading costs the reader attention and returns nothing. Adapt the
heading wording to the subject; these are the shapes, not the words.

- [README](#readme)
- [How-to (task-oriented)](#how-to-task-oriented)
- [Tutorial (learning-oriented)](#tutorial-learning-oriented)
- [Reference page](#reference-page)
- [Explanation / concept page](#explanation--concept-page)
- [Design doc](#design-doc)
- [Architecture decision record](#architecture-decision-record)
- [Changelog](#changelog)
- [Release notes](#release-notes)
- [Blog post](#blog-post)

The four documentation types — tutorial, how-to, reference, explanation — serve different
readers with different goals. Mixing them is the most common documentation failure: a
tutorial that stops to enumerate every config option loses the beginner, and a reference
page that tells a story wastes the expert's time. Decide which one you're writing.

## README

```markdown
# Project name

One or two sentences: what it does and who it's for. A reader who bounces here should
still know whether this is relevant to them.

## Install

## Usage

Smallest complete working example, copy-pasteable.

## Configuration

## Documentation

Links out. Don't inline the full docs.

## Contributing

## License
```

Front-load. Most README readers leave within a few seconds, so the first paragraph does
the real work. Badges, if any, go on one line under the H1 and never wrap to two. A
screenshot or short terminal capture is worth more than three paragraphs of description
for anything with a visible interface.

## How-to (task-oriented)

For a reader who has a specific goal and some existing competence.

```markdown
# Configure X to do Y

One sentence on what this accomplishes and when you'd want it.

## Before you start

Concrete prerequisites only — versions, permissions, credentials.

## Steps

1. Imperative step.
2. Imperative step.

## Verify

How to confirm it worked, with expected output.

## Troubleshooting

Symptom → cause → fix. Only failures that actually happen.
```

Each step is one action. If a step has substeps, it's probably two steps. Show expected
output after commands whose success isn't self-evident — that's what turns a procedure
into something a reader can trust.

## Tutorial (learning-oriented)

For a beginner who needs a guaranteed-success path, not comprehensive coverage.

```markdown
# Build your first X

## What you'll build

Describe or show the end state up front. Motivation carries people through the middle.

## Setup

## Step 1: [meaningful milestone]

## Step 2: [meaningful milestone]

## What you built

## Next steps
```

Every step must work, in order, with no prior knowledge. Resist explaining alternatives,
edge cases, and configuration options — they belong in the reference page and they are how
tutorials fail. Milestones should produce visible results, so the reader gets confirmation
they're on track.

## Reference page

For a reader who knows what they want and needs the exact details.

```markdown
# Component or API name

One-line description.

## Signature or syntax

## Parameters

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |

## Returns

## Errors

## Examples

## See also
```

Consistency across pages matters more than prose quality here — this is a lookup surface,
and readers navigate by shape. Same section order, same table columns, same phrasing
patterns on every page. Complete over readable: an undocumented parameter is a bug.

## Explanation / concept page

For a reader building a mental model.

```markdown
# How X works

## The problem it solves

## How it works

## Design tradeoffs

## When to use it, and when not to

## Related concepts
```

This is the one place where sustained prose is the right form. Diagrams earn their space
here more than anywhere else. Say plainly what the thing is *not*, and name the
alternatives it competes with — that's often the sentence the reader came for.

## Design doc

```markdown
# Title

**Status:** Draft | In review | Approved
**Author:** ·
**Last updated:** YYYY-MM-DD

## Summary

Two or three sentences. Assume some readers read only this.

## Problem

Evidence that this is worth solving. Numbers where they exist.

## Goals / Non-goals

Non-goals prevent the scope arguments.

## Proposal

## Alternatives considered

Each with why it was rejected. A doc with no rejected alternatives reads as unconsidered.

## Risks and open questions

## Rollout plan
```

Reviewers spend their attention on the tradeoffs, so the alternatives section is where a
design doc earns credibility. Open questions stated explicitly get answered; open questions
hidden become production incidents.

## Architecture decision record

Immutable once accepted. Supersede with a new ADR rather than editing.

```markdown
# ADR-0007: Use X for Y

**Status:** Proposed | Accepted | Superseded by ADR-0012
**Date:** YYYY-MM-DD

## Context

The forces at play — constraints, requirements, what made a decision necessary.

## Decision

"We will..." Active voice, unambiguous.

## Consequences

What becomes easier, what becomes harder, what we're now committed to.
```

The value of an ADR is entirely in the context section, read two years later by someone
asking why the system is like this. Write for that person.

## Changelog

Follow Keep a Changelog conventions and semantic versioning.

```markdown
# Changelog

## [Unreleased]

## [1.4.0] - 2026-03-14

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
```

Newest first. Omit empty categories. Entries describe the user-visible effect, not the
commit: "Fixed timezone handling in scheduled exports", not "bump dayjs". Breaking changes
get called out unmissably. Link issue or PR numbers at the end of each entry.

## Release notes

Different document from a changelog — narrative and audience-facing, not a categorized diff.

```markdown
# v1.4.0

Lead with the most significant change and why it matters to users.

## Highlights

## Breaking changes

Each with a concrete migration step.

## Upgrade notes

## Full changelog

Link.
```

## Blog post

```markdown
# Title that states the takeaway

Opening that earns the next paragraph — a concrete problem, a surprising result, a
specific moment. Not "In today's fast-paced world".

## [Body sections with substantive headings]

## [Closing that resolves the opening]
```

If the destination is a static site generator, the title lives in front matter and the body
starts at H2. No "Introduction" or "Conclusion" headings — they describe the document's
machinery instead of its content. Headings should tell the story on their own when someone
reads only them.
