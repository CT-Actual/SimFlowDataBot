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


def _run_optimizer(session_dir: Path):
    """Run the optimize_setup.py script for a session."""
    if not session_dir.exists():
        return
    cmd = ["python", "optimize_setup.py", "--session", str(session_dir)]
    print(f"\n🔧 Optimizing session: {session_dir.name}")
    subprocess.run(cmd, check=False)



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
        java_files = [str(p) for p in Path("src/main/java").glob("*.java")]
        subprocess.run([
            "javac", *java_files, "-d", "build/classes/java/main"
        ], check=True)
        
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
                _run_optimizer(sessions_root / session_id)
                
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
