import xarray as xr
import numpy as np
import scipy.stats as stats
import warnings

# Suppress annoying xarray warnings
warnings.filterwarnings("ignore")

def mqdm_daily_shift():
    print("Starting MQDM Daily Shift...")

    # 1. Load Data
    print("Loading datasets...")
    # ERA5 (Hourly)
    ds_era5 = xr.open_dataset('era5_clean.nc', engine='netcdf4')
    # CMIP6 Historical (Daily)
    ds_hist = xr.open_dataset('cmip6_hist_clean.nc', engine='netcdf4')
    # CMIP6 Future (Daily)
    ds_fut = xr.open_dataset('cmip6_clean.nc', engine='netcdf4')

    print(f"ERA5 Range: {ds_era5['valid_time'].min().values} to {ds_era5['valid_time'].max().values}")

    # 2. Resample ERA5 to Daily
    print("Resampling ERA5 to daily Tmax/Tmin...")
    # Rename 'valid_time' to 'time' if needed to match standard conventions, or use keyword
    # ERA5 usually has 'valid_time'. We'll use the coordinate name present.
    era5_time_name = 'valid_time' if 'valid_time' in ds_era5.coords else 'time'
    
    era5_daily_max = ds_era5['temp_hourly'].resample({era5_time_name: '1D'}).max()
    era5_daily_min = ds_era5['temp_hourly'].resample({era5_time_name: '1D'}).min()
    
    # Store results here
    tmax_shifted_list = []
    tmin_shifted_list = []
    
    # Grid Handling:
    # If CMIP6 grid is different (1x1) vs ERA5 (9x9), we need to broadcast or interpolate.
    # Since CMIP6 is coarser, we can treat its distribution as representative for the region
    # and apply the *deltas* globally to the ERA5 grid, OR interpolate the deltas.
    # For this script, we assume we apply the single CMIP6 loc's deltas to all ERA5 points 
    # (since the ERA5 domain is small, 2x2 degrees, this is physically reasonable).
    
    # 3. Monthly Loop
    print("\nProcessing Months...")
    months = range(1, 13)
    quantiles = np.linspace(0.01, 0.99, 99) # 99 percentiles
    
    # Pre-compute CMIP6 quantiles (simplifies loop)
    # Check which dims exist
    dims_to_reduce = [d for d in ['lat', 'lon', 'latitude', 'longitude'] if d in ds_hist.dims]
    print(f"Reducing CMIP6 over dimensions: {dims_to_reduce}")
    
    if dims_to_reduce:
        hist_tmax_all = ds_hist['tmax_daily'].mean(dim=dims_to_reduce)
        hist_tmin_all = ds_hist['tmin_daily'].mean(dim=dims_to_reduce)
    else:
        hist_tmax_all = ds_hist['tmax_daily']
        hist_tmin_all = ds_hist['tmin_daily']
        
    dims_to_reduce_fut = [d for d in ['lat', 'lon', 'latitude', 'longitude'] if d in ds_fut.dims]
    if dims_to_reduce_fut:
        fut_tmax_all = ds_fut['tmax_daily'].mean(dim=dims_to_reduce_fut)
        fut_tmin_all = ds_fut['tmin_daily'].mean(dim=dims_to_reduce_fut)
    else:
        fut_tmax_all = ds_fut['tmax_daily']
        fut_tmin_all = ds_fut['tmin_daily']

    # Prepare outputs initialized with ERA5 shape (but daily time)
    # We can't easily initialize xarray datasets empty, so we'll construct lists.
    
    for month in months:
        print(f" -> Month {month}")
        
        # --- A. Calculate DELTAS from CMIP6 ---
        # Select month
        hist_m_tmax = hist_tmax_all.sel(time=hist_tmax_all['time'].dt.month == month)
        fut_m_tmax = fut_tmax_all.sel(time=fut_tmax_all['time'].dt.month == month)
        
        hist_m_tmin = hist_tmin_all.sel(time=hist_tmin_all['time'].dt.month == month)
        fut_m_tmin = fut_tmin_all.sel(time=fut_tmin_all['time'].dt.month == month)
        
        # Compute Quantiles (Q)
        # dims: (quantile: 99)
        Q_hist_tmax = hist_m_tmax.quantile(quantiles, dim='time')
        Q_fut_tmax = fut_m_tmax.quantile(quantiles, dim='time')
        Delta_tmax = Q_fut_tmax - Q_hist_tmax
        
        Q_hist_tmin = hist_m_tmin.quantile(quantiles, dim='time')
        Q_fut_tmin = fut_m_tmin.quantile(quantiles, dim='time')
        Delta_tmin = Q_fut_tmin - Q_hist_tmin
        
        # --- B. Apply to ERA5 ---
        # Select ERA5 month
        # era5_daily_max is (time, lat, lon)
        era5_m_tmax = era5_daily_max.sel({era5_time_name: era5_daily_max[era5_time_name].dt.month == month})
        era5_m_tmin = era5_daily_min.sel({era5_time_name: era5_daily_min[era5_time_name].dt.month == month})
        
        if era5_m_tmax.sizes[era5_time_name] == 0:
            continue

        # Function to apply delta based on rank
        # We wrap this to apply over the spatial grid if needed, 
        # but xarray broadcasting usually handles the scalar addition fine.
        # The Step is: Identify Rank of each value -> Interpolate Delta -> Add
        
        def apply_shift(data_array, delta_quantiles, quantiles_lev):
            # 1. Compute Rank (0..1)
            # We use xarray's rank or rank along time?
            # Creating a CDF for the data itself is expensive if we do it per pixel.
            # A faster way: Convert data to ranks relative to ITSELF.
            # But the 'Delta' is defined on the *Model* quantiles.
            # Wait, Standard QDM applies Delta(tau) where tau is the quantile of the OBSERVATION (ERA5).
            
            # Map data to quantiles 0..1
            # We can use q = data.rank() / n
            valid_mask = data_array.notnull()
            ranks = data_array.rank(dim=era5_time_name, pct=True)
            
            # Interpolate Deltas
            # Delta_tmax is coords=(quantile,). ranks is (time, lat, lon).
            # We use interp() on the quantile dimension
            deltas_interpolated = delta_quantiles.interp(quantile=ranks, method='linear')
            
            # Shift
            return data_array + deltas_interpolated

        # Apply
        shifted_tmax = apply_shift(era5_m_tmax, Delta_tmax, quantiles)
        shifted_tmin = apply_shift(era5_m_tmin, Delta_tmin, quantiles)
        
        tmax_shifted_list.append(shifted_tmax)
        tmin_shifted_list.append(shifted_tmin)

    # 4. Concatenate and Sort
    print("Concatenating monthly results...")
    ds_out = xr.Dataset()
    
    # Concat along time
    ds_out['tmax_shifted'] = xr.concat(tmax_shifted_list, dim=era5_time_name).sortby(era5_time_name)
    ds_out['tmin_shifted'] = xr.concat(tmin_shifted_list, dim=era5_time_name).sortby(era5_time_name)
    
    # 5. Save
    print("Saving era5_future_daily.nc...")
    ds_out.to_netcdf('era5_future_daily.nc')
    print("Done!")

if __name__ == '__main__':
    mqdm_daily_shift()
