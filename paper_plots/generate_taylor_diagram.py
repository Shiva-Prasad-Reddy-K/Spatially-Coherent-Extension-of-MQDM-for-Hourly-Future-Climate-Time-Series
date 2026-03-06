import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os

try:
    import skill_metrics as sm
except ImportError:
    print("Error: The 'SkillMetrics' package is required for this script.")
    print("Please install it by running: pip install SkillMetrics")
    exit(1)

def plot_taylor(ref_file, fut_before_file, fut_after_file, output_file='taylor_diagram.png'):
    print("Loading datasets for Taylor Diagram...")
    ds_ref = xr.open_dataset(ref_file)
    ds_before = xr.open_dataset(fut_before_file)
    ds_after = xr.open_dataset(fut_after_file)
    
    # Pick a specific time index to compare spatial coherence
    time_idx = 0
    ref_vals = ds_ref['temp_hourly'].isel(valid_time=time_idx).values.flatten()
    before_vals = ds_before['temp_future'].isel(valid_time=time_idx).values.flatten()
    after_vals = ds_after['temp_coherent'].isel(valid_time=time_idx).values.flatten()
    
    # Remove NaNs
    valid_idx = ~np.isnan(ref_vals) & ~np.isnan(before_vals) & ~np.isnan(after_vals)
    ref_valid = ref_vals[valid_idx]
    before_valid = before_vals[valid_idx]
    after_valid = after_vals[valid_idx]
    
    # Compare anomalies (value - mean)
    ref_anom = ref_valid - np.mean(ref_valid)
    before_anom = before_valid - np.mean(before_valid)
    after_anom = after_valid - np.mean(after_valid)
    
    sdev = np.array([np.std(ref_anom), np.std(before_anom), np.std(after_anom)])
    
    crmsd = np.array([0.0, 
                      np.sqrt(np.mean((before_anom - ref_anom)**2)), 
                      np.sqrt(np.mean((after_anom - ref_anom)**2))])
    
    ccoef = np.array([1.0, 
                      np.corrcoef(ref_anom, before_anom)[0,1], 
                      np.corrcoef(ref_anom, after_anom)[0,1]])
    
    print("\nCalculated Metrics:")
    print(f"Standard Deviations: Reference={sdev[0]:.2f}, Before={sdev[1]:.2f}, After={sdev[2]:.2f}")
    print(f"Correlations: Reference={ccoef[0]:.2f}, Before={ccoef[1]:.2f}, After={ccoef[2]:.2f}")
    
    markers = {
        'Historical Reference': {'labelColor': 'r', 'symbol': 'o', 'size': 15, 'faceColor': 'r', 'edgeColor': 'r'},
        'Before Shuffle (Broken)': {'labelColor': 'b', 'symbol': 's', 'size': 15, 'faceColor': 'b', 'edgeColor': 'b'},
        'After Shuffle (Coherent)': {'labelColor': 'g', 'symbol': '^', 'size': 15, 'faceColor': 'g', 'edgeColor': 'g'}
    }
    
    sm.taylor_diagram(sdev, crmsd, ccoef, 
                      markerLegend = 'on',
                      markers = markers,
                      colRMS = 'g', styleRMS = ':', widthRMS = 1.5, titleRMS = 'on',
                      colSTD = 'b', styleSTD = '-.', widthSTD = 1.0, titleSTD = 'on',
                      colCOR = 'k', styleCOR = '--', widthCOR = 1.0, titleCOR = 'on')
                      
    plt.title('Taylor Diagram: Spatial Coherence Validation', y=1.08, fontsize=16, fontweight='bold')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nSaved Taylor Diagram to {output_file}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ref = os.path.join(base_dir, 'era5_clean.nc')
    before = os.path.join(base_dir, 'era5_future_hourly.nc')
    after = os.path.join(base_dir, 'era5_spatially_coherent.nc')
    
    if all(os.path.exists(f) for f in [ref, before, after]):
        plot_taylor(ref, before, after, output_file=os.path.join(base_dir, 'paper_plots', 'taylor_diagram_publication.png'))
    else:
        print("Data files not found. Ensure era5_clean.nc, era5_future_hourly.nc, and era5_spatially_coherent.nc exist.")
