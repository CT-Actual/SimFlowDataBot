"""
Main Session Analysis Script

Orchestrates the complete analysis workflow for a racing session.
"""

import sys
import os
from pathlib import Path
import argparse
from typing import Optional

# Add the analysis package to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'analysis'))

from analysis.data_parser import DataParser
from analysis.lap_analyzer import LapAnalyzer
from analysis.kpi_calculator import KPICalculator
from analysis.report_generator import ReportGenerator
from analysis.visualizer import Visualizer
from analysis.telemetry_analyzer import TelemetryAnalyzer


def analyze_session(session_path: str, output_dir: Optional[str] = None) -> bool:
    """
    Perform complete analysis of a racing session.
    
    Args:
        session_path: Path to session directory
        output_dir: Optional custom output directory (defaults to session/REPORTS)
        
    Returns:
        True if analysis completed successfully, False otherwise
    """
    try:
        session_path = Path(session_path)
        session_id = session_path.name
        
        print(f"🏁 Starting analysis for session: {session_id}")
        print(f"📁 Session path: {session_path}")
        
        # Set output directory
        if output_dir:
            reports_dir = Path(output_dir)
        else:
            reports_dir = session_path / "REPORTS"
        
        reports_dir.mkdir(parents=True, exist_ok=True)
        print(f"📊 Reports will be saved to: {reports_dir}")
        
        # Initialize visualizer
        visualizer = Visualizer(str(session_path))

        # Step 1: Parse data
        print("\n🔍 Step 1: Parsing session data...")
        # Determine the base parquet path for shared files
        # The shared PARQUET directory is one level up from the session directory, within SESSIONS/
        base_parquet_path = session_path.parent / "PARQUET"
        parser = DataParser(str(session_path), base_parquet_path=str(base_parquet_path))
        
        # Get session metadata
        metadata = parser.get_session_metadata()
        print(f"   Track: {metadata.get('track', 'Unknown')}")
        print(f"   Vehicle: {metadata.get('vehicle', 'Unknown')}")
        print(f"   Driver: {metadata.get('driver', 'Unknown')}")
        
        # Parse lap time data
        lap_data = parser.parse_lap_times()
        if lap_data is None or lap_data.empty:
            print("   ❌ No valid lap time data found")
            return False
        
        print(f"   ✅ Found {len(lap_data)} laps")
        
        # Parse vehicle data (optional)
        vehicle_data = parser.parse_vehicle_data()
        vehicle_files_found = sum(1 for v in vehicle_data.values() if v is not None)
        print(f"   ✅ Found {vehicle_files_found} vehicle data files")
        
        # Step 2.5: Analyze advanced telemetry if available
        print("\n📡 Step 2.5: Analyzing advanced telemetry...")
        telemetry_data = parser.parse_telemetry_data() # Get telemetry data explicitly
        advanced_telemetry_kpis = {}
        if telemetry_data is not None and not telemetry_data.empty:
            telemetry_analyzer = TelemetryAnalyzer(telemetry_data)
            advanced_telemetry_kpis = telemetry_analyzer.get_advanced_telemetry_kpis()
            print("   ✅ Advanced telemetry analysis complete.")
        else:
            print("   Skipping advanced telemetry analysis: No driver input data found.")

        # Step 2: Analyze laps
        print("\n📈 Step 2: Analyzing lap performance...")
        lap_analyzer = LapAnalyzer(lap_data)
        lap_summary = lap_analyzer.get_lap_summary()
        
        print(f"   Best lap: {lap_summary.get('best_lap_time', 0):.3f}s")
        print(f"   Average lap: {lap_summary.get('average_lap_time', 0):.3f}s")
        print(f"   Consistency: {lap_summary.get('consistency_index', 0):.4f}")
        print(f"   Valid laps: {lap_summary.get('valid_laps', 0)}")
        
        # Step 3: Generate charts
        print("\n📊 Step 3: Generating charts...")
        visualizer.plot_lap_times(lap_data)
        print("   ✅ Lap time progression chart generated.")

        # Step 4: Calculate KPIs
        print("\n🎯 Step 4: Computing performance KPIs...")
        kpi_calculator = KPICalculator(metadata)
        kpis = kpi_calculator.calculate_session_kpis(lap_summary, vehicle_data, advanced_telemetry_kpis)
        
        performance_grade = kpis.get('performance_summary', {}).get('performance_grade', 'N/A')
        overall_rating = kpis.get('session_rating', {}).get('overall_rating', 0)
        print(f"   Overall grade: {performance_grade} ({overall_rating}/100)")
        
        consistency_rating = kpis.get('consistency_metrics', {}).get('consistency_rating', 'N/A')
        print(f"   Consistency: {consistency_rating}")
        
        # Step 5: Generate reports
        print("\n📝 Step 5: Generating reports...")
        report_generator = ReportGenerator(session_id, str(reports_dir))
        report_paths = report_generator.generate_comprehensive_report(kpis, lap_data)
        
        # Generate session README
        readme_path = report_generator.generate_session_readme(kpis, report_paths)
        if readme_path:
            report_paths['readme'] = readme_path
        
        print("   ✅ Generated reports:")
        for report_type, path in report_paths.items():
            print(f"      {report_type}: {Path(path).name}")
        
        # Step 6: Export KPIs to JSON for external tools
        json_kpi_path = reports_dir / f"{session_id}_kpis.json"
        if kpi_calculator.export_kpis_to_json(kpis, str(json_kpi_path)):
            print(f"   ✅ Exported KPIs to: {json_kpi_path.name}")
        
        print(f"\n🎉 Analysis completed successfully!")
        print(f"📊 View reports in: {reports_dir}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_multiple_sessions(sessions_dir: str, pattern: str = "*") -> int:
    """
    Analyze multiple sessions in a directory.
    
    Args:
        sessions_dir: Directory containing session folders
        pattern: Pattern to match session directories
        
    Returns:
        Number of sessions successfully analyzed
    """
    sessions_path = Path(sessions_dir)
    
    if not sessions_path.exists():
        print(f"❌ Sessions directory not found: {sessions_path}")
        return 0
    
    # Find session directories
    session_dirs = [d for d in sessions_path.glob(pattern) if d.is_dir()]
    
    if not session_dirs:
        print(f"❌ No session directories found in: {sessions_path}")
        return 0
    
    print(f"🔍 Found {len(session_dirs)} sessions to analyze")
    
    successful = 0
    failed = 0
    
    for session_dir in session_dirs:
        print(f"\n{'='*60}")
        
        if analyze_session(str(session_dir)):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Analysis Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success rate: {successful/(successful+failed)*100:.1f}%")
    
    return successful


def main():
    """Main entry point for the analysis script."""
    parser = argparse.ArgumentParser(description="Analyze racing session data")
    parser.add_argument("session_path", help="Path to session directory or sessions parent directory")
    parser.add_argument("--output", "-o", help="Custom output directory for reports")
    parser.add_argument("--multiple", "-m", action="store_true", 
                       help="Analyze multiple sessions in the given directory")
    parser.add_argument("--pattern", "-p", default="*", 
                       help="Pattern to match session directories (for multiple mode)")
    
    args = parser.parse_args()
    
    if args.multiple:
        # Analyze multiple sessions
        successful = analyze_multiple_sessions(args.session_path, args.pattern)
        sys.exit(0 if successful > 0 else 1)
    else:
        # Analyze single session
        success = analyze_session(args.session_path, args.output)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
