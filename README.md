# Spatially Coherent Extension of MQDM for Hourly Future Climate Time Series

## Project Overview
This project implements a novel method to downscale Global Climate Model (GCM) projections to high-resolution hourly time series while preserving spatial coherence. It addresses the "broken spatial structure" problem often introduced by standard quantile mapping techniques.

## Pipeline Stages

### Phase 1 & 2: Data Ingestion
*   **Historical Reference**: ERA5 Hourly Data (2010-2023).
*   **Future Projection**: CMIP6 SSP3-7.0 (Year 2040).
*   **Historical Baseline**: CMIP6 Historical (Year 2000).

### Phase 3: MQDM Implementation
*   **Daily Shift**: Uses Monthly Quantile Delta Mapping (MQDM) to shift the daily temperature distributions.
*   **Hourly Reconstruction**: Imposes the new daily bounds onto the historical diurnal cycles to create a physically consistent hourly series.

### Phase 4: Validation
*   Demonstrates the "Break": Shows that standard MQDM degrades spatial correlations between neighboring grid points.

### Phase 5: The Solution
*   **Schaake Shuffle**: Re-orders the future fields based on historical rank templates to restore realistic spatial weather patterns.

## How to Run the Demo

### Prerequisites
*   Python 3.x
*   Required libraries: `xarray`, `numpy`, `scipy`, `matplotlib`, `dask`, `bottleneck`, `netCDF4`

### Quick Start
Run the master script to execute the pipeline from processing to validation:

```bash
bash run_pipeline.sh
```

## detailed File Descriptions

| Script | Phase | Description |
| :--- | :--- | :--- |
| `merge_era5.py` | 3.1 | Prepares the ERA5 reference dataset. |
| `mqdm_daily_shift.py` | 3.1 | **Core Algorithm**: Calculates and applies QDM shifts. |
| `reconstruct_hourly.py` | 3.2 | Downscales daily shifted data to hourly resolution. |
| `validate_and_break.py` | 4 | Generates plots showing warming and spatial decoherence. |
| `schaake_shuffle.py` | 5 | **Novel Extension**: Restores spatial coherence. |

## Outputs
*   `era5_spatially_coherent.nc`: The final, high-quality, spatially coherent future climate dataset.
*   `validation_histogram.png`: Evidence of warming shift.
*   `spatial_break_analysis.png`: Evidence of spatial structure restoration.