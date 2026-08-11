# Diagram patterns

Copy-paste-safe Mermaid for work summaries. Read this when you've decided a diagram earns its place; pick the closest pattern and adapt.

Contents: [Flow through components](#flow-through-components) · [Before/after refactor](#beforeafter-refactor) · [Sequence](#sequence) · [Schema](#schema) · [State](#state) · [Timeline](#timeline) · [Churn chart](#churn-chart) · [Syntax safety](#syntax-safety)

## Flow through components

Highlight what's new so the reader sees the delta immediately.

```mermaid
flowchart LR
    C[Client] --> A[API gateway]
    A --> H[Webhook handler]
    H --> I[Idempotency store]:::new
    H --> P[Payment processor]
    I --> P
    P --> D[(Postgres)]

    classDef new fill:#dcfce7,stroke:#16a34a,stroke-width:2px
```

## Before/after refactor

Two subgraphs in one diagram, no edges crossing between them. Easier to read than two separate diagrams and keeps the comparison on one screen.

```mermaid
flowchart TB
    subgraph after["After"]
        direction LR
        B1[handler] --> B2[service layer]:::new
        B2 --> B3[repository]:::new
        B3 --> B4[(db)]
    end
    subgraph before["Before"]
        direction LR
        A1[handler] --> A2[db calls inline]
        A2 --> A3[(db)]
    end

    classDef new fill:#dcfce7,stroke:#16a34a,stroke-width:2px
```

Put "After" first when the reader mainly needs the new mental model; put "Before" first when the point is what was wrong.

## Sequence

Best when ordering, retries, or async timing is the substance of the change.

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant S as Stripe
    participant Q as Retry queue

    C->>A: POST /charge (Idempotency-Key)
    A->>A: check key store
    alt key seen before
        A-->>C: 200 cached result
    else new key
        A->>S: create charge
        S--)A: webhook charge.succeeded
        A-->>C: 202 accepted
    end
    Note over A,Q: failures re-enqueue with backoff
```

## Schema

Show only the tables the work touched, and mark added columns in the label.

```mermaid
erDiagram
    CUSTOMER ||--o{ PAYMENT : makes
    PAYMENT ||--o| IDEMPOTENCY_KEY : "guarded by"
    PAYMENT {
        uuid id
        string status
        string idempotency_key "new"
    }
    IDEMPOTENCY_KEY {
        string key PK
        jsonb response "new table"
    }
```

## State

For lifecycle logic — order/job/auth states. Annotate transitions that the work changed.

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> processing: worker claims
    processing --> succeeded
    processing --> retrying: transient error
    retrying --> processing: backoff elapsed
    retrying --> failed: max attempts
    succeeded --> [*]
    failed --> [*]
```

## Timeline

For a sprint or multi-week window where sequencing matters.

```mermaid
timeline
    title Payments work, Jul 28 - Aug 8
    Week 1 : idempotency key store : migration 0043
    Week 2 : webhook handler rewrite : retry backoff
    Week 2 : CI workflow added
```

## Churn chart

Only when the distribution is itself informative. A table with inline bars renders everywhere and can't break:

| Area | Churn | |
|---|---|---|
| `billing/` | +1,240 / -890 | ████████████ |
| `api/` | +310 / -95 | ███ |
| `migrations/` | +80 / -0 | █ |

If a real chart is wanted:

```mermaid
xychart-beta
    title "Lines changed by area"
    x-axis [billing, api, migrations, tests]
    y-axis "Lines" 0 --> 2200
    bar [2130, 405, 80, 640]
```

## Syntax safety

Where Mermaid quietly breaks:

- **Punctuation in labels** — quote it: `A["handler (v2)"]`. Unquoted parentheses, colons, commas, and slashes are the most common failure.
- **`<br>`** — works in some renderers, not all. Prefer shorter labels or `"line one\nline two"` in quotes.
- **Node IDs** — keep them short and alphanumeric. Never reuse an ID for two different nodes; Mermaid silently merges them.
- **Reserved words** — `end`, `graph`, `class`, `click` as node IDs or bare labels break the parse. Capitalize or quote: `E["end"]`.
- **`classDef` placement** — define classes after the nodes that use them; `:::class` syntax needs no separate `class` statement.
- **Direction inside subgraphs** — `direction LR` works within a subgraph but the outer graph direction wins in some versions. Test by eye, and prefer `TB` outer / `LR` inner.
- **Size** — past roughly 15 nodes the diagram stops helping. Split it or narrow the scope.

Before shipping, reread each diagram once and ask whether a reader who knows nothing about this codebase would draw the right conclusion from it. If it needs a paragraph of explanation to be legible, the paragraph alone was probably the better artifact.
