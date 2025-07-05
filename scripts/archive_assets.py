#!/usr/bin/env python3
"""
Zip ASSETS/ once reports are final.

Usage:
    archive_assets.py <session_dir>
"""
import sys, pathlib, shutil

session_dir = pathlib.Path(sys.argv[1]).resolve()
assets_dir  = session_dir / "ASSETS"
if not assets_dir.exists():
    sys.exit("[archive_assets] no ASSETS directory found")

archive_root = session_dir.parents[2] / "ARCHIVE"
archive_root.mkdir(exist_ok=True)
zip_base = archive_root / f"{session_dir.name}-assets"
shutil.make_archive(str(zip_base), 'zip', assets_dir)

# leave stub
(assets_dir / "README.txt").write_text(
    f"Assets archived to {zip_base}.zip\n")

print(f"[archive_assets] archived to {zip_base}.zip")
