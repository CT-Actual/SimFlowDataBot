"""
Vehicle Profile Manager
Handles vehicle-specific setup parameters and validation
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

class VehicleProfileManager:
    """Manages vehicle setup profiles and parameter validation"""
    
    def __init__(self, profiles_directory: str = None):
        self.logger = logging.getLogger(__name__)
        self.profiles_dir = Path(profiles_directory) if profiles_directory else Path(__file__).parent / "vehicle_profiles"
        self.profiles = {}
        self._load_all_profiles()
    
    def _load_all_profiles(self):
        """Load all vehicle profiles from the profiles directory"""
        try:
            if not self.profiles_dir.exists():
                self.logger.warning(f"Vehicle profiles directory not found: {self.profiles_dir}")
                return
            
            for profile_file in self.profiles_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r') as f:
                        profile_data = json.load(f)
                    
                    profile_key = profile_file.stem
                    self.profiles[profile_key] = profile_data
                    self.logger.info(f"Loaded vehicle profile: {profile_key}")
                    
                except Exception as e:
                    self.logger.error(f"Error loading profile {profile_file}: {str(e)}")
            
            self.logger.info(f"Loaded {len(self.profiles)} vehicle profiles")
            
        except Exception as e:
            self.logger.error(f"Error loading vehicle profiles: {str(e)}")
    
    def get_profile(self, vehicle_key: str) -> Optional[Dict]:
        """Get a specific vehicle profile"""
        return self.profiles.get(vehicle_key)
    
    def list_profiles(self) -> List[str]:
        """List all available vehicle profiles"""
        return list(self.profiles.keys())
    
    def get_vehicle_categories(self) -> Dict[str, List[str]]:
        """Get vehicles organized by category"""
        categories = {}
        
        for profile_key, profile_data in self.profiles.items():
            category = profile_data.get("vehicle_info", {}).get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(profile_key)
        
        return categories
    
    def validate_setup_parameter(self, vehicle_key: str, parameter_category: str, 
                                parameter_name: str, value: Any) -> Tuple[bool, str]:
        """Validate a setup parameter against vehicle constraints"""
        
        profile = self.get_profile(vehicle_key)
        if not profile:
            return False, f"Vehicle profile '{vehicle_key}' not found"
        
        setup_params = profile.get("setup_parameters", {})
        category_params = setup_params.get(parameter_category, {})
        param_config = category_params.get(parameter_name)
        
        if not param_config:
            return False, f"Parameter '{parameter_name}' not found in category '{parameter_category}'"
        
        # Validate against min/max constraints
        if "min" in param_config and "max" in param_config:
            try:
                num_value = float(value)
                min_val = float(param_config["min"])
                max_val = float(param_config["max"])
                
                if num_value < min_val:
                    return False, f"Value {num_value} below minimum {min_val} {param_config.get('unit', '')}"
                elif num_value > max_val:
                    return False, f"Value {num_value} above maximum {max_val} {param_config.get('unit', '')}"
                else:
                    return True, "Valid"
                    
            except (ValueError, TypeError):
                return False, f"Invalid numeric value: {value}"
        
        # Validate against options if available
        if "options" in param_config:
            if value not in param_config["options"]:
                return False, f"Value '{value}' not in allowed options: {param_config['options']}"
            else:
                return True, "Valid"
        
        return True, "Valid"
    
    def validate_complete_setup(self, vehicle_key: str, setup_data: Dict) -> Dict:
        """Validate a complete setup configuration"""
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "parameter_results": {}
        }
        
        profile = self.get_profile(vehicle_key)
        if not profile:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Vehicle profile '{vehicle_key}' not found")
            return validation_results
        
        setup_params = profile.get("setup_parameters", {})
        
        # Validate each parameter in the setup
        for category, params in setup_data.items():
            if category not in setup_params:
                validation_results["warnings"].append(f"Unknown setup category: {category}")
                continue
            
            validation_results["parameter_results"][category] = {}
            
            for param_name, value in params.items():
                is_valid, message = self.validate_setup_parameter(
                    vehicle_key, category, param_name, value
                )
                
                validation_results["parameter_results"][category][param_name] = {
                    "value": value,
                    "valid": is_valid,
                    "message": message
                }
                
                if not is_valid:
                    validation_results["valid"] = False
                    validation_results["errors"].append(f"{category}.{param_name}: {message}")
        
        return validation_results
    
    def get_parameter_info(self, vehicle_key: str, parameter_category: str, 
                          parameter_name: str) -> Optional[Dict]:
        """Get detailed information about a specific parameter"""
        
        profile = self.get_profile(vehicle_key)
        if not profile:
            return None
        
        setup_params = profile.get("setup_parameters", {})
        category_params = setup_params.get(parameter_category, {})
        return category_params.get(parameter_name)
    
    def get_optimization_priorities(self, vehicle_key: str, track_type: str = None) -> Dict:
        """Get optimization priorities for a vehicle/track combination"""
        
        profile = self.get_profile(vehicle_key)
        if not profile:
            return {}
        
        optimization_priorities = profile.get("optimization_priorities", {})
        
        if track_type and track_type in optimization_priorities:
            return optimization_priorities[track_type]
        
        # Return first available track type if specific one not found
        if optimization_priorities:
            return list(optimization_priorities.values())[0]
        
        return {}
    
    def get_critical_telemetry_channels(self, vehicle_key: str) -> List[str]:
        """Get critical telemetry channels for a vehicle"""
        
        profile = self.get_profile(vehicle_key)
        if not profile:
            return []
        
        telemetry = profile.get("telemetry_channels", {})
        critical = telemetry.get("critical", [])
        important = telemetry.get("important", [])
        
        return critical + important
    
    def generate_setup_sheet_template(self, vehicle_key: str) -> str:
        """Generate a human-readable setup sheet template"""
        
        profile = self.get_profile(vehicle_key)
        if not profile:
            return f"Vehicle profile '{vehicle_key}' not found"
        
        vehicle_info = profile.get("vehicle_info", {})
        setup_params = profile.get("setup_parameters", {})
        
        template = f"""# {vehicle_info.get('name', 'Unknown Vehicle')} Setup Sheet

