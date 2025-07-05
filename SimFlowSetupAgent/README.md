# SimFlowSetupAgent - Expert iRacing Setup Engineer

## Overview

SimFlowSetupAgent is an advanced, data-driven setup optimization agent for iRacing. It acts as an expert setup engineer, providing analysis, recommendations, and comparisons for various car types and racing scenarios.

## Features

### Core Capabilities
- **Setup File Parsing**: Supports iRacing .htm exports and MoTeC setup sheets (.csv, .xlsm)
- **Parameter Analysis**: Validates setup parameters against vehicle-specific profiles
- **Balance Analysis**: Evaluates aerodynamic, suspension, and tire balance
- **Setup Comparison**: Side-by-side comparison of different setups
- **Optimization Recommendations**: Data-driven suggestions for improvement
- **Multi-format Export**: Text, CSV, Markdown, and JSON output formats

### Supported Vehicles
- **GT3 Cars**: Comprehensive parameter templates based on real iRacing data
- **NASCAR Next Gen**: Detailed rule-based parameter validation
- **Extensible**: Easy to add new vehicle categories with JSON templates

### Session Types
- **Sprint**: 25-30 minute races with 50% fuel load
- **Endurance**: 60+ minute races with 100% fuel load
- **Qualifying**: Maximum performance setups
- **Practice**: Balanced setups for learning
- **Road Course**: General road racing configurations

### Aggression Levels
- **Conservative**: Safe, stable setups with error margins
- **Balanced**: Moderate risk/reward optimization
- **Aggressive**: High-performance setups with tight margins
- **Experimental**: Cutting-edge setups for testing limits

## Installation

1. Clone or download the SimFlowSetupAgent directory
2. Install required Python packages from the repository root:
   ```bash
   pip install -r ../requirements.txt
   ```
3. Ensure you have Python 3.7+ installed

## Usage

### Command Line Interface

The agent provides a comprehensive command-line interface for various operations:

#### Analyze a Setup File
```bash
python simflow_setup_agent.py analyze --file setup.htm --vehicle gt3 --session road_course --output all
```

#### Compare Two Setups
```bash
python simflow_setup_agent.py compare --file1 setup1.htm --file2 setup2.htm --vehicle gt3
```

#### Generate Setup Recommendations
```bash
python simflow_setup_agent.py recommend --track "Watkins Glen" --vehicle gt3 --session sprint --aggression balanced
```

#### Generate Parameter Table
```bash
python simflow_setup_agent.py table --vehicle gt3
```

### Python API

The agent can also be used programmatically:

```python
from SimFlowSetupAgent import SimFlowSetupAgent

# Initialize agent
agent = SimFlowSetupAgent()

# Analyze a setup file
analysis = agent.analyze_setup_file("setup.htm", "gt3", "road_course")

# Compare two setups
comparison = agent.compare_setups("setup1.htm", "setup2.htm", "gt3")

# Generate recommendations
recommendations = agent.generate_setup_recommendations(
    "Watkins Glen", "sprint", "gt3", "balanced"
)

# Export results
exported_files = agent.export_analysis(analysis, "all")
```

## File Format Support

### iRacing .htm Files
- Complete setup parameter extraction
- Tire pressure and temperature data
- Aerodynamic balance calculations
- Suspension geometry and settings
- Brake configuration
- Differential settings
- Damper configurations
- Driver aid settings

### MoTeC Setup Sheets
- CSV format parsing
- Excel (.xlsx/.xlsm) support
- Parameter extraction with units
- Multi-setup comparison capability

## Vehicle Profiles

Vehicle profiles are stored as JSON files in the `vehicle_profiles/` directory. Each profile contains:

