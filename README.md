
SimFlowDataBot Optimization Plan Instructions
Overview
This document outlines the plan to enhance the SimFlowDataBot project into a reliable system for generating optimized car setups in sim racing (e.g., iRacing GT3 cars like Acura NSX Evo). The goal is to automate the translation of MoTeC telemetry data (CSVs) and setup files (HTM/PDF) into actionable setup recommendations for faster lap times. The workflow starts by parsing the setup file (HTM) to establish baselines, then analyzes telemetry metrics guided by those baselines, and applies rule-based suggestions to output tweaks.
The system should be simple, Python-only (no Java), and integrated into existing scripts like process_dropoff.py. Focus on reliability: Handle edge cases, log errors, and use configurable rules to avoid brittle AI guesses. This will be the foundation for the “world’s best” setup optimizer.
Key Principles:
	•	Driver-centric: Drop files into DROP-OFF/ → Auto-process → Get reports/new setups in REPORTS/.
	•	Start rules-based; expandable to ML/LLM later.
	•	Target common GT3 issues: Handling balance (under/oversteer), tire management, suspension/dampers.
	•	Use existing directory structure; unify agents (no separate SimFlowSetupAgent).
Requirements
	•	Python Version: 3.10+.
	•	Libraries (add to requirements.txt):
	◦	pandas (data handling).
	◦	duckdb (querying Parquet files).
	◦	beautifulsoup4 (parse HTM).
	◦	pypdf2 (parse PDF MoTeC sheets, if needed).
	◦	pyyaml (load rules config).
	◦	matplotlib (optional: for plots in reports).
	◦	watchdog (for auto-watching DROP-OFF).
	•	No external APIs/ML initially; keep offline.
Workflow Integration
	•	Extend process_dropoff.py to trigger optimization after file conversion/grouping.
	•	New Script: optimize_setup.py (CLI: python optimize_setup.py --session ).
	•	Full Chain: Detect files → Convert CSV to Parquet → Parse setup → Analyze telemetry → Generate recommendations → Save to SESSIONS//REPORTS/.
	•	Add --watch mode using watchdog to auto-run on file drops.
Step 1: Parse Setup File (HTM/PDF)
	•	Input: HTM file from DROP-OFF (e.g., iRacing setup export).
	•	Output: Dict of parameters (e.g., {'front_camber': '-3.5°', 'rear_wing': '5'}).
	•	Implementation:
	◦	Use BeautifulSoup for HTM: from bs4 import BeautifulSoup
	◦	from pathlib import Path
	◦	
	◦	def parse_setup_htm(htm_path: Path) -> dict:
	◦	    with open(htm_path, 'r', encoding='utf-8') as f:
	◦	        soup = BeautifulSoup(f, 'html.parser')
	◦	    params = {}
	◦	    # Extract from tables (adapt to iRacing HTM structure)
	◦	    for table in soup.find_all('table'):
	◦	        for row in table.find_all('tr'):
	◦	            cells = row.find_all('td')
	◦	            if len(cells) >= 2:
	◦	                key = cells[0].text.strip().lower().replace(' ', '_')  # Normalize keys
	◦	                value = cells[1].text.strip()
	◦	                params[key] = value
	◦	    return params
	◦	
	◦	For PDF (MoTeC sheets): Use PyPDF2 to extract text and regex-parse key-value pairs.
	◦	Error Handling: If parse fails, log warning and use default params (e.g., from config). Support multiple setups per session.
	◦	Fallback: If no setup file, prompt user or use generic GT3 defaults.
