"""Process one pending TrimCircle job through a configured GPU endpoint."""
import argparse
import sqlite3
import time
from app.job_store import DATABASE_PATH, cleanup_expired, initialize, update_job
from app.provider import ProviderUnavailable, process_remote_job

def next_job() -> dict | None:
    initialize()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM tryon_jobs WHERE status = 'awaiting_gpu' ORDER BY created_at LIMIT 1").fetchone()
    return dict(row) if row else None

def run_once() -> int:
    cleanup_expired()
    job = next_job()
    if not job:
        return 0
    update_job(job["id"], status="queued", progress=20)
    try:
        process_remote_job(job["id"])
    except ProviderUnavailable:
        update_job(job["id"], status="awaiting_gpu", progress=10)
        return 0
    return 1

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    while True:
        run_once()
        if not args.watch:
            break
        time.sleep(max(1, args.interval))

if __name__ == "__main__":
    main()
