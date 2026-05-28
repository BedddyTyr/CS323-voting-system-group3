# CS323 — Distributed Voting System (Supabase)

## Architecture

```
Edge Nodes  →  Edge Function (ingest-vote)  →  PostgreSQL (votes table)
                                                      ↓  Realtime
                                               Python Worker (worker.py)
```

## Project Structure

```
cs323-voting-groupX/
├── edge_node/
│   ├── edge_node.py          # Entry point — runs one edge node
│   ├── vote_generator.py     # Generates synthetic vote payloads
│   ├── vote_sender.py        # HTTP POST with retry/backoff logic
│   ├── requirements.txt
│   └── .env.example
├── worker/
│   ├── worker.py             # Entry point — Realtime subscriber
│   ├── vote_processor.py     # Processes + deduplicates a single vote
│   ├── catchup.py            # Catch-up query for backlogged votes
│   ├── requirements.txt
│   └── .env.example
├── supabase/
│   └── functions/
│       └── ingest-vote/
│           └── index.ts      # Edge Function — validates & upserts votes
└── sql/
    └── schema.sql            # votes table + RLS policies
```

## Setup

### 1. Supabase Project
1. Create a project at https://supabase.com (region: Southeast Asia — Singapore)
2. Run `sql/schema.sql` in the SQL Editor
3. Enable Realtime on the `votes` table: **Database → Replication → votes ✓**
4. Copy your **Project URL** and **anon key** from **Settings → API**

### 2. Deploy Edge Function
```bash
supabase login
supabase link --project-ref <your-ref>
supabase functions deploy ingest-vote --no-verify-jwt
```

### 3. Edge Nodes (one per group member)
```bash
cd edge_node
pip install -r requirements.txt
cp .env.example .env       # fill in your values; set EDGE_ID=node_1 / node_2 / …
python edge_node.py
```

### 4. Worker
```bash
cd worker
pip install -r requirements.txt
cp .env.example .env       # fill in your values
python worker.py
```

## Fault Injection (Part 5)

**Duplicate sends:**
```bash
python edge_node.py --fault-inject --repeat 3
```

**Worker failure simulation:**
- Stop `worker.py` (Ctrl+C) while edge nodes keep running
- Observe votes accumulating in the Supabase Table Editor
- Restart `worker.py` — catch-up query processes the backlog automatically

## Evaluation Queries

Run these in the Supabase SQL Editor during Part 6:

```sql
-- Total votes
SELECT COUNT(*) FROM votes;

-- No duplicates check
SELECT COUNT(DISTINCT id) FROM votes;

-- Choice distribution
SELECT choice, COUNT(*) FROM votes GROUP BY choice;

-- Per-node distribution
SELECT edge_id, COUNT(*) FROM votes GROUP BY edge_id;

-- Average end-to-end latency
SELECT AVG(EXTRACT(EPOCH FROM time_created) - timestamp) AS avg_latency_s
FROM votes;
```

---

## Individual Reflections

*(Each group member adds their reflection here.)*

### Member 1 — [Name]

### Member 2 — [Name]

### Member 3 — [Name]
