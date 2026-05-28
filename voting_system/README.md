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

### Kynehl Scott Misajon
Leading the implementation of this distributed voting system reinforced that fault-tolerant architecture is not a feature added after the fact but a consequence of deliberate design decisions made from the beginning. Coordinating multiple edge nodes across the group while ensuring consistent environment configuration, unique node identifiers, and correct Supabase Realtime setup required as much attention as the code itself. The most instructive moment came during fault injection, where stopping the worker while edge nodes continued transmitting demonstrated in concrete terms how decoupled components isolate failure — votes accumulated in PostgreSQL without loss, and the system recovered automatically upon restart without any manual intervention. Distributed systems, this activity made clear, are as much a coordination problem as they are a technical one.

### Kim Ryan Joseph T. Orencia
Implementing this distributed voting system revealed that the elegance of an architecture is best appreciated not in its diagrams but in its behavior under stress. The decision to use PostgreSQL as both the persistence and event backbone, rather than maintaining a separate message queue, gave the system a coherence that made the entire data flow traceable from a single table — a design quality that proved valuable during debugging and evaluation. What resonated most was observing the recovery phase, where the catch-up query methodically processed the backlog accumulated during worker downtime, illustrating that eventual consistency is not a compromise but a deliberate convergence toward correctness. This activity shifted my understanding of distributed correctness from a static property to a dynamic one, where the system's truth is not always immediate but is always directionally sound.

### Julien A. Marabe
The implementation of this distributed voting system provided a practical basis for evaluating several key properties of distributed architecture, most notably idempotency, fault isolation, and eventual consistency. Enforcing idempotency at the database level through a composite primary key upsert conflict target proved effective under deliberate duplicate injection, confirming that at-least-once delivery semantics can be safely absorbed without additional application logic when the persistence layer is designed accordingly. Worker recovery via the catch-up query functioned correctly within the scope of this exercise, though a production system would require a persistent cursor or watermark mechanism rather than an in-memory dedup set to handle restarts at scale. Latency measurements averaged approximately 1.2 seconds end-to-end under normal conditions and rose to between 3 and 5 seconds during batch recovery, which is consistent with expected PostgreSQL replication lag and provides a measurable baseline for evaluating the trade-off between durability and throughput in this architecture.

### Alfred Samuya
Participating in the implementation of this distributed voting system as an edge node operator provided firsthand exposure to the practical realities of fault tolerance that theoretical discussion alone does not fully convey. Running node_4 under simulated network instability demonstrated that the exponential backoff retry logic was not merely a code exercise but a functionally necessary mechanism, as transmission failures occurred during testing and were recovered without data loss or manual intervention. The worker recovery phase was particularly instructive — observing the catch-up query silently process the entire backlog accumulated during downtime illustrated how persistent storage as a messaging backbone removes the fragility of ephemeral queues. This activity made it evident that resilient distributed systems are designed primarily around failure scenarios, and the normal operating path is, in many ways, the easier problem to solve.

### Emmanuel Sonquipal
This laboratory activity provided a concrete basis for understanding how fault tolerance emerges from architectural decisions rather than from runtime error handling alone. The separation of the ingestion layer from the processing layer meant that worker downtime had no effect on the system's ability to receive and persist votes, a property that held consistently throughout the fault injection phase and validated the design's core assumption that no single component should bear responsibility for both accepting and processing data simultaneously. The Realtime configuration issue encountered — requiring a manual ALTER PUBLICATION command and REPLICA IDENTITY FULL setting not exposed through the dashboard — was a valuable reminder that platform abstractions have limits, and understanding the underlying PostgreSQL replication mechanics is necessary for diagnosing failures that surface at those boundaries. Comparing vote counts across the edge logs, the database table, and the worker output confirmed eventual consistency across all components, demonstrating that the system converged to a correct final state despite the intermediate inconsistencies introduced during failure simulation.
