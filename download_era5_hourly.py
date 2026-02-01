import cdsapi
import os
from datetime import datetime

# --- CONFIGURATION ---
# Region of Interest [North, West, South, East]
# Current Default: A region in South India (Telangana/AP). 
# PLEASE UPDATE this to your specific study area.
# ERA5 resolution is ~0.25 degrees. A 2x2 degree box gives ~64 grid points.
AREA = [18.0, 78.0, 16.0, 80.0] 

# Time Period
YEARS = [str(y) for y in range(2010, 2024)] # 2010 to 2023
MONTHS = [f"{m:02d}" for m in range(1, 13)]
DAYS = [f"{d:02d}" for d in range(1, 32)]
TIMES = [f"{h:02d}:00" for h in range(24)]

# Variable
VARIABLE = '2m_temperature'

# Output Directory
OUTPUT_DIR = 'data/raw'

def download_era5_hourly():
    c = cdsapi.Client()
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Starting download for Area: {AREA}")
    print(f"Variable: {VARIABLE}")
    
    for year in YEARS:
        for month in MONTHS:
            output_file = os.path.join(OUTPUT_DIR, f"era5_{VARIABLE}_{year}_{month}.nc")
            
            if os.path.exists(output_file):
                print(f"File already exists, skipping: {output_file}")
                continue
                
            print(f"Downloading data for {year}-{month}...")
            
            try:
                c.retrieve(
                    'reanalysis-era5-single-levels',
                    {
                        'product_type': 'reanalysis',
                        'format': 'netcdf',
                        'variable': VARIABLE,
                        'year': year,
                        'month': month,
                        'day': DAYS,
                        'time': TIMES,
                        'area': AREA,
                    },
                    output_file)
                print(f"Saved: {output_file}")
            except Exception as e:
                print(f"Failed to download {year}-{month}: {e}")

if __name__ == '__main__':
    download_era5_hourly()
