"""
update_persons_agent.py
Every 30 seconds, picks between 1-100 random persons and:
  - Increments age by 1 (capped at 120)
  - Adds a random value between 5.00 and 19.00 to microvolts

Requirements:
    pip install adbc-driver-gizmosql

Environment variables:
    GIZMOSQL_PASSWORD  - required
    GIZMOSQL_USERNAME  - optional (defaults to gizmosql_user)
    GIZMOSQL_HOST      - optional (defaults to localhost)
    GIZMOSQL_PORT      - optional (defaults to 31337)
"""

import os
import random
import time
from adbc_driver_gizmosql import dbapi as gizmosql

HOST     = os.getenv("GIZMOSQL_HOST",     "localhost")
PORT     = os.getenv("GIZMOSQL_PORT",     "31337")
USERNAME = os.getenv("GIZMOSQL_USERNAME", "scott")
PASSWORD = os.environ["GIZMOSQL_PASSWORD"]

INTERVAL_SECONDS = 30


def run_update(cur) -> int:
    count = random.randint(1, 100)

    cur.execute(f"""
        UPDATE persons
        SET
            age        = LEAST(age + 1, 120),
            microvolts = LEAST(ROUND(microvolts + 5.0 + random() * 14.0, 2), 100.0)
        WHERE person_id IN (
            SELECT person_id
            FROM persons
            USING SAMPLE {count} ROWS
        )
    """)

    return count


def main():
    uri = f"grpc://{HOST}:{PORT}"
    print(f"Connecting to {uri} as '{USERNAME}'...")

    with gizmosql.connect(uri, username=USERNAME, password=PASSWORD) as conn:
        print(f"Agent started — updating every {INTERVAL_SECONDS}s. Press Ctrl+C to stop.\n")

        iteration = 0
        try:
            while True:
                iteration += 1
                with conn.cursor() as cur:
                    updated = run_update(cur)
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] Iteration {iteration}: updated {updated} record(s)")
                time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nAgent stopped.")


if __name__ == "__main__":
    main()