"""
Setup Sheet Generator
Creates human-readable setup sheets and parameter tables
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

class SetupSheetGenerator:
    """Generates setup sheets and parameter tables for vehicles"""
    
    def __init__(self, vehicle_profile_manager):
        self.logger = logging.getLogger(__name__)
        self.profile_manager = vehicle_profile_manager
    
    def generate_parameter_table(self, vehicle_key: str, format_type: str = "markdown") -> str:
        """Generate a parameter table for a vehicle"""
        
        profile = self.profile_manager.get_profile(vehicle_key)
        if not profile:
            return f"Vehicle profile '{vehicle_key}' not found"
        
        if format_type.lower() == "markdown":
            return self._generate_markdown_table(profile)
        elif format_type.lower() == "html":
            return self._generate_html_table(profile)
        elif format_type.lower() == "csv":
            return self._generate_csv_table(profile)
        else:
            return self._generate_markdown_table(profile)
    
    def _generate_markdown_table(self, profile: Dict) -> str:
        """Generate a markdown formatted parameter table"""
        
        vehicle_info = profile.get("vehicle_info", {})
        setup_params = profile.get("setup_parameters", {})
        
        output = f"""# {vehicle_info.get('name', 'Unknown Vehicle')} - Setup Parameters

**Category**: {vehicle_info.get('category', 'Unknown')}  
**Track Type**: {vehicle_info.get('track_type', 'Unknown')}  
**Series**: {vehicle_info.get('series', 'Unknown')}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        for category, params in setup_params.items():
            output += f"## {category.replace('_', ' ').title()}\n\n"
            
            # Create table header
            output += "| Parameter | Minimum | Maximum | Unit | Default | Description |\n"
            output += "|-----------|---------|---------|------|---------|-------------|\n"
            
            for param_name, param_config in params.items():
                # Format parameter name
                display_name = param_name.replace('_', ' ').title()
                
                # Get min/max values
                min_val = param_config.get("min", "N/A")
                max_val = param_config.get("max", "N/A")
                
                # Handle options (e.g., P1-P5 for ARB arms)
                if "options" in param_config:
                    options = param_config["options"]
                    min_val = options[0] if options else "N/A"
                    max_val = options[-1] if options else "N/A"
                
                # Get other properties
                unit = param_config.get("unit", "")
                description = param_config.get("description", "")
                default = param_config.get("default", "TBD")
                
                # Format special cases
                if isinstance(min_val, float) and min_val < 0:
                    min_val = f"{min_val:+.3f}".rstrip('0').rstrip('.')
                elif isinstance(min_val, float):
                    min_val = f"{min_val:.3f}".rstrip('0').rstrip('.')
                
                if isinstance(max_val, float) and max_val < 0:
                    max_val = f"{max_val:+.3f}".rstrip('0').rstrip('.')
                elif isinstance(max_val, float):
                    max_val = f"{max_val:.3f}".rstrip('0').rstrip('.')
                
                output += f"| {display_name} | {min_val} | {max_val} | {unit} | {default} | {description} |\n"
            
            output += "\n"
        
        # Add optimization priorities if available
        optimization = profile.get("optimization_priorities", {})
        if optimization:
            output += "## Optimization Priorities\n\n"
            
            for track_type, priorities in optimization.items():
                output += f"### {track_type.title()} Tracks\n\n"
                
                if "primary" in priorities:
                    output += "**Primary Focus**:\n"
                    for param in priorities["primary"]:
                        output += f"- {param.replace('_', ' ').title()}\n"
                    output += "\n"
                
                if "secondary" in priorities:
                    output += "**Secondary**:\n"
                    for param in priorities["secondary"]:
                        output += f"- {param.replace('_', ' ').title()}\n"
                    output += "\n"
                
                if "fine_tuning" in priorities:
                    output += "**Fine Tuning**:\n"
                    for param in priorities["fine_tuning"]:
                        output += f"- {param.replace('_', ' ').title()}\n"
                    output += "\n"
        
        # Add telemetry channels
        telemetry = profile.get("telemetry_channels", {})
        if telemetry:
            output += "## Required Telemetry Channels\n\n"
            
            if "critical" in telemetry:
                output += "**Critical Channels**:\n"
                for channel in telemetry["critical"]:
                    output += f"- `{channel}`\n"
                output += "\n"
            
            if "important" in telemetry:
                output += "**Important Channels**:\n"
                for channel in telemetry["important"]:
                    output += f"- `{channel}`\n"
                output += "\n"
            
            if "supplementary" in telemetry:
                output += "**Supplementary Channels**:\n"
                for channel in telemetry["supplementary"]:
                    output += f"- `{channel}`\n"
                output += "\n"
        
        output += "---\n*Generated by SimFlowSetupBot - Expert iRacing Setup Engineering*\n"
        
        return output
    
    def _generate_html_table(self, profile: Dict) -> str:
        """Generate an HTML formatted parameter table"""
        
        vehicle_info = profile.get("vehicle_info", {})
        setup_params = profile.get("setup_parameters", {})
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{vehicle_info.get('name', 'Unknown Vehicle')} - Setup Parameters</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ccc; padding-bottom: 5px; }}
        .vehicle-info {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>{vehicle_info.get('name', 'Unknown Vehicle')} - Setup Parameters</h1>
    
    <div class="vehicle-info">
        <strong>Category:</strong> {vehicle_info.get('category', 'Unknown')}<br>
        <strong>Track Type:</strong> {vehicle_info.get('track_type', 'Unknown')}<br>
        <strong>Series:</strong> {vehicle_info.get('series', 'Unknown')}<br>
        <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
"""
        
        for category, params in setup_params.items():
            html += f"\n    <h2>{category.replace('_', ' ').title()}</h2>\n"
            html += "    <table>\n"
            html += "        <tr><th>Parameter</th><th>Minimum</th><th>Maximum</th><th>Unit</th><th>Description</th></tr>\n"
            
            for param_name, param_config in params.items():
                display_name = param_name.replace('_', ' ').title()
                min_val = param_config.get("min", "N/A")
                max_val = param_config.get("max", "N/A")
                unit = param_config.get("unit", "")
                description = param_config.get("description", "")
                
                # Handle options
                if "options" in param_config:
                    options = param_config["options"]
                    min_val = options[0] if options else "N/A"
                    max_val = options[-1] if options else "N/A"
                
                html += f"        <tr><td>{display_name}</td><td>{min_val}</td><td>{max_val}</td><td>{unit}</td><td>{description}</td></tr>\n"
            
            html += "    </table>\n"
        
        html += """
    <hr>
    <p><em>Generated by SimFlowSetupBot - Expert iRacing Setup Engineering</em></p>
</body>
</html>"""
        
        return html
    
    def _generate_csv_table(self, profile: Dict) -> str:
        """Generate a CSV formatted parameter table"""
        
        csv_lines = ["Category,Parameter,Minimum,Maximum,Unit,Description"]
        
        setup_params = profile.get("setup_parameters", {})
        
        for category, params in setup_params.items():
            for param_name, param_config in params.items():
                display_name = param_name.replace('_', ' ').title()
                min_val = param_config.get("min", "N/A")
                max_val = param_config.get("max", "N/A")
                unit = param_config.get("unit", "")
                description = param_config.get("description", "").replace(',', ';')  # Escape commas
                
                # Handle options
                if "options" in param_config:
                    options = param_config["options"]
                    min_val = options[0] if options else "N/A"
                    max_val = options[-1] if options else "N/A"
                
                csv_lines.append(f"{category},{display_name},{min_val},{max_val},{unit},{description}")
        
        return "\n".join(csv_lines)
    
    def generate_blank_setup_sheet(self, vehicle_key: str, format_type: str = "markdown") -> str:
        """Generate a blank setup sheet for data entry"""
        
        profile = self.profile_manager.get_profile(vehicle_key)
        if not profile:
            return f"Vehicle profile '{vehicle_key}' not found"
        
        vehicle_info = profile.get("vehicle_info", {})
        setup_params = profile.get("setup_parameters", {})
        
        output = f"""# {vehicle_info.get('name', 'Unknown Vehicle')} - Setup Sheet

**Track**: ________________________  
**Date**: ________________________  
**Session Type**: ________________________  
**Weather**: ________________________  

"""
        
        for category, params in setup_params.items():
            output += f"## {category.replace('_', ' ').title()}\n\n"
            
            for param_name, param_config in params.items():
                display_name = param_name.replace('_', ' ').title()
                unit = param_config.get("unit", "")
                min_val = param_config.get("min", "N/A")
                max_val = param_config.get("max", "N/A")
                
                # Handle options
                if "options" in param_config:
                    options = param_config["options"]
                    options_str = " / ".join(str(opt) for opt in options)
                    output += f"**{display_name}**: _______ ({options_str})\n\n"
                else:
                    output += f"**{display_name}**: _______ {unit} (Range: {min_val} - {max_val})\n\n"
        
        output += """## Notes

**Handling Characteristics**:
- Understeer/Oversteer: _________________________
- Balance: _________________________
- Strengths: _________________________
- Weaknesses: _________________________

**Lap Time Performance**:
- Best Lap: _________________________
- Consistency: _________________________
- Sectors: _________________________

**Additional Notes**:
_________________________________________________
_________________________________________________
_________________________________________________

---
*Generated by SimFlowSetupBot - Expert iRacing Setup Engineering*
"""
        
        return output
