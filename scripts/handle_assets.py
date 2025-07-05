#!/usr/bin/env python3
"""
Copy a PDF/PNG chart into ASSETS/ and register it in DuckDB.

Usage:
    handle_assets.py <asset_path> <session_id>
"""
import shutil, sys, pathlib, duckdb

src         = pathlib.Path(sys.argv[1]).resolve()
session_id  = sys.argv[2]
session_dir = src.parents[2]                      # adjust if layout changes
assets_dir  = session_dir / "ASSETS"
assets_dir.mkdir(exist_ok=True)

dst = assets_dir / src.name
shutil.copy2(src, dst)

# register in artifact_catalog
db_path = session_dir / "DB" / "session.duckdb"
con = duckdb.connect(str(db_path))
con.execute("""
CREATE TABLE IF NOT EXISTS artifact_catalog (
  session_id TEXT,
  file_name  TEXT,
  rel_path   TEXT
);
""")
con.execute("INSERT INTO artifact_catalog VALUES (?, ?, ?)",
            (session_id, dst.name, str(dst.relative_to(session_dir))))

print(f"[handle_assets] {src.name} → {dst}")
