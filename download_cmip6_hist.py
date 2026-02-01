import cdsapi
import zipfile
import os
import xarray as xr
import numpy as np

# --- CONFIGURATION ---
DATASET = 'projections-cmip6'
MODEL = 'mpi_esm1_2_lr'
EXPERIMENT = 'historical'
AREA = [20, 78, 19, 79] # North, West, South, East
YEAR = '2000'
MONTHS = [f"{m:02d}" for m in range(1, 13)]
DAYS = [f"{d:02d}" for d in range(1, 32)]

OUTPUT_DIR = 'data/raw'

def download_variable(variable_name, output_filename):
    c = cdsapi.Client()
    
    zip_filename = output_filename.replace('.nc', '.zip')
    full_zip_path = os.path.join(OUTPUT_DIR, zip_filename)
    full_nc_path = os.path.join(OUTPUT_DIR, output_filename)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    if os.path.exists(full_nc_path):
        print(f"File already exists: {full_nc_path}")
        return full_nc_path

    print(f"Downloading {variable_name} for {YEAR}...")
    
    try:
        c.retrieve(
            DATASET,
            {
                'format': 'zip',
                'temporal_resolution': 'daily',
                'experiment': EXPERIMENT,
                'level': 'single_levels',
                'variable': variable_name,
                'model': MODEL,
                'year': YEAR,
                'month': MONTHS,
                'day': DAYS,
                'area': AREA,
            },
            full_zip_path)
            
        print(f"Download complete. Extracting {zip_filename}...")
        
        with zipfile.ZipFile(full_zip_path, 'r') as zip_ref:
            extracted_files = zip_ref.namelist()
            
            # Find the NetCDF file in the zip
            nc_files = [f for f in extracted_files if f.endswith('.nc')]
            if not nc_files:
                print("Error: No .nc file found in zip.")
                return None
            
            original_nc_name = nc_files[0]
            print(f"Found NetCDF file: {original_nc_name}")
            
            zip_ref.extract(original_nc_name, OUTPUT_DIR)
            
            # Rename to clean target name
            extracted_path = os.path.join(OUTPUT_DIR, original_nc_name)
            os.rename(extracted_path, full_nc_path)
            print(f"Extracted and renamed to: {full_nc_path}")
            
        # Clean up zip file
        os.remove(full_zip_path)
        print("Zip file removed.")
        return full_nc_path
        
    except Exception as e:
        print(f"Failed to download/extract {variable_name}: {e}")
        return None

def standardize_history(tmax_file, tmin_file):
    print("\n--- Starting Merge and Standardization ---")
    
    sample_file = "cmip6_hist_sample.nc"
    clean_file = "cmip6_hist_clean.nc"
    
    try:
        # Load
        print("Loading files...")
        ds_tmax = xr.open_dataset(tmax_file, engine='netcdf4')
        ds_tmin = xr.open_dataset(tmin_file, engine='netcdf4')
        
        # Merge
        print("Merging...")
        ds_hist = xr.merge([ds_tmax, ds_tmin])
        ds_hist.to_netcdf(sample_file)
        print(f"Saved merged sample: {sample_file}")
        
        # Rename variables
        print("Renaming variables...")
        rename_dict = {}
        for var in ds_hist.data_vars:
            if 'tasmax' in var:
                rename_dict[var] = 'tmax_daily'
            elif 'tasmin' in var:
                rename_dict[var] = 'tmin_daily'
        
        if rename_dict:
            ds_hist = ds_hist.rename(rename_dict)
            
        # Convert Units
        print("Checking units...")
        for var in ['tmax_daily', 'tmin_daily']:
            if var in ds_hist:
                 if ds_hist[var].mean() > 200:
                    print(f"Converting {var} from Kelvin to Celsius")
                    ds_hist[var] = ds_hist[var] - 273.15
                    ds_hist[var].attrs['units'] = 'Celsius'

        # Save Clean
        ds_hist.to_netcdf(clean_file)
        print(f"Saved standardized file: {clean_file}")
        
        ds_tmax.close()
        ds_tmin.close()
        ds_hist.close()
        
    except Exception as e:
        print(f"Standardization Failed: {e}")

if __name__ == '__main__':
    # 1. Download Data
    tmax_path = download_variable('daily_maximum_near_surface_air_temperature', f'cmip6_hist_tmax_{YEAR}.nc')
    tmin_path = download_variable('daily_minimum_near_surface_air_temperature', f'cmip6_hist_tmin_{YEAR}.nc')
    
    # 2. Merge and Standardize (if downloads successful)
    if tmax_path and tmin_path:
        standardize_history(tmax_path, tmin_path)
    else:
        print("Skipping standardization due to download failure.")
