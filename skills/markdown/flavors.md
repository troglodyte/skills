# Destination-specific rules

Read only the section that matches the destination.

- [GitHub / GitLab (GFM)](#github--gitlab-gfm)
- [MkDocs and Material for MkDocs](#mkdocs-and-material-for-mkdocs)
- [Docusaurus and MDX](#docusaurus-and-mdx)
- [Hugo](#hugo)
- [Jekyll and GitHub Pages](#jekyll-and-github-pages)
- [Astro content collections](#astro-content-collections)
- [Obsidian and personal vaults](#obsidian-and-personal-vaults)
- [Notion, Confluence, Google Docs import](#notion-confluence-google-docs-import)
- [Slack and Discord](#slack-and-discord)
- [Pandoc to PDF or Word](#pandoc-to-pdf-or-word)
- [LLM and agent context files](#llm-and-agent-context-files)

## GitHub / GitLab (GFM)

No front matter — a `---` block at the top of a README renders as a table with garbage in
it, which is the single most common Markdown defect in the wild.

Available: tables, task lists (`- [ ]`), strikethrough, autolinked URLs, footnotes,
`:emoji:` shortcodes, a sanitized subset of HTML (`<br>`, `<details>`, `<img>`, `<sub>`,
alignment attributes), and GitHub alert callouts:

```markdown
> [!NOTE]
> Renders as a styled callout on GitHub. Renders as a plain blockquote everywhere else.
```

Not available: arbitrary HTML with `style` or `script`, MathJax outside the `math` fence
language, includes.

Relative links resolve against the repo path, so they work in the GitHub UI and in local
editors. Use them for cross-file links. Images from a `docs/` or `assets/` folder work
relatively; images pasted into issues get a CDN URL that is fine to keep.

`<details><summary>` collapsible blocks are worth using for long output, logs, or optional
detail in a README. Leave a blank line after the `<summary>` tag or the Markdown inside
won't be parsed.

Line length: GitHub doesn't wrap code blocks or tables, so keep table cells short and
prefer subheadings over a wide table.

## MkDocs and Material for MkDocs

Front matter is optional; when present, common keys are `title`, `description`, and
`hide` (for `navigation`/`toc`). Nav order comes from `mkdocs.yml`, not the files.

Keep the H1 — Material renders the first H1 as the page title and uses it in the nav.

Admonitions use the `!!!` syntax and require the `admonition` extension:

```markdown
!!! warning "Optional title"
    Indented four spaces. Blank line before the block.
```

Tabbed content (`===`), content includes, and `pymdownx` superfences are all extension-
dependent. Check `mkdocs.yml` for `markdown_extensions` before using any of them; if the
config isn't visible, stay portable.

Internal links point at the source file with its extension — `[link](../api/auth.md)` —
and MkDocs rewrites them. Linking to the built URL instead breaks the build-time link
checker.

## Docusaurus and MDX

The `.mdx` extension is the dangerous one. MDX parses the file as JSX, so:

- `{` and `}` are expression delimiters. Literal braces need `\{` or a code span.
- `<` starts a JSX tag. `<Foo>`, `<T>`, or `a < b` in prose breaks the build.
- Unclosed or unknown tags are compile errors, not silently-ignored text.
- HTML attribute names are JSX ones: `className`, not `class`.

Wrap anything with braces or angle brackets in backticks or a fenced block. Inside code
fences, MDX doesn't parse, so code samples are safe.

Front matter keys: `id`, `title`, `sidebar_label`, `sidebar_position`, `slug`, `tags`.
Docusaurus renders `title` as the H1, so omit the H1 in the body when `title` is set.

Admonitions use the `:::` syntax:

```markdown
:::tip Optional title
Content here.
:::
```

Blog posts use `<!-- truncate -->` to mark the excerpt cut. Versioned docs mean links
should be relative file paths so the version rewriting works.

## Hugo

Front matter can be YAML (`---`), TOML (`+++`), or JSON; match whatever the rest of the
site uses. `title`, `date`, `draft`, `weight`, `tags`, `categories` are the common keys.
`draft: true` means it will not publish — set it deliberately, either way.

Hugo's theme renders `title` as the page heading in almost every case, so start the body
at H2. Adding an H1 is the standard Hugo double-title bug.

Raw HTML is stripped by default under the Goldmark renderer unless `unsafe = true` is set
in config. Use shortcodes (`{{< notice >}}`) instead, but only ones the theme actually
defines — an undefined shortcode is a build failure. `<!--more-->` sets the summary split.

Page bundles matter for images: in a bundle, reference `image.png` relative to the page
directory; outside one, reference from `static/`.

## Jekyll and GitHub Pages

Front matter is mandatory. A file without it is copied verbatim and never rendered — the
most common Jekyll failure. Minimum is an empty pair of `---` lines. Typical keys:
`layout`, `title`, `date`, `categories`, `permalink`.

Post filenames must be `YYYY-MM-DD-title.md` in `_posts/`, or the post silently doesn't
appear.

The layout usually renders `title`, so start the body at H2.

Jekyll runs Liquid over the file first. Literal `{{` or `{%` — common in code samples for
templating, Vue, Handlebars, or Go templates — will be interpreted and destroyed. Wrap
those samples in `{% raw %}` / `{% endraw %}`.

Kramdown is the default parser. It supports attribute lists (`{: .class}`) and footnotes,
but not GFM task lists in older configurations.

## Astro content collections

Front matter is validated against a Zod schema in `src/content/config.ts`. Any key the
schema doesn't define is a build error, and any required key you omit is a build error.
Read the schema before writing the front matter; do not guess.

`.md` files are plain Markdown. `.mdx` files carry all the MDX constraints above and
require component imports at the top of the file.

Whether the layout renders the title varies by project — check an existing content file in
the same collection and match it exactly.

## Obsidian and personal vaults

No front matter required, but Obsidian reads a YAML block if present and treats `tags`,
`aliases`, and `cssclasses` specially. Arbitrary keys become displayed properties rather
than errors, so front matter is safe here.

The behavior difference that surprises people: **a single line break is a hard break**.
Obsidian's editor renders newlines literally, unlike almost every other renderer. Text
written with semantic line breaks — one sentence per line — will display as a ragged column
of short lines. In a vault, write paragraphs as single unbroken lines.

Obsidian-specific syntax, none of which survives outside Obsidian:

- `[[Note name]]` and `[[Note name|display text]]` wikilinks
- `![[Note name]]` and `![[image.png]]` embeds, including block and heading embeds
  (`![[Note#Heading]]`)
- `%%comment%%` for text hidden from the reader view
- `==highlight==`
- `- [ ]` tasks, which the Tasks plugin extends with due-date syntax
- Inline `key:: value` Dataview fields
- Callouts using GitHub's alert syntax plus many more types: `> [!info]`, `> [!question]`,
  and a `-`/`+` suffix for collapsible

Keep the H1 — Obsidian shows the filename as the title, but the graph and search work off
headings and links, so an H1 matching the filename is conventional and harmless.

Filenames are the identity of a note and appear inside every link to it, so use readable
Title Case names with spaces rather than kebab-case. Renaming a note updates links inside
Obsidian, but a note written outside the vault and dropped in won't have those links
rewritten.

If the vault is synced to git or published with Obsidian Publish, wikilinks may not resolve
in the other context. Standard `[text](path.md)` links work in both, so prefer them when
the notes have any life outside the app.

## Notion, Confluence, Google Docs import

Importers implement a small subset and drop the rest silently. Stay on the portable core.

- Tables usually survive but lose alignment and any HTML inside cells.
- Nested lists beyond two levels flatten.
- Task lists, footnotes, and admonitions do not survive.
- Raw HTML is stripped or shown as literal text.
- Code fences survive; the language tag may not.
- Front matter renders as literal text — omit it entirely.

Use plain headings, plain paragraphs, plain lists, and simple tables. Anything clever will
need manual cleanup by the person doing the import, which defeats the purpose.

## Slack and Discord

Neither is Markdown. Slack uses `*bold*` (single asterisks), `_italic_`, `~strike~`, and
`>` quotes; it has no headings, no tables, and no images from Markdown. Discord is closer
to Markdown but has no tables and no images either.

If the destination is a Slack or Discord message, don't write a `.md` file — write the
message text in the chat, structured with short paragraphs, bold labels, and code fences,
and drop headings and tables entirely.

## Pandoc to PDF or Word

Pandoc reads its own Markdown dialect. Front matter keys it uses: `title`, `author`,
`date`, plus `toc`, `geometry`, `fontsize`, `bibliography` when the template supports them.

Notable differences: implicit heading identifiers, `[@citation]` syntax, fenced divs
(`::: {.class}`), and `$...$` math all work. GFM task lists and alerts do not unless the
input format is set to `gfm`.

Structure for print rather than for scrolling. Page breaks come from `\newpage` (LaTeX
output only), heading depth maps to the document's section levels, and very wide tables
overflow the page — keep tables to four or five narrow columns, or use a definition list.

If the real deliverable is a Word or PDF file rather than Markdown, use the `docx` or `pdf`
skill instead of writing Markdown and converting.

## LLM and agent context files

`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, system-prompt fragments, and RAG source
documents are read by a model, not rendered. Optimize differently.

- Front-load the operative information. Instructions buried under three sections of
  background get diluted.
- Headings are retrieval anchors. Make them literal and keyword-dense: "Running tests",
  "Database migrations", not "Housekeeping".
- Write each section to stand alone. Chunked retrieval may deliver it without its
  neighbors, so avoid "as mentioned above" and unresolved pronouns.
- Be specific and imperative. Exact commands, exact paths, exact file names. `pnpm test
  --filter web`, not "run the test suite".
- State the reason behind a rule in one clause. A model that understands why a constraint
  exists generalizes it correctly to cases the file didn't anticipate.
- Skip visual polish — no emoji, no ASCII art, no decorative rules. It consumes context
  and conveys nothing.
- Prefer tables and tight lists for lookup data (commands, env vars, conventions) and
  prose for reasoning and rationale.
