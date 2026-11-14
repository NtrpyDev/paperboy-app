-- Subscribers, one row per Play purchase token, keyed by the token's SHA-256.
-- Applied with `wrangler d1 migrations apply paperboy-subscribers --env paid --remote`.

CREATE TABLE subscribers (
  -- Lowercase hex SHA-256 of the purchase token.
  token_hash TEXT PRIMARY KEY,
  purchase_token TEXT NOT NULL,
  product_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('trial', 'active', 'grace', 'on_hold', 'paused', 'canceled', 'expired', 'pending')),
  -- Epoch milliseconds, or null when Google gives no expiry (a pending purchase).
  expires_at INTEGER,
  -- JSON array of field wire values, for example ["math","space"].
  fields TEXT NOT NULL DEFAULT '[]',
  -- Epoch milliseconds.
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

-- GET /v1/active-fields selects by state, and canceled rows by expiry.
CREATE INDEX subscribers_state_expires ON subscribers (state, expires_at);

-- Tokens Google said it does not know, so the same bad token is not sent to Google again
-- for a few minutes. Holds only the token's hash and when the entry lapses.
CREATE TABLE unknown_purchases (
  token_hash TEXT PRIMARY KEY,
  until INTEGER NOT NULL
);
