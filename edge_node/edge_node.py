"""
edge_node.py
------------
Entry point for a single edge node instance.

Each group member runs this script independently with a unique EDGE_ID
set in their .env file (node_1, node_2, node_3 …). Together they simulate
multiple concurrent distributed data sources.

Usage:
    # Normal operation
    python edge_node.py

    # Fault injection mode (sends duplicate votes)
    python edge_node.py --fault-inject
"""

import time
import random
import argparse
import os
from dotenv import load_dotenv

from vote_generator import generate_vote
from vote_sender import send_vote, send_vote_duplicate

load_dotenv()

EDGE_ID = os.getenv("EDGE_ID", "node_1")


# ---------------------------------------------------------------------------
# Normal operation
# ---------------------------------------------------------------------------

def run_edge_node(min_delay: float = 1.0, max_delay: float = 3.0) -> None:
    """
    Continuously generate and send votes with random delays to simulate
    realistic, non-synchronised edge behaviour.

    Args:
        min_delay: Minimum sleep between votes (seconds).
        max_delay: Maximum sleep between votes (seconds).
    """
    print(f"[{EDGE_ID}] Edge node started. Sending votes…")
    while True:
        vote = generate_vote(edge_id=EDGE_ID)
        send_vote(vote)
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)


# ---------------------------------------------------------------------------
# Fault injection mode (Part 5 — Step 1)
# ---------------------------------------------------------------------------

def run_fault_inject(repeat: int = 2) -> None:
    """
    Send each vote multiple times to simulate retry-induced duplication.
    The Supabase upsert on the 'id' primary key should absorb duplicates.

    Args:
        repeat: How many times each vote is transmitted.
    """
    print(f"[{EDGE_ID}] ⚠ Fault-injection mode: each vote sent {repeat}x")
    while True:
        vote = generate_vote(edge_id=EDGE_ID)
        send_vote_duplicate(vote, repeat=repeat)
        time.sleep(random.uniform(1.0, 3.0))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CS323 Distributed Voting — Edge Node")
    parser.add_argument(
        "--fault-inject",
        action="store_true",
        help="Enable duplicate-send fault injection (Part 5)",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=2,
        help="Number of duplicate sends per vote in fault-inject mode (default: 2)",
    )
    parser.add_argument(
        "--min-delay", type=float, default=1.0,
        help="Min seconds between votes (default: 1.0)",
    )
    parser.add_argument(
        "--max-delay", type=float, default=3.0,
        help="Max seconds between votes (default: 3.0)",
    )
    args = parser.parse_args()

    if args.fault_inject:
        run_fault_inject(repeat=args.repeat)
    else:
        run_edge_node(min_delay=args.min_delay, max_delay=args.max_delay)
