---
name: markdown
description: Design spec for authoring Markdown (.md) files that render correctly and read well in their destination. Use this whenever producing a Markdown file the user will take somewhere else — READMEs, docs pages, blog posts, specs, changelogs, ADRs, notes, AGENTS.md/CLAUDE.md, PR descriptions, or anything saved as .md or .mdx. Also use when editing, cleaning up, converting, or restructuring existing Markdown, when the user pastes Markdown that renders wrong, or when the request is "write a doc/post/guide/spec" and a .md file is the natural deliverable. Consult it even for short files and even when the Markdown feels obvious — most Markdown defects are invisible in the source and only appear in the destination renderer.
---

# Markdown Design Spec

Markdown looks easy, which is why it fails quietly. A file can be perfectly readable in
source form and still render wrong: a table that collapses, a nested list that flattens, a
front-matter block that prints as literal text, an H1 duplicated by the site theme. The
author never sees it because the author never looks at the rendered page.

So the job has two halves. Get the **structure and voice** right so a human wants to read
it, and get the **mechanics** right so the destination renders what you intended. This spec
covers both, plus the flavor differences that cause most of the silent damage.

## Step 1: Identify the destination before writing

Markdown is not one language. It is a small portable core surrounded by mutually
incompatible extensions. The single highest-value thing to establish is where the file is
going, because that determines which features are available and whether front matter is
required or forbidden.

Usually you can infer it. A repo path, a mention of GitHub, a `docs/` folder, a static-site
config file in the project, an Obsidian vault, "for my blog" — all sufficient. Infer, state
the assumption in one line when you deliver, and move on.

Ask only when the answer would change the file materially and there's no signal at all. The
distinctions that actually matter:

| Signal | Destination | Consequence |
| --- | --- | --- |
| GitHub/GitLab repo, README, PR body, issue | GFM | Tables, task lists, footnotes, `<br>` fine. No front matter. |
| `docs/` + mkdocs.yml, Docusaurus, Astro, Hugo, Jekyll | Static site generator | Front matter usually **required**; H1 often auto-rendered from `title` |
| `.mdx` extension, Docusaurus/Next.js | MDX | `{` and `<` are code. Raw HTML-ish text breaks the build. |
| Obsidian, personal notes/vault | Obsidian | `[[wikilinks]]`, single line breaks are literal |
| "paste into Notion/Confluence/Google Docs" | Import target | Keep to the portable core; extensions get dropped |
| Pandoc, "convert to PDF/Word" | Pandoc | Its own front matter and extension set |
| AGENTS.md, CLAUDE.md, prompt/context file | LLM consumption | Optimize for retrieval, not visual polish |

When genuinely unknown, write to the portable core (next section) and omit front matter.
That degrades gracefully everywhere instead of breaking loudly somewhere.

For per-destination detail, read `references/flavors.md`. Do that when the destination is a
static site generator, MDX, an import target, or Pandoc — those are where the non-obvious
constraints live.

## Step 2: The portable core

These render the same essentially everywhere. Prefer them; reach for extensions only when
the destination is known to support them.

ATX headings (`##`), paragraphs separated by blank lines, `*` or `_` emphasis, `-`
unordered lists, `1.` ordered lists, fenced code blocks with a language tag, inline
`` `code` ``, `[text](url)` links, `![alt](path)` images, `>` blockquotes, `---`
thematic breaks.

Everything else — tables, task lists, footnotes, strikethrough, autolinks, admonitions,
math, emoji shortcodes, wikilinks, HTML — is an extension. Tables and strikethrough are
safe in most modern contexts. The rest, check first.

## Step 3: Structure

Headings are navigation, not decoration. They generate the table of contents, the anchor
links people share, and the outline screen readers announce.

- One H1 per file, and it is the document title — **unless** the destination renders a
  title from front matter, in which case omit the H1 entirely or you get the title twice.
- Never skip levels. H2 then H4 breaks outline tools.
- Never bold a line as a fake heading. `**Configuration**` produces no anchor, no TOC
  entry, and no semantic level. If it deserves emphasis on its own line, it deserves `###`.
- Write headings as scannable noun phrases or task phrases: "Rate limits", "Configure
  the webhook". Not "Some things to know about limits".
- Keep the tree shallow. Past H4 in a normal document, restructure or split the file.

Front matter, when the destination wants it, is the very first bytes of the file — no
leading blank line, no BOM, no preamble — delimited by `---` on its own lines. Use the
exact keys the destination expects rather than inventing plausible ones; a wrong key is
usually silently ignored, which is worse than an error.

