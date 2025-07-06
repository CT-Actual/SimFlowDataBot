# Analysis Guide

This guide provides an overview of the telemetry analysis system.

## Running Analysis on Existing Sessions
After `process_dropoff.py` has created sessions, you can run advanced analysis scripts on the stored Parquet files. Example:
```bash
python scripts/analyze_session.py --session 2025-07-04_TestTrack_01
```
The output Markdown and JSON reports are written to `SESSIONS/<Session_ID>/REPORTS/`.

## KPI Reference
Key metrics computed by the analysis system include:
- Best lap time and average lap time
- Consistency index
- Fuel consumption
- Tire temperature trends
- Aerodynamic efficiency

See `ANALYSIS_IMPLEMENTATION_PLAN.md` for a full list of planned metrics.

## Visualization
Charts can be produced using the optional MCP chart server. Configure `cline_mcp_settings.json` and run:
```bash
node mcp-server.js
```
Generated images are stored in the session `ASSETS/` directory.
