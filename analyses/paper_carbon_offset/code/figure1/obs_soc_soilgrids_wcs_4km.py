"""
SoilGrids 2.0 soil organic carbon stock (0-30 cm and 0-100 cm) on the ELM
SEUS 1/24 deg (4 km) grid, for the Figure 1 SOC evaluation.

Two modes, both stdlib + numpy + rasterio + netCDF4 (all in the Pathfinder
`make_surfdata_pf` environment):

    fetch   <out_dir>   network only. Downloads the five ISRIC SoilGrids 2.0
                        "ocd" (organic carbon density, mean) layers through
                        the ISRIC WCS 1.0.0 service, one GeoTIFF each, into
                        <out_dir>/raw/, requested directly on the ELM grid:
                        box lon -95..-74, lat 24..37.5 (cell edges) as
                        504 x 324 pixels, i.e. pixel edges coincide with the
                        ELM cell edges. Writes <out_dir>/raw/provenance.json.
    process <out_dir>   arithmetic only (Slurm). Converts hg/m3 -> kg/m3,
                        multiplies by layer thickness and sums:
                        0-30 cm  = 0-5 + 5-15 + 15-30 cm
                        0-100 cm = the above + 30-60 + 60-100 cm
                        (layer boundaries coincide with the target depths, so
                        no partial layers). A cell is valid only where every
                        layer used is valid. Writes
                        <out_dir>/SOC_soilgrids_SEUS_1_24deg.nc.

Resampling caveat: the WCS server, not this script, decides how the 250 m
product is resampled to the 504 x 324 request; the method is not documented
by ISRIC for this service. This is the same route the 2025 poster script
(download_soilgrid.py) used, but with the request box and pixel counts set to
the ELM grid instead of a 25-40N, 100-74W box. It is a point/resampled
estimate, not an area-weighted aggregate of the 250 m pixels.

SoilGrids OCD already accounts for coarse fragments. Units: the service
stores hg/m3 (= 0.1 kg/m3); stocks are kg C m-2.
"""
import datetime
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import netCDF4
import numpy as np
import rasterio

WCS = "https://maps.isric.org/mapserv?map=/map/ocd.map"
# (coverage id, top m, bottom m)
LAYERS = [("ocd_0-5cm_mean", 0.00, 0.05), ("ocd_5-15cm_mean", 0.05, 0.15),
          ("ocd_15-30cm_mean", 0.15, 0.30), ("ocd_30-60cm_mean", 0.30, 0.60),
          ("ocd_60-100cm_mean", 0.60, 1.00)]
WEST, SOUTH, EAST, NORTH = -95.0, 24.0, -74.0, 37.5
NX, NY = 504, 324
HG_M3_TO_KG_M3 = 0.1
NODATA = -32768


def wcs_url(coverage):
    q = {"SERVICE": "WCS", "VERSION": "1.0.0", "REQUEST": "GetCoverage", "COVERAGE": coverage,
         "CRS": "urn:ogc:def:crs:EPSG::4326", "BBOX": f"{WEST},{SOUTH},{EAST},{NORTH}",
         "WIDTH": str(NX), "HEIGHT": str(NY), "FORMAT": "GEOTIFF_INT16"}
    return WCS + "&" + urllib.parse.urlencode(q, safe=":,")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def check_grid(path):
    with rasterio.open(path) as r:
        assert (r.height, r.width) == (NY, NX), (path, r.shape)
        b = r.bounds
        assert np.allclose([b.left, b.bottom, b.right, b.top], [WEST, SOUTH, EAST, NORTH], atol=1e-6), b
        assert r.crs.to_epsg() == 4326, r.crs
        assert r.dtypes[0] == "int16" and r.nodata == NODATA, (r.dtypes, r.nodata)


