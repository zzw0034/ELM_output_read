"""
HWSD v1.2 soil organic carbon stock (0-30 cm and 0-100 cm) remapped onto the
ELM SEUS 1/24 deg (4 km) grid, for the Figure 1 SOC evaluation.

Source: the NCAR/ORNL DAAC regridded HWSD v1.2 (Wieder et al., ORNL DAAC
dataset 1247), 3 arc-minute (0.05 deg) global grid:
    AWT_T_SOC.nc4  SUM_t_c_12  topsoil 0-30 cm,   kg C m-2
    AWT_S_SOC.nc4  SUM_s_c_1   subsoil 30-100 cm, kg C m-2
Missing = -1 (ocean, water, rock, ice ...). 0-100 cm = topsoil + subsoil.

THE SOURCE IS COARSER THAN THE TARGET: 0.05 deg (3') > 1/24 deg (2.5'). This
script therefore *remaps* (each 4 km cell takes the exact area-overlap
weighted mean of the 0.05 deg cells it touches); it cannot add detail, and
neighbouring 4 km cells inherit nearly the same value. Do not read 4 km
structure in the HWSD panel as information.

Method: exact spherical-cell overlap weights (longitude overlap x difference
of sin(latitude) overlap), valid source cells only, so missing cells do not
pull the mean toward zero. 0-30 cm uses the topsoil validity alone; 0-100 cm
uses cells valid in BOTH layers (the old process_HWSD_1247.py added the two
files without masking the -1 fill, which would silently subtract 1 kg C m-2
wherever one layer is missing). Also saves the valid share of each target
cell.

Arithmetic only, tiny: run through Slurm.
    python obs_soc_hwsd_v12_4km.py <raw_dir> <out_dir>
raw_dir holds AWT_T_SOC.nc4 and AWT_S_SOC.nc4; writes
<out_dir>/SOC_hwsd_SEUS_1_24deg.nc.
"""
import datetime
import hashlib
import os
import sys

import netCDF4
import numpy as np

WEST, SOUTH, EAST, NORTH = -95.0, 24.0, -74.0, 37.5
NX, NY = 504, 324
SRC_FILES = {"T": ("AWT_T_SOC.nc4", "SUM_t_c_12"), "S": ("AWT_S_SOC.nc4", "SUM_s_c_1")}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def edges(c):
    d = np.diff(c).mean()
    return np.concatenate([c - d / 2, [c[-1] + d / 2]])


def overlap(coarse_edges, fine_edges):
    """Overlap length of each fine interval (columns) with each coarse
    interval (rows), ascending edges."""
    lo = np.maximum(coarse_edges[:-1, None], fine_edges[None, :-1])
    hi = np.minimum(coarse_edges[1:, None], fine_edges[None, 1:])
    return np.clip(hi - lo, 0.0, None)


def load_window(raw_dir):
    """Both layers on the SEUS window (with a 0.2 deg margin), -1 -> NaN."""
    out = {}
    lat = lon = None
    for key, (fn, var) in SRC_FILES.items():
        with netCDF4.Dataset(os.path.join(raw_dir, fn)) as ds:
            la = np.ma.filled(ds["lat"][:], np.nan).astype("f8")
            lo = np.ma.filled(ds["lon"][:], np.nan).astype("f8")
            assert np.all(np.diff(la) > 0) and np.all(np.diff(lo) > 0)
            assert ds[var].units.strip() == "kg C m-2", ds[var].units
            iy = np.where((la >= SOUTH - 0.2) & (la <= NORTH + 0.2))[0]
            ix = np.where((lo >= WEST - 0.2) & (lo <= EAST + 0.2))[0]
            a = np.ma.filled(ds[var][iy[0]:iy[-1] + 1, ix[0]:ix[-1] + 1].astype("f8"), np.nan)
        a = np.where(a < 0, np.nan, a)
        out[key] = a
        if lat is None:
            lat, lon = la[iy], lo[ix]
        else:
            assert np.array_equal(lat, la[iy]) and np.array_equal(lon, lo[ix]), "T and S grids differ"
    return out["T"], out["S"], lat, lon


def remap(field, wy, wx):
    """Valid-only area-weighted mean on the target grid and the valid share."""
    ok = np.isfinite(field)
    num = wy @ np.where(ok, field, 0.0) @ wx.T
    den = wy @ ok.astype("f8") @ wx.T
    tot = wy @ np.ones_like(field) @ wx.T
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan), den / tot


