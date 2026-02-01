import xarray as xr
import glob
import os

def merge_era5():
    print("Merging ERA5 files from data/raw/...")
    file_pattern = "data/raw/era5_2m_temperature_*.nc"
    files = sorted(glob.glob(file_pattern))
    
    if not files:
        print("No ERA5 files found!")
        return

    print(f"Found {len(files)} files.")
    
    # Open all files
    try:
        ds = xr.open_mfdataset(files, combine='by_coords', engine='netcdf4')
        print("Dataset loaded. Dimensions:", ds.dims)
        
        # Renaissance
        if 't2m' in ds:
            ds = ds.rename({'t2m': 'temp_hourly'})
        elif 'var167' in ds:
            ds = ds.rename({'var167': 'temp_hourly'})
            
        # Standardize Units
        if 'temp_hourly' in ds:
             if ds['temp_hourly'].mean() > 200:
                print("Converting to Celsius...")
                ds['temp_hourly'] = ds['temp_hourly'] - 273.15
                ds['temp_hourly'].attrs['units'] = 'Celsius'
        
        # Save
        print("Saving to era5_clean.nc (this might take a moment)...")
        # Encoding compression to save space
        encoding = {'temp_hourly': {'zlib': True, 'complevel': 5}}
        ds.to_netcdf('era5_clean.nc', encoding=encoding)
        print("Success: era5_clean.nc created.")
        
    except Exception as e:
        print(f"Merge failed: {e}")

if __name__ == "__main__":
    merge_era5()
