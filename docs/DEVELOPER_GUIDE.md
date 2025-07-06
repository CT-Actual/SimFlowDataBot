# SimFlowDataAgent Developer Guide

This document describes the code structure and how to extend the analysis system.

## Repository Layout
- `process_dropoff.py` – Main script that invokes the Java watcher and handles file processing.
- `src/` – Java sources for the DropOffWatcher and helper classes.
- `scripts/` – Python modules for ingesting CSVs, updating the TOC, and archiving assets.
- `SimFlowSetupAgent/` – Separate agent for setup analysis.
- `2025-Season3/<Car_Folder>/` – Example season directory used during development.

## Running Tests
Unit tests will be added under `tests/`. Use `pytest` to run all tests:
```bash
pytest
```

## Extending Analysis
New KPIs or metrics can be implemented inside `scripts/analysis/` (see `ANALYSIS_IMPLEMENTATION_PLAN.md`). Add functions to compute the metric and update the report generator.

## Adding New Vehicle Profiles
Place additional JSON profiles in `SimFlowSetupAgent/vehicle_profiles/`. Follow the existing structure and include parameter ranges and telemetry channels.

## Contributing
1. Fork the repository and create a feature branch.
2. Add or modify code with tests.
3. Open a pull request describing your changes.
