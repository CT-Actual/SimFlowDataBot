"""
Data Parser Module

Handles cleaning and standardizing MoTeC CSV data from Parquet files.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class DataParser:
    """Parse and clean MoTeC racing data from Parquet files."""
    
    def __init__(self, session_path: str, base_parquet_path: Optional[str] = None):
        """
        Initialize parser for a specific session.
        
        Args:
            session_path: Path to session directory containing PARQUET folder
            base_parquet_path: Optional path to a base PARQUET folder for shared files
        """
        self.session_path = Path(session_path)
        self.session_parquet_path = self.session_path / "PARQUET" # For session-specific parquet files
        self.base_parquet_path = Path(base_parquet_path) if base_parquet_path else None
        self.session_id = self.session_path.name
        
    def parse_lap_times(self) -> Optional[pd.DataFrame]:
        """
        Parse lap time data from Track Sections report.
        
        Returns:
            DataFrame with cleaned lap time data or None if not found
        """
        # First, try to find the lap file in the session's PARQUET directory
        lap_file = self.session_parquet_path / "Time Report - Track Sections (All Laps).parquet"
        
        # If not found, try the base PARQUET directory (for shared files)
        if not lap_file.exists() and self.base_parquet_path:
            lap_file = self.base_parquet_path / "Time Report - Track Sections (All Laps).parquet"
        
        if not lap_file.exists():
            print(f"Lap time file not found: {lap_file}")
            return None
            
        try:
            df = pd.read_parquet(lap_file)
            
            # Clean the data structure
            cleaned_df = self._clean_lap_time_data(df)
            return cleaned_df
            
        except Exception as e:
            print(f"Error parsing lap times: {e}")
            return None
    
    def _clean_lap_time_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and structure lap time data.
        
        Args:
            df: Raw lap time DataFrame
            
        Returns:
            Cleaned DataFrame with proper structure
        """
        # Find the row with sector names (usually contains "Str" or sector identifiers)
        sector_row_idx = None
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and any(keyword in str(row.iloc[0]).lower() 
                                           for keyword in ['str', 'sector', 'turn']):
                sector_row_idx = idx
                break
        
        if sector_row_idx is None:
            print("Could not find sector row in lap time data")
            return pd.DataFrame()
        
        # Extract sector names and lap data
        sectors = []
        lap_data = []
        
        # Get sector names from the first column
        for idx in range(sector_row_idx, len(df)):
            sector_name = df.iloc[idx, 0]
            if pd.notna(sector_name) and sector_name.strip():
                sectors.append(sector_name.strip())
                
                # Extract lap times for this sector
                lap_times = []
                for col_idx in range(1, len(df.columns) - 3):  # Exclude last 3 metadata columns
                    time_val = df.iloc[idx, col_idx]
                    if pd.notna(time_val) and self._is_valid_time(str(time_val)):
                        lap_times.append(self._parse_time_to_seconds(str(time_val)))
                    else:
                        lap_times.append(None)
                
                lap_data.append(lap_times)
        
        # Create structured DataFrame
        if not sectors or not lap_data:
            return pd.DataFrame()
        
        # Determine number of laps
        max_laps = max(len(times) for times in lap_data) if lap_data else 0
        
        # Create lap-based structure
        result_data = []
        for lap_num in range(max_laps):
            lap_dict = {'lap_number': lap_num + 1, 'session_id': self.session_id}
            
            for sector_idx, sector_name in enumerate(sectors):
                if lap_num < len(lap_data[sector_idx]):
                    lap_dict[f'sector_{sector_idx + 1}_{sector_name}'] = lap_data[sector_idx][lap_num]
                else:
                    lap_dict[f'sector_{sector_idx + 1}_{sector_name}'] = None
            
            # Calculate total lap time if we have all sectors
            sector_times = [lap_dict.get(f'sector_{i+1}_{sectors[i]}') 
                          for i in range(len(sectors))]
            if all(t is not None for t in sector_times):
                lap_dict['total_lap_time'] = sum(sector_times)
            else:
                lap_dict['total_lap_time'] = None
                
            result_data.append(lap_dict)
        
        return pd.DataFrame(result_data)
    
    def parse_telemetry_data(self) -> Optional[pd.DataFrame]:
        """
        Parse driver input telemetry data.
        
        Returns:
            DataFrame with telemetry data or None if not found
        """
        telemetry_file = self.session_parquet_path / "driverinputs.parquet"
        
        # If not found, try the base PARQUET directory (for shared files)
        if not telemetry_file.exists() and self.base_parquet_path:
            telemetry_file = self.base_parquet_path / "driverinputs.parquet"

        if not telemetry_file.exists():
            print(f"Telemetry file not found: {telemetry_file}")
            return None
            
        try:
            df = pd.read_parquet(telemetry_file)
            
            # Clean telemetry data
            cleaned_df = self._clean_telemetry_data(df)
            return cleaned_df
            
        except Exception as e:
            print(f"Error parsing telemetry: {e}")
            return None
    
    def _clean_telemetry_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and structure telemetry data.
        
        Args:
            df: Raw telemetry DataFrame
            
        Returns:
            Cleaned DataFrame with proper structure
        """
        # MoTeC CSV files often have metadata at the top, followed by a header row, then data.
        # We need to find the actual header row.
        data_start_idx = None
        header_row = None
        
        # Expected telemetry columns (case-insensitive for robustness)
        expected_cols = ['time', 'throttle', 'brake', 'steeringangle'] 
        
        for idx, row in df.iterrows():
            # Convert row to string and check for expected column names
            row_str = " ".join(str(x) for x in row.values if pd.notna(x)).lower()
            
            # Check if this row contains most of the expected column names
            if sum(col in row_str for col in expected_cols) >= len(expected_cols) / 2: # At least half
                data_start_idx = idx + 1 # Data starts on the next row
                header_row = row.values
                break
        
        if data_start_idx is None or header_row is None:
            print("Could not find telemetry data start or header row.")
            return pd.DataFrame()
        
        # Extract the actual telemetry data
        telemetry_df = df.iloc[data_start_idx:].copy()
        telemetry_df.reset_index(drop=True, inplace=True) # Reset index first

        # Determine the actual column names
        # Check if the first element of the header_row is the concatenated string
        if len(header_row) > 0 and isinstance(header_row[0], str) and 'TimeThrottleBrakeSteering' in header_row[0]:
            # This is the concatenated header case
            # Manually define expected columns based on the observed concatenated string
            potential_cols = ['Time', 'Throttle', 'Brake', 'SteeringWheelAngle', 'LatAccelms2', 'LongAccelms2', 'YawRate']
            
            # Assign these as the primary columns directly
            if len(telemetry_df.columns) >= len(potential_cols):
                telemetry_df.columns = potential_cols + list(telemetry_df.columns[len(potential_cols):])
            else:
                telemetry_df.columns = [f'col_{i}' for i in range(len(telemetry_df.columns))]
            
            # Drop the 'untagged_driverinputscsv' artifact if it exists
            if 'untagged_driverinputscsv' in telemetry_df.columns:
                telemetry_df.drop(columns=['untagged_driverinputscsv'], inplace=True)

        else:
            # Original logic for cleaning header names if not concatenated
            cleaned_header = [re.sub(r'\W+', '', str(col)).strip() for col in header_row]
            if len(cleaned_header) == len(telemetry_df.columns):
                telemetry_df.columns = cleaned_header
            else:
                print(f"Warning: Cleaned header length ({len(cleaned_header)}) does not match DataFrame column count ({len(telemetry_df.columns)}). Using default columns.")
                telemetry_df.columns = [f'col_{i}' for i in range(len(telemetry_df.columns))]
        
        print(f"Original Telemetry Columns after header extraction/manual fix: {telemetry_df.columns.tolist()}")

        # Standardize column names (this will now work on the manually set or cleaned headers)
        column_mapping = {
            'time': 'Time',
            'throttle': 'Throttle',
            'brake': 'Brake',
            'steeringangle': 'SteeringAngle',
            'steering': 'SteeringAngle', # Common alternative
            'speed': 'Speed', # Often useful for telemetry
            'distance': 'Distance', # Often useful for telemetry
            'lataccelms2': 'LatAccel', # Standardize
            'longaccelms2': 'LongAccel', # Standardize
            'yawrate': 'YawRate' # Standardize
        }
        
        new_columns = {}
        for col in telemetry_df.columns:
            cleaned_col = re.sub(r'\W+', '', str(col)).strip().lower()
            if cleaned_col in column_mapping:
                new_columns[col] = column_mapping[cleaned_col]
            else:
                new_columns[col] = col # Keep original if no mapping
        
        telemetry_df.rename(columns=new_columns, inplace=True)
        print(f"Renamed Telemetry Columns: {telemetry_df.columns.tolist()}")

        # Convert relevant columns to numeric, coercing errors
        for col in ['Time', 'Throttle', 'Brake', 'SteeringAngle', 'Speed', 'Distance']:
            if col in telemetry_df.columns:
                telemetry_df[col] = pd.to_numeric(telemetry_df[col], errors='coerce')
        
        return telemetry_df
    
    def parse_vehicle_data(self) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Parse various vehicle data files.
        
        Returns:
            Dictionary of DataFrames for different vehicle systems
        """
        vehicle_data = {}
        
        # Define vehicle data files to parse
        vehicle_files = {
            'fuel': 'fuel.parquet',
            'tire_temps_left': 'LeftsideTireTemps.parquet',
            'tire_temps_right': 'rightsidetiretemps.parquet',
            'aero_map': 'aeromap.parquet',
            'engine': 'engineoverview.parquet',
            'suspension': 'Suspension Histogram.parquet'
        }
        
        for data_type, filename in vehicle_files.items():
            file_path = self.session_parquet_path / filename
            
            # If not found in session-specific, try base parquet path
            if not file_path.exists() and self.base_parquet_path:
                file_path = self.base_parquet_path / filename

            if file_path.exists():
                try:
                    df = pd.read_parquet(file_path)
                    vehicle_data[data_type] = df
                except Exception as e:
                    print(f"Error parsing {data_type} data: {e}")
                    vehicle_data[data_type] = None
            else:
                vehicle_data[data_type] = None
        
        return vehicle_data
    
    def get_session_metadata(self) -> Dict[str, str]:
        """
        Extract session metadata from available data.
        
        Returns:
            Dictionary with session information
        """
        metadata = {
            'session_id': self.session_id,
            'session_path': str(self.session_path),
            'session_parquet_path': str(self.session_parquet_path),
            'base_parquet_path': str(self.base_parquet_path) if self.base_parquet_path else 'N/A'
        }
        
        # Try to extract additional metadata from telemetry file
        try:
            telemetry_file = self.session_parquet_path / "driverinputs.parquet"
            if not telemetry_file.exists() and self.base_parquet_path:
                telemetry_file = self.base_parquet_path / "driverinputs.parquet"

            if telemetry_file.exists():
                df = pd.read_parquet(telemetry_file)
                
                # Extract metadata from header rows
                for idx in range(min(10, len(df))):
                    row_data = str(df.iloc[idx, 0])
                    
                    if 'Venue' in row_data:
                        venue_match = re.search(r'"Venue","([^"]+)"', row_data)
                        if venue_match:
                            metadata['track'] = venue_match.group(1)
                    
                    elif 'Vehicle' in row_data:
                        vehicle_match = re.search(r'"Vehicle","([^"]+)"', row_data)
                        if vehicle_match:
                            metadata['vehicle'] = vehicle_match.group(1)
                    
                    elif 'Driver' in row_data:
                        driver_match = re.search(r'"Driver","([^"]+)"', row_data)
                        if driver_match:
                            metadata['driver'] = driver_match.group(1)
        
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        
        return metadata
    
    @staticmethod
    def _is_valid_time(time_str: str) -> bool:
        """Check if string represents a valid lap time."""
        time_pattern = r'^\d{1,2}:\d{2}\.\d{3}$'
        return bool(re.match(time_pattern, time_str.strip()))
    
    @staticmethod
    def _parse_time_to_seconds(time_str: str) -> float:
        """Convert time string (MM:SS.mmm) to seconds."""
        try:
            time_str = time_str.strip()
            if ':' in time_str:
                minutes, seconds = time_str.split(':')
                return float(minutes) * 60 + float(seconds)
            else:
                return float(time_str)
        except (ValueError, AttributeError):
            return 0.0
    
    @staticmethod
    def _looks_like_telemetry_data(value: str) -> bool:
        """Check if value looks like telemetry data (numeric or timestamp)."""
        try:
            float(value)
            return True
        except ValueError:
            # Check for timestamp patterns
            timestamp_patterns = [
                r'^\d+\.\d+$',  # Decimal timestamp
                r'^\d{1,2}:\d{2}:\d{2}',  # Time format
            ]
            return any(re.match(pattern, value) for pattern in timestamp_patterns)
