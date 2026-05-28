# CS323 — Distributed Voting System (Supabase)
**Edge Function URL (Cloud Run API equivalent):** https://trmofzgslbobpfbqytao.supabase.co/functions/v1/ingest-vote\
**Gif Proof:** 
![Alt Text](https://drive.google.com/file/d/1Rosf-YlkbVa8c3KryI6amk-_1H8hByVi/view?usp=sharing)

## Architecture

```
Edge Nodes  →  Edge Function (ingest-vote)  →  PostgreSQL (votes table)
                                                      ↓  Polling (every 3s)
                                               Python Worker (worker.py)
```

## Supabase Equivalent of GCP Services

| GCP Service | Supabase Equivalent |
|---|---|
| Cloud Run API | Edge Function (`ingest-vote`) |
| Pub/Sub | PostgreSQL + HTTP Polling |
| Firestore | PostgreSQL `votes` table |
| Worker Service | `worker.py` (polling-based) |

**Deployed Edge Function URL (Cloud Run equivalent):**
```
https://trmofzgslbobpfbqytao.supabase.co/functions/v1/ingest-vote
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
│   ├── worker.py             # Entry point — polling-based worker
│   ├── vote_processor.py     # Processes + deduplicates a single vote
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
3. Enable Realtime on the `votes` table by running in SQL Editor:
   ```sql
   ALTER TABLE votes REPLICA IDENTITY FULL;
   ALTER PUBLICATION supabase_realtime ADD TABLE votes;
   ```
4. Go to **Settings → API → Legacy anon, service_role API keys** and copy the **anon public** key (starts with `eyJ...`)
5. Copy your **Project URL** from **Settings → API**

### 2. Deploy Edge Function
Deploy via the Supabase dashboard (no CLI required):
1. Go to **Edge Functions** in the left sidebar
2. Click **Deploy a new function → Via Editor**
3. Name it exactly: `ingest-vote`
4. Paste the contents of `supabase/functions/ingest-vote/index.ts`
5. Click **Deploy**
6. Go to the function page and turn **JWT Verification OFF**

### 3. Configure .env files

**edge_node/.env**
```
SUPABASE_URL=https://<your-ref>.supabase.co
SUPABASE_ANON_KEY=eyJ...legacy anon key...
EDGE_FUNCTION_URL=https://<your-ref>.supabase.co/functions/v1/ingest-vote
EDGE_ID=node_1
```

**worker/.env**
```
SUPABASE_URL=https://<your-ref>.supabase.co
SUPABASE_ANON_KEY=eyJ...legacy anon key...
```

> Use the **legacy anon key** (`eyJ...`) from **Settings → API → Legacy anon, service_role API keys**, NOT the `sb_publishable_...` key.

### 4. Install Dependencies

```bash
# Edge node
cd edge_node
pip install -r requirements.txt

# Worker
cd ../worker
pip install -r requirements.txt
```

### 5. Run the System

Always start the worker first, then the edge node in a second terminal.

**Terminal 1 — Worker:**
```bash
cd worker
python worker.py
```

**Terminal 2 — Edge Node:**
```bash
cd edge_node
python edge_node.py
```

Each group member runs `edge_node.py` with a different `EDGE_ID` in their `.env` (node_1, node_2, node_3...).

---

## Fault Injection (Part 5)

**Duplicate sends:**
```bash
python edge_node.py --fault-inject --repeat 3
```

**Worker failure simulation:**
- Stop `worker.py` (Ctrl+C) while edge nodes keep running
- Observe votes accumulating in the Supabase Table Editor
- Restart `worker.py` — it automatically processes the backlog on startup

---

## Evaluation Queries

Run these in the Supabase SQL Editor during Part 6:

```sql
-- Total votes
SELECT COUNT(*) FROM votes;

-- No duplicates check (should equal COUNT(*))
SELECT COUNT(DISTINCT id) FROM votes;

-- Choice distribution
SELECT choice, COUNT(*) FROM votes GROUP BY choice ORDER BY choice;

-- Per-node distribution
SELECT edge_id, COUNT(*) FROM votes GROUP BY edge_id ORDER BY edge_id;

-- Average end-to-end latency
SELECT
    AVG(EXTRACT(EPOCH FROM time_created) - timestamp) AS avg_latency_s,
    MIN(EXTRACT(EPOCH FROM time_created) - timestamp) AS min_latency_s,
    MAX(EXTRACT(EPOCH FROM time_created) - timestamp) AS max_latency_s
FROM votes;
```

---

## Individual Reflections

### Kynehl Scott Misajon — Group Leader
Leading the implementation of this distributed voting system reinforced that fault-tolerant architecture is not a feature added after the fact but a consequence of deliberate design decisions made from the beginning. Coordinating multiple edge nodes across the group while ensuring consistent environment configuration, unique node identifiers, and correct Supabase setup required as much attention as the code itself. The most instructive moment came during fault injection, where stopping the worker while edge nodes continued transmitting demonstrated in concrete terms how decoupled components isolate failure — votes accumulated in PostgreSQL without loss, and the system recovered automatically upon restart without any manual intervention. Distributed systems, this activity made clear, are as much a coordination problem as they are a technical one.

### Kim Ryan Joseph T. Orencia
This implementation made me understand that the elegance of an architectural design is to be evaluated based on its performance in times of stress, rather than just based on its diagrams. The one thing that I found impressive with using PostgreSQL not only as the database layer, but also as the event store, is that all the data flow is completely traceable from looking at one single table. The most amazing part of the entire implementation came when we were observing the catch-up queries, which helped us get rid of the backlog during the downtime of our workers. It opened up my mind to the workings of eventual consistency and helped me understand that truth converges towards consistency.

### Julien A. Marabe
The implementation of this distributed voting system provided a practical basis for evaluating several key properties of distributed architecture, most notably idempotency, fault isolation, and eventual consistency. Enforcing idempotency at the database level through a composite primary key upsert conflict target proved effective under deliberate duplicate injection, confirming that at-least-once delivery semantics can be safely absorbed without additional application logic when the persistence layer is designed accordingly. Worker recovery via the catch-up query functioned correctly within the scope of this exercise, though a production system would require a persistent cursor or watermark mechanism rather than an in-memory dedup set to handle restarts at scale. Latency measurements averaged approximately 1.2 seconds end-to-end under normal conditions and rose to between 3 and 5 seconds during batch recovery, which is consistent with expected PostgreSQL replication lag and provides a measurable baseline for evaluating the trade-off between durability and throughput in this architecture.

### Alfred Samuya
Participating in the implementation of this distributed voting system as an edge node operator provided firsthand exposure to the practical realities of fault tolerance that theoretical discussion alone does not fully convey. Running node_4 under simulated network instability demonstrated that the exponential backoff retry logic was not merely a code exercise but a functionally necessary mechanism, as transmission failures occurred during testing and were recovered without data loss or manual intervention. The worker recovery phase was particularly instructive — observing the catch-up query silently process the entire backlog accumulated during downtime illustrated how persistent storage as a messaging backbone removes the fragility of ephemeral queues. This activity made it evident that resilient distributed systems are designed primarily around failure scenarios, and the normal operating path is, in many ways, the easier problem to solve.

### Emmanuel Sonquipal
This laboratory activity provided a concrete basis for understanding how fault tolerance emerges from architectural decisions rather than from runtime error handling alone. The separation of the ingestion layer from the processing layer meant that worker downtime had no effect on the system's ability to receive and persist votes, a property that held consistently throughout the fault injection phase and validated the design's core assumption that no single component should bear responsibility for both accepting and processing data simultaneously. The Realtime configuration issue encountered — requiring a manual ALTER PUBLICATION command and REPLICA IDENTITY FULL setting not exposed through the dashboard — was a valuable reminder that platform abstractions have limits, and understanding the underlying PostgreSQL replication mechanics is necessary for diagnosing failures that surface at those boundaries. Comparing vote counts across the edge logs, the database table, and the worker output confirmed eventual consistency across all components, demonstrating that the system converged to a correct final state despite the intermediate inconsistencies introduced during failure simulation.
