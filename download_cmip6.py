import cdsapi
import zipfile
import os

# --- CONIFGURATION ---
DATASET = 'projections-cmip6'
MODEL = 'mpi_esm1_2_lr'
EXPERIMENT = 'ssp3_7_0'
AREA = [20, 78, 19, 79] # North, West, South, East
YEAR = '2040'
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
        return

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
            # CMIP6 zips usually contain one NetCDF file with a long name
            extracted_files = zip_ref.namelist()
            if not extracted_files:
                print("Error: Zip file is empty.")
                return
            
            # Find the NetCDF file in the zip
            nc_files = [f for f in extracted_files if f.endswith('.nc')]
            if not nc_files:
                print("Error: No .nc file found in zip.")
                return
            
            # Use the first .nc file found (usually there's only one data file)
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
        
    except Exception as e:
        print(f"Failed to download/extract {variable_name}: {e}")

if __name__ == '__main__':
    # Download Daily Maximum Temperature
    download_variable('daily_maximum_near_surface_air_temperature', f'cmip6_tmax_{YEAR}.nc')
    
    # Download Daily Minimum Temperature
    download_variable('daily_minimum_near_surface_air_temperature', f'cmip6_tmin_{YEAR}.nc')
