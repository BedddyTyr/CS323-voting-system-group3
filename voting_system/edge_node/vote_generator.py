"""
vote_generator.py
-----------------
Responsible for generating synthetic vote payloads.
Each vote includes an idempotency key (id = user_id + '_' + poll_id)
and an edge_id to identify which node produced it.
"""

import uuid
import random
import time
import os


POLL_ID = "poll_1"
CHOICES = ["A", "B", "C"]


def generate_vote(edge_id: str = None) -> dict:
    """
    Generate a single synthetic vote payload.

    Extend this function to simulate multiple edge nodes by passing
    a different edge_id per node instance.

    Args:
        edge_id: Identifier for the originating edge node.
                 Defaults to the EDGE_ID environment variable.

    Returns:
        A dict representing one vote.
    """
    edge_id = edge_id or os.getenv("EDGE_ID", "node_1")
    user_id = str(uuid.uuid4())

    return {
        "id":        f"{user_id}_{POLL_ID}",   # idempotency key (PK in DB)
        "user_id":   user_id,
        "poll_id":   POLL_ID,
        "choice":    random.choice(CHOICES),
        "edge_id":   edge_id,
        "timestamp": time.time(),
    }