def main(raw_dir, out_dir):
    top, sub, lat_s, lon_s = load_window(raw_dir)
    print(f"source window {top.shape} at {np.diff(lat_s).mean():.4f} deg; "
          f"valid T {np.isfinite(top).sum()}, valid S {np.isfinite(sub).sum()}, "
          f"valid T but not S {int((np.isfinite(top) & ~np.isfinite(sub)).sum())}")
    both = np.isfinite(top) & np.isfinite(sub)
    soc30_src = top
    soc100_src = np.where(both, top + sub, np.nan)

    lat_t = SOUTH + (np.arange(NY) + 0.5) * (NORTH - SOUTH) / NY
    lon_t = WEST + (np.arange(NX) + 0.5) * (EAST - WEST) / NX
    # Latitude weights: clip each source band to the target band, then take the
    # sin(lat) difference (exact spherical band area per unit longitude).
    ey_t, ey_s = np.deg2rad(edges(lat_t)), np.deg2rad(edges(lat_s))
    lo = np.maximum(ey_t[:-1, None], ey_s[None, :-1])
    hi = np.minimum(ey_t[1:, None], ey_s[None, 1:])
    wy = np.where(hi > lo, np.sin(hi) - np.sin(lo), 0.0)
    wx = overlap(edges(lon_t), edges(lon_s))

    soc30, share30 = remap(soc30_src, wy, wx)
    soc100, share100 = remap(soc100_src, wy, wx)
    area_w = np.broadcast_to(np.cos(np.deg2rad(lat_t))[:, None], soc30.shape)
    for nm, src, f, sh in [("soc_0_30cm", soc30_src, soc30, share30), ("soc_0_100cm", soc100_src, soc100, share100)]:
        ok = np.isfinite(f)
        # mass check: the area-weighted mean over the target cells and over the source cells inside the box
        src_in = np.isfinite(src) & (lat_s[:, None] > SOUTH) & (lat_s[:, None] < NORTH) \
            & (lon_s[None, :] > WEST) & (lon_s[None, :] < EAST)
        src_w = np.broadcast_to(np.cos(np.deg2rad(lat_s))[:, None], src.shape)
        print(f"{nm}: valid target cells {ok.sum()} / {f.size}; area-weighted mean {np.average(f[ok], weights=area_w[ok]):.2f} "
              f"kg C m-2 (source cells in box: {np.average(src[src_in], weights=src_w[src_in]):.2f}); "
              f"min {f[ok].min():.2f} max {f[ok].max():.2f}; valid share < 0.5 in {int((ok & (sh < 0.5)).sum())} cells")

    out = os.path.join(out_dir, "SOC_hwsd_SEUS_1_24deg.nc")
    os.makedirs(out_dir, exist_ok=True)
    assert not os.path.exists(out), f"{out} exists; refusing to overwrite"
    with netCDF4.Dataset(out + ".part", "w") as ds:
        ds.createDimension("lat", NY)
        ds.createDimension("lon", NX)
        for nm, vals in [("lat", lat_t), ("lon", lon_t)]:
            v = ds.createVariable(nm, "f8", (nm,))
            v[:] = vals
            v.units = "degrees_north" if nm == "lat" else "degrees_east"
        for nm, f, ln, u in [("soc_0_30cm", soc30, "HWSD v1.2 topsoil organic carbon stock, 0-30 cm", "kg C m-2"),
                             ("soc_0_100cm", soc100, "HWSD v1.2 organic carbon stock, 0-100 cm (topsoil + subsoil)", "kg C m-2"),
                             ("valid_share_0_30cm", share30, "share of the 4 km cell covered by valid source cells (0-30 cm)", "1"),
                             ("valid_share_0_100cm", share100, "share of the 4 km cell covered by source cells valid in both layers", "1")]:
            v = ds.createVariable(nm, "f4", ("lat", "lon"), zlib=True, fill_value=np.float32(-9999.0))
            v[:] = np.where(np.isfinite(f), f, -9999.0).astype("f4")
            v.units, v.long_name = u, ln
        ds.title = "HWSD v1.2 SOC stock remapped to the ELM SEUS 1/24 deg grid"
        ds.source = ("Regridded HWSD v1.2, 3 arc-minute (ORNL DAAC 1247): AWT_T_SOC.nc4 SUM_t_c_12 (0-30 cm), "
                     "AWT_S_SOC.nc4 SUM_s_c_1 (30-100 cm); source md5 "
                     + ", ".join(f"{fn} {md5(os.path.join(raw_dir, fn))}" for fn, _ in SRC_FILES.values()))
        ds.method = ("exact area-overlap weighted mean of valid 0.05 deg cells (-1 = missing excluded); the source is "
                     "COARSER than 1/24 deg, so this is a remap, not an aggregation; 0-100 cm only where both layers valid")
        ds.history = "made by obs_soc_hwsd_v12_4km.py, " + datetime.datetime.now().strftime("%Y-%m-%d")
    os.rename(out + ".part", out)
    print(f"wrote {out} md5 {md5(out)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
