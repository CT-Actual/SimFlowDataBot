#!/usr/bin/env python3
"""
Manual processing script for SimFlowDataAgent.
Run this when you've added new files to the DROP-OFF directory.

Usage:
    python process_dropoff.py
"""
import subprocess
import sys
import shutil
from pathlib import Path
from datetime import datetime


def _run_setup_agent(file_path: Path, car_name: str):
    """Run SimFlowSetupAgent on the given file and store JSON output."""
    cmd = [
        "python",
        "SimFlowSetupAgent/simflow_setup_agent.py",
        "analyze",
        "--file",
        str(file_path),
        "--vehicle",
        car_name,
        "--output",
        "json",
    ]
    print(f"\n🛠️  Analyzing setup: {file_path.name}")
    subprocess.run(cmd, check=False)

    json_name = f"{file_path.stem}_analysis.json"
    json_path = Path("SimFlowSetupAgent/output") / json_name
    if json_path.exists():
        dest_dir = Path("SimFlowSetupAgent/PROCESSED/by_car") / car_name / datetime.now().strftime("%Y-%m-%d")
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(json_path), dest_dir / json_name)
        shutil.copy2(file_path, dest_dir / file_path.name)

def main():
    print("🏁 SimFlowDataAgent - Processing DROP-OFF directory...")
    
    # Check if DROP-OFF directory exists
    dropoff_dir = Path("2025-Season3/Car_Folder/DROP-OFF")
    if not dropoff_dir.exists():
        print("❌ DROP-OFF directory not found!")
        sys.exit(1)
    
    # Count files in DROP-OFF (excluding .done files)
    files = [f for f in dropoff_dir.iterdir() 
             if f.is_file() and not f.name.endswith('.done')]
    
    if not files:
        print("📁 No new files found in DROP-OFF directory.")
        return
    
    print(f"📊 Found {len(files)} files to process:")
    for file in files:
        print(f"   • {file.name}")
    
    # Confirm processing
    response = input("\n🚀 Process these files? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Processing cancelled.")
        return
    
    print("\n⚙️  Starting Java DropOffWatcher...")
    
    try:
        # Compile Java classes
        print("🔨 Compiling Java classes...")
        subprocess.run([
            "javac", "src/main/java/*.java", 
            "-d", "build/classes/java/main"
        ], check=True, capture_output=True)
        
        # Run DropOffWatcher in one-shot mode
        print("🏃 Running DropOffWatcher...")
        result = subprocess.run([
            "java", "-cp", "build/classes/java/main", "DropOffWatcher"
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print("✅ Processing completed successfully!")

            # Show results
            processed_files = [f for f in dropoff_dir.iterdir()
                             if f.name.endswith('.done')]
            print(f"📋 Processed {len(processed_files)} sessions")

            # Show TOC if it exists
            toc_path = Path("2025-Season3/Car_Folder/TOC.md")
            if toc_path.exists():
                print(f"📄 TOC updated: {toc_path}")

            # Show archives
            archive_dir = Path("2025-Season3/ARCHIVE")
            if archive_dir.exists():
                archives = list(archive_dir.glob("*.zip"))
                print(f"📦 {len(archives)} sessions archived")

            # Trigger setup analysis for any setup files moved to RAW
            car_name = dropoff_dir.parent.name
            sessions_root = dropoff_dir.parent / "SESSIONS"
            for done in dropoff_dir.glob("*.done"):
                session_id = done.stem
                raw_dir = sessions_root / session_id / "RAW"
                if not raw_dir.exists():
                    continue
                for f in raw_dir.iterdir():
                    lower = f.name.lower()
                    if lower.endswith('.htm') or lower.endswith('.xlsm') or \
                       lower.endswith('.xlsx') or (lower.endswith('.csv') and 'setup' in lower):
                        _run_setup_agent(f, car_name)
                
        else:
            print("❌ Processing failed!")
            print("Error output:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Processing timed out after 5 minutes")
    except subprocess.CalledProcessError as e:
        print(f"❌ Compilation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
