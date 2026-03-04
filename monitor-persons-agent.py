"""
monitor_persons_agent.py
An AI-powered monitoring agent that uses Claude to analyze the persons table
and surface meaningful insights every 30 seconds.

Requirements:
    pip install anthropic adbc-driver-gizmosql

Environment variables:
    ANTHROPIC_API_KEY  - required
    GIZMOSQL_PASSWORD  - required
    GIZMOSQL_USERNAME  - optional (defaults to scott)
    GIZMOSQL_HOST      - optional (defaults to localhost)
    GIZMOSQL_PORT      - optional (defaults to 31337)
"""

import os
import time
import anthropic
from adbc_driver_gizmosql import dbapi as gizmosql

HOST          = os.getenv("GIZMOSQL_HOST",     "localhost")
PORT          = os.getenv("GIZMOSQL_PORT",     "31337")
USERNAME      = os.getenv("GIZMOSQL_USERNAME", "scott")
PASSWORD      = os.environ["GIZMOSQL_PASSWORD"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

INTERVAL_SECONDS = 30

SYSTEM_PROMPT = """You are a data monitoring agent for a live persons sensor database.

The table 'persons' has these columns:
  - person_id  (integer, 1 to 1,000,000)
  - latitude   (double, geographic coordinate)
  - longitude  (double, geographic coordinate)
  - sex        ('Male' or 'Female')
  - age        (tinyint, 1–120, hard-capped at 120)
  - microvolts (double, live sensor reading, continuously updated)

The data is updated every 30 seconds:
  - A random 1–100 persons have their age incremented by 1 (capped at 120)
  - Those same persons have a random 5.00–19.00 added to their microvolts reading

Use the query_database tool to run SQL queries and surface useful insights such as:
  - Persons with critically high microvolts (> 100)
  - Persons who have hit or are near the age cap of 120
  - Statistical summary (avg, min, max, stddev) of microvolts and age
  - Geographic hotspots of high readings (latitude/longitude clusters)
  - Any anomalies or trends worth flagging

Be concise and actionable. Highlight anything that warrants attention."""

TOOL = {
    "name": "query_database",
    "description": "Run a SQL SELECT query against the persons table in GizmoSQL.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "A SQL SELECT query to execute against the persons table."
            }
        },
        "required": ["sql"]
    }
}


def run_query(conn, sql: str) -> str:
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            df = cur.fetch_arrow_table().to_pandas()
            if df.empty:
                return "Query returned no rows."
            return df.to_string(index=False, max_rows=25)
    except Exception as exc:
        return f"Query error: {exc}"


def run_monitoring_cycle(claude: anthropic.Anthropic, conn, iteration: int) -> str:
    messages = [
        {
            "role": "user",
            "content": (
                f"Monitoring cycle #{iteration}. "
                "Analyze the current state of the persons data and report your findings."
            )
        }
    ]

    while True:
        response = claude.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=[TOOL],
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(
                (block.text for block in response.content if block.type == "text"),
                "(no text in response)"
            )

        if response.stop_reason != "tool_use":
            return f"Unexpected stop reason: {response.stop_reason}"

        # Execute every tool call Claude requested
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                sql = block.input.get("sql", "")
                result = run_query(conn, sql)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


def main():
    uri = f"grpc://{HOST}:{PORT}"
    print(f"Connecting to GizmoSQL at {uri} as '{USERNAME}'...")

    claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    with gizmosql.connect(uri, username=USERNAME, password=PASSWORD) as conn:
        print(f"AI monitoring agent started — analyzing every {INTERVAL_SECONDS}s. Press Ctrl+C to stop.\n")

        iteration = 0
        try:
            while True:
                iteration += 1
                ts = time.strftime("%H:%M:%S")
                print(f"\n{'=' * 60}")
                print(f"[{ts}]  Monitoring cycle #{iteration}")
                print(f"{'=' * 60}")

                report = run_monitoring_cycle(claude, conn, iteration)
                print(report)

                time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nMonitoring agent stopped.")


if __name__ == "__main__":
    main()
