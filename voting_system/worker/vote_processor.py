"""
vote_processor.py
-----------------
Contains the core logic for processing a single vote record received
from the Supabase Realtime channel or from the catch-up query.

Keeps a local in-memory dedup set as a second line of defence on top of
the database-level PRIMARY KEY upsert constraint.
"""

import time

# In-memory set of doc IDs already processed this session.
# Prevents re-processing the same vote during the catch-up phase or
# when Realtime delivers a duplicate event.
_processed_ids: set = set()


def reset_processed() -> None:
    """Clear the in-memory dedup set (useful for testing)."""
    _processed_ids.clear()


def process_vote(record: dict) -> bool:
    """
    Process a single vote record.

    Steps:
      1. Validate the record has required fields.
      2. Check local dedup set to skip already-processed votes.
      3. Calculate and log end-to-end latency.
      4. Mark the vote as processed.

    Args:
        record: A dict representing one row from the 'votes' table.

    Returns:
        True  — vote was processed successfully.
        False — vote was skipped (duplicate or malformed).
    """
    doc_id = record.get("id")

    # ── Validation ────────────────────────────────────────────────────────
    if not doc_id:
        print("Worker: ✗ Malformed record (missing 'id') — skipped.")
        return False

    required = ["user_id", "poll_id", "choice", "timestamp"]
    for field in required:
        if field not in record:
            print(f"Worker: ✗ Missing field '{field}' in record {doc_id} — skipped.")
            return False

    # ── Deduplication ────────────────────────────────────────────────────
    if doc_id in _processed_ids:
        print(f"Worker: ⚠ Duplicate {doc_id[:20]}… — skipped.")
        return False

    # ── Processing ───────────────────────────────────────────────────────
    latency = time.time() - record["timestamp"]
    print(
        f"Worker: ✓ Processed  user={record['user_id'][:8]}…  "
        f"poll={record['poll_id']}  choice={record['choice']}  "
        f"edge={record.get('edge_id', 'unknown')}  "
        f"latency={latency:.3f}s"
    )

    _processed_ids.add(doc_id)
    return True


def get_processed_count() -> int:
    """Return the number of votes processed this session."""
    return len(_processed_ids)
