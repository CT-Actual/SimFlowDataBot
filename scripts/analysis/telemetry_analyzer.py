import pandas as pd
import numpy as np
from typing import Optional, Dict

class TelemetryAnalyzer:
    """
    Analyzes raw telemetry data for driver performance metrics.
    """

    def __init__(self, telemetry_data: pd.DataFrame):
        """
        Initializes the TelemetryAnalyzer with raw telemetry data.

        Args:
            telemetry_data (pd.DataFrame): DataFrame containing raw telemetry data.
                                           Expected columns: 'Time', 'Throttle', 'Brake', 'SteeringAngle'.
        """
        self.telemetry_data = telemetry_data
        self._validate_columns()

    def _validate_columns(self):
        """
        Validates that essential columns are present in the telemetry data.
        """
        required_columns = ['Time', 'Throttle', 'Brake', 'SteeringAngle']
        for col in required_columns:
            if col not in self.telemetry_data.columns:
                print(f"Warning: Required telemetry column '{col}' not found.")
                # Consider raising an error or handling missing columns more robustly
                # For now, we'll proceed, but analysis might be incomplete.

    def analyze_input_smoothness(self) -> Dict[str, float]:
        """
        Analyzes driver input smoothness (throttle, brake, steering).
        Lower values indicate smoother inputs.

        Returns:
            Dict[str, float]: Dictionary with smoothness metrics.
        """
        smoothness_metrics = {}

        # Throttle smoothness: standard deviation of throttle changes
        if 'Throttle' in self.telemetry_data.columns:
            throttle_diff = self.telemetry_data['Throttle'].diff().dropna()
            smoothness_metrics['throttle_smoothness'] = throttle_diff.std() if not throttle_diff.empty else 0.0

        # Brake smoothness: standard deviation of brake changes
        if 'Brake' in self.telemetry_data.columns:
            brake_diff = self.telemetry_data['Brake'].diff().dropna()
            smoothness_metrics['brake_smoothness'] = brake_diff.std() if not brake_diff.empty else 0.0

        # Steering smoothness: standard deviation of steering angle changes
        if 'SteeringAngle' in self.telemetry_data.columns:
            steering_diff = self.telemetry_data['SteeringAngle'].diff().dropna()
            smoothness_metrics['steering_smoothness'] = steering_diff.std() if not steering_diff.empty else 0.0
        
        return smoothness_metrics

    def analyze_braking_points(self) -> Dict[str, float]:
        """
        Analyzes braking points and efficiency.
        This is a simplified analysis. More advanced analysis would require track data.

        Returns:
            Dict[str, float]: Dictionary with braking metrics.
        """
        braking_metrics = {}

        if 'Brake' in self.telemetry_data.columns:
            # Identify braking events (where brake input is significant)
            # Threshold can be adjusted based on data characteristics
            braking_threshold = 0.1 # e.g., 10% brake application
            braking_events = self.telemetry_data[self.telemetry_data['Brake'] > braking_threshold]

            if not braking_events.empty:
                # Average brake application during braking events
                braking_metrics['avg_brake_application'] = braking_events['Brake'].mean()
                
                # Number of distinct braking events (simplified)
                # A more robust approach would group consecutive braking points
                braking_metrics['num_braking_events'] = (braking_events['Brake'].diff().fillna(0).abs() > braking_threshold).sum()
            else:
                braking_metrics['avg_brake_application'] = 0.0
                braking_metrics['num_braking_events'] = 0
        
        return braking_metrics

    def analyze_throttle_application(self) -> Dict[str, float]:
        """
        Analyzes throttle application patterns.

        Returns:
            Dict[str, float]: Dictionary with throttle metrics.
        """
        throttle_metrics = {}

        if 'Throttle' in self.telemetry_data.columns:
            # Average throttle application when throttle is applied
            throttle_applied = self.telemetry_data[self.telemetry_data['Throttle'] > 0.05] # e.g., >5% throttle
            if not throttle_applied.empty:
                throttle_metrics['avg_throttle_application'] = throttle_applied['Throttle'].mean()
                throttle_metrics['percent_throttle_on'] = (len(throttle_applied) / len(self.telemetry_data)) * 100
            else:
                throttle_metrics['avg_throttle_application'] = 0.0
                throttle_metrics['percent_throttle_on'] = 0.0
        
        return throttle_metrics

    def get_advanced_telemetry_kpis(self) -> Dict[str, float]:
        """
        Combines all advanced telemetry analysis into a single dictionary of KPIs.

        Returns:
            Dict[str, float]: Combined dictionary of advanced telemetry KPIs.
        """
        kpis = {}
        kpis.update(self.analyze_input_smoothness())
        kpis.update(self.analyze_braking_points())
        kpis.update(self.analyze_throttle_application())
        return kpis
