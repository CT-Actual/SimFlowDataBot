"""
KPI Calculator Module

Computes comprehensive racing performance KPIs from analyzed data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class KPICalculator:
    """Calculate comprehensive racing performance KPIs."""
    
    def __init__(self, session_metadata: Dict[str, str]):
        """
        Initialize KPI calculator.
        
        Args:
            session_metadata: Session information from DataParser
        """
        self.session_metadata = session_metadata
        self.session_id = session_metadata.get('session_id', 'unknown')
        
    def calculate_session_kpis(self, 
                              lap_summary: Dict[str, Any],
                              vehicle_data: Optional[Dict[str, pd.DataFrame]] = None,
                              advanced_telemetry_kpis: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive session KPIs.
        
        Args:
            lap_summary: Lap analysis summary from LapAnalyzer
            vehicle_data: Optional vehicle data from DataParser
            advanced_telemetry_kpis: Optional advanced telemetry KPIs from TelemetryAnalyzer
            
        Returns:
            Dictionary with all calculated KPIs
        """
        kpis = {
            'session_info': self._build_session_info(),
            'lap_performance': self._calculate_lap_performance_kpis(lap_summary),
            'consistency_metrics': self._calculate_consistency_kpis(lap_summary),
            'sector_performance': self._calculate_sector_kpis(lap_summary),
            'session_progression': self._calculate_progression_kpis(lap_summary),
        }
        
        # Add vehicle KPIs if data is available
        if vehicle_data:
            kpis['vehicle_performance'] = self._calculate_vehicle_kpis(vehicle_data)
        
        # Add advanced telemetry KPIs if available
        if advanced_telemetry_kpis:
            kpis['advanced_telemetry'] = advanced_telemetry_kpis
        
        # Calculate performance summary (needs kpis to be partially built)
        kpis['performance_summary'] = self._calculate_performance_summary(lap_summary, kpis)

        # Add overall session rating
        kpis['session_rating'] = self._calculate_session_rating(kpis)
        
        return kpis
    
    def _build_session_info(self) -> Dict[str, Any]:
        """Build session information section."""
        return {
            'session_id': self.session_id,
            'track': self.session_metadata.get('track', 'Unknown'),
            'vehicle': self.session_metadata.get('vehicle', 'Unknown'),
            'driver': self.session_metadata.get('driver', 'Unknown'),
            'analysis_timestamp': datetime.now().isoformat(),
            'session_path': self.session_metadata.get('session_path', '')
        }
    
    def _calculate_lap_performance_kpis(self, lap_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate lap performance KPIs."""
        best_lap = lap_summary.get('best_lap_time', 0)
        avg_lap = lap_summary.get('average_lap_time', 0)
        theoretical_best = lap_summary.get('theoretical_best', 0)
        
        return {
            'best_lap_time_seconds': best_lap,
            'best_lap_time_formatted': self._format_lap_time(best_lap),
            'average_lap_time_seconds': avg_lap,
            'average_lap_time_formatted': self._format_lap_time(avg_lap),
            'theoretical_best_seconds': theoretical_best,
            'theoretical_best_formatted': self._format_lap_time(theoretical_best),
            'time_lost_to_theoretical': lap_summary.get('time_lost_to_theoretical', 0),
            'pace_efficiency_percent': (theoretical_best / best_lap * 100) if best_lap > 0 else 0,
            'average_vs_best_gap': avg_lap - best_lap if avg_lap > 0 and best_lap > 0 else 0,
            'average_vs_best_percent': ((avg_lap - best_lap) / best_lap * 100) if best_lap > 0 else 0
        }
    
    def _calculate_consistency_kpis(self, lap_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate consistency metrics."""
        consistency_index = lap_summary.get('consistency_index', 0)
        performance_window = lap_summary.get('performance_window_1pct', 0)
        lap_std = lap_summary.get('lap_time_std', 0)
        
        # Consistency rating (lower is better)
        if consistency_index <= 0.01:
            consistency_rating = "Excellent"
        elif consistency_index <= 0.02:
            consistency_rating = "Good"
        elif consistency_index <= 0.03:
            consistency_rating = "Average"
        elif consistency_index <= 0.05:
            consistency_rating = "Poor"
        else:
            consistency_rating = "Very Poor"
        
        return {
            'consistency_index': consistency_index,
            'consistency_rating': consistency_rating,
            'lap_time_standard_deviation': lap_std,
            'performance_window_1_percent': performance_window,
            'consistency_score': max(0, 100 - (consistency_index * 1000)),  # 0-100 scale
            'repeatability_factor': performance_window / 100 if performance_window > 0 else 0
        }
    
    def _calculate_sector_kpis(self, lap_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate sector-specific KPIs."""
        sector_analysis = lap_summary.get('sector_analysis', {})
        
        if not sector_analysis:
            return {'sector_count': 0, 'sectors': {}}
        
        sector_kpis = {}
        total_improvement = 0
        best_sector = None
        worst_sector = None
        best_consistency = float('inf')
        worst_consistency = 0
        
        for sector_name, sector_data in sector_analysis.items():
            consistency = sector_data.get('consistency', 0)
            improvement = sector_data.get('improvement', 0)
            
            sector_kpis[sector_name] = {
                'best_time': sector_data.get('best_time', 0),
                'best_time_formatted': self._format_lap_time(sector_data.get('best_time', 0)),
                'average_time': sector_data.get('average_time', 0),
                'consistency_index': consistency,
                'improvement_seconds': improvement,
                'consistency_rating': self._rate_sector_consistency(consistency),
                'improvement_rating': self._rate_sector_improvement(improvement)
            }
            
            total_improvement += improvement
            
            # Track best/worst sectors
            if consistency < best_consistency:
                best_consistency = consistency
                best_sector = sector_name
            
            if consistency > worst_consistency:
                worst_consistency = consistency
                worst_sector = sector_name
        
        return {
            'sector_count': len(sector_analysis),
            'sectors': sector_kpis,
            'overall_sector_improvement': total_improvement,
            'most_consistent_sector': best_sector,
            'least_consistent_sector': worst_sector,
            'sector_consistency_range': worst_consistency - best_consistency
        }
    
    def _calculate_progression_kpis(self, lap_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate session progression metrics."""
        progression_trend = lap_summary.get('lap_progression_trend', 0)
        valid_laps = lap_summary.get('valid_laps', 0)
        
        # Determine progression rating
        if progression_trend > 0.1:
            progression_rating = "Strong Improvement"
        elif progression_trend > 0.05:
            progression_rating = "Moderate Improvement"
        elif progression_trend > -0.05:
            progression_rating = "Stable"
        elif progression_trend > -0.1:
            progression_rating = "Slight Decline"
        else:
            progression_rating = "Significant Decline"
        
        return {
            'lap_progression_trend': progression_trend,
            'progression_rating': progression_rating,
            'session_length_laps': valid_laps,
            'learning_rate': abs(progression_trend) if progression_trend > 0 else 0,
            'session_stability': 1 - abs(progression_trend) if abs(progression_trend) < 1 else 0
        }
    
    def _calculate_performance_summary(self, lap_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance summary."""
        best_lap = lap_summary.get('best_lap_time', 0)
        consistency_index = lap_summary.get('consistency_index', 0)
        performance_window = lap_summary.get('performance_window_1pct', 0)
        progression_trend = lap_summary.get('lap_progression_trend', 0)
        
        # Calculate overall performance score (0-100)
        pace_score = 50  # Base score, would need reference data for proper rating
        consistency_score = max(0, 100 - (consistency_index * 1000))
        progression_score = min(100, max(0, 50 + (progression_trend * 500)))
        
        overall_score = (pace_score + consistency_score + progression_score) / 3
        
        # Performance grade
        if overall_score >= 90:
            grade = "A+"
        elif overall_score >= 85:
            grade = "A"
        elif overall_score >= 80:
            grade = "A-"
        elif overall_score >= 75:
            grade = "B+"
        elif overall_score >= 70:
            grade = "B"
        elif overall_score >= 65:
            grade = "B-"
        elif overall_score >= 60:
            grade = "C+"
        elif overall_score >= 55:
            grade = "C"
        elif overall_score >= 50:
            grade = "C-"
        else:
            grade = "D"
        
        return {
            'overall_performance_score': round(overall_score, 1),
            'performance_grade': grade,
            'pace_score': round(pace_score, 1),
            'consistency_score': round(consistency_score, 1),
            'progression_score': round(progression_score, 1),
            'key_strengths': self._identify_strengths(kpis_full), # Pass full kpis
            'improvement_areas': self._identify_improvement_areas(kpis_full) # Pass full kpis
        }
    
    def _calculate_performance_summary(self, lap_summary: Dict[str, Any], kpis_full: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance summary."""
        best_lap = lap_summary.get('best_lap_time', 0)
        consistency_index = lap_summary.get('consistency_index', 0)
        performance_window = lap_summary.get('performance_window_1pct', 0)
        progression_trend = lap_summary.get('lap_progression_trend', 0)
        
        # Calculate overall performance score (0-100)
        pace_score = 50  # Base score, would need reference data for proper rating
        consistency_score = max(0, 100 - (consistency_index * 1000))
        progression_score = min(100, max(0, 50 + (progression_trend * 500)))
        
        overall_score = (pace_score + consistency_score + progression_score) / 3
        
        # Performance grade
        if overall_score >= 90:
            grade = "A+"
        elif overall_score >= 85:
            grade = "A"
        elif overall_score >= 80:
            grade = "A-"
        elif overall_score >= 75:
            grade = "B+"
        elif overall_score >= 70:
            grade = "B"
        elif overall_score >= 65:
            grade = "B-"
        elif overall_score >= 60:
            grade = "C+"
        elif overall_score >= 55:
            grade = "C"
        elif overall_score >= 50:
            grade = "C-"
        else:
            grade = "D"
        
        return {
            'overall_performance_score': round(overall_score, 1),
            'performance_grade': grade,
            'pace_score': round(pace_score, 1),
            'consistency_score': round(consistency_score, 1),
            'progression_score': round(progression_score, 1),
            'key_strengths': self._identify_strengths(kpis_full), # Pass full kpis
            'improvement_areas': self._identify_improvement_areas(kpis_full) # Pass full kpis
        }
    
    def _calculate_vehicle_kpis(self, vehicle_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate vehicle-specific KPIs if data is available."""
        vehicle_kpis = {}
        
        # Fuel efficiency
        if vehicle_data.get('fuel') is not None:
            fuel_df = vehicle_data['fuel']
            if not fuel_df.empty:
                vehicle_kpis['fuel'] = {
                    'data_available': True,
                    'total_rows': len(fuel_df)
                }
        
        # Tire performance
        if vehicle_data.get('tire_temps_left') is not None or vehicle_data.get('tire_temps_right') is not None:
            vehicle_kpis['tires'] = {
                'left_data_available': vehicle_data.get('tire_temps_left') is not None,
                'right_data_available': vehicle_data.get('tire_temps_right') is not None
            }
        
        # Aerodynamics
        if vehicle_data.get('aero_map') is not None:
            aero_df = vehicle_data['aero_map']
            if not aero_df.empty:
                vehicle_kpis['aerodynamics'] = {
                    'data_available': True,
                    'total_rows': len(aero_df)
                }
        
        return vehicle_kpis
    
    def _calculate_session_rating(self, kpis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall session rating."""
        performance_score = kpis['performance_summary']['overall_performance_score']
        consistency_score = kpis['consistency_metrics']['consistency_score']
        
        # Weight the scores
        weighted_score = (performance_score * 0.6) + (consistency_score * 0.4)
        
        return {
            'overall_rating': round(weighted_score, 1),
            'rating_breakdown': {
                'performance_weight': 0.6,
                'consistency_weight': 0.4,
                'weighted_score': round(weighted_score, 1)
            }
        }
    
    def _identify_strengths(self, kpis: Dict[str, Any]) -> List[str]:
        """Identify key strengths from the session."""
        strengths = []
        
        lap_summary = kpis['lap_performance'] # Use the full kpis dict
        consistency_index = kpis['consistency_metrics']['consistency_index']
        performance_window = kpis['consistency_metrics']['performance_window_1_percent']
        progression_trend = kpis['session_progression']['lap_progression_trend']
        
        if consistency_index <= 0.02:
            strengths.append("Excellent lap time consistency")
        
        if performance_window >= 80:
            strengths.append("High percentage of laps within optimal window")
        
        if progression_trend > 0.05:
            strengths.append("Strong improvement throughout session")

        # Add telemetry-based strengths
        if 'advanced_telemetry' in kpis:
            telemetry = kpis['advanced_telemetry']
            if telemetry.get('throttle_smoothness', float('inf')) < 0.05: # Example threshold
                strengths.append("Smooth throttle application")
            if telemetry.get('brake_smoothness', float('inf')) < 0.05: # Example threshold
                strengths.append("Smooth braking technique")
            if telemetry.get('steering_smoothness', float('inf')) < 0.1: # Example threshold
                strengths.append("Precise steering inputs")
        
        if not strengths:
            strengths.append("Completed session with valid data")
        
        return strengths
    
    def _identify_improvement_areas(self, kpis: Dict[str, Any]) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        
        lap_summary = kpis['lap_performance'] # Use the full kpis dict
        consistency_index = kpis['consistency_metrics']['consistency_index']
        time_lost = lap_summary.get('time_lost_to_theoretical', 0)
        progression_trend = kpis['session_progression']['lap_progression_trend']
        
        if consistency_index > 0.03:
            improvements.append("Improve lap time consistency")
        
        if time_lost > 0.5:
            improvements.append("Reduce gap to theoretical best lap")
        
        if progression_trend < -0.05:
            improvements.append("Maintain performance throughout session")

        # Add telemetry-based improvement areas
        if 'advanced_telemetry' in kpis:
            telemetry = kpis['advanced_telemetry']
            if telemetry.get('throttle_smoothness', 0.0) > 0.1: # Example threshold
                improvements.append("Smoothen throttle application")
            if telemetry.get('brake_smoothness', 0.0) > 0.1: # Example threshold
                improvements.append("Refine braking technique for smoother transitions")
            if telemetry.get('steering_smoothness', 0.0) > 0.2: # Example threshold
                improvements.append("Work on smoother steering inputs")
        
        return improvements
    
    @staticmethod
    def _format_lap_time(seconds: float) -> str:
        """Format lap time in MM:SS.mmm format."""
        if seconds <= 0:
            return "00:00.000"
        
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        
        return f"{minutes:02d}:{remaining_seconds:06.3f}"
    
    @staticmethod
    def _rate_sector_consistency(consistency: float) -> str:
        """Rate sector consistency."""
        if consistency <= 0.01:
            return "Excellent"
        elif consistency <= 0.02:
            return "Good"
        elif consistency <= 0.03:
            return "Average"
        else:
            return "Poor"
    
    @staticmethod
    def _rate_sector_improvement(improvement: float) -> str:
        """Rate sector improvement."""
        if improvement > 0.1:
            return "Strong Improvement"
        elif improvement > 0.05:
            return "Moderate Improvement"
        elif improvement > -0.05:
            return "Stable"
        else:
            return "Decline"
    
    def export_kpis_to_json(self, kpis: Dict[str, Any], output_path: str) -> bool:
        """
        Export KPIs to JSON file.
        
        Args:
            kpis: KPI dictionary to export
            output_path: Path to save JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(kpis, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error exporting KPIs to JSON: {e}")
            return False
