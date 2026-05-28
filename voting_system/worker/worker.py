"""
worker.py
---------
Entry point for the distributed voting worker service.

On startup the worker:
  1. Runs a catch-up query to process any votes written during downtime.
  2. Subscribes to the Supabase Realtime 'postgres_changes' channel on
     the 'votes' table to process new votes as they arrive.

This mirrors the behaviour of a Pub/Sub pull subscriber + Cloud Run
worker but uses Supabase Realtime instead.

Usage:
    python worker.py
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

from vote_processor import process_vote, get_processed_count
from catchup import run_catchup

load_dotenv()


# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------

def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env"
        )
    return create_client(url, key)


# ---------------------------------------------------------------------------
# Realtime callback
# ---------------------------------------------------------------------------

def on_vote_insert(payload: dict) -> None:
    """
    Callback invoked by Supabase Realtime whenever a row is INSERTed
    into the 'votes' table.

    Args:
        payload: Realtime event payload; the new row is under payload["new"].
    """
    record = payload.get("new", {})
    process_vote(record)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_worker() -> None:
    """
    Start the worker:
      1. Catch up on any backlogged votes.
      2. Subscribe to Realtime for live events.
      3. Keep the process alive.
    """
    supabase = get_supabase_client()

    # ── Step 1: Catch-up ─────────────────────────────────────────────────
    run_catchup(supabase)

    # ── Step 2: Subscribe to Realtime ────────────────────────────────────
    print("Worker: Subscribing to Realtime channel 'votes-channel'…")
    channel = (
        supabase
        .channel("votes-channel")
        .on_postgres_changes(
            event="INSERT",
            schema="public",
            table="votes",
            callback=on_vote_insert,
        )
        .subscribe()
    )

    print("Worker: Listening for new votes… (Ctrl+C to stop)")

    # ── Step 3: Keep alive ───────────────────────────────────────────────
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\nWorker: Shutting down. Session total: {get_processed_count()} vote(s) processed.")
        supabase.remove_channel(channel)


if __name__ == "__main__":
    run_worker()
