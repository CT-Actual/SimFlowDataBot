#!/usr/bin/env python3
"""
Convert a MoTeC CSV to Parquet and register it in DuckDB.

Usage:
    ingest_csv.py <csv_path> <session_id>
"""
import duckdb, sys, pathlib

csv_path   = pathlib.Path(sys.argv[1]).resolve()
session_id = sys.argv[2]

session_dir = csv_path.parents[2]           # …/SESSIONS/<id>/RAW/…
parquet_dir = session_dir / "PARQUET"
parquet_dir.mkdir(exist_ok=True)
parquet_file = parquet_dir / (csv_path.stem + ".parquet")

db_path = session_dir / "DB" / "session.duckdb"
db_path.parent.mkdir(exist_ok=True)
con = duckdb.connect(str(db_path))

try:
    con.execute(f"""
    COPY (
      SELECT *, '{session_id}' AS session_id
      FROM read_csv_auto('{csv_path}', HEADER=TRUE, AUTO_DETECT=TRUE)
    ) TO '{parquet_file}' (FORMAT PARQUET, COMPRESSION ZSTD);
    """)
except Exception as e:
    # Try with relaxed parsing for problematic files
    try:
        con.execute(f"""
        COPY (
          SELECT *, '{session_id}' AS session_id
          FROM read_csv_auto('{csv_path}', HEADER=TRUE, AUTO_DETECT=TRUE, IGNORE_ERRORS=TRUE, NULL_PADDING=TRUE)
        ) TO '{parquet_file}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """)
    except Exception as e2:
        # Final fallback with manual delimiter
        con.execute(f"""
        COPY (
          SELECT *, '{session_id}' AS session_id
          FROM read_csv_auto('{csv_path}', HEADER=TRUE, DELIM=',', QUOTE='"', IGNORE_ERRORS=TRUE, NULL_PADDING=TRUE)
        ) TO '{parquet_file}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """)

print(f"[ingest_csv] {csv_path.name} → {parquet_file.name}")
