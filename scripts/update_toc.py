#!/usr/bin/env python3
"""
Append or update a row in TOC.md for the given session.

Usage:
    update_toc.py <session_id> <car_root>
"""
import pandas as pd, sys, pathlib, datetime as dt, duckdb

session_id, car_root = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
toc_path = car_root / "TOC.md"

def load_toc(path):
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=[
            "Session ID","Date","Track","Run","Laps","Fast Lap","Notes"])
    try:
        df = pd.read_table(path, sep="|", skiprows=2)
        # Drop any unnamed columns and empty columns
        cols_to_drop = [col for col in df.columns if 
                       col.strip() == "" or 
                       col.startswith("Unnamed:") or 
                       col == " " or
                       str(col).strip() == "nan"]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        return df.rename(str.strip, axis=1)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=[
            "Session ID","Date","Track","Run","Laps","Fast Lap","Notes"])

df = load_toc(toc_path)

# Handle different session ID formats
parts = session_id.split("_")
if len(parts) >= 3:
    # Standard format: YYYY-MM-DD_Track_Run
    date, track, run = parts[0], parts[1], parts[2]
elif session_id == "untagged_session":
    # Grouped untagged session
    date, track, run = "untagged", "mixed", "01"
elif session_id.startswith("untagged_"):
    # Other untagged format: untagged_filename
    date, track, run = "untagged", parts[1] if len(parts) > 1 else "unknown", "01"
else:
    # Fallback for other formats
    date, track, run = "unknown", session_id, "01"

session_dir = car_root / "SESSIONS" / session_id
db_file = session_dir / "DB" / "session.duckdb"
laps = 0
fast_lap = "--"
if db_file.exists():
    try:
        con = duckdb.connect(str(db_file))
        laps = con.execute("SELECT COUNT(*) FROM laps").fetchone()[0]
        row = con.execute(
            "SELECT MIN(total_lap_time) FROM laps WHERE total_lap_time IS NOT NULL"
        ).fetchone()
        if row and row[0] is not None:
            fast_lap = f"{row[0]:.3f}s"
        con.close()
    except Exception as e:
        print(f"[update_toc] DuckDB query failed: {e}")
else:
    print(f"[update_toc] DB not found: {db_file}")

meta = {
    "Session ID": session_id,
    "Date"      : date,
    "Track"     : track,
    "Run"       : run,
    "Laps"      : laps,
    "Fast Lap"  : fast_lap,
    "Notes"     : ""
}

df = df[df["Session ID"] != session_id]     # remove stale row
df = pd.concat([df, pd.DataFrame([meta])], ignore_index=True)

header = f"# TOC  (updated {dt.date.today()})\n\n"
table  = df.to_markdown(index=False)
toc_path.write_text(header + table + "\n")

print(f"[update_toc] wrote {toc_path}")
