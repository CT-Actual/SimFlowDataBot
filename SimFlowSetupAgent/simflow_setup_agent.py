#!/usr/bin/env python3
"""
SimFlowSetupAgent - Main Agent Script
Expert iRacing setup engineer agent with data-driven optimization
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add the scripts directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from setup_file_parser import SetupFileParser
from setup_sheet_generator import SetupSheetGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimFlowSetupAgent:
    """
    Expert iRacing setup engineer agent
    
    Capabilities:
    - Parse iRacing .htm setup files
    - Parse MoTeC setup sheets (.csv, .xlsm)
    - Generate setup parameter tables
    - Compare setups and provide optimization recommendations
    - Export results in multiple formats
    """
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).parent
        self.vehicle_profiles_dir = self.workspace_dir / "vehicle_profiles"
        self.output_dir = self.workspace_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize parsers
        self.parser = SetupFileParser(str(self.vehicle_profiles_dir))
        self.generator = SetupSheetGenerator(str(self.vehicle_profiles_dir))
        
        self.session_types = {
            "sprint": "Sprint race setup (25-30 minutes, 50% fuel)",
            "endurance": "Endurance race setup (60+ minutes, 100% fuel)",
            "road_course": "General road course setup",
            "qualifying": "Qualifying setup (maximum performance)",
            "practice": "Practice setup (balanced for learning)"
        }
        
        self.aggression_levels = {
            "conservative": "Safe, stable setup with margin for error",
            "balanced": "Balanced setup with moderate risk/reward",
            "aggressive": "High-performance setup with tight margins",
            "experimental": "Experimental setup for testing limits"
        }
        
        logger.info("SimFlowSetupAgent initialized")
    
    def analyze_setup_file(self, file_path: str, vehicle_category: str = "gt3", 
                          session_type: str = "road_course") -> Dict[str, Any]:
        """Analyze a setup file and generate recommendations"""
        logger.info(f"Analyzing setup file: {file_path}")
        
        # Determine file type and parse accordingly
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.htm':
            setup_data = self.parser.parse_iracing_htm(file_path)
        elif file_ext == '.csv':
            setup_data = self.parser.parse_motec_csv(file_path)
        elif file_ext in ['.xlsx', '.xlsm']:
            setup_data = self.parser.parse_motec_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        if "error" in setup_data:
            logger.error(f"Error parsing file: {setup_data['error']}")
            return setup_data
        
        # Generate analysis report
        analysis = {
            "setup_data": setup_data,
            "parameter_analysis": self._analyze_parameters(setup_data, vehicle_category),
            "balance_analysis": self._analyze_balance(setup_data),
            "optimization_recommendations": self._generate_optimization_recommendations(
                setup_data, vehicle_category, session_type
            ),
            "telemetry_channels": self._get_telemetry_channels(vehicle_category),
            "session_type": session_type,
            "vehicle_category": vehicle_category
        }
        
        logger.info("Setup analysis completed")
        return analysis
    
    def compare_setups(self, file1: str, file2: str, vehicle_category: str = "gt3") -> Dict[str, Any]:
        """Compare two setup files"""
        logger.info(f"Comparing setups: {file1} vs {file2}")
        
        # Parse both files
        setup1 = self.analyze_setup_file(file1, vehicle_category)
        setup2 = self.analyze_setup_file(file2, vehicle_category)
        
        if "error" in setup1 or "error" in setup2:
            return {"error": "Failed to parse one or both setup files"}
        
        # Generate comparison
        comparison = self.parser.compare_setups(
            setup1["setup_data"], 
            setup2["setup_data"]
        )
        
        # Add detailed analysis
        comparison["detailed_analysis"] = self._generate_detailed_comparison(
            setup1, setup2, vehicle_category
        )
        
        logger.info("Setup comparison completed")
        return comparison
    
    def generate_setup_recommendations(self, track_name: str, session_type: str = "road_course",
                                     vehicle_category: str = "gt3", 
                                     aggression_level: str = "balanced") -> Dict[str, Any]:
        """Generate setup recommendations for a specific track and session"""
        logger.info(f"Generating setup recommendations for {track_name}")
        
        # Get vehicle profile
        if vehicle_category not in self.parser.vehicle_profiles:
            return {"error": f"Vehicle category '{vehicle_category}' not found"}
        
        profile = self.parser.vehicle_profiles[vehicle_category]
        
        # Generate baseline setup
        baseline_setup = self._generate_baseline_setup(
            profile, track_name, session_type, aggression_level
        )
        
        # Add track-specific adjustments
        track_adjustments = self._get_track_specific_adjustments(track_name, vehicle_category)
        
        # Add session-specific adjustments
        session_adjustments = self._get_session_specific_adjustments(session_type, aggression_level)
        
        recommendations = {
            "track_name": track_name,
            "session_type": session_type,
            "vehicle_category": vehicle_category,
            "aggression_level": aggression_level,
            "baseline_setup": baseline_setup,
            "track_adjustments": track_adjustments,
            "session_adjustments": session_adjustments,
            "final_recommendations": self._combine_setup_adjustments(
                baseline_setup, track_adjustments, session_adjustments
            )
        }
        
        logger.info("Setup recommendations generated")
        return recommendations
    
    def _analyze_parameters(self, setup_data: Dict[str, Any], vehicle_category: str) -> Dict[str, Any]:
        """Analyze individual parameters against vehicle profile"""
        analysis = {}
        
        if vehicle_category not in self.parser.vehicle_profiles:
            return {"error": f"Vehicle category '{vehicle_category}' not found"}
        
        profile = self.parser.vehicle_profiles[vehicle_category]
        setup_params = profile.get("setup_parameters", {})
        parsed_data = setup_data.get("parsed_data", {})
        
        for section_name, section_data in parsed_data.items():
            if isinstance(section_data, dict):
                section_analysis = {}
                
                for param_name, param_value in section_data.items():
                    # Find parameter spec in profile
                    param_spec = self._find_parameter_spec(setup_params, param_name)
                    
                    if param_spec:
                        param_analysis = self._analyze_single_parameter(
                            param_name, param_value, param_spec
                        )
                        section_analysis[param_name] = param_analysis
                
                if section_analysis:
                    analysis[section_name] = section_analysis
        
        return analysis
    
    def _analyze_balance(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze setup balance characteristics"""
        balance_analysis = {
            "front_rear_balance": {},
            "left_right_balance": {},
            "tire_balance": {},
            "aero_balance": {},
            "spring_balance": {},
            "overall_assessment": []
        }
        
        parsed_data = setup_data.get("parsed_data", {})
        
        # Analyze tire balance
        tire_data = parsed_data.get('tires', {})
        if tire_data:
            balance_analysis["tire_balance"] = self._analyze_tire_balance(tire_data)
        
        # Analyze aero balance
        aero_data = parsed_data.get('aerodynamics', {})
        if aero_data:
            balance_analysis["aero_balance"] = self._analyze_aero_balance(aero_data)
        
        # Analyze suspension balance
        suspension_data = parsed_data.get('suspension', {})
        if suspension_data:
            balance_analysis["spring_balance"] = self._analyze_suspension_balance(suspension_data)
        
        # Generate overall assessment
        balance_analysis["overall_assessment"] = self._generate_balance_assessment(balance_analysis)
        
        return balance_analysis
    
    def _generate_optimization_recommendations(self, setup_data: Dict[str, Any], 
                                            vehicle_category: str, session_type: str) -> Dict[str, Any]:
        """Generate optimization recommendations based on setup analysis"""
        recommendations = {
            "priority_adjustments": [],
            "fine_tuning": [],
            "experimental": [],
            "session_specific": []
        }
        
        if vehicle_category not in self.parser.vehicle_profiles:
            return recommendations
        
        profile = self.parser.vehicle_profiles[vehicle_category]
        priorities = profile.get("optimization_priorities", {}).get(session_type, {})
        
        # Generate priority-based recommendations
        for priority_level, params in priorities.items():
            priority_recs = []
            
            for param in params:
                param_rec = self._generate_parameter_recommendation(
                    param, setup_data, profile, session_type
                )
                if param_rec:
                    priority_recs.append(param_rec)
            
            if priority_level == "primary":
                recommendations["priority_adjustments"] = priority_recs
            elif priority_level == "secondary":
                recommendations["fine_tuning"] = priority_recs
            else:
                recommendations["experimental"] = priority_recs
        
        return recommendations
    
    def _get_telemetry_channels(self, vehicle_category: str) -> List[str]:
        """Get recommended telemetry channels for vehicle category"""
        if vehicle_category not in self.parser.vehicle_profiles:
            return []
        
        profile = self.parser.vehicle_profiles[vehicle_category]
        telemetry = profile.get("telemetry_channels", {})
        
        channels = []
        for level in ["critical", "important", "supplementary"]:
            if level in telemetry:
                channels.extend(telemetry[level])
        
        return channels
    
    def export_analysis(self, analysis: Dict[str, Any], output_format: str = "all") -> List[str]:
        """Export analysis results in specified format(s)"""
        exported_files = []
        
        setup_data = analysis.get("setup_data", {})
        file_name = Path(setup_data.get("file_path", "analysis")).stem
        
        if output_format in ["all", "txt"]:
            # Export as text report
            txt_file = self.output_dir / f"{file_name}_analysis.txt"
            with open(txt_file, 'w') as f:
                f.write(self._generate_text_report(analysis))
            exported_files.append(str(txt_file))
        
        if output_format in ["all", "csv"]:
            # Export as CSV
            csv_file = self.output_dir / f"{file_name}_data.csv"
            self.generator.export_to_csv(setup_data, str(csv_file))
            exported_files.append(str(csv_file))
        
        if output_format in ["all", "markdown"]:
            # Export as Markdown
            md_file = self.output_dir / f"{file_name}_analysis.md"
            self.generator.export_to_markdown(setup_data, str(md_file))
            exported_files.append(str(md_file))
        
        if output_format in ["all", "json"]:
            # Export as JSON
            json_file = self.output_dir / f"{file_name}_analysis.json"
            with open(json_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            exported_files.append(str(json_file))
        
        return exported_files
    
    def _generate_text_report(self, analysis: Dict[str, Any]) -> str:
        """Generate comprehensive text report"""
        report = []
        
        # Header
        report.append("=" * 80)
        report.append("SIMFLOW SETUP AGENT - ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Setup info
        setup_data = analysis.get("setup_data", {})
        report.append(f"File: {setup_data.get('file_path', 'Unknown')}")
        report.append(f"Vehicle Category: {analysis.get('vehicle_category', 'Unknown')}")
        report.append(f"Session Type: {analysis.get('session_type', 'Unknown')}")
        report.append("")
        
        # Parameter analysis
        param_analysis = analysis.get("parameter_analysis", {})
        if param_analysis:
            report.append("PARAMETER ANALYSIS:")
            report.append("-" * 40)
            for section, params in param_analysis.items():
                report.append(f"\n{section.upper().replace('_', ' ')}:")
                for param, analysis_data in params.items():
                    report.append(f"  {param.replace('_', ' ').title()}: {analysis_data.get('status', 'Unknown')}")
                    if 'recommendation' in analysis_data:
                        report.append(f"    → {analysis_data['recommendation']}")
            report.append("")
        
        # Balance analysis
        balance_analysis = analysis.get("balance_analysis", {})
        if balance_analysis:
            report.append("BALANCE ANALYSIS:")
            report.append("-" * 40)
            for assessment in balance_analysis.get("overall_assessment", []):
                report.append(f"• {assessment}")
            report.append("")
        
        # Optimization recommendations
        opt_recs = analysis.get("optimization_recommendations", {})
        if opt_recs:
            report.append("OPTIMIZATION RECOMMENDATIONS:")
            report.append("-" * 40)
            
            for category, recs in opt_recs.items():
                if recs:
                    report.append(f"\n{category.replace('_', ' ').title()}:")
                    for rec in recs:
                        report.append(f"• {rec}")
            report.append("")
        
        # Telemetry channels
        telemetry = analysis.get("telemetry_channels", [])
        if telemetry:
            report.append("RECOMMENDED TELEMETRY CHANNELS:")
            report.append("-" * 40)
            for i, channel in enumerate(telemetry[:15]):  # Show first 15
                report.append(f"• {channel}")
            if len(telemetry) > 15:
                report.append(f"... and {len(telemetry) - 15} more channels")
            report.append("")
        
        return "\n".join(report)
    
    # Placeholder methods for complex analysis functions
    def _find_parameter_spec(self, setup_params: Dict[str, Any], param_name: str) -> Optional[Dict[str, Any]]:
        """Find parameter specification in setup parameters"""
        for section_data in setup_params.values():
            if isinstance(section_data, dict) and param_name in section_data:
                return section_data[param_name]
        return None
    
    def _analyze_single_parameter(self, param_name: str, param_value: Any, 
                                param_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single parameter against its specification"""
        analysis = {"value": param_value, "spec": param_spec}
        
        # Check if value is within range
        if 'min' in param_spec and 'max' in param_spec:
            try:
                min_val = float(param_spec['min'])
                max_val = float(param_spec['max'])
                curr_val = float(param_value)
                
                if curr_val < min_val:
                    analysis["status"] = "Below minimum"
                    analysis["recommendation"] = f"Increase to at least {min_val}"
                elif curr_val > max_val:
                    analysis["status"] = "Above maximum"
                    analysis["recommendation"] = f"Decrease to no more than {max_val}"
                else:
                    analysis["status"] = "Within range"
                    analysis["recommendation"] = "Value is acceptable"
            except (ValueError, TypeError):
                analysis["status"] = "Cannot analyze"
                analysis["recommendation"] = "Check value format"
        else:
            analysis["status"] = "No range specified"
            analysis["recommendation"] = "No specific recommendations"
        
        return analysis
    
    def _analyze_tire_balance(self, tire_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tire pressure balance"""
        analysis = {"front_rear_diff": 0, "left_right_diff": 0, "recommendations": []}
        
        # Get tire pressures
        pressures = {}
        for pos in ['left_front', 'right_front', 'left_rear', 'right_rear']:
            key = f"{pos}_start_pressure"
            if key in tire_data:
                pressures[pos] = tire_data[key]
        
        if len(pressures) == 4:
            front_avg = (pressures['left_front'] + pressures['right_front']) / 2
            rear_avg = (pressures['left_rear'] + pressures['right_rear']) / 2
            left_avg = (pressures['left_front'] + pressures['left_rear']) / 2
            right_avg = (pressures['right_front'] + pressures['right_rear']) / 2
            
            analysis["front_rear_diff"] = front_avg - rear_avg
            analysis["left_right_diff"] = left_avg - right_avg
            
            if abs(analysis["front_rear_diff"]) > 1.0:
                analysis["recommendations"].append(
                    f"Large F/R pressure difference: {analysis['front_rear_diff']:.1f} psi"
                )
            
            if abs(analysis["left_right_diff"]) > 0.5:
                analysis["recommendations"].append(
                    f"L/R pressure imbalance: {analysis['left_right_diff']:.1f} psi"
                )
        
        return analysis
    
    def _analyze_aero_balance(self, aero_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze aerodynamic balance"""
        analysis = {"recommendations": []}
        
        if 'front_downforce_percent' in aero_data:
            front_df = aero_data['front_downforce_percent']
            
            if front_df < 38:
                analysis["recommendations"].append("Low front downforce - may cause understeer")
            elif front_df > 45:
                analysis["recommendations"].append("High front downforce - may cause oversteer")
            else:
                analysis["recommendations"].append("Aero balance within normal range")
        
        return analysis
    
    def _analyze_suspension_balance(self, suspension_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze suspension balance"""
        analysis = {"recommendations": []}
        
        # Analyze spring rates
        front_springs = []
        rear_springs = []
        
        for pos in ['left_front', 'right_front']:
            key = f"{pos}_spring_rate"
            if key in suspension_data:
                front_springs.append(suspension_data[key])
        
        for pos in ['left_rear', 'right_rear']:
            key = f"{pos}_spring_rate"
            if key in suspension_data:
                rear_springs.append(suspension_data[key])
        
        if front_springs and rear_springs:
            front_avg = sum(front_springs) / len(front_springs)
            rear_avg = sum(rear_springs) / len(rear_springs)
            
            if front_avg / rear_avg > 1.5:
                analysis["recommendations"].append(
                    f"Front springs much stiffer than rear ({front_avg:.0f}/{rear_avg:.0f})"
                )
            elif rear_avg / front_avg > 1.2:
                analysis["recommendations"].append(
                    f"Rear springs much stiffer than front ({front_avg:.0f}/{rear_avg:.0f})"
                )
        
        return analysis
    
    def _generate_balance_assessment(self, balance_analysis: Dict[str, Any]) -> List[str]:
        """Generate overall balance assessment"""
        assessments = []
        
        # Collect all recommendations
        for section, data in balance_analysis.items():
            if isinstance(data, dict) and 'recommendations' in data:
                assessments.extend(data['recommendations'])
        
        return assessments
    
    def _generate_parameter_recommendation(self, param: str, setup_data: Dict[str, Any], 
                                         profile: Dict[str, Any], session_type: str) -> Optional[str]:
        """Generate recommendation for a specific parameter"""
        # This is a placeholder - would contain sophisticated logic
        return f"Optimize {param.replace('_', ' ')} for {session_type} session"
    
    def _generate_baseline_setup(self, profile: Dict[str, Any], track_name: str, 
                               session_type: str, aggression_level: str) -> Dict[str, Any]:
        """Generate baseline setup recommendations"""
        # This is a placeholder - would contain track database and setup logic
        return {"message": "Baseline setup generation not fully implemented"}
    
    def _get_track_specific_adjustments(self, track_name: str, vehicle_category: str) -> Dict[str, Any]:
        """Get track-specific setup adjustments"""
        # This is a placeholder - would contain track database
        return {"message": f"Track-specific adjustments for {track_name} not implemented"}
    
    def _get_session_specific_adjustments(self, session_type: str, aggression_level: str) -> Dict[str, Any]:
        """Get session-specific setup adjustments"""
        # This is a placeholder - would contain session-specific logic
        return {"message": f"Session adjustments for {session_type} not implemented"}
    
    def _combine_setup_adjustments(self, baseline: Dict[str, Any], 
                                 track_adj: Dict[str, Any], 
                                 session_adj: Dict[str, Any]) -> Dict[str, Any]:
        """Combine all setup adjustments into final recommendations"""
        # This is a placeholder - would contain sophisticated combination logic
        return {"message": "Setup combination logic not fully implemented"}
    
    def _generate_detailed_comparison(self, setup1: Dict[str, Any], 
                                    setup2: Dict[str, Any], 
                                    vehicle_category: str) -> Dict[str, Any]:
        """Generate detailed comparison between two setups"""
        # This is a placeholder - would contain detailed comparison logic
        return {"message": "Detailed comparison logic not fully implemented"}


def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(description="SimFlow Setup Agent - Expert iRacing Setup Engineer")
    parser.add_argument("command", choices=["analyze", "compare", "recommend", "table"], 
                       help="Command to execute")
    parser.add_argument("--file", help="Setup file to analyze")
    parser.add_argument("--file1", help="First setup file for comparison")
    parser.add_argument("--file2", help="Second setup file for comparison")
    parser.add_argument("--track", help="Track name for recommendations")
    parser.add_argument("--vehicle", default="gt3", help="Vehicle category (default: gt3)")
    parser.add_argument("--session", default="road_course", help="Session type (default: road_course)")
    parser.add_argument("--aggression", default="balanced", help="Aggression level (default: balanced)")
    parser.add_argument("--output", default="all", help="Output format (txt, csv, markdown, json, all)")
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = SimFlowSetupAgent()
    
    try:
        if args.command == "analyze":
            if not args.file:
                print("Error: --file is required for analyze command")
                return
            
            print(f"Analyzing setup file: {args.file}")
            analysis = agent.analyze_setup_file(args.file, args.vehicle, args.session)
            
            if "error" in analysis:
                print(f"Error: {analysis['error']}")
                return
            
            # Export results
            exported_files = agent.export_analysis(analysis, args.output)
            print(f"Analysis completed. Results exported to:")
            for file in exported_files:
                print(f"  {file}")
        
        elif args.command == "compare":
            if not args.file1 or not args.file2:
                print("Error: --file1 and --file2 are required for compare command")
                return
            
            print(f"Comparing setups: {args.file1} vs {args.file2}")
            comparison = agent.compare_setups(args.file1, args.file2, args.vehicle)
            
            if "error" in comparison:
                print(f"Error: {comparison['error']}")
                return
            
            # Generate and save comparison report
            report = agent.generator.generate_setup_comparison_table(
                comparison["setup1_data"], comparison["setup2_data"]
            )
            
            output_file = agent.output_dir / "setup_comparison.txt"
            with open(output_file, 'w') as f:
                f.write(report)
            
            print(f"Comparison completed. Report saved to: {output_file}")
        
        elif args.command == "recommend":
            if not args.track:
                print("Error: --track is required for recommend command")
                return
            
            print(f"Generating setup recommendations for {args.track}")
            recommendations = agent.generate_setup_recommendations(
                args.track, args.session, args.vehicle, args.aggression
            )
            
            if "error" in recommendations:
                print(f"Error: {recommendations['error']}")
                return
            
            # Save recommendations
            output_file = agent.output_dir / f"{args.track}_recommendations.json"
            with open(output_file, 'w') as f:
                json.dump(recommendations, f, indent=2)
            
            print(f"Recommendations generated and saved to: {output_file}")
        
        elif args.command == "table":
            print(f"Generating parameter table for {args.vehicle}")
            table = agent.generator.generate_parameter_table(args.vehicle)
            
            output_file = agent.output_dir / f"{args.vehicle}_parameter_table.txt"
            with open(output_file, 'w') as f:
                f.write(table)
            
            print(f"Parameter table generated and saved to: {output_file}")
            print("\nTable preview:")
            print(table[:2000] + "..." if len(table) > 2000 else table)
    
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
