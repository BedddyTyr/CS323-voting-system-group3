-- schema.sql
-- Run this in the Supabase SQL Editor to set up the votes table.
-- ---------------------------------------------------------------

-- Create the votes table
-- 'id' is the idempotency key: user_id + '_' + poll_id
-- Duplicate upserts on the same id overwrite rather than create new rows.

CREATE TABLE IF NOT EXISTS votes (
    id           TEXT             PRIMARY KEY,
    user_id      UUID             NOT NULL,
    poll_id      TEXT             NOT NULL DEFAULT 'poll_1',
    choice       TEXT             NOT NULL CHECK (choice IN ('A', 'B', 'C')),
    edge_id      TEXT,
    timestamp    DOUBLE PRECISION NOT NULL,
    time_created TIMESTAMPTZ      DEFAULT NOW()
);

-- ── Row Level Security ──────────────────────────────────────────────────────
-- Enable RLS so only explicitly granted operations are allowed.

ALTER TABLE votes ENABLE ROW LEVEL SECURITY;

-- Allow anonymous clients (edge nodes / worker) to insert votes
CREATE POLICY "allow_anon_insert"
    ON votes FOR INSERT TO anon
    WITH CHECK (true);

-- Allow anonymous clients to read votes (needed by the worker catch-up query)
CREATE POLICY "allow_anon_select"
    ON votes FOR SELECT TO anon
    USING (true);

-- ── Enable Realtime ─────────────────────────────────────────────────────────
-- After running this migration, also go to:
--   Database → Replication → Tables that broadcast changes
-- and toggle ON the 'votes' table to enable postgres_changes events.

-- ── Useful analytical queries (run during evaluation) ──────────────────────

-- Total votes stored
-- SELECT COUNT(*) FROM votes;

-- Confirm no duplicates exist (should equal COUNT(*))
-- SELECT COUNT(DISTINCT id) FROM votes;

-- Vote distribution per choice
-- SELECT choice, COUNT(*) AS total FROM votes GROUP BY choice ORDER BY choice;

-- Vote distribution per edge node
-- SELECT edge_id, COUNT(*) AS total FROM votes GROUP BY edge_id ORDER BY edge_id;

-- Approximate end-to-end latency (seconds from edge timestamp to DB write)
-- SELECT
--     AVG(EXTRACT(EPOCH FROM time_created) - timestamp) AS avg_latency_s,
--     MIN(EXTRACT(EPOCH FROM time_created) - timestamp) AS min_latency_s,
--     MAX(EXTRACT(EPOCH FROM time_created) - timestamp) AS max_latency_s
-- FROM votes;
