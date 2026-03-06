import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_diurnal_cycle(hist_file, future_file, output_file='dtr_plot.png'):
    print("Loading datasets for Diurnal Cycle Plot...")
    ds_hist = xr.open_dataset(hist_file)
    ds_fut = xr.open_dataset(future_file)
    
    print("Calculating mean diurnal cycle grouped by hour...")
    # Group by the 'hour' component of the time dimension and calculate the mean
    # Variable names: temp_hourly for historical, temp_coherent for future
    # Time coordinate is 'valid_time' instead of 'time'
    hist_hourly_mean = ds_hist['temp_hourly'].groupby('valid_time.hour').mean(dim=xr.ALL_DIMS)
    fut_hourly_mean = ds_fut['temp_coherent'].groupby('valid_time.hour').mean(dim=xr.ALL_DIMS)
    
    # Convert from Kelvin to Celsius for better readability in the paper
    if hist_hourly_mean.mean().values > 200:
        hist_hourly_mean = hist_hourly_mean - 273.15
        fut_hourly_mean = fut_hourly_mean - 273.15
        ylabel = 'Mean Temperature (°C)'
    else:
        ylabel = 'Mean Temperature'
        
    hours = hist_hourly_mean['hour'].values
    
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(hours, hist_hourly_mean.values, marker='o', linestyle='-', color='#1f77b4', linewidth=2.5, markersize=8, label='Historical Reference (ERA5)')
    plt.plot(hours, fut_hourly_mean.values, marker='s', linestyle='-', color='#d62728', linewidth=2.5, markersize=8, label='Future Downscaled (Coherent)')
    
    plt.title('Average Diurnal Temperature Cycle Preservation', fontsize=16, fontweight='bold')
    plt.xlabel('Hour of Day (UTC)', fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    
    # Ensure x-axis shows all 24 hours cleanly
    plt.xticks(np.arange(0, 24, 2))
    plt.xlim(-0.5, 23.5)
    
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=12, loc='upper left')
    
    # Fill the gap to show the warming delta visually
    plt.fill_between(hours, hist_hourly_mean.values, fut_hourly_mean.values, color='red', alpha=0.1)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved Diurnal Cycle plot to {output_file}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hist = os.path.join(base_dir, 'era5_clean.nc')
    fut = os.path.join(base_dir, 'era5_spatially_coherent.nc')
    
    if os.path.exists(hist) and os.path.exists(fut):
        plot_diurnal_cycle(hist, fut, output_file=os.path.join(base_dir, 'paper_plots', 'diurnal_cycle_publication.png'))
    else:
        print("Data files not found.")
