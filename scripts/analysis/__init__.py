"""
SimFlowDataAgent Analysis Package

Racing data analysis and KPI computation system for MoTeC exports.
"""

__version__ = "1.0.0"
__author__ = "SimFlowDataAgent"

from .data_parser import DataParser
from .lap_analyzer import LapAnalyzer
from .kpi_calculator import KPICalculator
from .report_generator import ReportGenerator

__all__ = [
    'DataParser',
    'LapAnalyzer', 
    'KPICalculator',
    'ReportGenerator'
]
