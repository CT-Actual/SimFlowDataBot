# Installation Guide

This guide describes how to set up the environment for SimFlowDataAgent.

## 1. Clone the Repository
```bash
git clone https://github.com/your-org/SimFlowDataAgent.git
cd SimFlowDataAgent
```

## 2. Install Dependencies
Ensure Python 3.8+ and Java 17+ are installed on your system.

Install Python packages:
```bash
pip install -r requirements.txt
```

(Optional) install Node.js if you plan to use the chart server for visualization.

## 3. Verify Java Build
Compile the Java components:
```bash
./gradlew build
```

## 4. First-Time Setup
Create the season folder structure:
```bash
mkdir -p 2025-Season3/Car_Folder/DROP-OFF
mkdir -p 2025-Season3/Car_Folder/SESSIONS
```

You're now ready to process data using `process_dropoff.py`.
