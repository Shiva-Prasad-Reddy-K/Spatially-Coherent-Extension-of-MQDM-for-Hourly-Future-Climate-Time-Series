#!/bin/bash

# Master Script to Run the MQDM Project Pipeline
# This script assumes data has been downloaded (Phase 1 & 2). 
# It runs the processing, modeling, and validation steps (Phase 3, 4, 5).

echo "================================================================="
echo "   Spatially Coherent Extension of MQDM - Project Demo"
echo "================================================================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

echo "[Phase 3.1] Preparing Data & Running Core MQDM..."
# Step 1: Merge/Prepare ERA5 (if not already clean)
if [ ! -f "era5_clean.nc" ]; then
    echo " -> Merging ERA5 data..."
    python3 merge_era5.py
else
    echo " -> era5_clean.nc already exists. Skipping merge."
fi

# Step 2: Daily Shift
echo " -> Executing Quantile Delta Mapping (mqdm_daily_shift.py)..."
python3 mqdm_daily_shift.py

echo ""
echo "[Phase 3.2] Reconstructing Hourly Time Series..."
echo " -> Downscaling to hourly resolution (reconstruct_hourly.py)..."
python3 reconstruct_hourly.py

echo ""
echo "[Phase 4] Validation & Problem Identification..."
echo " -> Generating validation plots (validate_and_break.py)..."
python3 validate_and_break.py
echo " -> Check 'validation_histogram.png' and 'spatial_break_analysis.png'!"

echo ""
echo "[Phase 5] The Solution: Spatially Coherent Extension..."
echo " -> Applying Schaake Shuffle (schaake_shuffle.py)..."
python3 schaake_shuffle.py

echo ""
echo "================================================================="
echo "   DEMO COMPLETE"
echo "================================================================="
echo "Final Output: era5_spatially_coherent.nc"
echo "Correlation Analysis above shows the improvement in spatial structure."
