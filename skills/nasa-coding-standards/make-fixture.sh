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
// Provider metadata arrives as JSON. The audit store only accepts flat string
// values, so top-level entries are stringified.
export function flattenMetadata(input: Record<string, unknown>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(input)) {
    out[key] = String(value);
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

// Counts how many refunds the provider has recorded against a charge.
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
    hasMore = page.has_more;
  }

  return refunds.length;
}
EOF

cat > src/refunds.ts <<'EOF'
import { recordAudit } from './audit.js';
import { getCharge } from './charges.js';
import { PROVIDER_KEY, PROVIDER_URL } from './config.js';
import { flattenMetadata } from './metadata.js';
import { countRefunds } from './reconcile.js';
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
  const priorRefunds = await countRefunds(event.chargeId);
  console.warn(
    `refund failed for charge ${event.chargeId} after ${priorRefunds} prior refunds: ${event.reason ?? 'unknown'}`,
  );
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
- `src/reconcile.ts` — counts prior refunds against a charge
EOF

# ALLOW_PROTECTED=1 because the global git-guard hook refuses commits on `main`,
# and the fixture wants a realistic default branch.
ALLOW_PROTECTED=1 git add -A
ALLOW_PROTECTED=1 git commit -qm "Mirror provider refunds into the audit store"
