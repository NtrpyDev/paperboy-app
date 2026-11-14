-- One row per UTC day, written by the daily Cron Trigger, so the owner's numbers page can show
-- past months: the subscriber table only knows the present.

CREATE TABLE snapshots (
  -- UTC date, YYYY-MM-DD.
  day TEXT PRIMARY KEY,
  -- Subscribers paying at the time: active, grace, and canceled before expiry.
  paying INTEGER NOT NULL,
  -- Subscribers in a free trial.
  trials INTEGER NOT NULL,
  -- JSON object: field wire value to the number of paying subscribers who picked it.
  fields TEXT NOT NULL,
  -- Epoch milliseconds the snapshot was taken.
  taken_at INTEGER NOT NULL
);
