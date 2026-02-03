import xarray as xr
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np

def validate_and_break():
    print("Starting Validation & Break Analysis...")

    # Load Data
    print("Loading datasets...")
    ds_hist = xr.open_dataset('era5_clean.nc', engine='netcdf4')
    ds_fut = xr.open_dataset('era5_future_hourly.nc', engine='netcdf4')

    # Ensure consistent variable names/access
    var_hist = 'temp_hourly'
    var_fut = 'temp_future'
    
    # --- PART 1: The Sanity Check (Did it warm?) ---
    print("\n--- Part 1: Warming Check ---")
    
    # Select first location (lat=0, lon=0 in the array)
    # We assume dims are (time, lat, lon) or similar
    t_hist_loc0 = ds_hist[var_hist].isel(latitude=0, longitude=0).values.flatten()
    t_fut_loc0 = ds_fut[var_fut].isel(latitude=0, longitude=0).values.flatten()
    
    # Remove NaNs if any
    t_hist_loc0 = t_hist_loc0[~np.isnan(t_hist_loc0)]
    t_fut_loc0 = t_fut_loc0[~np.isnan(t_fut_loc0)]
    
    plt.figure(figsize=(10, 6))
    plt.hist(t_hist_loc0, bins=50, alpha=0.5, label='Historical (ERA5)', color='blue', density=True)
    plt.hist(t_fut_loc0, bins=50, alpha=0.5, label='Future (MQDM)', color='red', density=True)
    
    mean_hist = np.mean(t_hist_loc0)
    mean_fut = np.mean(t_fut_loc0)
    
    plt.title(f"Temperature Distribution Shift (Loc 0,0)\nMean Hist: {mean_hist:.2f}C, Mean Fut: {mean_fut:.2f}C")
    plt.xlabel("Temperature (Celsius)")
    plt.ylabel("Density")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig('validation_histogram.png')
    print("Saved validation_histogram.png")
    plt.close()

    # --- PART 2: The "Break" Analysis (Spatial Coherence) ---
    print("\n--- Part 2: Spatial Coherence Analysis ---")
    
    # Select Loc A and Loc B (Neighbors)
    # Using isel for indices 0 and 1
    # Check if we have enough neighbors
    if ds_hist.dims['longitude'] < 2:
        print("Error: Not enough longitude points for spatial analysis.")
        return

    # Extract time series
    # Historical
    ts_hist_A = ds_hist[var_hist].isel(latitude=0, longitude=0).values.flatten()
    ts_hist_B = ds_hist[var_hist].isel(latitude=0, longitude=1).values.flatten()
    
    # Future
    ts_fut_A = ds_fut[var_fut].isel(latitude=0, longitude=0).values.flatten()
    ts_fut_B = ds_fut[var_fut].isel(latitude=0, longitude=1).values.flatten()
    
    # Filter common NaNs
    valid_hist = (~np.isnan(ts_hist_A)) & (~np.isnan(ts_hist_B))
    ts_hist_A = ts_hist_A[valid_hist]
    ts_hist_B = ts_hist_B[valid_hist]
    
    valid_fut = (~np.isnan(ts_fut_A)) & (~np.isnan(ts_fut_B))
    ts_fut_A = ts_fut_A[valid_fut]
    ts_fut_B = ts_fut_B[valid_fut]

    # Calculate Correlations
    r_hist, _ = stats.pearsonr(ts_hist_A, ts_hist_B)
    r_fut, _ = stats.pearsonr(ts_fut_A, ts_fut_B)
    
    print(f"Historical Correlation (Loc A vs B): {r_hist:.4f}")
    print(f"Future Correlation     (Loc A vs B): {r_fut:.4f}")
    
    # Scatter Plot
    plt.figure(figsize=(8, 8))
    
    # Plot Hist
    plt.scatter(ts_hist_A, ts_hist_B, 
                color='blue', alpha=0.3, s=10, 
                label=f'Historical (R={r_hist:.3f})')
                
    # Plot Future
    plt.scatter(ts_fut_A, ts_fut_B, 
                color='red', alpha=0.3, s=10, 
                label=f'Future (R={r_fut:.3f})')
    
    # 1:1 Line for reference
    min_val = min(np.min(ts_hist_A), np.min(ts_fut_A))
    max_val = max(np.max(ts_hist_A), np.max(ts_fut_A))
    plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='1:1 Line')
    
    plt.title("Spatial Coherence: Loc A vs Loc B\n(Loss of correlation indicates broken structure)")
    plt.xlabel("Temperature at Loc A (C)")
    plt.ylabel("Temperature at Loc B (C)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig('spatial_break_analysis.png')
    print("Saved spatial_break_analysis.png")
    plt.close()

if __name__ == "__main__":
    validate_and_break()
