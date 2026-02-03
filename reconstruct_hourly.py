import xarray as xr
import numpy as np

def reconstruct_hourly():
    print("Starting Hourly Reconstruction...")
    
    # 1. Load Data
    print("Loading datasets...")
    # Historical Hourly
    ds_obs = xr.open_dataset('era5_clean.nc', engine='netcdf4')
    # Future Daily (Shifted)
    ds_fut_daily = xr.open_dataset('era5_future_daily.nc', engine='netcdf4')
    
    # Check variable name
    var_name_obs = 'temp_hourly'
    if var_name_obs not in ds_obs:
        print(f"Error: Variable {var_name_obs} not found in era5_clean.nc")
        return

    # 2. Compute Observed Daily Statistics
    print("Computing observed daily Tmax/Tmin...")
    # We need to map these back to hourly
    # Resample to daily
    obs_tmax_daily = ds_obs[var_name_obs].resample(valid_time='1D').max()
    obs_tmin_daily = ds_obs[var_name_obs].resample(valid_time='1D').min()
    
    # 3. Broadcast Daily Observed to Hourly
    print("Broadcasting daily observed stats to hourly...")
    # Use reindex with ffill to propagate daily value to all hours in that day
    # 'valid_time' is the coordinate
    
    # Ensure daily time coords match up for broadcasting
    # Resample puts time at 00:00:00 usually.
    
    obs_tmax_hourly = obs_tmax_daily.reindex(valid_time=ds_obs['valid_time'], method='ffill')
    obs_tmin_hourly = obs_tmin_daily.reindex(valid_time=ds_obs['valid_time'], method='ffill')
    
    # 4. Calculate Alpha (Shape Factor)
    print("Calculating Alpha...")
    # Alpha = (T_obs - Tmin_obs) / (Tmax_obs - Tmin_obs)
    dtr_obs = obs_tmax_hourly - obs_tmin_hourly
    
    # Avoid division by zero
    dtr_obs = dtr_obs.where(dtr_obs != 0, np.nan) 
    
    alpha = (ds_obs[var_name_obs] - obs_tmin_hourly) / dtr_obs
    
    # Fill NaNs where DTR was 0 (Alpha is technically undefined, usually means constant temp)
    # If DTR is 0, temp is constant, so alpha is irrelevant if we map correctly.
    # But usually we can set alpha to 0.5 or just 0. Let's use 0.
    alpha = alpha.fillna(0)
    
    # 5. Broadcast Future Daily to Hourly
    print("Broadcasting future daily stats to hourly...")
    
    # ds_fut_daily likely uses 'valid_time' if we preserved it in mqdm script, or 'time'.
    # In mqdm script we sorted by 'era5_time_name'.
    # Let's check the coordinate name in ds_fut_daily
    fut_time_name = list(ds_fut_daily.coords.keys())[0] # Guessing if not standard
    if 'valid_time' in ds_fut_daily.coords:
        fut_time_name = 'valid_time'
    elif 'time' in ds_fut_daily.coords:
        fut_time_name = 'time'
        
    print(f"Future time dim: {fut_time_name}")
    
    # We need to reindex `ds_fut_daily` to `ds_obs['valid_time']`
    # BUT `ds_fut_daily` might have a slightly different time coordinate labeling or name
    # We must rename it to match ds_obs if needed for direct reindex
    
    if fut_time_name != 'valid_time':
        ds_fut_daily = ds_fut_daily.rename({fut_time_name: 'valid_time'})
        
    fut_tmax_hourly = ds_fut_daily['tmax_shifted'].reindex(valid_time=ds_obs['valid_time'], method='ffill')
    fut_tmin_hourly = ds_fut_daily['tmin_shifted'].reindex(valid_time=ds_obs['valid_time'], method='ffill')
    
    # 6. Reconstruct Future Hourly
    print("Reconstructing future hourly temperatures...")
    # T_fut = Tmin_fut + Alpha * (Tmax_fut - Tmin_fut)
    
    dtr_fut = fut_tmax_hourly - fut_tmin_hourly
    temp_future = fut_tmin_hourly + (alpha * dtr_fut)
    
    # 7. Save
    print("Saving era5_future_hourly.nc...")
    ds_out = xr.Dataset()
    ds_out['temp_future'] = temp_future
    ds_out['temp_future'].attrs = {
        'units': 'Celsius',
        'long_name': 'MQDM Shifted Hourly 2m Temperature',
        'description': 'Reconstructed hourly time series based on CMIP6 daily shifts and ERA5 diurnal cycle.'
    }
    
    # Compressing
    encoding = {'temp_future': {'zlib': True, 'complevel': 5}}
    ds_out.to_netcdf('era5_future_hourly.nc', encoding=encoding)
    print("Done!")

if __name__ == '__main__':
    reconstruct_hourly()
