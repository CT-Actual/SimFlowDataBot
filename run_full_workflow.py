#!/usr/bin/env python3
"""Run telemetry processing and setup analysis in one step."""
import subprocess
from pathlib import Path


def run_process_dropoff():
    subprocess.run(["python", "process_dropoff.py"], check=False)


def run_setup_analysis():
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
                "gt3",
                "--session",
                "sprint",
            ]
            subprocess.run(cmd, check=False)


def main():
    run_process_dropoff()
    run_setup_analysis()


if __name__ == "__main__":
    main()
