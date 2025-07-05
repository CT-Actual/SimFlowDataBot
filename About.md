# Analyst‑Agent Design Charter

> Last updated: 2025‑07‑04
> Project root: **\<Season\_Folder> / \<Car\_Folder>**
> *(example: **`2025‑Season3 / BMW_M4_GT4`**)*

---

## 1 — North‑Star Goal

| Item                  | Decision                                                                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Mission**           | Ingest MoTeC telemetry & exports → produce machine‑readable KPIs + human‑readable analysis for the **Setup‑Engineer** and **Driver‑Profile** agents |
| **Core outputs**      | `analysis_<session>.md`, `channels_<session>.json`, `driver_profile_patch_<session>.json`                                                           |
| **Turn‑around**       | ≤ 2 min for ≤ 200 MB per session; batch mode for larger                                                                                             |
| **Context retention** | Derived features cached as Parquet + DuckDB; raw CSV never re‑parsed                                                                                |

---

## 2 — Folder Hierarchy

```text
<Season_Folder>/
└── <Car_Folder>/
    ├── DROP-OFF/                  ← watcher inbox
    ├── SESSIONS/
    │   ├── <Session_ID>/          ← e.g. 2025-07-04_<Track_Name>_01
    │   │   ├── RAW/
    │   │   ├── PARQUET/
    │   │   ├── DB/
    │   │   ├── FEATURES/
    │   │   ├── ASSETS/
    │   │   └── REPORTS/
    │   └── …
    └── TOC.md                     ← auto‑generated index
```

### Session‑ID Grammar

```
<YYYY-MM-DD>_<Track_Name>_<RunTag>
# <RunTag> auto‑increments 01, 02, … unless a slug is provided.
```

---

## 3 — Data‑Lifecycle Pipeline

1. **Watch** `DROP-OFF/` → debounce 10 s.
2. **Create session folder** ➜ `SESSIONS/<Session_ID>/RAW/`.
3. **Intake & move** originals; SHA‑256 logged.
4. **Convert & load** CSV → Parquet; loaders fill `histogram_bins`, `lap_section_times`, `aero_map`; PDFs copied to `ASSETS/` & registered in `artifact_catalog`.
5. **Analyse** via Python DuckDB notebook; write KPIs & charts.
6. **Emit reports** to `REPORTS/`.
7. \*\*Update \*\*\`\` at car root.
8. **Archive assets** once reports marked *final*.
9. **Cleanup** inbox; leave `.done` marker.

---

## 4 — Logical Schema (Parquet + DuckDB)

### Core Tables

* `sessions`  — one row per session.
* `laps`  — per‑lap metadata & KPIs.
* `channel_samples`  — tall time‑series (`session_id`, `lap_num`, `ts_ms`, `channel_name`, `value`).
* `channel_catalog`  — units, descriptions, enum types, deprecation info.

### Extra Exports

| Table               | Purpose                                    |
| ------------------- | ------------------------------------------ |
| `histogram_bins`    | Damper/velocity etc. distribution bins     |
| `lap_section_times` | Per‑lap ΔT for named track sections        |
| `aero_map`          | Front/rear ride height × speed → aero load |
| `artifact_catalog`  | PDFs/PNGs linked to session                |

---

## 5 — Agent Components

| Layer            | Tech                                                                      |
| ---------------- | ------------------------------------------------------------------------- |
| **Orchestrator** | Java (FS watcher, job queue, folder ops)                                  |
| **Workers**      | Stateless Python pods (DuckDB, Pandas, Matplotlib, Pandoc)                |
| **Storage**      | Local Parquet + DuckDB; optional MotherDuck/Iceberg for cloud concurrency |

---

## 6 — TOC.md Specification

* Regenerated after each ingest.
* Columns: `Session ID`, `Date`, `Track`, `Run`, `Laps`, `Fast Lap`, `Notes`.
* Markdown table (diff‑friendly); sample:

```markdown
| Session ID                   | Date       | Track      | Run | Laps | Fast Lap | Notes           |
|------------------------------|------------|------------|-----|------|----------|-----------------|
| 2025-07-04_Fuji_01           | 2025-07-04 | Fuji       | 01  | 18   | 1:28.562 | Baseline setup  |
| 2025-07-04_Fuji_02           | 2025-07-04 | Fuji       | 02  | 20   | 1:27.944 | Damper tweak A  |
```

(Values above are illustrative.)

---

## 7 — Assets Retention

* Archive `ASSETS/` once reports are final → `ARCHIVE/<Season_Folder>/<Car_Folder>/<Session_ID>-assets.zip`.
* Leave stub `ASSETS/README.txt` with archive path.

---

## 8 — Implementation Sprint 01 Checklist

| # | Task                                       | Done when…                                         |
| - | ------------------------------------------ | -------------------------------------------------- |
| 1 | Java DROP-OFF watcher                      | Creates `SESSIONS/<Session_ID>/RAW/` automatically |
| 2 | CSV→Parquet converter (DuckDB)             | File lands in `PARQUET/` partitioned correctly     |
| 3 | Loaders for histogram & lap‑section tables | Row counts visible in DuckDB                       |
| 4 | Minimal analysis notebook                  | `analysis.md` + chart PNG in REPORTS/              |
| 5 | TOC.md generator                           | New row appended/updated                           |
| 6 | Asset archiver stub                        | Assets zipped & README left                        |

---

## 9 — Open Item

* **Driver‑Profile KPI list** → *TBD*: provide ranked metrics to finalise JSON schema.

---

## 10 — Starter Code Snippets

Below are minimal but working code fragments you can paste straight into a new repo.  They are **proof‑of‑concept level**: no error‑handling, logging, or dependency injection—add those as you harden the pipeline.

### 10.1 Java — DROP‑OFF Watcher Skeleton

```java
import java.io.IOException;
import java.nio.file.*;
import static java.nio.file.StandardWatchEventKinds.*;

