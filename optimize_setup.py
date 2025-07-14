#!/usr/bin/env python3
"""Setup optimization script.

Parses iRacing setup files and basic telemetry data to generate
rule-based setup recommendations.
"""
import argparse
import logging
from pathlib import Path
import duckdb
import pandas as pd
from bs4 import BeautifulSoup
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_setup_htm(htm_path: Path) -> dict:
    """Parse a simple iRacing .htm setup export file.

    Parameters are extracted from tables as key/value pairs.
    """
    params = {}
    try:
        with open(htm_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower().replace(" ", "_")
                    value = cells[1].get_text(strip=True)
                    if key:
                        params[key] = value
    except Exception as exc:
        logger.warning("Failed to parse %s: %s", htm_path, exc)
    return params

def analyze_telemetry(parquet_dir: Path, setup_params: dict, rules_path: Path) -> list:
    """Analyze telemetry Parquet files with simple rule checks."""
    rules = {}
    if rules_path.exists():
        with open(rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            rules = data.get("rules", {})
    recommendations = []
    parquet_files = list(parquet_dir.glob("*.parquet"))
    if not parquet_files:
        logger.warning("No Parquet files found in %s", parquet_dir)
        return recommendations
    con = duckdb.connect()
    df = pd.concat([
        con.execute(f"SELECT * FROM parquet_scan('{p}')").fetchdf()
        for p in parquet_files
    ], ignore_index=True)
    for issue, rule in rules.items():
        mid_corner_df = df[(df.get("Speed", 0) > 50) & (df.get("Steering", 0).abs() > 10)]
        if mid_corner_df.empty:
            continue
        front_slip_avg = (mid_corner_df.get("Slip Angle FL", pd.Series([0])).mean() +
                          mid_corner_df.get("Slip Angle FR", pd.Series([0])).mean()) / 2
        rear_slip_avg = (mid_corner_df.get("Slip Angle RL", pd.Series([0])).mean() +
                         mid_corner_df.get("Slip Angle RR", pd.Series([0])).mean()) / 2
        if front_slip_avg > rear_slip_avg * 1.05:
            for sug in rule.get("setup_suggestions", []):
                current_val = setup_params.get(sug.get("param"), "unknown")
                rec = (
                    f"{issue}: Change {sug.get('param')} from {current_val} "
                    f"to {sug.get('change')}. Reason: {sug.get('reason')} "
                    f"Expected gain: {rule.get('expected_gain','N/A')}"
                )
                recommendations.append(rec)
    con.close()
    return recommendations

def generate_report(recommendations: list, output_path: Path) -> None:
    """Save recommendations to a Markdown report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Setup Optimization Report\n\n")
        if not recommendations:
            f.write("No issues detected. Setup looks good.\n")
            return
        for rec in recommendations:
            f.write(f"- {rec}\n")

def optimize_session(session_path: Path, rules_file: Path) -> None:
    """Run optimization for a given session directory."""
    raw_dir = session_path / "RAW"
    parquet_dir = session_path / "PARQUET"
    reports_dir = session_path / "REPORTS"
    setup_files = list(raw_dir.glob("*.htm"))
    if not setup_files:
        logger.info("No setup file found in %s", raw_dir)
        setup_params = {}
    else:
        setup_params = parse_setup_htm(setup_files[0])
    recs = analyze_telemetry(parquet_dir, setup_params, rules_file)
    generate_report(recs, reports_dir / "optimization_report.md")


def main():
    parser = argparse.ArgumentParser(description="Optimize racing setup")
    parser.add_argument("--session", required=True, help="Path to session dir")
    parser.add_argument("--rules", default="rules.yaml", help="Path to rules file")
    args = parser.parse_args()
    optimize_session(Path(args.session), Path(args.rules))

if __name__ == "__main__":
    main()