Step 2: Analyze Telemetry with Setup Context
	•	Input: Parquet files from PARQUET/ + Parsed setup dict.
	•	Output: List of recommendations (e.g., [“Soften front ARB from 3 to 2 clicks”]).
	•	Key MoTeC Channels to Scan (assume standard exports):
	◦	Slip Angle: FL/FR/RL/RR (for under/oversteer).
	◦	Tire Temp: Inner/Mid/Outer per tire.
	◦	Damper Velocity/Position: Per corner (histograms for bump/rebound).
	◦	Ride Height: Front/Rear (aero balance).
	◦	G-Forces: Lateral/Longitudinal.
	◦	Yaw Rate, Steering Angle, Throttle/Brake.
	◦	Filter by sectors (e.g., mid-corner: speed >50kmh, steering >10°).
	•	Rules Config: rules.yaml (expandable): rules:
	•	  understeer:
	•	    telemetry_checks:
	•	      - channel: slip_angle_front_avg  # Compute as (FL + FR)/2
	•	        condition: "> rear_slip_avg + 5%"  # In mid-corner
	•	        severity: high
	•	    setup_suggestions:
	•	      - param: front_arb_stiffness
	•	        change: "soften by 1-2 clicks"
	•	        reason: "Reduce front roll resistance for better turn-in"
	•	      - param: rear_wing_angle
	•	        change: "increase by 1"
	•	        reason: "Add rear downforce for balance"
	•	    expected_gain: "0.1-0.3s/lap"
	•	
	•	  tire_overheat_front:
	•	    telemetry_checks:
	•	      - channel: tire_temp_outer_front_avg
	•	        condition: "> 100°C"
	•	        severity: medium
	•	    setup_suggestions:
	•	      - param: front_camber
	•	        change: "reduce negative by 0.2°"
	•	        reason: "Less camber to even temp spread"
	•	      - param: front_tire_pressure
	•	        change: "increase by 0.2 psi"
	•	        reason: "Higher pressure for reduced flex"
	•	
	•	  # Add more: oversteer, braking instability, damper optimization, etc.
	•	
	•	Implementation: import pandas as pd
	•	import duckdb
	•	import yaml
	•	from pathlib import Path
	•	
	•	def analyze_telemetry(parquet_path: Path, setup_params: dict) -> list:
	•	    # Load data (use DuckDB for efficiency)
	•	    con = duckdb.connect()
	•	    df = con.execute(f"SELECT * FROM parquet_scan('{parquet_path}')").fetchdf()
	•	    
	•	    rules = yaml.safe_load(open('rules.yaml'))['rules']
	•	    recommendations = []
	•	    
	•	    for issue, rule in rules.items():
	•	        # Example: Compute understeer
	•	        mid_corner_df = df[(df['Speed'] > 50) & (abs(df['Steering']) > 10)]  # Adjust column names to MoTeC standards
	•	        front_slip_avg = (mid_corner_df['Slip Angle FL'].mean() + mid_corner_df['Slip Angle FR'].mean()) / 2
	•	        rear_slip_avg = (mid_corner_df['Slip Angle RL'].mean() + mid_corner_df['Slip Angle RR'].mean()) / 2
	•	        
	•	        if front_slip_avg > rear_slip_avg * 1.05:  # Condition match
	•	            for sug in rule['setup_suggestions']:
	•	                current_val = setup_params.get(sug['param'], 'unknown')
	•	                rec = f"{issue.capitalize()}: Change {sug['param']} from {current_val} to {sug['change']}. Reason: {sug['reason']}. Expected gain: {rule['expected_gain']}"
	•	                recommendations.append(rec)
	•	    
	•	    con.close()
	•	    return recommendations
	•	
	•	Enhancements:
	◦	Compute aggregates (means, peaks) per lap/sector.
	◦	Generate plots (e.g., slip angle over time) and save to ASSETS/.
	◦	Log detailed metrics for debugging.
Step 3: Generate Outputs
	•	Report: Markdown file in REPORTS/ (e.g., optimization_report.md):
	◦	Summary of issues.
	◦	List of recommendations.
	◦	Baseline setup vs. suggested.
	◦	Optional: Export new setup file (text diff or .sto template).
	•	Implementation: def generate_report(recommendations: list, output_path: Path):
	•	    with open(output_path, 'w') as f:
	•	        f.write("# Setup Optimization Report\n\n")
	•	        for rec in recommendations:
	•	            f.write(f"- {rec}\n")
	•	
	•	Archiving: Include in ZIP as per existing workflow.
Testing and Edge Cases
	•	Unit Tests: Use pytest. Test parsing with sample HTM, analysis with mock Parquet.
	•	Samples: Include samples/ dir with example HTM/CSV for dev.
	•	Errors: Log to logs/optimize.log. Handle missing channels (fallback metrics), no setup (defaults), malformed files (skip with warning).
	•	Performance: Optimize DuckDB queries for large files.
Next Steps for Programmers
	1	Implement parse_setup_htm and test with real iRacing HTM.
	2	Create rules.yaml with 5-10 initial rules (focus on understeer, oversteer, tires).
	3	Build analyze_telemetry and integrate into optimize_setup.py.
	4	Hook into process_dropoff.py (auto-call after conversion).
	5	Add CLI args (e.g., --vehicle gt3 --session sprint for rule filtering).
	6	Test end-to-end: Drop files → Verify report outputs logical tweaks.
This plan keeps the project lean while delivering value. Expand rules based on testing; aim for 99% reliability. If issues, iterate on rules.yaml.


######################


# SimFlowDataAgent - Racing Data Processing System
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A multi-agent racing data workflow system that processes MoTeC exports, converts to Parquet, and generates reports.

Additional guides are available in the `docs/` directory:
- [User Manual](docs/USER_MANUAL.md)
- [Installation Guide](docs/INSTALLATION.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)

## 🚀 Quick Start

### Manual Processing Mode

When you have new racing data files to process:

1. **Add files** to the `2025-Season3/Car_Folder/DROP-OFF/` directory
2. **Run the processing script**:
   ```bash
   python process_dropoff.py
   ```
3. **Confirm processing** when prompted
4. **Check results** in the generated session directories
5. **Optional combined workflow**:
   ```bash
   python run_full_workflow.py --vehicle gt3
   ```
   This processes telemetry and any setup files in one step. The `--vehicle`
   argument lets you specify a different setup profile when needed.

## 📁 Directory Structure

