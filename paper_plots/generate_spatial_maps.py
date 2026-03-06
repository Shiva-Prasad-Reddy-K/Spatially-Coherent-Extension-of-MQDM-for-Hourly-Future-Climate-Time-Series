import xarray as xr
import matplotlib.pyplot as plt
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    USE_CARTOPY = True
except ImportError:
    print("Warning: cartopy not installed. Maps will be drawn as basic 2D grids without coastlines.")
    print("For publication-quality geographic maps, please: pip install cartopy")
    USE_CARTOPY = False

def plot_spatial_comparison(ref_file, before_file, after_file, output_file='spatial_maps.png', time_idx=0):
    print("Loading datasets for Spatial Geographic Maps...")
    ds_ref = xr.open_dataset(ref_file)
    ds_before = xr.open_dataset(before_file)
    ds_after = xr.open_dataset(after_file)
    
    data_ref = ds_ref['temp_hourly'].isel(valid_time=time_idx)
    data_before = ds_before['temp_future'].isel(valid_time=time_idx)
    data_after = ds_after['temp_coherent'].isel(valid_time=time_idx)
    
    # Calculate common min and max for the Future maps to equalize the colorbars
    vmin = min(float(data_before.min()), float(data_after.min()))
    vmax = max(float(data_before.max()), float(data_after.max()))
    
    if USE_CARTOPY:
        fig, axes = plt.subplots(1, 3, figsize=(20, 6), subplot_kw={'projection': ccrs.PlateCarree()})
    else:
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))

    def format_map(ax, data, title, vmin_val, vmax_val, cmap='viridis'):
        if USE_CARTOPY:
            img = data.plot(ax=ax, transform=ccrs.PlateCarree(),
                            vmin=vmin_val, vmax=vmax_val, cmap=cmap, add_colorbar=False)
            ax.coastlines(color='black', linewidth=1)
            ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5)
        else:
            img = data.plot(ax=ax, vmin=vmin_val, vmax=vmax_val, cmap=cmap, add_colorbar=False)
            
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
        return img
        
    # Map 1: Historical ERA5
    img1 = format_map(axes[0], data_ref, 'Original ERA5\n(Historical Reference)', data_ref.min(), data_ref.max(), 'coolwarm')
    cb1 = fig.colorbar(img1, ax=axes[0], orientation='horizontal', pad=0.08, aspect=30)
    cb1.set_label('Temperature (K)', fontsize=12)
    
    # Map 2 and 3: Future Comparisons
    img2 = format_map(axes[1], data_before, 'Future via Standard Downscaling\n(Spatial Structure Broken)', vmin, vmax, 'inferno')
    img3 = format_map(axes[2], data_after, 'Future via Schaake Shuffle\n(Spatial Coherence Restored)', vmin, vmax, 'inferno')
    
    # Shared colorbar for future maps
    cb_shared = fig.colorbar(img2, ax=axes[1:3], orientation='horizontal', pad=0.08, aspect=50)
    cb_shared.set_label('Temperature (K)', fontsize=12)
    
    plt.suptitle('Geographic Evaluation of Spatial Restructuring', fontsize=20, fontweight='bold', y=1.05)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved Geographic Maps to {output_file}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ref = os.path.join(base_dir, 'era5_clean.nc')
    before = os.path.join(base_dir, 'era5_future_hourly.nc')
    after = os.path.join(base_dir, 'era5_spatially_coherent.nc')
    
    if all(os.path.exists(f) for f in [ref, before, after]):
        plot_spatial_comparison(ref, before, after, output_file=os.path.join(base_dir, 'paper_plots', 'geographic_maps_publication.png'))
    else:
        print("Data files not found.")