**Category**: {vehicle_info.get('category', 'Unknown')}
**Track Type**: {vehicle_info.get('track_type', 'Unknown')}
**Series**: {vehicle_info.get('series', 'Unknown')}

"""
        
        # Add parameter tables
        for category, params in setup_params.items():
            template += f"## {category.replace('_', ' ').title()}\n\n"
            template += "| Parameter | Min | Max | Unit | Current | Notes |\n"
            template += "|-----------|-----|-----|------|---------|-------|\n"
            
            for param_name, param_config in params.items():
                min_val = param_config.get("min", "N/A")
                max_val = param_config.get("max", "N/A")
                unit = param_config.get("unit", "")
                description = param_config.get("description", "")
                
                # Handle special cases for options
                if "options" in param_config:
                    min_val = param_config["options"][0]
                    max_val = param_config["options"][-1]
                
                template += f"| {param_name.replace('_', ' ').title()} | {min_val} | {max_val} | {unit} | ___ | {description} |\n"
            
            template += "\n"
        
        template += "---\n*Generated by SimFlowSetupBot - Expert iRacing Setup Engineering*\n"
        
        return template
    
    def export_profile_summary(self) -> str:
        """Export a summary of all available vehicle profiles"""
        
        summary = "# Vehicle Profile Summary\n\n"
        
        categories = self.get_vehicle_categories()
        
        for category, vehicles in categories.items():
            summary += f"## {category.title()}\n\n"
            
            for vehicle_key in vehicles:
                profile = self.get_profile(vehicle_key)
                vehicle_info = profile.get("vehicle_info", {})
                
                summary += f"### {vehicle_info.get('name', vehicle_key)}\n"
                summary += f"- **File**: `{vehicle_key}.json`\n"
                summary += f"- **Track Type**: {vehicle_info.get('track_type', 'Unknown')}\n"
                summary += f"- **Series**: {vehicle_info.get('series', 'Unknown')}\n"
                
                # Count parameters
                setup_params = profile.get("setup_parameters", {})
                param_count = sum(len(params) for params in setup_params.values())
                summary += f"- **Parameters**: {param_count} setup parameters\n"
                
                summary += "\n"
        
        return summary
