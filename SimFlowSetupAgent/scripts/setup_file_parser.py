#!/usr/bin/env python3
"""
SimFlowSetupAgent - Setup File Parser
Parses iRacing .htm setup files and MoTeC setup sheets (.csv/.xlsm).
"""

import os
import re
import json
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SetupFileParser:
    """Parse various setup file formats used in iRacing and MoTeC"""
    
    def __init__(self, vehicle_profiles_dir: str = "vehicle_profiles", drop_off_dir: str = "DROP-OFF"):
        self.vehicle_profiles_dir = Path(vehicle_profiles_dir)
        self.drop_off_dir = Path(drop_off_dir)
        self.processed_dir = Path("PROCESSED")
        self.vehicle_profiles = {}
        self.car_type_mappings = {}
        self.load_vehicle_profiles()
        self.setup_directories()
    
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
    
    def setup_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.drop_off_dir / "setup_files",
            self.drop_off_dir / "motec_sheets", 
            self.drop_off_dir / "images",
            self.processed_dir / "by_car",
            self.processed_dir / "by_track",
            self.processed_dir / "reports"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory ready: {directory}")
    
    def parse_iracing_htm(self, htm_file_path: str) -> Dict[str, Any]:
        """Parse iRacing .htm setup export file"""
        try:
            with open(htm_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse HTML content
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract setup data
            setup_data = {
                "file_type": "iracing_htm",
                "file_path": htm_file_path,
                "parsed_data": {},
                "metadata": {}
            }
            
            # Extract car and track info from title
            title_match = re.search(r'(\w+) setup: (.+?)<br>\s*track: (.+?)</H2>', content)
            if title_match:
                setup_data["car_name"] = title_match.group(1)
                setup_data["setup_name"] = title_match.group(2)
                setup_data["track_name"] = title_match.group(3)
            
            # Detect car and track types
            car_type = self.detect_car_type(content, htm_file_path)
            track_info = self.detect_track_type(content)
            
            setup_data["metadata"] = {
                "car_type": car_type,
                "track_info": track_info,
                "parsing_timestamp": str(pd.Timestamp.now())
            }
            
            # Parse different sections based on car type
            setup_data["parsed_data"]["tires"] = self._parse_tire_section(content, car_type)
            setup_data["parsed_data"]["aerodynamics"] = self._parse_aero_section(content, car_type)
            setup_data["parsed_data"]["suspension"] = self._parse_suspension_section(content, car_type)
            setup_data["parsed_data"]["brakes"] = self._parse_brake_section(content, car_type)
            setup_data["parsed_data"]["differential"] = self._parse_diff_section(content, car_type)
            setup_data["parsed_data"]["dampers"] = self._parse_damper_section(content, car_type)
            setup_data["parsed_data"]["driver_aids"] = self._parse_driver_aids_section(content, car_type)
            setup_data["parsed_data"]["gears"] = self._parse_gear_section(content, car_type)
            setup_data["parsed_data"]["fuel_weight"] = self._parse_fuel_weight_section(content, car_type)
            
            return setup_data
            
        except Exception as e:
            logger.error(f"Error parsing iRacing .htm file {htm_file_path}: {e}")
            return {"error": str(e)}
    
    def _parse_tire_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse tire pressure and temperature data"""
        tire_data = {}
        
        # Extract tire pressures
        tire_positions = ['LEFT FRONT', 'RIGHT FRONT', 'LEFT REAR', 'RIGHT REAR']
        for pos in tire_positions:
            pos_key = pos.lower().replace(' ', '_')
            
            # Find starting pressure
            start_pressure_match = re.search(rf'<H2><U>{pos}:</U></H2>\s*Starting pressure: <U>([0-9.]+) psi</U>', content)
            if start_pressure_match:
                tire_data[f"{pos_key}_start_pressure"] = float(start_pressure_match.group(1))
            
            # Find hot pressure
            hot_pressure_match = re.search(rf'Starting pressure: <U>[0-9.]+ psi</U><br>Last hot pressure: <U>([0-9.]+) psi</U>', content)
            if hot_pressure_match:
                tire_data[f"{pos_key}_hot_pressure"] = float(hot_pressure_match.group(1))
            
            # Find temperatures (O M I or I M O pattern)
            temp_match = re.search(rf'Last temps [OMI ]+: <U>([0-9]+)F</U><br><U>([0-9]+)F</U><br><U>([0-9]+)F</U>', content)
            if temp_match:
                tire_data[f"{pos_key}_temps"] = [int(temp_match.group(1)), int(temp_match.group(2)), int(temp_match.group(3))]
        
        # Extract tire type (Dry/Wet/etc.)
        tire_type_match = re.search(r'Tire type: <U>([^<]+)</U>', content)
        if tire_type_match:
            tire_data["tire_type"] = tire_type_match.group(1)
        
        return tire_data
    
    def _parse_aero_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse aerodynamic setup data"""
        aero_data = {}
        
        # GT3 and sports cars typically have these
        if "gt3" in car_type or "lmp" in car_type or "formula" in car_type:
            # Rear wing angle
            wing_match = re.search(r'(?:Rear )?Wing (?:setting|angle): <U>([0-9.-]+) degrees</U>', content)
            if wing_match:
                aero_data["rear_wing_angle"] = float(wing_match.group(1))
            
            # Front splitter height
            splitter_match = re.search(r'(?:Center )?(?:front )?[Ss]plitter height:? <U>([0-9.]+) in</U>', content)
            if splitter_match:
                aero_data["front_splitter_height"] = float(splitter_match.group(1))
            
            # Ride heights at speed
            front_rh_match = re.search(r'Front RH at speed: <U>([0-9.]+)"</U>', content)
            if front_rh_match:
                aero_data["front_rh_at_speed"] = float(front_rh_match.group(1))
            
            rear_rh_match = re.search(r'Rear RH at speed: <U>([0-9.]+)"</U>', content)
            if rear_rh_match:
                aero_data["rear_rh_at_speed"] = float(rear_rh_match.group(1))
            
            # Front downforce percentage
            df_match = re.search(r'Front downforce: <U>([0-9.]+)%</U>', content)
            if df_match:
                aero_data["front_downforce_percent"] = float(df_match.group(1))
        
        # NASCAR specific aero
        elif "nascar" in car_type:
            # NASCAR has different aero parameters
            spoiler_match = re.search(r'Rear spoiler: <U>([0-9.]+) (?:degrees|in)</U>', content)
            if spoiler_match:
                aero_data["rear_spoiler"] = float(spoiler_match.group(1))
            
            splitter_match = re.search(r'Front splitter: <U>([0-9.]+) (?:degrees|in)</U>', content)
            if splitter_match:
                aero_data["front_splitter"] = float(splitter_match.group(1))
        
        # Touring cars might have different patterns
        elif "tcr" in car_type or "touring" in car_type:
            # TCR cars often have rear wing settings
            wing_match = re.search(r'Rear Wing setting: <U>([+-]?[0-9.]+) degrees</U>', content)
            if wing_match:
                aero_data["rear_wing_angle"] = float(wing_match.group(1))
        
        return aero_data
    
    def _parse_suspension_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse suspension setup data"""
        suspension_data = {}
        
        # Corner weights, ride heights, spring rates, camber
        corners = ['LEFT FRONT', 'RIGHT FRONT', 'LEFT REAR', 'RIGHT REAR']
        for corner in corners:
            corner_key = corner.lower().replace(' ', '_')
            
            # Corner weight
            weight_match = re.search(rf'<H2><U>{corner}:</U></H2>\s*Corner weight: <U>([0-9]+) lbs</U>', content)
            if weight_match:
                suspension_data[f"{corner_key}_weight"] = int(weight_match.group(1))
            
            # Ride height
            rh_match = re.search(rf'Ride height: <U>([0-9.]+) in</U>', content)
            if rh_match:
                suspension_data[f"{corner_key}_ride_height"] = float(rh_match.group(1))
            
            # Spring rate
            spring_match = re.search(rf'Spring rate: <U>([0-9]+) lbs/in</U>', content)
            if spring_match:
                suspension_data[f"{corner_key}_spring_rate"] = int(spring_match.group(1))
            
            # Camber
            camber_match = re.search(rf'Camber: <U>([+-][0-9.]+) deg</U>', content)
            if camber_match:
                suspension_data[f"{corner_key}_camber"] = float(camber_match.group(1))
            
            # Car-specific suspension parameters
            if "tcr" in car_type or "touring" in car_type:
                # TCR cars often have spring perch offset
                perch_match = re.search(rf'Spring perch offset: <U>([0-9.]+)"</U>', content)
                if perch_match:
                    suspension_data[f"{corner_key}_spring_perch_offset"] = float(perch_match.group(1))
                
                # TCR damper settings are different (bump/rebound stiffness)
                bump_match = re.search(rf'Bump stiffness: <U>([+-][0-9]+) clicks</U>', content)
                if bump_match:
                    suspension_data[f"{corner_key}_bump_stiffness"] = int(bump_match.group(1))
                
                rebound_match = re.search(rf'Rebound stiffness: <U>([+-][0-9]+) clicks</U>', content)
                if rebound_match:
                    suspension_data[f"{corner_key}_rebound_stiffness"] = int(rebound_match.group(1))
            
            elif "gt3" in car_type or "lmp" in car_type:
                # GT3 cars have bump rubber gap
                bump_rubber_match = re.search(rf'Bump rubber gap: <U>([0-9.]+) in</U>', content)
                if bump_rubber_match:
                    suspension_data[f"{corner_key}_bump_rubber_gap"] = float(bump_rubber_match.group(1))
            
            # Toe settings (varies by car)
            if 'REAR' in corner:
                toe_match = re.search(rf'Toe-in: <U>([+-][0-9.]+) in</U>', content)
                if toe_match:
                    suspension_data[f"{corner_key}_toe"] = float(toe_match.group(1))
                
                # Some cars have toe in fractions (e.g., TCR)
                toe_fraction_match = re.search(rf'Toe-in: <U>([+-]?[0-9]+)/32"</U>', content)
                if toe_fraction_match:
                    suspension_data[f"{corner_key}_toe_fraction"] = toe_fraction_match.group(1)
        
        # Front total toe
        front_toe_match = re.search(r'Total toe-in: <U>([+-][0-9.]+) in</U>', content)
        if front_toe_match:
            suspension_data["front_total_toe"] = float(front_toe_match.group(1))
        
        # Front toe fraction format (e.g., TCR)
        front_toe_fraction_match = re.search(r'Toe-in: <U>([+-]?[0-9]+)/32"</U>', content)
        if front_toe_fraction_match:
            suspension_data["front_toe_fraction"] = front_toe_fraction_match.group(1)
        
        # Anti-roll bar settings (varies by car type)
        if "gt3" in car_type or "lmp" in car_type:
            # GT3 typically has ARB settings as numbers
            front_arb_match = re.search(r'ARB setting: <U>([0-9]+)</U>', content)
            if front_arb_match:
                suspension_data["front_arb_setting"] = int(front_arb_match.group(1))
            
            rear_arb_match = re.search(r'RARB setting: <U>([0-9]+)</U>', content)
            if rear_arb_match:
                suspension_data["rear_arb_setting"] = int(rear_arb_match.group(1))
        
        elif "tcr" in car_type or "touring" in car_type:
            # TCR has ARB wall thickness and blade length
            front_arb_thickness_match = re.search(r'Anti-roll bar wall thickness: <U>([0-9.]+)"</U>', content)
            if front_arb_thickness_match:
                suspension_data["front_arb_wall_thickness"] = float(front_arb_thickness_match.group(1))
            
            front_arb_blade_match = re.search(r'Anti-roll bar blade length: <U>([0-9.]+)"</U>', content)
            if front_arb_blade_match:
                suspension_data["front_arb_blade_length"] = float(front_arb_blade_match.group(1))
        
        # Weight distribution parameters
        nose_weight_match = re.search(r'Nose weight: <U>([0-9.]+)%</U>', content)
        if nose_weight_match:
            suspension_data["nose_weight_percent"] = float(nose_weight_match.group(1))
        
        cross_weight_match = re.search(r'Cross weight: <U>([0-9.]+)%</U>', content)
        if cross_weight_match:
            suspension_data["cross_weight_percent"] = float(cross_weight_match.group(1))
        
        return suspension_data
    
    def _parse_brake_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse brake setup data"""
        brake_data = {}
        
        # Brake bias
        bias_match = re.search(r'Brake pressure bias: <U>([0-9.]+)%</U>', content)
        if bias_match:
            brake_data["brake_bias"] = float(bias_match.group(1))
        
        # Master cylinder diameters
        front_mc_match = re.search(r'Front master cyl(?:inder)?: <U>([0-9.]+) in</U>', content)
        if front_mc_match:
            brake_data["front_master_cylinder"] = float(front_mc_match.group(1))
        
        rear_mc_match = re.search(r'Rear master cyl(?:inder)?: <U>([0-9.]+) in</U>', content)
        if rear_mc_match:
            brake_data["rear_master_cylinder"] = float(rear_mc_match.group(1))
        
        # Brake pads
        pad_match = re.search(r'Brake pads: <U>([^<]+)</U>', content)
        if pad_match:
            brake_data["brake_pads"] = pad_match.group(1)
        
        # TCR-specific brake parameters
        if "tcr" in car_type or "touring" in car_type:
            # Rear brake valve
            valve_match = re.search(r'Rear brake valve: <U>([0-9]+)</U>', content)
            if valve_match:
                brake_data["rear_brake_valve"] = int(valve_match.group(1))
            
            # Handbrake ratio
            handbrake_match = re.search(r'Handbrake ratio: <U>([0-9.]+):1</U>', content)
            if handbrake_match:
                brake_data["handbrake_ratio"] = float(handbrake_match.group(1))
        
        return brake_data
    
    def _parse_diff_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse differential setup data"""
        diff_data = {}
        
        # Friction faces
        faces_match = re.search(r'Friction Faces: <U>([0-9]+)</U>', content)
        if faces_match:
            diff_data["friction_faces"] = int(faces_match.group(1))
        
        # Differential preload
        preload_match = re.search(r'Diff preload: <U>([0-9]+) ft-lbs</U>', content)
        if preload_match:
            diff_data["diff_preload"] = int(preload_match.group(1))
        
        return diff_data
    
    def _parse_damper_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse damper setup data"""
        damper_data = {}
        
        # GT3/LMP style dampers
        if "gt3" in car_type or "lmp" in car_type:
            # Front dampers
            front_lsc_match = re.search(r'<H2><U>FRONT DAMPERS:</U></H2>\s*Low Speed Compression damping: <U>([0-9]+) clicks</U>', content)
            if front_lsc_match:
                damper_data["front_low_speed_compression"] = int(front_lsc_match.group(1))
            
            front_hsc_match = re.search(r'High Speed Compression damping: <U>([0-9]+) clicks</U>', content)
            if front_hsc_match:
                damper_data["front_high_speed_compression"] = int(front_hsc_match.group(1))
            
            front_lsr_match = re.search(r'Low Speed Rebound damping: <U>([0-9]+) clicks</U>', content)
            if front_lsr_match:
                damper_data["front_low_speed_rebound"] = int(front_lsr_match.group(1))
            
            front_hsr_match = re.search(r'High Speed Rebound damping: <U>([0-9]+) clicks</U>', content)
            if front_hsr_match:
                damper_data["front_high_speed_rebound"] = int(front_hsr_match.group(1))
            
            # Rear dampers
            rear_lsc_match = re.search(r'<H2><U>REAR DAMPERS:</U></H2>\s*Low Speed Compression damping: <U>([0-9]+) clicks</U>', content)
            if rear_lsc_match:
                damper_data["rear_low_speed_compression"] = int(rear_lsc_match.group(1))
            
            rear_hsc_match = re.search(r'High Speed Compression damping: <U>([0-9]+) clicks</U>', content)
            if rear_hsc_match:
                damper_data["rear_high_speed_compression"] = int(rear_hsc_match.group(1))
            
            rear_lsr_match = re.search(r'Low Speed Rebound damping: <U>([0-9]+) clicks</U>', content)
            if rear_lsr_match:
                damper_data["rear_low_speed_rebound"] = int(rear_lsr_match.group(1))
            
            rear_hsr_match = re.search(r'High Speed Rebound damping: <U>([0-9]+) clicks</U>', content)
            if rear_hsr_match:
                damper_data["rear_high_speed_rebound"] = int(rear_hsr_match.group(1))
        
        # TCR style dampers are handled in suspension section as bump/rebound stiffness
        
        return damper_data
    
    def _parse_driver_aids_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse driver aids setup data"""
        aids_data = {}
        
        # ABS setting
        abs_match = re.search(r'ABS setting: <U>([0-9]+) \(ABS\)</U>', content)
        if abs_match:
            aids_data["abs_setting"] = int(abs_match.group(1))
        
        # TC setting
        tc_match = re.search(r'TC setting: <U>([0-9]+) \([^)]+\)</U>', content)
        if tc_match:
            aids_data["tc_setting"] = int(tc_match.group(1))
        
        # GT3-specific aids
        if "gt3" in car_type:
            # Throttle shape
            throttle_match = re.search(r'Throttle shape setting: <U>([0-9]+)</U>', content)
            if throttle_match:
                aids_data["throttle_shape"] = int(throttle_match.group(1))
        
        # TCR-specific aids
        if "tcr" in car_type or "touring" in car_type:
            # Launch RPM limit
            launch_match = re.search(r'Launch RPM limit: <U>([0-9]+)</U>', content)
            if launch_match:
                aids_data["launch_rpm_limit"] = int(launch_match.group(1))
        
        return aids_data
    
    def _parse_gear_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse gear setup data"""
        gear_data = {}
        
        # Gear stack
        gear_match = re.search(r'Gear stack: <U>([^<]+)</U>', content)
        if gear_match:
            gear_data["gear_stack"] = gear_match.group(1)
        
        return gear_data
    
    def _parse_fuel_weight_section(self, content: str, car_type: str = "unknown") -> Dict[str, Any]:
        """Parse fuel level and weight distribution"""
        fuel_weight_data = {}
        
        # Fuel level
        fuel_match = re.search(r'Fuel level: <U>([0-9.]+) gal</U>', content)
        if fuel_match:
            fuel_weight_data["fuel_level"] = float(fuel_match.group(1))
        
        # Weight distribution
        weight_dist_match = re.search(r'%F WtDist: <U>([0-9.]+)%</U>', content)
        if weight_dist_match:
            fuel_weight_data["front_weight_dist"] = float(weight_dist_match.group(1))
        
        # Cross weight
        cross_weight_match = re.search(r'Cross weight: <U>([0-9.]+)%</U>', content)
        if cross_weight_match:
            fuel_weight_data["cross_weight"] = float(cross_weight_match.group(1))
        
        return fuel_weight_data
    
    def parse_motec_csv(self, csv_file_path: str) -> Dict[str, Any]:
        """Parse MoTeC setup sheet CSV file"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            
            setup_data = {
                "file_type": "motec_csv",
                "file_path": csv_file_path,
                "parsed_data": {}
            }
            
            # Parse header to get parameter names and units
            if len(df) > 0:
                header_row = df.iloc[0]  # Parameter names
                unit_row = df.iloc[1] if len(df) > 1 else None  # Units
                
                # Extract parameters
                for col in df.columns:
                    if pd.notna(header_row[col]) and header_row[col] != '':
                        param_name = header_row[col]
                        unit = unit_row[col] if unit_row is not None and pd.notna(unit_row[col]) else ''
                        
                        setup_data["parsed_data"][param_name] = {
                            "unit": unit,
                            "values": []
                        }
                        
                        # Extract values from subsequent rows
                        for i in range(2, len(df)):
                            value = df.iloc[i][col]
                            if pd.notna(value) and value != '':
                                setup_data["parsed_data"][param_name]["values"].append(value)
            
            return setup_data
            
        except Exception as e:
            logger.error(f"Error parsing MoTeC CSV file {csv_file_path}: {e}")
            return {"error": str(e)}
    
    def parse_motec_excel(self, excel_file_path: str) -> Dict[str, Any]:
        """Parse MoTeC setup sheet Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(excel_file_path)
            
            setup_data = {
                "file_type": "motec_excel",
                "file_path": excel_file_path,
                "parsed_data": {}
            }
            
            # Similar parsing logic as CSV but for Excel format
            # This would need specific implementation based on Excel structure
            
            return setup_data
            
        except Exception as e:
            logger.error(f"Error parsing MoTeC Excel file {excel_file_path}: {e}")
            return {"error": str(e)}
    
    def detect_car_type(self, content: str, filename: str = "") -> str:
        """Detect car type from setup file content"""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Car type mappings based on iRacing internal names and common patterns
        car_mappings = {
            # GT3 Cars
            "acuransxevo22gt3": "gt3_acura_nsx_evo22",
            "porsche992rgt3": "gt3_porsche_992",
            "ferrari296gt3": "gt3_ferrari_296", 
            "bmwm4gt3": "gt3_bmw_m4",
            "audiR8GT3": "gt3_audi_r8",
            "mercedesamggt3": "gt3_mercedes_amg",
            
            # NASCAR
            "nascarcup": "nascar_next_gen",
            "nextgen": "nascar_next_gen",
            
            # Formula Cars
            "dallaraF3": "f3_dallara",
            "dallaraF2": "f2_dallara", 
            "dallaraIR18": "indycar_ir18",
            
            # Touring Cars
            "audirs3lms": "tcr_audi_rs3",
            "hyundaiveloster": "tcr_hyundai_veloster",
            
            # Sports Cars
            "porsche963gtp": "lmp_porsche_963",
            "cadillacvr": "lmp_cadillac_vr",
        }
        
        # Check content for car identifiers
        for car_id, car_type in car_mappings.items():
            if car_id.lower() in content_lower or car_id.lower() in filename_lower:
                return car_type
        
        # Check for category indicators
        if "gt3" in content_lower or "gt3" in filename_lower:
            return "gt3_generic"
        elif "nascar" in content_lower or "cup" in content_lower:
            return "nascar_next_gen" 
        elif "formula" in content_lower or "f3" in content_lower:
            return "formula_generic"
        elif "tcr" in content_lower or "touring" in content_lower:
            return "tcr_generic"
        
        return "unknown"
    
    def detect_track_type(self, content: str) -> Dict[str, str]:
        """Detect track information from setup file content"""
        track_info = {"name": "unknown", "type": "unknown", "category": "unknown"}
        
        # Extract track name from title
        track_match = re.search(r'track: ([^<]+)', content, re.IGNORECASE)
        if track_match:
            track_name = track_match.group(1).strip()
            track_info["name"] = track_name
        
        # Track type mappings
        road_courses = [
            "silverstone", "spa", "nurburgring", "watkins", "road america", 
            "sebring", "daytona road", "cota", "brands hatch", "oulton", 
            "donnington", "snetterton", "lime rock", "laguna seca", "sonoma"
        ]
        
        ovals = [
            "daytona", "talladega", "charlotte", "atlanta", "las vegas",
            "texas", "kansas", "michigan", "indianapolis", "pocono",
            "bristol", "martinsville", "richmond", "phoenix", "homestead"
        ]
        
        street_circuits = [
            "monaco", "long beach", "baltimore", "houston", "st pete",
            "toronto", "detroit", "adelaide"
        ]
        
        track_name_lower = track_info["name"].lower();
        
        if any(track in track_name_lower for track in road_courses):
            track_info["type"] = "road_course"
            track_info["category"] = "permanent"
        elif any(track in track_name_lower for track in ovals):
            track_info["type"] = "oval"
            track_info["category"] = "speedway"
        elif any(track in track_name_lower for track in street_circuits):
            track_info["type"] = "street_circuit"  
            track_info["category"] = "temporary"
        else:
            # Try to detect from other indicators
            if "gp" in track_name_lower or "grand prix" in track_name_lower:
                track_info["type"] = "road_course"
            elif "speedway" in track_name_lower or "motor speedway" in track_name_lower:
                track_info["type"] = "oval"
        
        return track_info
    
    def compare_setups(self, setup1: Dict[str, Any], setup2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two parsed setup files"""
        comparison = {
            "setup1_file": setup1.get("file_path", "Unknown"),
            "setup2_file": setup2.get("file_path", "Unknown"),
            "differences": {},
            "common_parameters": {},
            "setup1_only": {},
            "setup2_only": {}
        }
        
        # Get all parameters from both setups
        params1 = set()
        params2 = set()
        
        for section in setup1.get("parsed_data", {}).values():
            if isinstance(section, dict):
                params1.update(section.keys())
        
        for section in setup2.get("parsed_data", {}).values():
            if isinstance(section, dict):
                params2.update(section.keys())
        
        # Find common parameters and differences
        common_params = params1 & params2
        setup1_only = params1 - params2
        setup2_only = params2 - params1
        
        comparison["common_parameters"] = list(common_params)
        comparison["setup1_only"] = list(setup1_only)
        comparison["setup2_only"] = list(setup2_only)
        
        return comparison
    
    def generate_setup_report(self, setup_data: Dict[str, Any]) -> str:
        """Generate human-readable setup report"""
        report = []
        
        # Header
        report.append("="*60)
        report.append("SETUP ANALYSIS REPORT")
        report.append("="*60)
        
        # File info
        report.append(f"File: {setup_data.get('file_path', 'Unknown')}")
        report.append(f"Type: {setup_data.get('file_type', 'Unknown')}")
        
        if 'car_name' in setup_data:
            report.append(f"Car: {setup_data['car_name']}")
        if 'track_name' in setup_data:
            report.append(f"Track: {setup_data['track_name']}")
        if 'setup_name' in setup_data:
            report.append(f"Setup: {setup_data['setup_name']}")
        
        report.append("")
        
        # Parse each section
        parsed_data = setup_data.get("parsed_data", {})
        
        for section_name, section_data in parsed_data.items():
            if section_data:
                report.append(f"{section_name.upper().replace('_', ' ')}:")
                report.append("-" * 40)
                
                if isinstance(section_data, dict):
                    for param, value in section_data.items():
                        report.append(f"  {param.replace('_', ' ').title()}: {value}")
                
                report.append("")
        
        return "\n".join(report)
    
    def process_drop_off_files(self) -> List[Dict[str, Any]]:
        """Process all files in the DROP-OFF folder"""
        processed_files = []
        
        # Process setup files
        setup_files_dir = self.drop_off_dir / "setup_files"
        for file_path in setup_files_dir.glob("*.htm"):
            logger.info(f"Processing setup file: {file_path}")
            setup_data = self.parse_iracing_htm(str(file_path))
            if "error" not in setup_data:
                organized_path = self.organize_setup_file(setup_data)
                setup_data["organized_path"] = organized_path
                processed_files.append(setup_data)
        
        # Process MoTeC files
        motec_files_dir = self.drop_off_dir / "motec_sheets"
        for file_path in motec_files_dir.glob("*.csv"):
            logger.info(f"Processing MoTeC CSV: {file_path}")
            motec_data = self.parse_motec_csv(str(file_path))
            if "error" not in motec_data:
                organized_path = self.organize_motec_file(motec_data)
                motec_data["organized_path"] = organized_path
                processed_files.append(motec_data)
        
        # Process Excel files
        for file_path in motec_files_dir.glob("*.xlsx"):
            logger.info(f"Processing Excel file: {file_path}")
            excel_data = self.parse_motec_excel(str(file_path))
            if "error" not in excel_data:
                organized_path = self.organize_motec_file(excel_data)
                excel_data["organized_path"] = organized_path
                processed_files.append(excel_data)
        
        return processed_files
    
    def organize_setup_file(self, setup_data: Dict[str, Any]) -> str:
        """Organize setup file into appropriate folder structure: by_car > date"""
        metadata = setup_data.get("metadata", {})
        car_type = metadata.get("car_type", "unknown")
        track_info = metadata.get("track_info", {})
        track_name = track_info.get("name", "unknown").replace(" ", "_").lower()
        
        # Create organized folder structure: by_car > date
        date_folder = pd.Timestamp.now().strftime("%Y-%m-%d")
        car_date_folder = self.processed_dir / "by_car" / car_type / date_folder
        car_date_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp and track info
        original_filename = Path(setup_data["file_path"]).name
        timestamp = pd.Timestamp.now().strftime("%H%M%S")
        new_filename = f"{timestamp}_{track_name}_{original_filename}"
        
        # Copy file to organized location
        import shutil
        organized_file_path = car_date_folder / new_filename
        shutil.copy2(setup_data["file_path"], organized_file_path)
        
        # Save parsed data as JSON
        json_filename = new_filename.replace(".htm", "_parsed.json")
        json_path = car_date_folder / json_filename
        
        with open(json_path, 'w') as f:
            json.dump(setup_data, f, indent=2, default=str)
        
        logger.info(f"Organized setup file to: {organized_file_path}")
        return str(organized_file_path)
    
    def organize_motec_file(self, motec_data: Dict[str, Any]) -> str:
        """Organize MoTeC file into appropriate folder structure: by_car > date"""
        # Try to extract car info from filename or content
        file_path = motec_data.get("file_path", "")
        filename = Path(file_path).name.lower()
        
        # Attempt to detect car type from filename
        car_type = "unknown"
        if "gt3" in filename:
            car_type = "gt3_generic"
        elif "nascar" in filename:
            car_type = "nascar_generic"
        elif "tcr" in filename:
            car_type = "tcr_generic"
        elif "formula" in filename:
            car_type = "formula_generic"
        
        # Create organized folder structure: motec_analysis > car_type > date
        date_folder = pd.Timestamp.now().strftime("%Y-%m-%d")
        motec_car_date_folder = self.processed_dir / "motec_analysis" / car_type / date_folder
        motec_car_date_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        original_filename = Path(file_path).name
        timestamp = pd.Timestamp.now().strftime("%H%M%S")
        new_filename = f"{timestamp}_{original_filename}"
        
        # Copy file to organized location
        import shutil
        organized_path = motec_car_date_folder / new_filename
        shutil.copy2(file_path, organized_path)
        
        # Save parsed data as JSON
        json_filename = new_filename.replace(".csv", "_parsed.json").replace(".xlsx", "_parsed.json")
        json_path = motec_car_date_folder / json_filename
        
        with open(json_path, 'w') as f:
            json.dump(motec_data, f, indent=2, default=str)
        
        logger.info(f"Organized MoTeC file to: {organized_path}")
        return str(organized_path)
    
    def generate_comparison_report(self, setup_files: List[Dict[str, Any]]) -> str:
        """Generate comparison report for multiple setup files"""
        if len(setup_files) < 2:
            return "Need at least 2 setup files for comparison"
        
        report = []
        report.append("="*80)
        report.append("SETUP COMPARISON REPORT")
        report.append("="*80)
        report.append(f"Generated: {pd.Timestamp.now()}")
        report.append(f"Comparing {len(setup_files)} setup files")
        report.append("")
        
        # Group by car type
        by_car_type = {}
        for setup in setup_files:
            car_type = setup.get("metadata", {}).get("car_type", "unknown")
            if car_type not in by_car_type:
                by_car_type[car_type] = []
            by_car_type[car_type].append(setup)
        
        # Compare setups within each car type
        for car_type, setups in by_car_type.items():
            if len(setups) > 1:
                report.append(f"CAR TYPE: {car_type.upper()}")
                report.append("-" * 40)
                
                for i, setup in enumerate(setups):
                    setup_name = setup.get("setup_name", f"Setup {i+1}")
                    track_name = setup.get("track_name", "Unknown")
                    report.append(f"  {i+1}. {setup_name} @ {track_name}")
                
                # Compare key parameters
                report.append("\nKEY PARAMETER DIFFERENCES:")
                report.append("-" * 30)
                
                # Compare tire pressures
                if len(setups) >= 2:
                    setup1 = setups[0]
                    setup2 = setups[1]
                    
                    tire1 = setup1.get("parsed_data", {}).get("tires", {})
                    tire2 = setup2.get("parsed_data", {}).get("tires", {})
                    
                    if tire1 and tire2:
                        report.append("TIRE PRESSURES:")
                        for position in ["left_front", "right_front", "left_rear", "right_rear"]:
                            pressure1 = tire1.get(f"{position}_start_pressure")
                            pressure2 = tire2.get(f"{position}_start_pressure")
                            if pressure1 is not None and pressure2 is not None:
                                diff = pressure2 - pressure1
                                report.append(f"  {position.replace('_', ' ').title()}: {pressure1:.1f} vs {pressure2:.1f} psi (Δ{diff:+.1f})")
                
                report.append("")
        
        return "\n".join(report)
    
    def watch_drop_off_folder(self, interval: int = 30):
        """Watch DROP-OFF folder for new files (for future automated processing)"""
        import time
        
        logger.info(f"Watching DROP-OFF folder every {interval} seconds...")
        
        last_processed = {}
        
        while True:
            try:
                current_files = {}
                
                # Check for new files
                for folder in ["setup_files", "motec_sheets", "images"]:
                    folder_path = self.drop_off_dir / folder
                    if folder_path.exists():
                        for file_path in folder_path.iterdir():
                            if file_path.is_file():
                                mod_time = file_path.stat().st_mtime
                                current_files[str(file_path)] = mod_time
                
                # Process new or modified files
                for file_path, mod_time in current_files.items():
                    if file_path not in last_processed or last_processed[file_path] < mod_time:
                        logger.info(f"New/modified file detected: {file_path}")
                        # Process the file here
                        last_processed[file_path] = mod_time
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping file watcher...")
                break
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                time.sleep(interval)
    
def main():
    """Test the enhanced setup parser with different car types"""
    parser = SetupFileParser()
    
    # Test files from current directory
    test_files = [
        "SimFlow_Fuji_RACEfinal.htm",  # Acura NSX GT3
        "GNG-Porsche-Fuji-R.htm",     # Porsche 992 GT3
        "RYCO_25S3_TCRVC_Audi_BHatch_R_Wet.htm",  # Audi TCR
        "baseline.htm",
        "baselineWET.htm"
    ]
    
    processed_setups = []
    
    for htm_file in test_files:
        if os.path.exists(htm_file):
            print(f"\n{'='*60}")
            print(f"PARSING: {htm_file}")
            print('='*60)
            
            setup_data = parser.parse_iracing_htm(htm_file)
            
            if "error" not in setup_data:
                processed_setups.append(setup_data)
                
                # Print basic info
                print(f"Car: {setup_data.get('car_name', 'Unknown')}")
                print(f"Track: {setup_data.get('track_name', 'Unknown')}")
                print(f"Setup: {setup_data.get('setup_name', 'Unknown')}")
                
                metadata = setup_data.get("metadata", {})
                print(f"Detected Car Type: {metadata.get('car_type', 'Unknown')}")
                
                track_info = metadata.get("track_info", {})
                print(f"Track Type: {track_info.get('type', 'Unknown')}")
                print(f"Track Category: {track_info.get('category', 'Unknown')}")
                
                # Show some parsed parameters
                parsed_data = setup_data.get("parsed_data", {})
                
                # Tire pressures
                tires = parsed_data.get("tires", {})
                if tires:
                    print("\nTIRE PRESSURES:")
                    for position in ["left_front", "right_front", "left_rear", "right_rear"]:
                        pressure = tires.get(f"{position}_start_pressure")
                        if pressure is not None:
                            print(f"  {position.replace('_', ' ').title()}: {pressure} psi")
                
                # Aerodynamics
                aero = parsed_data.get("aerodynamics", {})
                if aero:
                    print("\nAERODYNAMICS:")
                    for param, value in aero.items():
                        print(f"  {param.replace('_', ' ').title()}: {value}")
                
                # Weight distribution
                suspension = parsed_data.get("suspension", {})
                if suspension:
                    print("\nWEIGHT & SUSPENSION:")
                    for param in ["nose_weight_percent", "cross_weight_percent"]:
                        if param in suspension:
                            print(f"  {param.replace('_', ' ').title()}: {suspension[param]}%")
            else:
                print(f"ERROR: {setup_data['error']}")
    
    # Generate comparison report
    if len(processed_setups) > 1:
        print(f"\n{'='*80}")
        print("COMPARISON REPORT")
        print('='*80)
        comparison_report = parser.generate_comparison_report(processed_setups)
        print(comparison_report)
    
    # Test DROP-OFF processing
    print(f"\n{'='*60}")
    print("TESTING DROP-OFF PROCESSING")
    print('='*60)
    
    # Move some files to DROP-OFF for testing
    import shutil
    drop_off_setup_dir = parser.drop_off_dir / "setup_files"
    
    for test_file in test_files[:2]:  # Move first 2 files
        if os.path.exists(test_file):
            dest_path = drop_off_setup_dir / test_file
            if not dest_path.exists():
                shutil.copy2(test_file, dest_path)
                print(f"Copied {test_file} to DROP-OFF folder")
    
    # Process DROP-OFF files
    processed_files = parser.process_drop_off_files()
    print(f"Processed {len(processed_files)} files from DROP-OFF folder")
    
    for processed_file in processed_files:
        print(f"  - {Path(processed_file['file_path']).name} -> {processed_file.get('organized_path', 'Not organized')}")


if __name__ == "__main__":
    main()
