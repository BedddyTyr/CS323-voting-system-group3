import os
import time
import requests
from dotenv import load_dotenv
from vote_processor import process_vote, get_processed_count

load_dotenv()

SUPABASE_URL      = os.getenv("SUPABASE_URL").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

HEADERS = {
    "apikey":        SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type":  "application/json",
}


def fetch_votes():
    url = f"{SUPABASE_URL}/rest/v1/votes?select=*"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def run_worker(poll_interval: float = 3.0):
    print("Worker: Starting...")
    print(f"Worker: Polling every {poll_interval}s... (Ctrl+C to stop)")

    while True:
        try:
            records = fetch_votes()
            new_count = 0
            for record in records:
                if process_vote(record):
                    new_count += 1
            if new_count:
                print(f"Worker: {new_count} new vote(s). "
                      f"Session total: {get_processed_count()}")
            else:
                print("Worker: No new votes.")
        except Exception as e:
            print(f"Worker: Error — {e}")

        time.sleep(poll_interval)


if __name__ == "__main__":
    run_worker()