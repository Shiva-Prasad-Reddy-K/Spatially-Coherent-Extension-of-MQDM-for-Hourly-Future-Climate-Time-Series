import xarray as xr
import numpy as np
import scipy.stats as stats

def schaake_shuffle():
    print("Starting Schaake Shuffle (Spatially Coherent Extension)...")
    
    # 1. Load Data
    print("Loading datasets...")
    ds_obs = xr.open_dataset('era5_clean.nc', engine='netcdf4') # Template source
    ds_fut = xr.open_dataset('era5_future_hourly.nc', engine='netcdf4') # Target to reorder
    
    var_obs = 'temp_hourly'
    var_fut = 'temp_future'
    
    # Check alignment
    if ds_obs.sizes['valid_time'] != ds_fut.sizes['valid_time']:
         print("Warning: Time dimensions do not match exactly. Truncating to shorter one.")
         min_len = min(ds_obs.sizes['valid_time'], ds_fut.sizes['valid_time'])
         ds_obs = ds_obs.isel(valid_time=slice(0, min_len))
         ds_fut = ds_fut.isel(valid_time=slice(0, min_len))

    # 2. Prepare Dimensions (Flatten Spatial)
    print("Flattening spatial dimensions...")
    # Stack lat/lon into a single 'location' dimension
    # We want shape (time, space)
    
    # Historical
    da_obs_flat = ds_obs[var_obs].stack(space=('latitude', 'longitude'))
    # Future
    da_fut_flat = ds_fut[var_fut].stack(space=('latitude', 'longitude'))
    
    # Convert to numpy for fast processing
    X_obs = da_obs_flat.values # Shape (Time, Space)
    X_fut = da_fut_flat.values # Shape (Time, Space)
    
    print(f"Data Shape: {X_fut.shape}")
    
    # 3. The Schaake Shuffle
    print("Applying Shuffle...")
    
    # Step A: Sort Future (Ascending along space)
    # We want to re-arrange the VALUES of X_fut spatially to match the RANK PATTERN of X_obs.
    # Note: Schaake Shuffle typically sorts *independent samples*, usually temporal.
    # BUT here use it for SPATIAL coherence.
    # Wait, the Schaake Shuffle creates dependence between variables (locations).
    # Correct Logic:
    # 1. Identify the dependence structure (rank) of the Reference (X_obs) across locations? 
    #    No, standard Schaake Shuffle: reconstructs vector dependence.
    #    For a given timestep t:
    #    Vector Y_fut(t) = [y1, y2, ... yN]. 
    #    Vector Y_obs(t) = [x1, x2, ... xN].
    #    We want Y_new(t) to have distribution of Y_fut but correlation of Y_obs.
    #    Implementation:
    #      Y_new(t) = Sort(Y_fut(t)) [ Rank(Y_obs(t)) ]
    #    Wait, Sort(Y_fut) gives the ordered magnitudes.
    #    Rank(Y_obs) gives the indices of where the smallest, 2nd smallest, etc. are located on the map.
    #    So if Obs has the cold spot at loc 5, Future should put its coldest value at loc 5.
    
    # Vectorized implementation Loop over Time (or can we broadcast?)
    # Sorting per row (time step)
    
    # Sort Future along Spatial Axis (axis=1)
    X_fut_sorted = np.sort(X_fut, axis=1)
    
    # Get Rank/Indices of Historical along Spatial Axis
    # argsort gives limits that would sort the array.
    # We want the 'rank structure'.
    # If X_obs = [20, 30, 10], argsort -> [2, 0, 1] (indices of min, mid, max).
    # X_fut_sorted = [15, 25, 35] (values min, mid, max).
    # We want X_new to be [25, 35, 15] (matching the pattern: medium, high, low).
    
    # BUT argsort gives indices FROM sorted TO original.
    # We want to place X_fut_sorted[0] at index 2, X_fut_sorted[1] at index 0, etc.
    # This is effectively "unsorting".
    
    # Let idx = argsort(X_obs). 
    # X_obs[idx] is sorted.
    # We want Y such that Y[idx] = X_fut_sorted.
    # So Y = X_fut_sorted[inverse_permutation] ?
    
    # Actually simpler:
    # argsort(X_obs) tells us which element is 1st, 2nd, 3rd.
    #   idx = [2, 0, 1] means:
    #   Element at 2 is smallest (Rank 0)
    #   Element at 0 is middle (Rank 1)
    #   Element at 1 is largest (Rank 2)
    
    # However we want to construct the array.
    # Let's use `argsort(argsort(X_obs))` which gives the Rank (0..N-1) of each element.
    #   X_obs = [20, 30, 10]
    #   argsort -> [2, 0, 1]
    #   argsort(argsort) -> [1, 2, 0]
    #   This means: Index 0 has rank 1. Index 1 has rank 2. Index 2 has rank 0.
    
    # Now take X_fut_sorted = [15, 25, 35].
    # We want result[i] = X_fut_sorted[ rank[i] ].
    #   i=0: rank=1 -> 25
    #   i=1: rank=2 -> 35
    #   i=2: rank=0 -> 15
    #   Result: [25, 35, 15].
    # Pattern matches Obs ([20, 30, 10] -> Mid, High, Low). Values match Fut. 
    # Correct!
    
    ranks = np.argsort(np.argsort(X_obs, axis=1), axis=1)
    
    # Apply ranks to grab from sorted future
    # We need advanced indexing.
    # X_new[t, s] = X_fut_sorted[t, ranks[t, s]]
    
    # Create grid of time indices
    rows = np.arange(X_obs.shape[0])[:, np.newaxis]
    X_coherent = X_fut_sorted[rows, ranks] # Broadcasting magic
    
    # 4. Reconstruct & Save
    print("Reconstructing Dimensions...")
    
    # Put back into DataArray
    da_coherent = xr.DataArray(
        X_coherent,
        coords=da_fut_flat.coords,
        dims=da_fut_flat.dims,
        name='temp_coherent'
    )
    
    # Unstack
    da_coherent_unstacked = da_coherent.unstack('space')
    
    ds_out = xr.Dataset()
    ds_out['temp_coherent'] = da_coherent_unstacked
    
    # Copy attributes
    ds_out.attrs = ds_fut.attrs
    ds_out.attrs['description'] = 'Spatially Coherent MQDM (Schaake Shuffle Applied)'
    
    print("Saving era5_spatially_coherent.nc...")
    encoding = {'temp_coherent': {'zlib': True, 'complevel': 5}}
    ds_out.to_netcdf('era5_spatially_coherent.nc', encoding=encoding)
    print("Done!")
    
    # 5. Verify Correlation Improvement
    print("\n--- Verification: Spatial Correlation ---")
    
    # Select Loc A (0,0) and Loc B (0,1)
    # Check if we have enough points
    if ds_out.sizes['longitude'] < 2:
        print("Not enough points to verify.")
        return

    ts_A = ds_out['temp_coherent'].isel(latitude=0, longitude=0).values.flatten()
    ts_B = ds_out['temp_coherent'].isel(latitude=0, longitude=1).values.flatten()
    
    valid = (~np.isnan(ts_A)) & (~np.isnan(ts_B))
    ts_A = ts_A[valid]
    ts_B = ts_B[valid]
    
    r_coherent, _ = stats.pearsonr(ts_A, ts_B)
    print(f"Coherent Correlation (Loc A vs B): {r_coherent:.4f}")
    print("(Compare this to ~0.9926 from broken phase, and ~0.9958 from historical)")

if __name__ == '__main__':
    schaake_shuffle()
