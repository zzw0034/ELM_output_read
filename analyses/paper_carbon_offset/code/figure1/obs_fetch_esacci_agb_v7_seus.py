"""
Fetch the SEUS subset of the ESA CCI Biomass v7.0 1 km aggregated AGB
product straight from CEDA with HTTP byte-range reads (netCDF-C
"#mode=bytes"), without downloading the 3 GB global file.

Source (open access, doi:10.5285/6429d1aafe1e43b9b414e4a5a7f8b903):
    https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/netcdf/
    ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0.nc
Global 0.01 deg grid (GeoTransform -180, 0.01, 90, -0.01), 18 epochs
(2005-2012, 2015-2024), variables agb and agb_sd in Mg/ha. Per the CEDA
catalogue abstract, AGB is oven-dry weight of the woody parts of living
trees (stem, bark, branches, twigs), excluding stump and roots -- i.e. dry
biomass, not carbon. Values are copied unchanged (raw int16, same
_FillValue); no unit or carbon-fraction conversion is applied here.

Subset = the nominal SEUS 1/24 deg grid bbox (make_scrip_1_24_deg.py):
lon -95..-74, lat 24..37.5. Its edges fall exactly on 0.01 deg pixel
edges, so the subset is index-exact:
    lon index 8500..10599 (centers -94.995..-74.005, 2100 columns)
    lat index 5250..6599  (centers  37.495..24.005, 1350 rows, N->S)
The script asserts those coordinates before copying.

Network-bound data transfer, one epoch (~5.7 MB per variable) in memory at
a time. Usage (on Pathfinder, run through the make_surfdata_pf python):
    python obs_fetch_esacci_agb_v7_seus.py <out_dir> [<md5 of this script>]
(the md5 argument lets a stdin-streamed run still record which script version ran).
"""
import datetime
import os
import sys
import time

import netCDF4
import numpy as np

URL = ("https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/netcdf/"
       "ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0.nc")
LON_SLICE = slice(8500, 10600)
LAT_SLICE = slice(5250, 6600)
OUT_NAME = "ESACCI-BIOMASS-L4-AGB-MERGED-1000m-fv7.0_SEUS_lat24-37.5_lon-95--74.nc"
DATA_VARS = ["agb", "agb_sd"]
N_RETRY = 4


def read_with_retry(var, idx):
    for attempt in range(1, N_RETRY + 1):
        try:
            return var[idx]
        except (RuntimeError, OSError) as e:
            if attempt == N_RETRY:
                raise
            print(f"    read failed ({e}); retry {attempt}/{N_RETRY - 1}", flush=True)
            time.sleep(10 * attempt)


def main():
    out_dir = sys.argv[1]
    out_path = os.path.join(out_dir, OUT_NAME)
    tmp_path = out_path + ".part"
    assert not os.path.exists(out_path), f"{out_path} exists; refusing to overwrite"

    src = netCDF4.Dataset(URL + "#mode=bytes")
    src.set_auto_maskandscale(False)

    lon = src["lon"][LON_SLICE]
    lat = src["lat"][LAT_SLICE]
    assert lon.size == 2100 and lat.size == 1350
    assert np.isclose(lon[0], -94.995) and np.isclose(lon[-1], -74.005), (lon[0], lon[-1])
    assert np.isclose(lat[0], 37.495) and np.isclose(lat[-1], 24.005), (lat[0], lat[-1])
    ntime = src.dimensions["time"].size
    print(f"subset lon {lon[0]}..{lon[-1]}  lat {lat[0]}..{lat[-1]}  ntime={ntime}", flush=True)

    dst = netCDF4.Dataset(tmp_path, "w", format="NETCDF4_CLASSIC")
    dst.createDimension("lon", lon.size)
    dst.createDimension("lat", lat.size)
    dst.createDimension("time", ntime)
    dst.createDimension("nv", 2)

    def copy_attrs(sv, dv):
        dv.setncatts({k: sv.getncattr(k) for k in sv.ncattrs() if k != "_FillValue"})

    for name, data in [("lon", lon), ("lat", lat)]:
        v = dst.createVariable(name, "f8", (name,))
        copy_attrs(src[name], v)
        v[:] = data
    bnd = dst.createVariable("lon_bnds", "f8", ("lon", "nv"))
    bnd[:] = src["lon_bnds"][LON_SLICE, :]
    bnd = dst.createVariable("lat_bnds", "f8", ("lat", "nv"))
    bnd[:] = src["lat_bnds"][LAT_SLICE, :]
    for name in ["time", "time_bnds"]:
        dims = src[name].dimensions
        v = dst.createVariable(name, "f8", dims)
        copy_attrs(src[name], v)
        v[:] = src[name][:]

    crs = dst.createVariable("crs", "S1")
    copy_attrs(src["crs"], crs)
    crs.GeoTransform = "-95.0 0.01 0 37.5 0 -0.01"

    for name in DATA_VARS:
        sv = src[name]
        dv = dst.createVariable(name, sv.dtype, ("time", "lat", "lon"), zlib=True, complevel=4,
                                chunksizes=(1, lat.size, lon.size), fill_value=sv.getncattr("_FillValue"))
        copy_attrs(sv, dv)

    years = []
    for t in range(ntime):
        year = (datetime.date(1990, 1, 1) + datetime.timedelta(days=float(src["time"][t]))).year
        years.append(year)
        for name in DATA_VARS:
            t0 = time.time()
            block = read_with_retry(src[name], (t, LAT_SLICE, LON_SLICE))
            dst[name][t, :, :] = block
            valid = block[block != src[name].getncattr("_FillValue")]
            print(f"  {year} {name}: valid={valid.size} min={valid.min() if valid.size else 'NA'} "
                  f"max={valid.max() if valid.size else 'NA'} ({time.time() - t0:.1f}s)", flush=True)

    dst.setncatts({k: src.getncattr(k) for k in src.ncattrs()})
    dst.geospatial_lat_min = "24.0"
    dst.geospatial_lat_max = "37.5"
    dst.geospatial_lon_min = "-95.0"
    dst.geospatial_lon_max = "-74.0"
    script_md5 = sys.argv[2] if len(sys.argv) > 2 else "unknown"
    dst.subset_source_url = URL
    dst.subset_index = "lon[8500:10600], lat[5250:6600] of the global 0.01 deg grid"
    dst.subset_epochs = " ".join(str(y) for y in years)
    dst.subset_note = ("Values unchanged from source (int16 Mg/ha, oven-dry woody AGB, not carbon). "
                       "Fetched by HTTP byte-range read; script obs_fetch_esacci_agb_v7_seus.py in "
                       "zzw0034/ELM_output_read analyses/paper_carbon_offset/code/.")
    dst.history = (f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%dT%H:%M:%SZ}: SEUS subset "
                   f"of {URL} (script md5 {script_md5}); " + src.getncattr("history"))
    dst.close()
    src.close()
    os.rename(tmp_path, out_path)
    print(f"wrote {out_path} ({os.path.getsize(out_path) / 1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
