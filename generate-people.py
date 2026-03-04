"""
generate_persons.py
Generates 1,000,000 rows of synthetic person data and stores them
in a local DuckDB database file (persons.duckdb).

Requirements:
    pip install duckdb
"""

import time
import duckdb

DB_FILE = "persons.duckdb"
TABLE_NAME = "persons"
ROW_COUNT = 1_000_000

SQL_CREATE = f"""
CREATE OR REPLACE TABLE {TABLE_NAME} AS
SELECT
    i                                                           AS person_id,
    ROUND(random() * 180.0 - 90.0,  6)::DOUBLE                AS latitude,
    ROUND(random() * 360.0 - 180.0, 6)::DOUBLE                AS longitude,
    CASE WHEN random() < 0.5 THEN 'Male' ELSE 'Female' END     AS sex,
    (1 + (random() * 79)::INT)::TINYINT                        AS age,
    ROUND(10.0 + random() * 65.0, 2)::DOUBLE                   AS microvolts
FROM range(1, {ROW_COUNT + 1}) t(i);
"""

SQL_VERIFY = f"""
SELECT
    COUNT(*)                        AS total_rows,
    COUNT(DISTINCT person_id)       AS unique_ids,
    ROUND(MIN(latitude), 6)         AS min_lat,
    ROUND(MAX(latitude), 6)         AS max_lat,
    ROUND(MIN(longitude), 6)        AS min_lon,
    ROUND(MAX(longitude), 6)        AS max_lon,
    MIN(age)                        AS min_age,
    MAX(age)                        AS max_age,
    ROUND(MIN(microvolts), 2)       AS min_uv,
    ROUND(MAX(microvolts), 2)       AS max_uv
FROM {TABLE_NAME};
"""

SQL_SEX_SPLIT = f"""
SELECT sex, COUNT(*) AS count
FROM {TABLE_NAME}
GROUP BY sex
ORDER BY sex;
"""


def main():
    print(f"Connecting to '{DB_FILE}'...")
    con = duckdb.connect(DB_FILE)

    print(f"Generating {ROW_COUNT:,} rows into table '{TABLE_NAME}'...")
    start = time.perf_counter()
    con.execute(SQL_CREATE)
    elapsed = time.perf_counter() - start
    print(f"Done in {elapsed:.2f}s\n")

    print("--- Verification ---")
    result = con.execute(SQL_VERIFY).fetchdf()
    for col in result.columns:
        print(f"  {col}: {result[col][0]}")

    print("\n--- Sex split ---")
    split = con.execute(SQL_SEX_SPLIT).fetchdf()
    for _, row in split.iterrows():
        print(f"  {row['sex']}: {row['count']:,}")

    con.close()
    print(f"\nDatabase saved to '{DB_FILE}'")


if __name__ == "__main__":
    main()