### Structure
```json
{
  "vehicle_info": {
    "name": "GT3 Cars (Generic)",
    "category": "gt3",
    "track_type": "road_course",
    "series": "IMSA/VRS/GT3 Series",
    "description": "Generic GT3 car setup parameters"
  },
  "setup_parameters": {
    "tires": { /* tire parameters */ },
    "aerodynamics": { /* aero parameters */ },
    "suspension": { /* suspension parameters */ },
    "brakes": { /* brake parameters */ },
    "differential": { /* diff parameters */ },
    "dampers": { /* damper parameters */ },
    "driver_aids": { /* aid parameters */ },
    "gears": { /* gear parameters */ },
    "fuel": { /* fuel parameters */ },
    "weight_distribution": { /* weight parameters */ }
  },
  "optimization_priorities": {
    "road_course": {
      "primary": [ /* high-priority parameters */ ],
      "secondary": [ /* medium-priority parameters */ ],
      "fine_tuning": [ /* detail parameters */ ]
    }
  },
  "telemetry_channels": {
    "critical": [ /* essential channels */ ],
    "important": [ /* useful channels */ ],
    "supplementary": [ /* additional channels */ ]
  }
}
```

### Adding New Vehicle Profiles

1. Create a new JSON file in `vehicle_profiles/`
2. Follow the existing structure
3. Define parameter ranges based on real-world data
4. Set optimization priorities for different session types
5. List relevant telemetry channels

## Output Formats

### Text Reports
Comprehensive human-readable analysis with:
- Parameter validation results
- Balance analysis
- Optimization recommendations
- Telemetry channel suggestions

### CSV Export
Structured data suitable for:
- Spreadsheet analysis
- Data visualization
- Statistical analysis
- External tool integration

### Markdown Export
Documentation-ready format with:
- Formatted tables
- Clear sectioning
- GitHub-compatible syntax

### JSON Export
Machine-readable format for:
- API integration
- Data processing
- Automation workflows

## Analysis Capabilities

### Parameter Validation
- Range checking against vehicle profiles
- Out-of-bounds detection
- Optimization suggestions
- Context-specific recommendations

### Balance Analysis
- Tire pressure balance (F/R and L/R)
- Aerodynamic balance assessment
- Suspension balance evaluation
- Weight distribution analysis
- Cross-weight validation

### Optimization Recommendations
- Priority-based suggestions
- Session-specific advice
- Aggression-level adjustments
- Track-specific modifications

### Telemetry Integration
- Recommended channel lists
- Critical parameter monitoring
- Performance validation metrics
- Data correlation suggestions

## Advanced Features

### Setup Comparison
- Side-by-side parameter comparison
- Difference highlighting
- Performance impact analysis
- Balanced vs. aggressive trade-offs

### Track-Specific Recommendations
- Downforce level suggestions
- Gear ratio optimization
- Brake bias recommendations
- Tire pressure adjustments

### Session Optimization
- Fuel load considerations
- Tire wear predictions
- Performance vs. consistency trade-offs
- Risk assessment

## Integration with SimFlowDataAgent

The SimFlowSetupAgent integrates seamlessly with the main SimFlowDataAgent:

### Data Flow
1. Session data processed by SimFlowDataAgent
2. Setup files analyzed by SimFlowSetupAgent
3. Telemetry data correlated with setup parameters
4. Combined analysis and recommendations

### Shared Resources
- Common telemetry channels
- Integrated reporting
- Unified data storage
- Cross-analysis capabilities

## Development and Extension

### Adding New Vehicle Types
1. Research actual parameter ranges
2. Create comprehensive JSON profile
3. Define optimization priorities
4. Add telemetry channel mappings
5. Test with real setup files

### Extending Analysis Capabilities
1. Add new analysis functions
2. Update parameter validation logic
3. Enhance recommendation algorithms
4. Expand export formats

### Custom Track Database
1. Create track-specific profiles
2. Define optimal setup characteristics
3. Add track-specific recommendations
4. Include historical performance data

## Troubleshooting

### Common Issues
- **File parsing errors**: Check file format and encoding
- **Parameter validation failures**: Verify vehicle profile accuracy
- **Import errors**: Ensure all dependencies are installed
- **Analysis incomplete**: Check for missing data sections

### Debug Mode
Enable detailed logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## License

This project is part of the SimFlowDataAgent system and follows the same licensing terms.

## Support

For issues, feature requests, or contributions, please refer to the main SimFlowDataAgent project documentation.

---

*SimFlowSetupAgent - Bringing data-driven engineering to iRacing setup optimization*
