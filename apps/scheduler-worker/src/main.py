# OldClaw Scheduler Worker
# Periodically checks `schedules` table and enqueues job runs.

import time
from fastapi import FastAPI

app = FastAPI(title="Scheduler Worker")

@app.get("/health")
async def health_check():
    return {"status": "scheduler ok"}

def poll_schedules():
    # TODO: query DB for due schedules and create JobRun entries
    raise NotImplementedError("poll_schedules not implemented in M0 – DB integration pending")

def main():
    while True:
        poll_schedules()
        time.sleep(60)  # run every minute

if __name__ == "__main__":
    main()

