#!/usr/bin/env python3
"""Run telemetry processing and setup analysis in one step."""
import subprocess
from pathlib import Path
import argparse


def run_process_dropoff():
    subprocess.run(["python", "process_dropoff.py"], check=False)


def run_setup_analysis(vehicle: str):
    setup_dir = Path("SimFlowSetupAgent/DROP-OFF/setup_files")
    if not setup_dir.exists():
        print("No setup files directory found.")
        return
    for file in setup_dir.iterdir():
        if file.is_file():
            cmd = [
                "python",
                "SimFlowSetupAgent/simflow_setup_agent.py",
                "analyze",
                "--file",
                str(file),
                "--vehicle",
                vehicle,
                "--session",
                "sprint",
            ]
            subprocess.run(cmd, check=False)


def main():
    parser = argparse.ArgumentParser(
        description="Run telemetry processing and setup analysis in one step"
    )
    parser.add_argument(
        "--vehicle",
        default="gt3",
        help="Vehicle category for setup analysis (default: gt3)",
    )
    args = parser.parse_args()

    run_process_dropoff()
    run_setup_analysis(args.vehicle)


if __name__ == "__main__":
    main()