def fetch(out_dir):
    raw = os.path.join(out_dir, "raw")
    os.makedirs(raw, exist_ok=True)
    prov = {"service": WCS, "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "request": {"BBOX": [WEST, SOUTH, EAST, NORTH], "WIDTH": NX, "HEIGHT": NY, "FORMAT": "GEOTIFF_INT16"},
            "layers": {}}
    for cov, _, _ in LAYERS:
        dst = os.path.join(raw, f"{cov}.tif")
        assert not os.path.exists(dst), f"{dst} exists; refusing to overwrite"
        url = wcs_url(cov)
        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(url, timeout=300) as resp:
                    ctype, body = resp.headers.get("Content-Type", ""), resp.read()
                assert ctype == "image/tiff", f"{cov}: Content-Type {ctype}: {body[:300]!r}"
                break
            except Exception as exc:  # network hiccup: retry, then fail loudly
                print(f"{cov}: attempt {attempt} failed: {exc}", flush=True)
                if attempt == 3:
                    raise
                time.sleep(10 * attempt)
        part = dst + ".part"
        with open(part, "wb") as fh:
            fh.write(body)
        check_grid(part)
        os.rename(part, dst)
        prov["layers"][cov] = {"url": url, "bytes": len(body), "md5": md5(dst)}
        print(f"{cov}: {len(body)} bytes md5 {prov['layers'][cov]['md5']}", flush=True)
    with open(os.path.join(raw, "provenance.json"), "w") as fh:
        json.dump(prov, fh, indent=2)


def layer_kg_m2(raw, cov, top, bot):
    path = os.path.join(raw, f"{cov}.tif")
    check_grid(path)
    with rasterio.open(path) as r:
        a = r.read(1)
    ok = a != NODATA
    return np.where(ok, a.astype("f8") * HG_M3_TO_KG_M3 * (bot - top), np.nan)[::-1, :]  # lat ascending


def process(out_dir):
    raw = os.path.join(out_dir, "raw")
    stocks = [layer_kg_m2(raw, *lay) for lay in LAYERS]
    soc30 = stocks[0] + stocks[1] + stocks[2]
    soc100 = soc30 + stocks[3] + stocks[4]
    lat = SOUTH + (np.arange(NY) + 0.5) * (NORTH - SOUTH) / NY
    lon = WEST + (np.arange(NX) + 0.5) * (EAST - WEST) / NX
    w = np.broadcast_to(np.cos(np.deg2rad(lat))[:, None], soc30.shape)  # equal-dlon cells: area ~ cos(lat)
    for name, f in [("soc_0_30cm", soc30), ("soc_0_100cm", soc100)]:
        ok = np.isfinite(f)
        print(f"{name}: valid cells {ok.sum()} / {f.size}; area-weighted mean over valid cells "
              f"{np.average(f[ok], weights=w[ok]):.2f} kg C m-2 (min {f[ok].min():.2f}, max {f[ok].max():.2f})")
    print("cells valid in 0-30 but not in 0-100:", int((np.isfinite(soc30) & ~np.isfinite(soc100)).sum()))

    out = os.path.join(out_dir, "SOC_soilgrids_SEUS_1_24deg.nc")
    assert not os.path.exists(out), f"{out} exists; refusing to overwrite"
    with netCDF4.Dataset(out + ".part", "w") as ds:
        ds.createDimension("lat", NY)
        ds.createDimension("lon", NX)
        for nm, vals in [("lat", lat), ("lon", lon)]:
            v = ds.createVariable(nm, "f8", (nm,))
            v[:] = vals
            v.units = "degrees_north" if nm == "lat" else "degrees_east"
        for nm, f, ln in [("soc_0_30cm", soc30, "SoilGrids 2.0 organic carbon stock, 0-30 cm"),
                          ("soc_0_100cm", soc100, "SoilGrids 2.0 organic carbon stock, 0-100 cm")]:
            v = ds.createVariable(nm, "f4", ("lat", "lon"), zlib=True, fill_value=np.float32(-9999.0))
            v[:] = np.where(np.isfinite(f), f, -9999.0).astype("f4")
            v.units, v.long_name = "kg C m-2", ln
        ds.title = "SoilGrids 2.0 SOC stock on the ELM SEUS 1/24 deg grid"
        ds.source = ("ISRIC SoilGrids 2.0 ocd (mean) layers 0-5, 5-15, 15-30, 30-60, 60-100 cm via WCS 1.0.0, "
                     "requested on the ELM grid (box -95..-74E, 24..37.5N, 504x324, server-side resampling)")
        ds.method = ("kg C m-2 = sum over layers of ocd[hg/m3] x 0.1 x thickness[m]; a cell is valid only where "
                     "all layers used are valid; lat ascending, cell centres at the ELM grid centres")
        ds.history = "made by obs_soc_soilgrids_wcs_4km.py process, " + datetime.datetime.now().strftime("%Y-%m-%d")
    os.rename(out + ".part", out)
    print(f"wrote {out} md5 {md5(out)}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("fetch", "process"):
        sys.exit(__doc__)
    {"fetch": fetch, "process": process}[sys.argv[1]](sys.argv[2])
