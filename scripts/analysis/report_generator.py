"""
Report Generator Module

Generates comprehensive racing analysis reports in multiple formats.
"""

import pandas as pd
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import os


class ReportGenerator:
    """Generate comprehensive racing analysis reports."""
    
    def __init__(self, session_id: str, output_dir: str):
        """
        Initialize report generator.
        
        Args:
            session_id: Session identifier
            output_dir: Directory to save reports
        """
        self.session_id = session_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_comprehensive_report(self, 
                                    kpis: Dict[str, Any],
                                    lap_data: Optional[pd.DataFrame] = None) -> Dict[str, str]:
        """
        Generate comprehensive analysis report in multiple formats.
        
        Args:
            kpis: KPI data from KPICalculator
            lap_data: Optional lap data for detailed analysis
            
        Returns:
            Dictionary with paths to generated reports
        """
        report_paths = {}
        
        # Generate JSON report
        json_path = self._generate_json_report(kpis)
        if json_path:
            report_paths['json'] = json_path
        
        # Generate Markdown report
        md_path = self._generate_markdown_report(kpis)
        if md_path:
            report_paths['markdown'] = md_path
        
        # Generate CSV summary
        csv_path = self._generate_csv_summary(kpis, lap_data)
        if csv_path:
            report_paths['csv'] = csv_path
        
        # Generate executive summary
        summary_path = self._generate_executive_summary(kpis)
        if summary_path:
            report_paths['executive_summary'] = summary_path
        
        return report_paths
    
    def _generate_json_report(self, kpis: Dict[str, Any]) -> Optional[str]:
        """Generate detailed JSON report."""
        try:
            json_path = self.output_dir / f"{self.session_id}_analysis.json"
            
            with open(json_path, 'w') as f:
                json.dump(kpis, f, indent=2, default=str)
            
            return str(json_path)
        except Exception as e:
            print(f"Error generating JSON report: {e}")
            return None
    
    def _generate_markdown_report(self, kpis: Dict[str, Any]) -> Optional[str]:
        """Generate comprehensive Markdown report."""
        try:
            md_path = self.output_dir / f"{self.session_id}_report.md"
            
            # Build markdown content
            md_content = self._build_markdown_content(kpis)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return str(md_path)
        except Exception as e:
            print(f"Error generating Markdown report: {e}")
            return None
    
    def _build_markdown_content(self, kpis: Dict[str, Any]) -> str:
        """Build comprehensive Markdown report content."""
        session_info = kpis.get('session_info', {})
        lap_perf = kpis.get('lap_performance', {})
        consistency = kpis.get('consistency_metrics', {})
        sectors = kpis.get('sector_performance', {})
        progression = kpis.get('session_progression', {})
        summary = kpis.get('performance_summary', {})
        rating = kpis.get('session_rating', {})
        
        md_content = f"""# Racing Analysis Report

## Session Information
- **Session ID**: {session_info.get('session_id', 'Unknown')}
- **Track**: {session_info.get('track', 'Unknown')}
- **Vehicle**: {session_info.get('vehicle', 'Unknown')}
- **Driver**: {session_info.get('driver', 'Unknown')}
- **Analysis Date**: {session_info.get('analysis_timestamp', 'Unknown')}

---

## 🏁 Performance Summary

### Overall Rating: {summary.get('performance_grade', 'N/A')} ({rating.get('overall_rating', 0)}/100)

**Key Performance Indicators:**
- **Best Lap Time**: {lap_perf.get('best_lap_time_formatted', 'N/A')}
- **Average Lap Time**: {lap_perf.get('average_lap_time_formatted', 'N/A')}
- **Theoretical Best**: {lap_perf.get('theoretical_best_formatted', 'N/A')}
- **Consistency Rating**: {consistency.get('consistency_rating', 'N/A')}

---

## 📊 Detailed Analysis

### Lap Performance
- **Best Lap Time**: {lap_perf.get('best_lap_time_formatted', 'N/A')} ({lap_perf.get('best_lap_time_seconds', 0):.3f}s)
- **Average Lap Time**: {lap_perf.get('average_lap_time_formatted', 'N/A')} ({lap_perf.get('average_lap_time_seconds', 0):.3f}s)
- **Theoretical Best**: {lap_perf.get('theoretical_best_formatted', 'N/A')} ({lap_perf.get('theoretical_best_seconds', 0):.3f}s)
- **Time Lost to Theoretical**: {lap_perf.get('time_lost_to_theoretical', 0):.3f}s
- **Pace Efficiency**: {lap_perf.get('pace_efficiency_percent', 0):.1f}%
- **Average vs Best Gap**: {lap_perf.get('average_vs_best_gap', 0):.3f}s ({lap_perf.get('average_vs_best_percent', 0):.1f}%)

### Consistency Metrics
- **Consistency Index**: {consistency.get('consistency_index', 0):.4f}
- **Consistency Rating**: {consistency.get('consistency_rating', 'N/A')}
- **Lap Time Std Dev**: {consistency.get('lap_time_standard_deviation', 0):.3f}s
- **Performance Window (1%)**: {consistency.get('performance_window_1_percent', 0):.1f}%
- **Consistency Score**: {consistency.get('consistency_score', 0):.1f}/100
- **Repeatability Factor**: {consistency.get('repeatability_factor', 0):.3f}

### Session Progression
- **Progression Trend**: {progression.get('lap_progression_trend', 0):.3f}s
- **Progression Rating**: {progression.get('progression_rating', 'N/A')}
- **Session Length**: {progression.get('session_length_laps', 0)} laps
- **Learning Rate**: {progression.get('learning_rate', 0):.3f}
- **Session Stability**: {progression.get('session_stability', 0):.3f}

---

## 🎯 Sector Analysis

"""
        
        # Add sector details
        sector_data = sectors.get('sectors', {})
        if sector_data:
            md_content += f"**Sector Count**: {sectors.get('sector_count', 0)}\n\n"
            
            for sector_name, sector_info in sector_data.items():
                md_content += f"### {sector_name}\n"
                md_content += f"- **Best Time**: {sector_info.get('best_time_formatted', 'N/A')}\n"
                md_content += f"- **Average Time**: {sector_info.get('average_time', 0):.3f}s\n"
                md_content += f"- **Consistency**: {sector_info.get('consistency_rating', 'N/A')} ({sector_info.get('consistency_index', 0):.4f})\n"
                md_content += f"- **Improvement**: {sector_info.get('improvement_rating', 'N/A')} ({sector_info.get('improvement_seconds', 0):.3f}s)\n\n"
            
            md_content += f"**Most Consistent Sector**: {sectors.get('most_consistent_sector', 'N/A')}\n"
            md_content += f"**Least Consistent Sector**: {sectors.get('least_consistent_sector', 'N/A')}\n"
            md_content += f"**Overall Sector Improvement**: {sectors.get('overall_sector_improvement', 0):.3f}s\n\n"
        else:
            md_content += "No sector data available.\n\n"
        
        md_content += """---

## 💪 Strengths & Improvement Areas

### Key Strengths
"""
        
        strengths = summary.get('key_strengths', [])
        for strength in strengths:
            md_content += f"- {strength}\n"
        
        md_content += "\n### Areas for Improvement\n"
        
        improvements = summary.get('improvement_areas', [])
        for improvement in improvements:
            md_content += f"- {improvement}\n"
        
        md_content += f"""

---

## 📈 Performance Scores

- **Overall Performance**: {summary.get('overall_performance_score', 0):.1f}/100
- **Pace Score**: {summary.get('pace_score', 0):.1f}/100
- **Consistency Score**: {summary.get('consistency_score', 0):.1f}/100
- **Progression Score**: {summary.get('progression_score', 0):.1f}/100

### Rating Breakdown
- **Performance Weight**: {rating.get('rating_breakdown', {}).get('performance_weight', 0):.1f}
- **Consistency Weight**: {rating.get('rating_breakdown', {}).get('consistency_weight', 0):.1f}
- **Weighted Score**: {rating.get('rating_breakdown', {}).get('weighted_score', 0):.1f}/100

---

## 🔧 Technical Details

**Analysis Parameters:**
- Valid laps analyzed: {progression.get('session_length_laps', 0)}
- Sectors identified: {sectors.get('sector_count', 0)}
- Data quality: High (automated outlier removal applied)

**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

*This report was generated by SimFlowDataAgent Analysis System*
"""
        
        return md_content
    
    def _generate_csv_summary(self, kpis: Dict[str, Any], lap_data: Optional[pd.DataFrame] = None) -> Optional[str]:
        """Generate CSV summary of key metrics."""
        try:
            csv_path = self.output_dir / f"{self.session_id}_summary.csv"
            
            # Build summary data
            summary_data = []
            
            session_info = kpis.get('session_info', {})
            lap_perf = kpis.get('lap_performance', {})
            consistency = kpis.get('consistency_metrics', {})
            summary = kpis.get('performance_summary', {})
            
            summary_data.append({
                'Metric': 'Session ID',
                'Value': session_info.get('session_id', 'Unknown'),
                'Unit': '',
                'Category': 'Session Info'
            })
            
            summary_data.append({
                'Metric': 'Track',
                'Value': session_info.get('track', 'Unknown'),
                'Unit': '',
                'Category': 'Session Info'
            })
            
            summary_data.append({
                'Metric': 'Vehicle',
                'Value': session_info.get('vehicle', 'Unknown'),
                'Unit': '',
                'Category': 'Session Info'
            })
            
            summary_data.append({
                'Metric': 'Best Lap Time',
                'Value': lap_perf.get('best_lap_time_seconds', 0),
                'Unit': 'seconds',
                'Category': 'Lap Performance'
            })
            
            summary_data.append({
                'Metric': 'Average Lap Time',
                'Value': lap_perf.get('average_lap_time_seconds', 0),
                'Unit': 'seconds',
                'Category': 'Lap Performance'
            })
            
            summary_data.append({
                'Metric': 'Theoretical Best',
                'Value': lap_perf.get('theoretical_best_seconds', 0),
                'Unit': 'seconds',
                'Category': 'Lap Performance'
            })
            
            summary_data.append({
                'Metric': 'Consistency Index',
                'Value': consistency.get('consistency_index', 0),
                'Unit': 'ratio',
                'Category': 'Consistency'
            })
            
            summary_data.append({
                'Metric': 'Performance Window 1%',
                'Value': consistency.get('performance_window_1_percent', 0),
                'Unit': 'percent',
                'Category': 'Consistency'
            })
            
            summary_data.append({
                'Metric': 'Overall Performance Score',
                'Value': summary.get('overall_performance_score', 0),
                'Unit': 'score (0-100)',
                'Category': 'Summary'
            })
            
            summary_data.append({
                'Metric': 'Performance Grade',
                'Value': summary.get('performance_grade', 'N/A'),
                'Unit': 'grade',
                'Category': 'Summary'
            })
            
            # Create DataFrame and save
            df = pd.DataFrame(summary_data)
            df.to_csv(csv_path, index=False)
            
            return str(csv_path)
        except Exception as e:
            print(f"Error generating CSV summary: {e}")
            return None
    
    def _generate_executive_summary(self, kpis: Dict[str, Any]) -> Optional[str]:
        """Generate executive summary report."""
        try:
            summary_path = self.output_dir / f"{self.session_id}_executive_summary.md"
            
            session_info = kpis.get('session_info', {})
            lap_perf = kpis.get('lap_performance', {})
            summary = kpis.get('performance_summary', {})
            rating = kpis.get('session_rating', {})
            
            content = f"""# Executive Summary - {session_info.get('session_id', 'Unknown')}

## Quick Overview
- **Track**: {session_info.get('track', 'Unknown')}
- **Vehicle**: {session_info.get('vehicle', 'Unknown')}
- **Overall Grade**: {summary.get('performance_grade', 'N/A')} ({rating.get('overall_rating', 0)}/100)

## Key Results
- **Best Lap**: {lap_perf.get('best_lap_time_formatted', 'N/A')}
- **Consistency**: {kpis.get('consistency_metrics', {}).get('consistency_rating', 'N/A')}
- **Progression**: {kpis.get('session_progression', {}).get('progression_rating', 'N/A')}

## Strengths
"""
            
            strengths = summary.get('key_strengths', [])
            for strength in strengths:
                content += f"- {strength}\n"
            
            content += "\n## Focus Areas\n"
            
            improvements = summary.get('improvement_areas', [])
            for improvement in improvements:
                content += f"- {improvement}\n"
            
            content += f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return str(summary_path)
        except Exception as e:
            print(f"Error generating executive summary: {e}")
            return None
    
    def generate_session_readme(self, kpis: Dict[str, Any], report_paths: Dict[str, str]) -> Optional[str]:
        """Generate README file for the session with links to all reports."""
        try:
            readme_path = self.output_dir / "README.md"
            
            session_info = kpis.get('session_info', {})
            
            content = f"""# Session Analysis - {session_info.get('session_id', 'Unknown')}

## Session Details
- **Track**: {session_info.get('track', 'Unknown')}
- **Vehicle**: {session_info.get('vehicle', 'Unknown')}
- **Driver**: {session_info.get('driver', 'Unknown')}
- **Analysis Date**: {session_info.get('analysis_timestamp', 'Unknown')}

## Available Reports

"""
            
            if 'executive_summary' in report_paths:
                content += f"- [Executive Summary]({os.path.basename(report_paths['executive_summary'])})\n"
            
            if 'markdown' in report_paths:
                content += f"- [Detailed Analysis Report]({os.path.basename(report_paths['markdown'])})\n"
            
            if 'json' in report_paths:
                content += f"- [Raw Data (JSON)]({os.path.basename(report_paths['json'])})\n"
            
            if 'csv' in report_paths:
                content += f"- [Summary Data (CSV)]({os.path.basename(report_paths['csv'])})\n"
            
            content += f"""
## Quick Stats
- **Best Lap**: {kpis.get('lap_performance', {}).get('best_lap_time_formatted', 'N/A')}
- **Overall Grade**: {kpis.get('performance_summary', {}).get('performance_grade', 'N/A')}
- **Consistency**: {kpis.get('consistency_metrics', {}).get('consistency_rating', 'N/A')}

---
*Generated by SimFlowDataAgent Analysis System*
"""
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return str(readme_path)
        except Exception as e:
            print(f"Error generating README: {e}")
            return None
