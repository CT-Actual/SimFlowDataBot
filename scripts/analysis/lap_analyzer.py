"""
Lap Analyzer Module

Analyzes lap time data and computes lap-based performance metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LapAnalysisResult:
    """Container for lap analysis results."""
    best_lap_time: float
    average_lap_time: float
    lap_time_std: float
    consistency_index: float
    theoretical_best: float
    time_lost_to_theoretical: float
    valid_laps: int
    sector_analysis: Dict[str, Dict[str, float]]
    lap_progression: List[float]
    performance_window: float


class LapAnalyzer:
    """Analyze lap time data and compute performance metrics."""
    
    def __init__(self, lap_data: pd.DataFrame):
        """
        Initialize analyzer with lap time data.
        
        Args:
            lap_data: DataFrame with lap time data from DataParser
        """
        self.lap_data = lap_data.copy()
        self.session_id = lap_data['session_id'].iloc[0] if not lap_data.empty else "unknown"
        
        # Identify sector columns
        self.sector_columns = [col for col in lap_data.columns 
                              if col.startswith('sector_') and not col.endswith('_time')]
        
        # Clean data
        self._clean_lap_data()
    
    def _clean_lap_data(self):
        """Clean lap data by removing invalid laps and outliers."""
        # Remove laps with missing total lap time
        self.lap_data = self.lap_data.dropna(subset=['total_lap_time'])
        
        # Remove obvious outliers (laps > 3x median or < 0.5x median)
        if len(self.lap_data) > 3:
            median_time = self.lap_data['total_lap_time'].median()
            
            # Define outlier bounds
            lower_bound = median_time * 0.5
            upper_bound = median_time * 3.0
            
            # Filter outliers
            mask = (self.lap_data['total_lap_time'] >= lower_bound) & \
                   (self.lap_data['total_lap_time'] <= upper_bound)
            
            outliers_removed = len(self.lap_data) - mask.sum()
            if outliers_removed > 0:
                print(f"Removed {outliers_removed} outlier laps")
            
            self.lap_data = self.lap_data[mask]
        
        # Reset index
        self.lap_data.reset_index(drop=True, inplace=True)
    
    def analyze_laps(self) -> LapAnalysisResult:
        """
        Perform comprehensive lap analysis.
        
        Returns:
            LapAnalysisResult with all computed metrics
        """
        if self.lap_data.empty:
            return self._empty_result()
        
        # Basic lap time metrics
        lap_times = self.lap_data['total_lap_time']
        
        best_lap = lap_times.min()
        avg_lap = lap_times.mean()
        lap_std = lap_times.std()
        consistency_index = lap_std / avg_lap if avg_lap > 0 else 0
        valid_laps = len(lap_times)
        
        # Theoretical best lap (sum of best sectors)
        theoretical_best = self._calculate_theoretical_best()
        time_lost = best_lap - theoretical_best if theoretical_best > 0 else 0
        
        # Sector analysis
        sector_analysis = self._analyze_sectors()
        
        # Lap progression analysis
        lap_progression = self._analyze_lap_progression()
        
        # Performance window (% of laps within 1% of best)
        performance_window = self._calculate_performance_window(lap_times, best_lap)
        
        return LapAnalysisResult(
            best_lap_time=best_lap,
            average_lap_time=avg_lap,
            lap_time_std=lap_std,
            consistency_index=consistency_index,
            theoretical_best=theoretical_best,
            time_lost_to_theoretical=time_lost,
            valid_laps=valid_laps,
            sector_analysis=sector_analysis,
            lap_progression=lap_progression,
            performance_window=performance_window
        )
    
    def _calculate_theoretical_best(self) -> float:
        """Calculate theoretical best lap from best sector times."""
        if not self.sector_columns:
            return 0.0
        
        theoretical_time = 0.0
        sectors_found = 0
        
        for sector_col in self.sector_columns:
            sector_times = self.lap_data[sector_col].dropna()
            if not sector_times.empty:
                theoretical_time += sector_times.min()
                sectors_found += 1
        
        return theoretical_time if sectors_found > 0 else 0.0
    
    def _analyze_sectors(self) -> Dict[str, Dict[str, float]]:
        """Analyze sector performance."""
        sector_analysis = {}
        
        for sector_col in self.sector_columns:
            sector_times = self.lap_data[sector_col].dropna()
            
            if not sector_times.empty:
                sector_name = sector_col.replace('sector_', '').replace('_', ' ')
                
                sector_analysis[sector_name] = {
                    'best_time': sector_times.min(),
                    'average_time': sector_times.mean(),
                    'std_dev': sector_times.std(),
                    'consistency': sector_times.std() / sector_times.mean() if sector_times.mean() > 0 else 0,
                    'improvement': self._calculate_sector_improvement(sector_times)
                }
        
        return sector_analysis
    
    def _calculate_sector_improvement(self, sector_times: pd.Series) -> float:
        """Calculate improvement from first to last 3 laps in sector."""
        if len(sector_times) < 6:
            return 0.0
        
        first_3 = sector_times.head(3).mean()
        last_3 = sector_times.tail(3).mean()
        
        return first_3 - last_3  # Positive = improvement
    
    def _analyze_lap_progression(self) -> List[float]:
        """Analyze lap time progression throughout session."""
        if len(self.lap_data) < 2:
            return []
        
        lap_times = self.lap_data['total_lap_time'].tolist()
        
        # Calculate rolling average improvement
        window_size = min(3, len(lap_times) // 2)
        progression = []
        
        for i in range(window_size, len(lap_times)):
            current_window = lap_times[i-window_size:i]
            previous_window = lap_times[max(0, i-2*window_size):i-window_size]
            
            if previous_window:
                current_avg = np.mean(current_window)
                previous_avg = np.mean(previous_window)
                improvement = previous_avg - current_avg  # Positive = improvement
                progression.append(improvement)
        
        return progression
    
    def _calculate_performance_window(self, lap_times: pd.Series, best_lap: float) -> float:
        """Calculate percentage of laps within 1% of best lap time."""
        if best_lap <= 0:
            return 0.0
        
        threshold = best_lap * 1.01  # 1% window
        laps_in_window = (lap_times <= threshold).sum()
        
        return (laps_in_window / len(lap_times)) * 100
    
    def get_lap_summary(self) -> Dict[str, any]:
        """Get a summary of lap analysis in dictionary format."""
        result = self.analyze_laps()
        
        return {
            'session_id': self.session_id,
            'total_laps': len(self.lap_data),
            'valid_laps': result.valid_laps,
            'best_lap_time': result.best_lap_time,
            'average_lap_time': result.average_lap_time,
            'lap_time_std': result.lap_time_std,
            'consistency_index': result.consistency_index,
            'theoretical_best': result.theoretical_best,
            'time_lost_to_theoretical': result.time_lost_to_theoretical,
            'performance_window_1pct': result.performance_window,
            'sector_count': len(result.sector_analysis),
            'lap_progression_trend': np.mean(result.lap_progression) if result.lap_progression else 0,
            'sector_analysis': result.sector_analysis
        }
    
    def get_fastest_lap_details(self) -> Dict[str, any]:
        """Get detailed information about the fastest lap."""
        if self.lap_data.empty:
            return {}
        
        fastest_lap_idx = self.lap_data['total_lap_time'].idxmin()
        fastest_lap = self.lap_data.loc[fastest_lap_idx]
        
        details = {
            'lap_number': fastest_lap['lap_number'],
            'total_time': fastest_lap['total_lap_time'],
            'session_id': fastest_lap['session_id']
        }
        
        # Add sector times
        for sector_col in self.sector_columns:
            if pd.notna(fastest_lap[sector_col]):
                sector_name = sector_col.replace('sector_', '').replace('_', ' ')
                details[f'sector_{sector_name}'] = fastest_lap[sector_col]
        
        return details
    
    def compare_to_theoretical_best(self) -> Dict[str, float]:
        """Compare actual best lap to theoretical best by sector."""
        if self.lap_data.empty or not self.sector_columns:
            return {}
        
        fastest_lap_idx = self.lap_data['total_lap_time'].idxmin()
        fastest_lap = self.lap_data.loc[fastest_lap_idx]
        
        comparison = {}
        
        for sector_col in self.sector_columns:
            if pd.notna(fastest_lap[sector_col]):
                sector_name = sector_col.replace('sector_', '').replace('_', ' ')
                actual_time = fastest_lap[sector_col]
                best_possible = self.lap_data[sector_col].min()
                
                time_lost = actual_time - best_possible
                comparison[sector_name] = {
                    'actual_time': actual_time,
                    'best_possible': best_possible,
                    'time_lost': time_lost,
                    'percentage_lost': (time_lost / best_possible * 100) if best_possible > 0 else 0
                }
        
        return comparison
    
    def _empty_result(self) -> LapAnalysisResult:
        """Return empty result for cases with no valid data."""
        return LapAnalysisResult(
            best_lap_time=0.0,
            average_lap_time=0.0,
            lap_time_std=0.0,
            consistency_index=0.0,
            theoretical_best=0.0,
            time_lost_to_theoretical=0.0,
            valid_laps=0,
            sector_analysis={},
            lap_progression=[],
            performance_window=0.0
        )
