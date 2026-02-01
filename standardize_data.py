import xarray as xr
import numpy as np

def standardize():
    print("Starting Data Standardization...")
    
    # --- ERA5 ---
    try:
        print("\nProcessing ERA5...")
        ds_era5 = xr.open_dataset('era5_smoke_test.nc', engine='netcdf4')
        print(f"Original ERA5 variables: {list(ds_era5.data_vars)}")
        
        # Rename loop (more robust than assuming 't2m')
        if 't2m' in ds_era5:
            ds_era5 = ds_era5.rename({'t2m': 'temp_hourly'})
        elif 'var167' in ds_era5: # Common code for 2m temp
             ds_era5 = ds_era5.rename({'var167': 'temp_hourly'})
             
        # Unit conversion
        if 'temp_hourly' in ds_era5:
            # Check if likely Kelvin (mean > 200)
            if ds_era5['temp_hourly'].mean() > 200:
                print("Converting ERA5 from Kelvin to Celsius")
                ds_era5['temp_hourly'] = ds_era5['temp_hourly'] - 273.15
                ds_era5['temp_hourly'].attrs['units'] = 'Celsius'
        
        ds_era5.to_netcdf('era5_clean.nc')
        print("Saved: era5_clean.nc")
        ds_era5.close()
        
    except Exception as e:
        print(f"FAILED to process ERA5: {e}")

    # --- CMIP6 ---
    try:
        print("\nProcessing CMIP6...")
        ds_cmip6 = xr.open_dataset('cmip6_sample.nc', engine='netcdf4')
        print(f"Original CMIP6 variables: {list(ds_cmip6.data_vars)}")
        
        # Rename
        rename_dict = {}
        for var in ds_cmip6.data_vars:
            if 'tasmax' in var:
                rename_dict[var] = 'tmax_daily'
            elif 'tasmin' in var:
                rename_dict[var] = 'tmin_daily'
        
        if rename_dict:
            print(f"Renaming: {rename_dict}")
            ds_cmip6 = ds_cmip6.rename(rename_dict)
            
        # Unit conversion
        for var in ['tmax_daily', 'tmin_daily']:
            if var in ds_cmip6:
                 if ds_cmip6[var].mean() > 200:
                    print(f"Converting {var} from Kelvin to Celsius")
                    ds_cmip6[var] = ds_cmip6[var] - 273.15
                    ds_cmip6[var].attrs['units'] = 'Celsius'

        ds_cmip6.to_netcdf('cmip6_clean.nc')
        print("Saved: cmip6_clean.nc")
        
        # --- Spatial Check ---
        print("\n--- Spatial Alignment Check ---")
        if 'lat' in ds_cmip6.coords:
            lat_name = 'lat'
        elif 'latitude' in ds_cmip6.coords:
            lat_name = 'latitude'
        else:
            lat_name = None

        if lat_name:
             print(f"CMIP6 Lats: {ds_cmip6[lat_name].values}")
             
        ds_cmip6.close()

    except Exception as e:
        print(f"FAILED to process CMIP6: {e}")

if __name__ == '__main__':
    standardize()
