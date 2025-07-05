# SimFlowSetupAgent - DROP-OFF Folder

## 📁 File Organization System

This folder system is designed to organize and process setup files from various sources. Simply drop your files into the appropriate folders and the SimFlowSetupAgent will automatically detect, parse, and organize them.

## 📂 Folder Structure

### 🎯 DROP-OFF Folders (Input)
Place your files here for automatic processing:

#### `setup_files/`
**iRacing Setup Files (.htm, .sto)**
- iRacing exported setup files
- Supported formats: .htm, .sto
- Any car type (GT3, NASCAR, F1, etc.)
- Any track type (Road, Oval, Street)

**Example files to drop here:**
- `MyGT3Setup_Silverstone.htm`
- `NASCARSetup_Daytona.sto`
- `F1Setup_Monaco.htm`

#### `motec_sheets/`
**MoTeC Setup Sheets (.csv, .xlsm, .xlsx)**
- MoTeC setup parameter sheets
- Professional engineering templates
- Data analysis exports

**Example files to drop here:**
- `GT3_setup_sheet.csv`
- `NASCAR_parameter_analysis.xlsm`
- `Setup_comparison.xlsx`

#### `images/`
**Setup Screenshots and Images (.png, .jpg, .jpeg, .gif)**
- Setup screenshots from iRacing
- MoTeC analysis plots
- Telemetry charts
- Reference images

**Example files to drop here:**
- `setup_screenshot.png`
- `tire_temp_analysis.jpg`
- `suspension_telemetry.jpeg`

### 📊 PROCESSED Folders (Output)
Automatically organized processed files:

#### `by_car/`
**Organized by Car Type, then Date**

```
PROCESSED/
├── by_car/
│   ├── gt3_porsche_992/
│   │   ├── 2025-07-05/
│   │   │   ├── 133045_fuji_gp_MySetup.htm
│   │   │   ├── 133045_fuji_gp_MySetup_parsed.json
│   │   │   └── 140215_silverstone_gp_QualifySetup.htm
│   │   └── 2025-07-04/
│   │       └── 091230_brands_hatch_gp_TestSetup.htm
│   ├── gt3_ferrari_296/
│   │   └── 2025-07-05/
│   │       └── 142030_monza_gp_RaceSetup.htm
│   └── tcr_audi_rs3/
│       └── 2025-07-05/
│           └── 151500_brands_hatch_gp_WetSetup.htm
├── motec_analysis/
│   ├── gt3_generic/
│   │   └── 2025-07-05/
│   │       ├── 133045_setup_sheet.csv
│   │       └── 133045_setup_sheet_parsed.json
│   └── unknown/
│       └── 2025-07-05/
│           └── 160000_parameter_analysis.xlsx
└── reports/
    ├── comparison_reports/
    └── analysis_reports/
```

**Benefits of this structure:**

- **Easy to find**: All setups for a specific car in one place
- **Chronological**: Recent setups are easy to locate by date
- **Scalable**: Supports unlimited cars and dates
- **Organized**: Clear separation between setup files and analysis data

#### `motec_analysis/`
**MoTeC Files organized by Car Type, then Date**

Professional setup sheets and analysis data from MoTeC software.

#### `reports/`
**Generated Analysis Reports**

- Comparison reports between multiple setups
- Performance analysis reports
- Setup recommendation reports

## 🚀 Usage Instructions

### 1. Drop Files

- Setup files → `DROP-OFF/setup_files/`
- MoTeC sheets → `DROP-OFF/motec_sheets/`
- Images → `DROP-OFF/images/`

### 2. Run Processing

The system will automatically:
- Detect new files
- Parse setup parameters
- Organize by car type and date
- Generate analysis reports
- Create comparison data

### 3. View Results

- `PROCESSED/by_car/` - Organized by vehicle and date
- `PROCESSED/motec_analysis/` - MoTeC analysis data
- `PROCESSED/reports/` - Generated reports

## 📋 Supported File Types

### iRacing Setup Files

| Extension | Description | Car Types |
|-----------|-------------|-----------|
| .htm | iRacing HTML setup export | All car types |
| .sto | iRacing setup file | All car types |

### MoTeC Files

| Extension | Description | Use Case |
|-----------|-------------|----------|
| .csv | Parameter sheets | Setup analysis |
| .xlsm/.xlsx | Excel workbooks | Advanced analysis |

### Images

| Extension | Description | Use Case |
|-----------|-------------|----------|
| .png/.jpg/.jpeg | Screenshots | Setup documentation |
| .gif | Animated analysis | Telemetry visualization |

## 🔧 Processing Features

### Automatic Detection
- **Car Type Recognition**: Automatically detects GT3, NASCAR, TCR, Formula cars
- **Track Classification**: Identifies road courses, ovals, street circuits
- **Parameter Extraction**: Extracts key setup parameters for analysis

### Organization
- **Date-based Filing**: Organizes by date for easy chronological access
- **Car-specific Folders**: Separate folders for each car type
- **JSON Export**: Parsed data available in structured format

### Analysis
- **Parameter Comparison**: Compare setups across different sessions
- **Balance Analysis**: Evaluate aerodynamic and suspension balance
- **Performance Metrics**: Track setup effectiveness

## 📈 Example Workflow

1. **Export Setup** from iRacing → Save as .htm file
2. **Drop File** into `DROP-OFF/setup_files/`
3. **Run Parser** (automatic or manual)
4. **Find Results** in `PROCESSED/by_car/[car_type]/[date]/`
5. **Review Analysis** in generated JSON and reports

## 🛠️ Technical Details

### File Naming Convention
- **Timestamp**: HHMMSS format for easy sorting
- **Track Info**: Track name included for context
- **Original Name**: Preserved for reference
- **JSON Parsed**: Structured data for analysis

### Error Handling
- **Encoding Detection**: Automatic fallback for different file encodings
- **Parsing Errors**: Graceful handling of malformed files
- **Validation**: Parameter range checking against vehicle profiles

## 🎯 Best Practices

1. **Consistent Naming**: Use descriptive names for setup files
2. **Regular Processing**: Run processing regularly to keep data organized
3. **Backup Important Setups**: Keep copies of championship-winning setups
4. **Document Changes**: Include notes about setup modifications
5. **Archive Old Data**: Move old seasons to archive folders

## 🔍 Troubleshooting

### Common Issues
- **File Not Parsing**: Check file encoding and format
- **Missing Parameters**: Verify iRacing export settings
- **Organization Errors**: Ensure proper folder permissions

### Getting Help
- Check log files for detailed error messages
- Verify file format compatibility
- Ensure all required directories exist

---

*SimFlowSetupAgent - Professional iRacing Setup Management*