## Step 4: Voice and density

Default to prose. Markdown's affordances make bullets cheap, and the failure mode is a
document shredded into fragments that assert things without connecting them. Bullets are
for genuinely enumerable, parallel items — options, steps, requirements. Explanation,
reasoning, and tradeoffs belong in sentences.

- Lead with the answer or the purpose. Readers scan the first line of each section and
  leave; put the conclusion there, not at the end of a windup.
- One idea per paragraph, two to five sentences.
- Keep nesting to two levels. Three-level bullet trees are a sign the content wanted
  subheadings or a table.
- Tables are for comparing several items across the same few dimensions. If there's one
  column of real content, use a list. If cells need paragraphs, lists, or code blocks,
  use subheadings — table cells can't hold block content.
- Link text describes the target: "the authentication guide", never "click here" or a
  bare URL in running prose.
- Every image gets meaningful alt text describing what it conveys, not "screenshot".
- No decorative emoji, no horizontal rules between every section, no bold scattered
  through paragraphs for emphasis. Restraint reads as authority.
- Nothing conversational in the file. No "Here's your document", no "I hope this helps",
  no notes about being AI-generated, no meta-commentary about choices you made. Put that
  in the chat message, not the artifact. The file should read as if a competent human
  wrote it for its actual audience.

## Step 5: Mechanics that bite

These are the defects that survive review because they're invisible in the source.

| Construct | What goes wrong | Do this |
| --- | --- | --- |
| Single newline inside a paragraph | Collapses to a space in most renderers, stays a break in Obsidian/Slack | Blank line for a new paragraph |
| Two trailing spaces for a line break | Invisible; stripped by formatters and linters | Restructure, or `<br>` where HTML is allowed |
| Pipe inside a table cell | Splits the cell | Escape as `\|` |
| Blank line inside a table | Ends the table; rest renders as text | No blank lines between rows |
| Fenced code inside a list item | Breaks out of the list | Indent the fence to the item's content column |
| Triple backticks inside a code block | Fence closes early | Outer fence of four backticks or `~~~` |
| Untagged code fence | No syntax highlighting; some linters fail | Always tag the language; `text` if none fits |
| `snake_case` or `<Type>` in prose | Underscore emphasis or swallowed as HTML | Wrap identifiers in backticks |
| Hand-written anchor link | Slug guessed wrong, silent dead link | Slug = lowercase, spaces→hyphens, punctuation dropped; duplicates get `-1` |
| Relative image/link path | Resolves against the rendered URL, not the file | Match the destination's convention; verify depth |
| `:sparkles:`, `- [ ]`, `[^1]`, `$x$` | GitHub- or extension-only; print literally elsewhere | Confirm support first |
| CRLF, smart quotes, non-breaking spaces | Diff noise, broken code samples | UTF-8, LF, straight quotes, single trailing newline |

Ordered lists: renderers renumber automatically, so `1.` repeated works and avoids churn in
files that get edited often. Sequential numbers read better in raw source. Pick one per
file and hold it. Never mix tabs and spaces for indentation.

Line wrapping: in a git repo, put one sentence per line. Semantic line breaks make diffs
and review comments land on the changed sentence instead of reflowing a whole paragraph.
Outside version control, don't hard-wrap at all — let the renderer do it. Never wrap at a
fixed column inside a paragraph; it produces the worst diffs of the three options.

Never wrap the entire file in a code fence. The deliverable is Markdown, not a display of
Markdown.

## Step 6: Deliver

Write the file, put it in the outputs directory with a `kebab-case.md` name, and present it
so the user can actually open it. A file that is written but never presented is unreachable.

Before delivering, check:

- Front matter present or absent as the destination requires, first bytes of the file
- Exactly one H1, or none if the theme supplies the title; no skipped levels
- Every code fence tagged, opened, and closed
- Tables: header separator row present, pipes escaped, no blank lines, no block content
- All internal anchors correspond to real headings; relative paths right for the render root
- No extension used that the destination doesn't support
- No conversational filler, no fake bold headings, no bullet-shredded prose
- Trailing newline, LF endings

## Reference files

- `references/flavors.md` — per-destination rules: GFM, MkDocs, Docusaurus/MDX, Hugo,
  Jekyll, Astro, Obsidian, Notion/Confluence import, Slack, Pandoc, LLM context files.
  Read the relevant section once the destination is known.
- `references/templates.md` — opening structures for README, how-to, tutorial, reference
  page, design doc, ADR, changelog, release notes. Starting points, not molds; cut
  sections that have nothing to say rather than filling them with padding.
