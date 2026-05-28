"""
catchup.py
----------
Processes any votes that were written to the Supabase 'votes' table
while the worker was offline (Part 5 — Step 3: Restoring Worker).

Run this once at worker startup before subscribing to Realtime so that
no votes are silently skipped after a downtime period.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

from vote_processor import process_vote, get_processed_count

load_dotenv()


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env"
        )
    return create_client(url, key)


def run_catchup(supabase: Client) -> int:
    print("Worker [catch-up]: Querying backlog…")
    try:
        response = supabase.table("votes").select("*").execute()
        records = response.data or []
        caught_up = 0

        for record in records:
            if process_vote(record):
                caught_up += 1

        print(f"Worker [catch-up]: {caught_up} backlogged vote(s) processed.")
        return caught_up
    except Exception as e:
        print(f"Worker [catch-up]: Could not query backlog — {e}. Skipping.")
        return 0

if __name__ == "__main__":
    # Allow running catch-up standalone for debugging
    client = get_supabase_client()
    run_catchup(client)
    print(f"Session total processed: {get_processed_count()}")
