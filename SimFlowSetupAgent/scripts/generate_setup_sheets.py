#!/usr/bin/env python3
"""
Setup Sheet Generator Script
Generate setup parameter tables and blank setup sheets for vehicles
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.vehicle_profile_manager import VehicleProfileManager
from src.setup_sheet_generator import SetupSheetGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate vehicle setup sheets and parameter tables")
    parser.add_argument("action", choices=["list", "parameters", "sheet", "summary"], 
                       help="Action to perform")
    parser.add_argument("--vehicle", "-v", help="Vehicle profile key (e.g., nascar_nextgen_speedway)")
    parser.add_argument("--format", "-f", choices=["markdown", "html", "csv"], default="markdown",
                       help="Output format")
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    # Initialize managers
    vehicles_dir = project_root / "vehicle_profiles"
    profile_manager = VehicleProfileManager(vehicles_dir)
    sheet_generator = SetupSheetGenerator(profile_manager)
    
    if args.action == "list":
        # List all available vehicle profiles
        print("Available Vehicle Profiles:")
        print("=" * 50)
        
        categories = profile_manager.get_vehicle_categories()
        for category, vehicles in categories.items():
            print(f"\n{category.upper()}:")
            for vehicle_key in vehicles:
                profile = profile_manager.get_profile(vehicle_key)
                vehicle_info = profile.get("vehicle_info", {})
                print(f"  • {vehicle_key} - {vehicle_info.get('name', 'Unknown')}")
    
    elif args.action == "parameters":
        # Generate parameter table
        if not args.vehicle:
            print("Error: --vehicle required for parameters action")
            print("Use 'list' action to see available vehicles")
            sys.exit(1)
        
        print(f"Generating parameter table for: {args.vehicle}")
        print("=" * 60)
        
        table = sheet_generator.generate_parameter_table(args.vehicle, args.format)
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(table)
            print(f"Parameter table saved to: {output_path}")
        else:
            print(table)
    
    elif args.action == "sheet":
        # Generate blank setup sheet
        if not args.vehicle:
            print("Error: --vehicle required for sheet action")
            print("Use 'list' action to see available vehicles")
            sys.exit(1)
        
        print(f"Generating blank setup sheet for: {args.vehicle}")
        print("=" * 60)
        
        sheet = sheet_generator.generate_blank_setup_sheet(args.vehicle, args.format)
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(sheet)
            print(f"Setup sheet saved to: {output_path}")
        else:
            print(sheet)
    
    elif args.action == "summary":
        # Generate summary of all profiles
        print("Vehicle Profile Summary")
        print("=" * 60)
        
        summary = profile_manager.export_profile_summary()
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"Summary saved to: {output_path}")
        else:
            print(summary)

if __name__ == "__main__":
    main()