public class DropOffWatcher implements Runnable {
    private final Path dropOffDir = Paths.get("DROP-OFF");
    private final int debounceMillis = 2_000;   // 2 s
    private final int bundleWindowMillis = 30_000; // 30 s

    @Override
    public void run() {
        try (WatchService ws = FileSystems.getDefault().newWatchService()) {
            dropOffDir.register(ws, ENTRY_CREATE);
            while (true) {
                WatchKey key = ws.take();
                key.pollEvents();
                key.reset();
                Thread.sleep(debounceMillis);
                processBundles();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void processBundles() throws IOException {
        // 1) Group files by <Session_ID>
        // 2) If last‑modified for a group > bundleWindowMillis ago, move to RAW/
        // 3) Spawn Python ingest via ProcessBuilder or message queue
    }
}
```

### 10.2 Java — SHA‑256 Helper

```java
public static String sha256(Path file) throws IOException, NoSuchAlgorithmException {
    MessageDigest md = MessageDigest.getInstance("SHA-256");
    try (InputStream in = Files.newInputStream(file); DigestInputStream dis = new DigestInputStream(in, md)) {
        byte[] buffer = new byte[8192];
        while (dis.read(buffer) != -1) { /* stream */ }
    }
    return HexFormat.of().formatHex(md.digest());
}
```

### 10.3 Python — `ingest_csv.py` (CSV → Parquet)

```python
#!/usr/bin/env python3
import duckdb, sys, pathlib, argparse

parser = argparse.ArgumentParser()
parser.add_argument("csv", type=pathlib.Path)
parser.add_argument("session", help="session_id")
args = parser.parse_args()

csv_path = args.csv
session = args.session
parquet_dir = csv_path.parents[2] / "PARQUET"  # ../../PARQUET
parquet_dir.mkdir(exist_ok=True)
parquet_file = parquet_dir / (csv_path.stem + ".parquet")

db = duckdb.connect(str((csv_path.parents[2] / "DB" / "session.duckdb")))

db.execute(f"""
COPY (
  SELECT * FROM read_csv_auto('{csv_path}', HEADER=TRUE, AUTO_DETECT=TRUE)
) TO '{parquet_file}' (FORMAT PARQUET, COMPRESSION ZSTD);
""")

print("Converted", csv_path.name, "→", parquet_file.name)
```

### 10.4 Python — `update_toc.py`

```python
import pandas as pd, pathlib, sys, datetime as dt

session_id = sys.argv[1]
session_dir = pathlib.Path(sys.argv[2])  # e.g. …/SESSIONS/<ID>
car_root = session_dir.parents[1]

toc_path = car_root / "TOC.md"

# --- gather minimal metadata ---
meta = {
    "Session ID": session_id,
    "Date": session_id.split("_")[0],
    "Track": session_id.split("_")[1],
    "Run": session_id.split("_")[2],
    "Laps": 0,          # TODO: query DuckDB laps table
    "Fast Lap": "--",  # TODO: query laps table
    "Notes": ""         # optional
}

df = pd.DataFrame([meta])
if toc_path.exists():
    orig = pd.read_table(toc_path, sep="|", skiprows=2).drop(columns=[" "]).rename(str.strip, axis=1)
    df = pd.concat([orig, df]).drop_duplicates(["Session ID"], keep="last")

toc_markdown = "| " + " | ".join(df.columns) + " |
|" + "|".join(["-"*len(c) for c in df.columns]) + "|
" + df.to_markdown(index=False)

with open(toc_path, "w") as f:
    f.write("# TOC

" + toc_markdown)
```

### 10.5 Python — Asset Copier Stub

```python
import shutil, sys, pathlib

src = pathlib.Path(sys.argv[1])  # path to PDF/PNG
session_dir = src.parents[2]
assets_dir = session_dir / "ASSETS"
assets_dir.mkdir(exist_ok=True)

dst = assets_dir / src.name
shutil.copy2(src, dst)
# TODO: insert row into DuckDB artifact_catalog
```

---

## 11 — Storage Backend Variants (DuckDB / MotherDuck / other MCP)

| Option                                   | When to use                                                      | Pros                                   | Caveats                                                   |
| ---------------------------------------- | ---------------------------------------------------------------- | -------------------------------------- | --------------------------------------------------------- |
| **Embedded DuckDB** (default)            | Single‑machine workflows; ≤ \~200 GB season data                 | Zero setup, blazing fast local queries | Limited concurrency; local disk I/O only                  |
| **MotherDuck Cloud**                     | Need shared SQL workspace; want snapshot backups; bursty compute | Same SQL, 100 × scale, managed backups | Requires MD account & API key; egress fees for large data |
| **DuckDB + Iceberg**                     | Multi‑writer concurrency; seasons spanning TBs                   | ACID table versioning; open format     | Operational overhead (Iceberg catalog, object store)      |
| **External MPP (e.g. BigQuery, Athena)** | Cross‑team analytics or ML on > TB telemetry                     | Serverless scaling, BI integration     | Latency & cost; extra ETL step                            |

**Agent toggle**  – Set environment variable `MCP_TARGET`:

```text
# local (default)
MCP_TARGET=duckdb

# use MotherDuck cloud (requires $MOTHERDUCK_TOKEN)
MCP_TARGET=motherduck
```

The orchestrator passes the target to worker pods, which call

```python
duckdb.connect("md:?motherduck_token=…")
```

when `MCP_TARGET=="motherduck"` and a standard file path otherwise.

> For Sprint 01 we implement **embedded DuckDB** only. Adding MotherDuck support is a small patch: swap the connection string + ensure Parquet lives in an S3 bucket accessible to MD.

---

## 12 — Initial System Prompt (for CLI / VS Code)

*(unchanged)*  — Initial System Prompt (for CLI / VS Code)

```text
You are **Analyst‑Agent** in a multi‑agent racing workflow.  Your job:
1. Watch a DROP‑OFF folder...
```

---

## DROP‑OFF Folder Monitoring Clarifications — Initial System Prompt (for CLI / VS Code)

*(unchanged)*  — Initial System Prompt (for CLI / VS Code)

> Paste the following block into your ChatGPT‑CLI **system prompt** field (or the `--system` flag) so every REPL interaction stays aligned with this design.

```text
You are **Analyst‑Agent** in a multi‑agent racing workflow.  Your job:
1. Watch a DROP‑OFF folder, create a new session workspace using the pattern <YYYY‑MM‑DD>_<Track_Name>_<RunTag>.
2. Move raw MoTeC exports into RAW/, hash them, log intake.
3. Convert every CSV to Parquet and load specialised exports (histogram, lap section, aero map) into DuckDB tables.
4. Run analysis scripts: compute KPIs, generate charts, write Markdown & JSON reports into REPORTS/.
5. Update the car‑level TOC.md table.
6. Zip ASSETS/ into ARCHIVE/ when reports are final.
Follow DRY principles, never re‑parse CSVs if Parquet exists.  Use the project root **<Season_Folder>/<Car_Folder>** provided by the user.  Assume helper Python pods exist for heavy data work.
```

---

*End of document*

---

## DROP‑OFF Folder Monitoring Clarifications

### 1 — Watcher Mechanism

* **Primary**: OS file‑system events via Java `WatchService` (inotify / ReadDirectoryChanges).
* **Fallback**: poll the `DROP‑OFF/` directory every **5 s** if events are unsupported.
* **Debounce**: wait **2 s** after the first create event to avoid half‑written files.
* **Bundle window**: treat all files with the same `<Session_ID>` that arrive within **30 s** as one bundle.

### 2 — Expected Raw File Extensions

| Extension      | Description                                                     | Ingest action                                      |
| -------------- | --------------------------------------------------------------- | -------------------------------------------------- |
| `.csv`         | MoTeC channel logs, histograms, aero maps, track‑section tables | Convert → Parquet then load tables                 |
| `.ld`, `.ldx`  | Native iRacing binary logs (future feature)                     | Currently **ignored** with warning                 |
| `.pdf`, `.png` | MoTeC‑exported charts                                           | Copy to `ASSETS/` → register in `artifact_catalog` |
| `.txt`, `.md`  | Driver notes, manifests                                         | Store raw; surface in reports                      |
| `.zip`         | Optional bundled drop                                           | Unzip to temp → process contents                   |

### 3 — Filename Grammar

```
<YYYY-MM-DD>_<Track_Name>_<RunTag>_<ExportType>.<ext>
```

*Example parses*

| Filename                                      | Track\_Name | RunTag  | Session\_ID                 |
| --------------------------------------------- | ----------- | ------- | --------------------------- |
| `2025-07-04_Fuji_01_Suspension Histogram.csv` | Fuji        | 01      | 2025‑07‑04\_Fuji\_01        |
| `2025-07-04_Fuji_WetTest_Time Report.csv`     | Fuji        | WetTest | 2025‑07‑04\_Fuji\_WetTest   |
| `2025-07-04_RedBullRing_03_rideheights.csv`   | RedBullRing | 03      | 2025‑07‑04\_RedBullRing\_03 |

If a file lacks a `RunTag`, the watcher assigns the next numeric tag (`01`, `02`, …) for that date/track.

### 4 — Workflow Summary

1. **Watcher triggers** on new file → debounce 2 s.
2. **Group** files by `<Session_ID>`; start ingest when no new file for that session arrives within 30 s.
3. **Move** originals to `SESSIONS/<Session_ID>/RAW/`.
4. **Convert / load / analyse** according to the pipeline in §2.
5. **Emit** reports, update **TOC.md**, archive assets if marked final.

---

## Sprint 01 — Ingestion & Session Management

> **Goal**: Implement the Java watcher, CSV→Parquet pipeline, and scaffolding for TOC & asset handling.

| Task ID  | Component                       | Deliverable                                                                                                         |
| -------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **S1‑1** | Java **DROP‑OFF watcher**       | `WatcherService` class with debounce + bundle window; moves files to `SESSIONS/<Session_ID>/RAW/` and logs SHA‑256. |
| **S1‑2** | Session‑ID logic                | Helper `SessionIdBuilder` that auto‑increments numeric RunTag (`01`, `02`, …) when missing.                         |
| **S1‑3** | Python **CSV→Parquet loader**   | Script `ingest_csv.py` that calls DuckDB `COPY … TO` and fills `histogram_bins`, `lap_section_times`, `aero_map`.   |
| **S1‑4** | **TOC.md generator** (stub)     | Function `update_toc()` that appends/updates row in `TOC.md` with placeholder lap counts.                           |
| **S1‑5** | **Asset copier & catalog stub** | Script `handle_assets.py` to copy PDFs/PNGs → `ASSETS/` and add row to DuckDB `artifact_catalog`.                   |
| **S1‑6** | **Archive stub**                | Shell/Python function `archive_assets()` that zips `ASSETS/` after reports marked “final”.                          |

**Sprint exit‑criteria**

* A dummy bundle in `DROP‑OFF/` produces a fully populated `SESSIONS/<Session_ID>/` tree with RAW & PARQUET sub‑dirs and an updated `TOC.md`.
* SHA‑256 hashes logged; `.done` marker appears in `DROP‑OFF/`.
* Stubs for asset handling & archiving run without error (no‑op if no PDFs/PNGs).
