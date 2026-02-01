import os
import glob
import xarray as xr

# Define path to data
DATA_DIR = "data/raw"

def verify_data():
    if not os.path.exists(DATA_DIR):
        print(f"Error: Directory {DATA_DIR} does not exist.")
        return

    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.nc")))
    print(f"Found {len(files)} files in {DATA_DIR}")

    if len(files) == 0:
        print("No .nc files found!")
        return

    valid_count = 0
    for f in files:
        try:
            ds = xr.open_dataset(f)
            # Basic check: Access "2m_temperature"
            _ = ds['t2m']
            ds.close()
            valid_count += 1
            # print(f"Valid: {os.path.basename(f)}")
        except Exception as e:
            print(f"INVALID: {os.path.basename(f)} - {e}")

    print(f"\nVerification Complete: {valid_count}/{len(files)} files are valid.")

if __name__ == "__main__":
    verify_data()
