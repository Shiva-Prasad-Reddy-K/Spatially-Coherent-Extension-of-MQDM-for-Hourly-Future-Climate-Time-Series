import shutil
import xarray as xr
import os

def prepare_samples():
    print("Preparing sample data...")

    # 1. Create ERA5 Sample
    # We use the test_download.nc file if it exists, otherwise we take the first available file from data/raw
    if os.path.exists("test_download.nc"):
        print("Using test_download.nc for ERA5 sample.")
        shutil.copy("test_download.nc", "era5_smoke_test.nc")
    else:
        # Fallback to data/raw
        era5_files = sorted([f for f in os.listdir("data/raw") if f.startswith("era5") and f.endswith(".nc")])
        if era5_files:
            print(f"Using data/raw/{era5_files[0]} for ERA5 sample.")
            shutil.copy(os.path.join("data/raw", era5_files[0]), "era5_smoke_test.nc")
        else:
            print("Error: No ERA5 data found to create sample!")
            return

    # 2. Create CMIP6 Sample (Merge Tmax and Tmin)
    tmax_path = "data/raw/cmip6_tmax_2040.nc"
    tmin_path = "data/raw/cmip6_tmin_2040.nc"

    if os.path.exists(tmax_path) and os.path.exists(tmin_path):
        print("Merging CMIP6 Tmax and Tmin...")
        try:
            ds_tmax = xr.open_dataset(tmax_path, engine='netcdf4')
            ds_tmin = xr.open_dataset(tmin_path, engine='netcdf4')
            
            # Merge
            ds_cmip6 = xr.merge([ds_tmax, ds_tmin])
            ds_cmip6.to_netcdf("cmip6_sample.nc")
            print("Created cmip6_sample.nc")
            
            ds_tmax.close()
            ds_tmin.close()
            ds_cmip6.close()
        except Exception as e:
            print(f"Error merging CMIP6 files: {e}")
    else:
        print("Error: CMIP6 raw files not found in data/raw!")

if __name__ == "__main__":
    prepare_samples()
