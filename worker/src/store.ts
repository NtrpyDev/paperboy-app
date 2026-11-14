// The subscriber store in D1 (migrations/0001_subscribers.sql).
// D1 Worker API: https://developers.cloudflare.com/d1/worker-api/

export type State = "trial" | "active" | "grace" | "on_hold" | "paused" | "canceled" | "expired" | "pending";

export interface Subscriber {
  tokenHash: string;
  purchaseToken: string;
  productId: string;
  state: State;
  expiresAt: number | null;
  fields: string[];
}

interface Row {
  token_hash: string;
  purchase_token: string;
  product_id: string;
  state: State;
  expires_at: number | null;
  fields: string;
}

function fromRow(row: Row): Subscriber {
  let fields: unknown;
  try {
    fields = JSON.parse(row.fields);
  } catch {
    fields = [];
  }
  return {
    tokenHash: row.token_hash,
    purchaseToken: row.purchase_token,
    productId: row.product_id,
    state: row.state,
    expiresAt: row.expires_at,
    fields: Array.isArray(fields) ? fields.filter((f): f is string => typeof f === "string") : [],
  };
}

export async function getSubscriber(db: D1Database, tokenHash: string): Promise<Subscriber | null> {
  const row = await db.prepare("SELECT * FROM subscribers WHERE token_hash = ?1").bind(tokenHash).first<Row>();
  return row ? fromRow(row) : null;
}

// Writes the subscriber row and removes the rows of the tokens it replaces, in one transaction.
export async function saveSubscriber(db: D1Database, sub: Subscriber, replaces: string[], now: number): Promise<void> {
  const statements = [
    db
      .prepare(
        `INSERT INTO subscribers (token_hash, purchase_token, product_id, state, expires_at, fields, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?7)
         ON CONFLICT (token_hash) DO UPDATE SET
           product_id = excluded.product_id, state = excluded.state, expires_at = excluded.expires_at,
           fields = excluded.fields, updated_at = excluded.updated_at`,
      )
      .bind(sub.tokenHash, sub.purchaseToken, sub.productId, sub.state, sub.expiresAt, JSON.stringify(sub.fields), now),
    ...replaces
      .filter((hash) => hash !== sub.tokenHash)
      .map((hash) => db.prepare("DELETE FROM subscribers WHERE token_hash = ?1").bind(hash)),
  ];
  await db.batch(statements);
}

export async function deleteSubscriber(db: D1Database, tokenHash: string): Promise<void> {
  await db.prepare("DELETE FROM subscribers WHERE token_hash = ?1").bind(tokenHash).run();
}

// Field lists of every subscriber whose state counts toward the active fields.
export async function countingFields(db: D1Database, countTrials: boolean, now: number): Promise<string[][]> {
  const { results } = await db
    .prepare(
      `SELECT fields FROM subscribers
       WHERE state IN ('active', 'grace')
          OR (state = 'trial' AND ?1 = 1)
          OR (state = 'canceled' AND expires_at > ?2)`,
    )
    .bind(countTrials ? 1 : 0, now)
    .all<{ fields: string }>();
  return results.map((row) => fromRow({ fields: row.fields } as Row).fields);
}

export async function isKnownUnknown(db: D1Database, tokenHash: string, now: number): Promise<boolean> {
  const row = await db
    .prepare("SELECT 1 AS hit FROM unknown_purchases WHERE token_hash = ?1 AND until > ?2")
    .bind(tokenHash, now)
    .first<{ hit: number }>();
  return row !== null;
}

export async function rememberUnknown(db: D1Database, tokenHash: string, until: number, now: number): Promise<void> {
  await db.batch([
    db.prepare("DELETE FROM unknown_purchases WHERE until <= ?1").bind(now),
    db
      .prepare("INSERT INTO unknown_purchases (token_hash, until) VALUES (?1, ?2) ON CONFLICT (token_hash) DO UPDATE SET until = excluded.until")
      .bind(tokenHash, until),
  ]);
}