```
2025-Season3/Car_Folder/
├── DROP-OFF/           # Input directory for new files
├── SESSIONS/           # Processing workspace
│   └── <session_id>/
│       ├── RAW/        # Original files with SHA-256 hashes
│       ├── PARQUET/    # Converted CSV files
│       ├── DB/         # DuckDB database files
│       ├── ASSETS/     # PDF/PNG files
│       └── REPORTS/    # Generated analysis reports
├── ARCHIVE/            # Completed sessions (ZIP files)
└── TOC.md             # Table of contents for all sessions
```

## 🔧 Supported File Types

### Session ID Patterns
- **Standard**: `YYYY-MM-DD_Track_Run` (e.g., `2025-07-04_Silverstone_01`)
- **Alternative**: `car_track_date_stint` (e.g., `acuransxevo22gt3_fuji gp 2025-07-02 17-06-13_Stint`)
- **Fallback**: `untagged_filename` (e.g., `untagged_fuel.csv`)

### File Types
- **CSV Files**: Automatically converted to Parquet format
- **PDF Files**: Moved to ASSETS directory
- **PNG Files**: Moved to ASSETS directory

## 📊 Processing Workflow

1. **File Detection**: Scans DROP-OFF directory for new files
2. **Session Grouping**: Groups files by extracted session ID
3. **Directory Creation**: Creates session workspace structure
4. **File Movement**: Moves files to RAW/ with SHA-256 hashing
5. **Data Conversion**: Converts CSV files to Parquet format
6. **Asset Handling**: Organizes PDF/PNG files
7. **TOC Update**: Updates table of contents
8. **Archiving**: Creates ZIP archive of completed session

## 🛠️ Requirements

- **Java**: For the main processing engine
- **Python 3.x**: For data processing scripts
- **Required Python packages**:
  - `pandas`
  - `duckdb`
  - `pathlib`

The Java watcher uses the `PYTHON_CMD` environment variable to locate the
Python interpreter. If unset, it falls back to `python`. You may also pass the
interpreter path as the first argument when running `DropOffWatcher` directly.

## 💻 Development Setup

To set up the development environment:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/SimFlowDataAgent.git
    cd SimFlowDataAgent
    ```
2.  **Install Java dependencies**:
    ```bash
    ./gradlew build
    ```
3.  **Set up Python virtual environment**:
    ```bash
    python -m venv .venv
    # Activate (Windows CMD)
    .venv\Scripts\activate.bat
    # Activate (Windows PowerShell)
    .venv\Scripts\Activate.ps1
    # Activate (Linux/macOS)
    source .venv/bin/activate
    ```
4.  **Install Python packages** (for both agents):
    ```bash
    # Run this from the repository root
    pip install -r requirements.txt  # includes SimFlowSetupAgent
    ```

## 📝 Example Usage

```bash
# Add your MoTeC export files to DROP-OFF
cp /path/to/motec/exports/* 2025-Season3/Car_Folder/DROP-OFF/

# Process the files
python process_dropoff.py

# Check the results
ls 2025-Season3/Car_Folder/SESSIONS/
cat 2025-Season3/Car_Folder/TOC.md
```

## 🏎️ Setup Optimization with SimFlowSetupAgent

SimFlowSetupAgent is included in this repository to analyze iRacing setup files
and MoTeC setup sheets. Drop your setup files into
`SimFlowSetupAgent/DROP-OFF/setup_files/` (MoTeC sheets go in
`SimFlowSetupAgent/DROP-OFF/motec_sheets/`).

### Running `simflow_setup_agent.py`

Run the analysis script from the repository root:

```bash
python SimFlowSetupAgent/simflow_setup_agent.py analyze --file SimFlowSetupAgent/DROP-OFF/setup_files/MySetup.htm --vehicle gt3 --session sprint
```

Use `--help` to view commands like `compare`, `recommend`, and `table`. Results
are written to `SimFlowSetupAgent/PROCESSED/`.

Setup analysis complements the telemetry workflow handled by `process_dropoff.py`.
After processing telemetry data, copy the setup reports into the matching
`SESSIONS/<session_id>/REPORTS/` directory. Keeping both datasets together lets
you correlate car setup choices with on-track performance.

### Example Combined Workflow

```bash
# Process telemetry data
python process_dropoff.py

# Analyze the associated setup
python SimFlowSetupAgent/simflow_setup_agent.py analyze --file SimFlowSetupAgent/DROP-OFF/setup_files/MySetup.htm --vehicle gt3 --session sprint

# Review results
ls 2025-Season3/Car_Folder/SESSIONS/
ls SimFlowSetupAgent/PROCESSED/by_car/
```

## 🔍 Troubleshooting

### Common Issues
- **No files found**: Ensure files are in the correct DROP-OFF directory
- **Processing failed**: Check that all Python dependencies are installed
- **Session ID errors**: Verify filename follows supported patterns

### Log Output
The processing script provides detailed output showing:
- Files detected for processing
- Session creation and file movement
- Python script execution results
- Final archive creation

## 📈 Future Features

- Analysis script development
- Report template generation
- DuckDB schema optimization
- Performance monitoring dashboard

---
