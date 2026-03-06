# Publication Plots
Run these scripts to generate high-quality validation plots for your research paper.

## Requirements
To generate all plots successfully, you need the following libraries:
`pip install xarray numpy pandas matplotlib skillmetrics cartopy`

## Scripts
1. **`generate_qq_plot.py`**: Validates the statistical match (Phase 2 MQDM).
2. **`generate_dtr_plot.py`**: Validates average diurnal cycle preservation (Phase 3 Temporal Downscaling).
3. **`generate_taylor_diagram.py`**: Validates spatial correlation/structure (Phase 4 Schaake Shuffle).
4. **`generate_spatial_maps.py`**: Generates visual geographic heatmaps to prove spatial consistency physically.
