import cdsapi

def verify_connection():
    c = cdsapi.Client()

    print("Sending request to CDS API...")
    # Downloading a very small sample: 1 hour of 2m temperature for a generic location
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': '2m_temperature',
            'year': '2023',
            'month': '01',
            'day': '01',
            'time': '12:00',
        },
        'test_download.nc')
    print("Download successful: test_download.nc")

if __name__ == '__main__':
    verify_connection()
