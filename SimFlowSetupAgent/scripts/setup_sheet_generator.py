#!/usr/bin/env python3
"""
SimFlowSetupAgent - Setup Sheet Generator
Generates human-readable setup sheets from parsed setup data
"""

import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SetupSheetGenerator:
    """Generate setup sheets in various formats"""
    
    def __init__(self, vehicle_profiles_dir: str = "vehicle_profiles"):
        self.vehicle_profiles_dir = Path(vehicle_profiles_dir)
        self.vehicle_profiles = {}
        self.load_vehicle_profiles()
    
    def load_vehicle_profiles(self):
        """Load all vehicle profile JSON files"""
        try:
            for profile_file in self.vehicle_profiles_dir.glob("*.json"):
                with open(profile_file, 'r') as f:
                    profile_data = json.load(f)
                    category = profile_data.get("vehicle_info", {}).get("category", "unknown")
                    self.vehicle_profiles[category] = profile_data
                    logger.info(f"Loaded vehicle profile: {profile_file.name}")
        except Exception as e:
            logger.error(f"Error loading vehicle profiles: {e}")
    
    def generate_parameter_table(self, vehicle_category: str = "gt3") -> str:
        """Generate a formatted parameter table for a vehicle category"""
        if vehicle_category not in self.vehicle_profiles:
            return f"Vehicle category '{vehicle_category}' not found in profiles."
        
        profile = self.vehicle_profiles[vehicle_category]
        vehicle_info = profile.get("vehicle_info", {})
        setup_params = profile.get("setup_parameters", {})
        
        table = []
        table.append("="*120)
        table.append(f"SETUP PARAMETERS - {vehicle_info.get('name', 'Unknown Vehicle')}")
        table.append(f"Category: {vehicle_info.get('category', 'N/A')} | Track Type: {vehicle_info.get('track_type', 'N/A')}")
        table.append(f"Series: {vehicle_info.get('series', 'N/A')}")
        table.append("="*120)
        table.append("")
        
        # Generate table for each section
        for section_name, section_params in setup_params.items():
            table.append(f"{section_name.upper().replace('_', ' ')}:")
            table.append("-" * 80)
            
            # Table header
            table.append(f"{'Parameter':<35} {'Min':<12} {'Max':<12} {'Unit':<15} {'Description'}")
            table.append("-" * 80)
            
            for param_name, param_info in section_params.items():
                if isinstance(param_info, dict):
                    param_display = param_name.replace('_', ' ').title()
                    min_val = param_info.get('min', 'N/A')
                    max_val = param_info.get('max', 'N/A')
                    unit = param_info.get('unit', 'N/A')
                    description = param_info.get('description', 'N/A')
                    
                    # Handle options instead of min/max
                    if 'options' in param_info:
                        min_val = 'Options:'
                        max_val = ', '.join(param_info['options'])
                    
                    table.append(f"{param_display:<35} {str(min_val):<12} {str(max_val):<12} {unit:<15} {description}")
            
            table.append("")
        
        return "\n".join(table)
    
    def generate_setup_comparison_table(self, setup1: Dict[str, Any], setup2: Dict[str, Any]) -> str:
        """Generate a comparison table between two setups"""
        table = []
        table.append("="*120)
        table.append("SETUP COMPARISON")
        table.append("="*120)
        
        # File info
        file1 = os.path.basename(setup1.get('file_path', 'Setup 1'))
        file2 = os.path.basename(setup2.get('file_path', 'Setup 2'))
        
        table.append(f"Setup 1: {file1}")
        table.append(f"Setup 2: {file2}")
        table.append("")
        
        # Compare each section
        parsed1 = setup1.get('parsed_data', {})
        parsed2 = setup2.get('parsed_data', {})
        
        all_sections = set(parsed1.keys()) | set(parsed2.keys())
        
        for section in sorted(all_sections):
            section_data1 = parsed1.get(section, {})
            section_data2 = parsed2.get(section, {})
            
            if section_data1 or section_data2:
                table.append(f"{section.upper().replace('_', ' ')}:")
                table.append("-" * 80)
                
                # Table header
                table.append(f"{'Parameter':<35} {'Setup 1':<20} {'Setup 2':<20} {'Difference'}")
                table.append("-" * 80)
                
                all_params = set()
                if isinstance(section_data1, dict):
                    all_params.update(section_data1.keys())
                if isinstance(section_data2, dict):
                    all_params.update(section_data2.keys())
                
                for param in sorted(all_params):
                    param_display = param.replace('_', ' ').title()
                    val1 = section_data1.get(param, 'N/A') if isinstance(section_data1, dict) else 'N/A'
                    val2 = section_data2.get(param, 'N/A') if isinstance(section_data2, dict) else 'N/A'
                    
                    # Calculate difference if both values are numeric
                    diff = 'N/A'
                    try:
                        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                            diff = f"{val2 - val1:+.3f}"
                        elif val1 == val2:
                            diff = "Same"
                        else:
                            diff = "Different"
                    except:
                        diff = "N/A"
                    
                    table.append(f"{param_display:<35} {str(val1):<20} {str(val2):<20} {diff}")
                
                table.append("")
        
        return "\n".join(table)
    
    def generate_optimization_report(self, setup_data: Dict[str, Any], vehicle_category: str = "gt3", 
                                   session_type: str = "road_course") -> str:
        """Generate optimization recommendations based on setup data"""
        if vehicle_category not in self.vehicle_profiles:
            return f"Vehicle category '{vehicle_category}' not found in profiles."
        
        profile = self.vehicle_profiles[vehicle_category]
        setup_params = profile.get("setup_parameters", {})
        opt_priorities = profile.get("optimization_priorities", {}).get(session_type, {})
        
        report = []
        report.append("="*80)
        report.append("SETUP OPTIMIZATION REPORT")
        report.append("="*80)
        
        # File info
        report.append(f"Setup File: {os.path.basename(setup_data.get('file_path', 'Unknown'))}")
        report.append(f"Vehicle Category: {vehicle_category}")
        report.append(f"Session Type: {session_type}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Analysis by priority
        parsed_data = setup_data.get("parsed_data", {})
        
        for priority_level in ["primary", "secondary", "fine_tuning"]:
            if priority_level in opt_priorities:
                params = opt_priorities[priority_level]
                report.append(f"{priority_level.upper().replace('_', ' ')} OPTIMIZATION PARAMETERS:")
                report.append("-" * 60)
                
                for param in params:
                    # Find the parameter in the setup data
                    current_value = self._find_parameter_value(parsed_data, param)
                    param_spec = self._find_parameter_spec(setup_params, param)
                    
                    if current_value is not None and param_spec:
                        recommendations = self._generate_parameter_recommendations(
                            param, current_value, param_spec
                        )
                        
                        report.append(f"  {param.replace('_', ' ').title()}:")
                        report.append(f"    Current: {current_value} {param_spec.get('unit', '')}")
                        report.append(f"    Range: {param_spec.get('min', 'N/A')} - {param_spec.get('max', 'N/A')} {param_spec.get('unit', '')}")
                        
                        if recommendations:
                            report.append(f"    Recommendations: {recommendations}")
                        
                        report.append("")
                
                report.append("")
        
        # Balance analysis
        balance_analysis = self._analyze_balance(parsed_data)
        if balance_analysis:
            report.append("BALANCE ANALYSIS:")
            report.append("-" * 60)
            for analysis in balance_analysis:
                report.append(f"  {analysis}")
            report.append("")
        
        return "\n".join(report)
    
    def _find_parameter_value(self, parsed_data: Dict[str, Any], param_name: str) -> Optional[Any]:
        """Find a parameter value in parsed setup data"""
        # Search through all sections for the parameter
        for section_data in parsed_data.values():
            if isinstance(section_data, dict) and param_name in section_data:
                return section_data[param_name]
        return None
    
    def _find_parameter_spec(self, setup_params: Dict[str, Any], param_name: str) -> Optional[Dict[str, Any]]:
        """Find parameter specification in vehicle profile"""
        for section_data in setup_params.values():
            if isinstance(section_data, dict) and param_name in section_data:
                return section_data[param_name]
        return None
    
    def _generate_parameter_recommendations(self, param_name: str, current_value: Any, 
                                         param_spec: Dict[str, Any]) -> str:
        """Generate recommendations for a specific parameter"""
        recommendations = []
        
        # Check if value is within range
        if 'min' in param_spec and 'max' in param_spec:
            try:
                min_val = float(param_spec['min'])
                max_val = float(param_spec['max'])
                curr_val = float(current_value)
                
                if curr_val < min_val:
                    recommendations.append(f"Increase to at least {min_val}")
                elif curr_val > max_val:
                    recommendations.append(f"Decrease to no more than {max_val}")
                else:
                    # Value is in range, provide context-specific advice
                    range_position = (curr_val - min_val) / (max_val - min_val)
                    
                    if 'tire_pressure' in param_name:
                        if range_position < 0.3:
                            recommendations.append("Consider increasing for better tire temps")
                        elif range_position > 0.7:
                            recommendations.append("Consider decreasing for better grip")
                    
                    elif 'wing_angle' in param_name:
                        if range_position < 0.4:
                            recommendations.append("Low downforce setup - good for speed")
                        elif range_position > 0.6:
                            recommendations.append("High downforce setup - good for corners")
                    
                    elif 'spring_rate' in param_name:
                        if range_position < 0.4:
                            recommendations.append("Soft springs - good for mechanical grip")
                        elif range_position > 0.6:
                            recommendations.append("Stiff springs - good for aero platform")
                    
                    if not recommendations:
                        recommendations.append("Value within optimal range")
            
            except (ValueError, TypeError):
                recommendations.append("Unable to analyze numeric value")
        
        return "; ".join(recommendations) if recommendations else "No specific recommendations"
    
    def _analyze_balance(self, parsed_data: Dict[str, Any]) -> List[str]:
        """Analyze setup balance and provide recommendations"""
        analysis = []
        
        # Analyze tire pressure balance
        tire_data = parsed_data.get('tires', {})
        if tire_data:
            pressures = []
            for pos in ['left_front', 'right_front', 'left_rear', 'right_rear']:
                key = f"{pos}_start_pressure"
                if key in tire_data:
                    pressures.append(tire_data[key])
            
            if len(pressures) == 4:
                front_avg = (pressures[0] + pressures[1]) / 2
                rear_avg = (pressures[2] + pressures[3]) / 2
                left_avg = (pressures[0] + pressures[2]) / 2
                right_avg = (pressures[1] + pressures[3]) / 2
                
                if abs(front_avg - rear_avg) > 1.0:
                    analysis.append(f"Tire pressure F/R imbalance: {front_avg:.1f} vs {rear_avg:.1f} psi")
                
                if abs(left_avg - right_avg) > 0.5:
                    analysis.append(f"Tire pressure L/R imbalance: {left_avg:.1f} vs {right_avg:.1f} psi")
        
        # Analyze weight distribution
        suspension_data = parsed_data.get('suspension', {})
        fuel_weight_data = parsed_data.get('fuel_weight', {})
        
        if 'cross_weight' in fuel_weight_data:
            cross_weight = fuel_weight_data['cross_weight']
            if cross_weight < 48.0:
                analysis.append(f"Cross weight low at {cross_weight:.1f}% - may cause loose handling")
            elif cross_weight > 52.0:
                analysis.append(f"Cross weight high at {cross_weight:.1f}% - may cause tight handling")
        
        # Analyze spring rate balance
        if 'left_front_spring_rate' in suspension_data and 'left_rear_spring_rate' in suspension_data:
            front_rate = suspension_data['left_front_spring_rate']
            rear_rate = suspension_data['left_rear_spring_rate']
            
            if front_rate / rear_rate > 1.5:
                analysis.append(f"Front springs much stiffer than rear ({front_rate}/{rear_rate}) - may cause understeer")
            elif rear_rate / front_rate > 1.2:
                analysis.append(f"Rear springs much stiffer than front ({front_rate}/{rear_rate}) - may cause oversteer")
        
        return analysis
    
    def export_to_csv(self, setup_data: Dict[str, Any], output_file: str):
        """Export setup data to CSV format"""
        try:
            rows = []
            
            # Flatten setup data for CSV export
            parsed_data = setup_data.get('parsed_data', {})
            
            for section_name, section_data in parsed_data.items():
                if isinstance(section_data, dict):
                    for param_name, param_value in section_data.items():
                        rows.append({
                            'Section': section_name,
                            'Parameter': param_name,
                            'Value': param_value,
                            'Source_File': os.path.basename(setup_data.get('file_path', 'Unknown'))
                        })
            
            # Create DataFrame and export
            df = pd.DataFrame(rows)
            df.to_csv(output_file, index=False)
            
            logger.info(f"Setup data exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def export_to_markdown(self, setup_data: Dict[str, Any], output_file: str):
        """Export setup data to Markdown format"""
        try:
            with open(output_file, 'w') as f:
                f.write("# Setup Analysis Report\n\n")
                
                # File info
                f.write(f"**File:** {os.path.basename(setup_data.get('file_path', 'Unknown'))}\n")
                f.write(f"**Type:** {setup_data.get('file_type', 'Unknown')}\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if 'car_name' in setup_data:
                    f.write(f"**Car:** {setup_data['car_name']}\n")
                if 'track_name' in setup_data:
                    f.write(f"**Track:** {setup_data['track_name']}\n")
                if 'setup_name' in setup_data:
                    f.write(f"**Setup:** {setup_data['setup_name']}\n")
                
                f.write("\n")
                
                # Parse each section
                parsed_data = setup_data.get("parsed_data", {})
                
                for section_name, section_data in parsed_data.items():
                    if section_data:
                        f.write(f"## {section_name.replace('_', ' ').title()}\n\n")
                        
                        if isinstance(section_data, dict):
                            f.write("| Parameter | Value |\n")
                            f.write("|-----------|-------|\n")
                            
                            for param, value in section_data.items():
                                param_display = param.replace('_', ' ').title()
                                f.write(f"| {param_display} | {value} |\n")
                        
                        f.write("\n")
            
            logger.info(f"Setup data exported to {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting to Markdown: {e}")


def main():
    """Test the setup sheet generator"""
    generator = SetupSheetGenerator()
    
    # Generate parameter table for GT3
    print("Generating GT3 parameter table...")
    table = generator.generate_parameter_table("gt3")
    print(table)
    
    # Save to file
    with open("gt3_parameter_table.txt", "w") as f:
        f.write(table)
    
    print("\nParameter table saved to gt3_parameter_table.txt")


if __name__ == "__main__":
    main()
