import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import os

def plot_qq(hist_file, future_file, output_file='qq_plot.png'):
    print("Loading datasets for Q-Q Plot...")
    ds_hist = xr.open_dataset(hist_file)
    ds_fut = xr.open_dataset(future_file)
    
    # Extract values and flatten arrays, removing NaNs
    hist_vals = ds_hist['temp_hourly'].values.flatten()
    fut_vals = ds_fut['temp_coherent'].values.flatten()
    
    hist_vals = hist_vals[~np.isnan(hist_vals)]
    fut_vals = fut_vals[~np.isnan(fut_vals)]
    
    print("Calculating quantiles...")
    # Compute 100 quantiles (1st to 99th percentile)
    quantiles = np.linspace(0.01, 0.99, 100)
    q_hist = np.quantile(hist_vals, quantiles)
    q_fut = np.quantile(fut_vals, quantiles)
    
    # Plotting
    plt.figure(figsize=(8, 8))
    plt.scatter(q_hist, q_fut, c='#1f77b4', alpha=0.7, edgecolors='k', s=40, label='Quantiles')
    
    # Add a 1:1 reference line
    min_val = min(np.min(q_hist), np.min(q_fut))
    max_val = max(np.max(q_hist), np.max(q_fut))
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='1:1 Reference Line')
    
    plt.title('Quantile-Quantile (Q-Q) Plot:\nHistorical vs. Future Downscaled Temperatures', fontsize=14, fontweight='bold')
    plt.xlabel('Historical ERA5 Quantiles (K)', fontsize=12)
    plt.ylabel('Future Coherent Quantiles (K)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved Q-Q plot to {output_file}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist = os.path.join(base_dir, 'era5_clean.nc')
    fut = os.path.join(base_dir, 'era5_spatially_coherent.nc')
    
    if os.path.exists(hist) and os.path.exists(fut):
        plot_qq(hist, fut, output_file=os.path.join(base_dir, 'paper_plots', 'qq_plot_publication.png'))
    else:
        print("Data files not found. Please ensure era5_clean.nc and era5_spatially_coherent.nc exist in the root directory.")
