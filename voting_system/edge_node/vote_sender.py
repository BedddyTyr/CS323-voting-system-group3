"""
vote_sender.py
--------------
Handles HTTP transmission of votes to the Supabase Edge Function.
Implements exponential backoff retry logic to simulate unreliable
network conditions common in distributed edge environments.
"""

import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

EDGE_FUNCTION_URL = os.getenv("EDGE_FUNCTION_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
EDGE_ID           = os.getenv("EDGE_ID", "node_1")

HEADERS = {
    "Content-Type":  "application/json",
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
}


def send_vote(vote: dict, max_retries: int = 3, backoff: float = 1.5) -> bool:
    """
    POST a vote payload to the Supabase Edge Function.

    Retries on failure using exponential backoff to handle transient
    network instability. If all attempts fail the vote is dropped and
    False is returned — callers may log or queue for later.

    Args:
        vote:        Vote dict produced by vote_generator.generate_vote().
        max_retries: Maximum number of transmission attempts.
        backoff:     Exponential backoff base (seconds).

    Returns:
        True if the vote was accepted (HTTP 2xx), False otherwise.
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                EDGE_FUNCTION_URL,
                json=vote,
                headers=HEADERS,
                timeout=5,
            )
            resp.raise_for_status()
            print(
                f"[{EDGE_ID}] ✓ Sent  user={vote['user_id'][:8]}…  "
                f"choice={vote['choice']}  status={resp.status_code}"
            )
            return True

        except requests.exceptions.Timeout:
            wait = backoff ** attempt
            print(f"[{EDGE_ID}] ✗ Attempt {attempt} timed out. Retrying in {wait:.1f}s…")
            time.sleep(wait)

        except requests.exceptions.ConnectionError as e:
            wait = backoff ** attempt
            print(f"[{EDGE_ID}] ✗ Connection error: {e}. Retrying in {wait:.1f}s…")
            time.sleep(wait)

        except requests.exceptions.HTTPError as e:
            # 4xx errors are client-side; no point retrying
            print(f"[{EDGE_ID}] ✗ HTTP {e.response.status_code} — vote dropped (client error).")
            return False

        except Exception as e:
            wait = backoff ** attempt
            print(f"[{EDGE_ID}] ✗ Unexpected error: {e}. Retrying in {wait:.1f}s…")
            time.sleep(wait)

    print(f"[{EDGE_ID}] ✗ Vote dropped after {max_retries} retries.")
    return False


def send_vote_duplicate(vote: dict, repeat: int = 2) -> None:
    """
    Fault-injection helper: send the same vote multiple times to
    simulate retry-induced duplication (Part 5 — Fault Injection).

    Args:
        vote:   The vote to duplicate.
        repeat: Number of times to send (default 2).
    """
    print(f"[{EDGE_ID}] ⚠ Sending duplicate vote {repeat}x for fault injection…")
    for i in range(repeat):
        send_vote(vote)
