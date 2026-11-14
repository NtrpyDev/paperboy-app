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

// Who counts on the owner's numbers page: paying is active, grace, and canceled before expiry;
// trials are counted on their own. On hold, paused, expired, and pending count as neither.
export interface Counts {
  paying: number;
  trials: number;
  // Field wire value to the number of paying subscribers who picked it.
  fields: Record<string, number>;
}

export async function liveCounts(db: D1Database, now: number): Promise<Counts> {
  const { results } = await db
    .prepare("SELECT state, expires_at, fields FROM subscribers WHERE state IN ('active', 'grace', 'canceled', 'trial')")
    .all<{ state: State; expires_at: number | null; fields: string }>();
  const counts: Counts = { paying: 0, trials: 0, fields: {} };
  for (const row of results) {
    if (row.state === "trial") {
      counts.trials++;
      continue;
    }
    if (row.state === "canceled" && !(row.expires_at !== null && row.expires_at > now)) continue;
    counts.paying++;
    for (const field of new Set(fromRow({ fields: row.fields } as Row).fields)) counts.fields[field] = (counts.fields[field] ?? 0) + 1;
  }
  return counts;
}

export interface DaySnapshot extends Counts {
  day: string;
}

export async function saveSnapshot(db: D1Database, day: string, counts: Counts, now: number): Promise<void> {
  await db
    .prepare(
      `INSERT INTO snapshots (day, paying, trials, fields, taken_at) VALUES (?1, ?2, ?3, ?4, ?5)
       ON CONFLICT (day) DO UPDATE SET paying = excluded.paying, trials = excluded.trials, fields = excluded.fields, taken_at = excluded.taken_at`,
    )
    .bind(day, counts.paying, counts.trials, JSON.stringify(counts.fields), now)
    .run();
}

// The last snapshot of each month, newest month first.
export async function monthEndSnapshots(db: D1Database, months: number): Promise<DaySnapshot[]> {
  const { results } = await db
    .prepare(
      `SELECT s.day, s.paying, s.trials, s.fields FROM snapshots s
       JOIN (SELECT MAX(day) AS day FROM snapshots GROUP BY substr(day, 1, 7)) m ON m.day = s.day
       ORDER BY s.day DESC LIMIT ?1`,
    )
    .bind(months)
    .all<{ day: string; paying: number; trials: number; fields: string }>();
  return results.map((row) => {
    let fields: unknown;
    try {
      fields = JSON.parse(row.fields);
    } catch {
      fields = {};
    }
    return { day: row.day, paying: row.paying, trials: row.trials, fields: typeof fields === "object" && fields ? (fields as Record<string, number>) : {} };
  });
}

// Epoch milliseconds of the oldest subscriber row, or null with none.
export async function firstSubscriberAt(db: D1Database): Promise<number | null> {
  const row = await db.prepare("SELECT MIN(created_at) AS first FROM subscribers").first<{ first: number | null }>();
  return row?.first ?? null;
}
