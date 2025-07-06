# SimFlowDataAgent User Manual

This manual explains how to process telemetry files and analyze setups using the two agents in this repository.

## 1. Prerequisites
- Python 3.8+
- Java 17+
- Optional: `file` command to inspect files
- Install dependencies from the repository root:
  ```bash
  pip install -r requirements.txt
  ```

## 2. Folder Layout
```
2025-Season3/Car_Folder/
├── DROP-OFF/        # place new MoTeC exports here
├── SESSIONS/        # created automatically for each session
└── TOC.md           # index of processed sessions
```

Setup files for `SimFlowSetupAgent` go in:
```
SimFlowSetupAgent/DROP-OFF/setup_files/
SimFlowSetupAgent/DROP-OFF/motec_sheets/
```

## 3. Processing Telemetry
1. Copy your MoTeC CSV/PDF/PNG files into `DROP-OFF/`.
2. Run the processing script:
   ```bash
   python process_dropoff.py
   ```
3. Confirm when prompted. The watcher moves files into `SESSIONS/<Session_ID>/` and converts CSV data to Parquet.
4. Reports and archives are placed inside each session directory.

## 4. Analyzing Setups
1. Add setup files to `SimFlowSetupAgent/DROP-OFF/setup_files/`.
2. Run the setup analysis command:
   ```bash
   python SimFlowSetupAgent/simflow_setup_agent.py analyze --file SimFlowSetupAgent/DROP-OFF/setup_files/MySetup.htm --vehicle gt3 --session sprint
   ```
3. Results are saved in `SimFlowSetupAgent/PROCESSED/`.
4. Move the generated reports into the corresponding `SESSIONS/<Session_ID>/REPORTS/` folder to keep telemetry and setup data together.

## 5. Combined Workflow
For convenience you can run both agents sequentially:
```bash
python run_full_workflow.py --vehicle gt3
```
This processes any files in `DROP-OFF/` and then analyzes all setup files waiting in `SimFlowSetupAgent/DROP-OFF/setup_files/`. Pass `--vehicle` to select a different setup profile when needed.

## 6. Troubleshooting
- **No files processed**: Ensure the `DROP-OFF/` directory exists and contains files.
- **Java compilation errors**: Check that JDK 17+ is installed.
- **Setup analysis fails**: Verify the vehicle profile is present and the file format is supported.

---
This user manual is a starting point. See `docs/ANALYSIS_GUIDE.md` and `docs/DEVELOPER_GUIDE.md` for advanced usage.
