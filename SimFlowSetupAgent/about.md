# SimFlowSetupAgent - Expert iRacing Setup Engineering

**Author**: Chris - SimFlow Engineering  
**Version**: 1.0.0  
**Target Simulator**: iRacing

## 🎯 Mission

**Create the world's fastest iRacing setups** through expert-level racing engineering, aggressive optimization strategies, and comprehensive telemetry data analysis.

## 🏗️ Architecture Overview

### Core Components

1. **Vehicle Profile System** - Structured setup parameters for each car/track type
2. **Setup Sheet Generator** - Creates human-readable parameter tables and templates  
3. **File Handlers** - Supports HTM, STO, MoTeC CSV/XLSM, and image files
4. **Expert Analysis Engine** - Applies racing engineering principles for optimization
5. **Integration Layer** - Seamless compatibility with SimFlowDataAgent

## 📋 Vehicle Profile System

### Current Profiles

- **NASCAR Next Gen (Speedway)** - `nascar_nextgen_speedway.json`
- **GT3 Generic (Road Course)** - `gt3_generic_road.json`

### Profile Structure

Each vehicle profile contains:
- **Vehicle Information** - Name, category, series, track type
- **Setup Parameters** - Min/max ranges, units, descriptions for all adjustable parameters
- **Optimization Priorities** - Track-specific tuning focus areas
- **Telemetry Channels** - Required data channels for analysis

### Parameter Categories

- **Tires** - Pressure settings and compound selection
- **Suspension** - Springs, dampers, geometry settings
- **Aerodynamics** - Wing angles, ride heights, splitter settings
- **Anti-Roll Bars** - Stiffness and preload settings
- **Differential** - Preload, power, and coast settings
- **Weight Distribution** - Ballast and balance adjustments

## 🔧 Setup Sheet Generation

### Available Formats

- **Markdown** - Human-readable tables for documentation
- **HTML** - Web-formatted tables with styling
- **CSV** - Data export for spreadsheet applications

### Sheet Types

1. **Parameter Tables** - Complete setup parameter reference
2. **Blank Setup Sheets** - Data entry templates for track sessions
3. **Optimization Guides** - Priority-based tuning recommendations

## 🚀 Usage Examples

### Generate Parameter Table
```bash
# List available vehicles
python scripts/generate_setup_sheets.py list

# Generate NASCAR parameter table
python scripts/generate_setup_sheets.py parameters --vehicle nascar_nextgen_speedway

# Save GT3 parameters as HTML
python scripts/generate_setup_sheets.py parameters --vehicle gt3_generic_road --format html --output gt3_params.html
```

### Generate Setup Sheets
```bash
# Create blank NASCAR setup sheet
python scripts/generate_setup_sheets.py sheet --vehicle nascar_nextgen_speedway --output nascar_setup.md

# Generate all vehicle summaries
python scripts/generate_setup_sheets.py summary --output vehicle_summary.md
```

## 📊 NASCAR Next Gen Setup Parameters

| Category | Parameters | Key Focus Areas |
|----------|------------|-----------------|
| **Tires** | LF/LR: 15-35 psi, RF/RR: 45-65 psi | Pressure optimization for grip |
| **Weight** | Nose Weight: 48.2-52.6% | Balance and handling characteristics |
| **Suspension** | Springs: 400-4600 lbs/in | Ride quality and aerodynamics |
| **Anti-Roll Bars** | Diameter: 1.375-2.000", Arms: P1-P5 | Roll stiffness and balance |
| **Geometry** | Camber, caster, toe settings | Tire contact patch optimization |
| **Differential** | Preload: 0-75 ft-lbs | Traction and handling balance |

## 🏁 GT3 Setup Parameters

| Category | Parameters | Key Focus Areas |
|----------|------------|-----------------|
| **Aerodynamics** | Wings: 1-11 clicks, Ride Height: 50-120mm | Downforce vs drag balance |
| **Suspension** | Springs: 80-200 N/mm, Dampers: 1-30 clicks | Mechanical grip and platform |
| **Differential** | Preload: 20-200 Nm, Power/Coast: 10-90% | Traction out of corners |
| **Tires** | Pressure: 25-32 psi | Optimal operating temperature |
| **Brakes** | Balance: 50-65% front | Stability and performance |

## 🎯 Expert Optimization Approach

### Philosophy
- **Raw Speed Priority** - Lap time over tire preservation
- **Physics Exploitation** - Leverage iRacing-specific advantages  
- **Data-Driven Decisions** - All recommendations backed by telemetry
- **Aggressive Baseline** - Default to maximum legal performance

### Optimization Priorities

**Primary Focus**:
- Aerodynamic balance (GT3)
- Weight distribution (NASCAR)
- Tire pressure optimization
- Brake balance

**Secondary Adjustments**:
- Spring rate balance
- Anti-roll bar settings
- Differential tuning

**Fine Tuning**:
- Geometry adjustments
- Damper settings
- Preload optimization

## 🔬 Technical Integration

### File Format Support
- **iRacing Setup Files** - .htm (full read/write), .sto (analysis)
- **MoTeC Data** - .csv exports, .xlsm workbooks
- **User Content** - .png/.jpg screenshots and analysis
- **SimFlowDataAgent** - All existing report and telemetry formats

### Telemetry Requirements

**Critical Channels**:
- Tire pressures and temperatures (all corners)
- Wing angles and aerodynamic settings
- Weight distribution measurements

**Important Channels**:
- Spring rates and suspension travel
- Damper velocities and forces
- Ride height measurements

**Supplementary Channels**:
- Camber and toe settings
- Brake temperatures and bias
- Driver input data

## 📈 Professional Workflow

1. **Session Analysis** - Import telemetry and setup data
2. **Parameter Validation** - Check against vehicle constraints
3. **Performance Gap Analysis** - Identify optimization opportunities
4. **Setup Generation** - Create optimized configurations
5. **Documentation** - Generate setup sheets and recommendations
6. **Validation** - Track performance improvements

## 🎮 iRacing Integration

### Setup Import/Export
- Direct .htm file generation for iRacing import
- Setup comparison and optimization tools
- Parameter validation against iRacing constraints

### Session Workflow
1. Export setup from iRacing (.htm)
2. Import telemetry from MoTeC (.csv/.xlsm)
3. Analyze with SimFlowSetupAgent
4. Generate optimized setup
5. Import back to iRacing for testing

---

**Ready to dominate the track with expert-engineered setups!** 🏁

*Generated by SimFlowSetupBot - Expert iRacing Setup Engineering*
---

## ChatGPT-CLI System Prompt

> Paste the following block into your ChatGPT-CLI **system prompt** field (or the `--system` flag) so interactions follow the SimFlowSetupAgent workflow.

```text
You are **SimFlowSetupAgent**, an expert iRacing setup engineer.

Tasks:
1. Watch the `DROP-OFF` folder for new setup files (`setup_files/`, `motec_sheets/`, `images/`).
2. Parse iRacing `.htm`/`.sto` files and MoTeC setup sheets (`.csv`, `.xlsm`) and organize them by car type and date.
3. Validate all parameters against the appropriate vehicle profile.
4. Perform balance analysis (aerodynamics, suspension, tires, etc.) and generate optimization recommendations.
5. Support session types like sprint, endurance, qualifying, practice, and road course.
6. Output analysis in text, CSV, Markdown, and JSON formats within `PROCESSED/` folders.
7. Provide side-by-side comparisons and parameter tables when requested.

Goal: **Create the world’s fastest iRacing setups** using aggressive optimization strategies and comprehensive telemetry data analysis.
```

