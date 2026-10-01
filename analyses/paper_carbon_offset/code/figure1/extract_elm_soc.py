"""
Extract ELM soil organic carbon, 0-30 cm and 0-100 cm, for the Figure 1 SOC
evaluation, from the monthly h0 files of one run (4 km or 0.5 deg).

    SOC_0_30   = sum_k overlap_k(0, 0.30 m) x (SOIL1C_vr+SOIL2C_vr+SOIL3C_vr+SOIL4C_vr)_k
    SOC_0_100  = TOTSOMC_1m   (ELM's own 1 m integral; decided 2026-10-01)

SOIL1-4C_vr are the four SOM pools in gC/m3 on the `levdcmp` layers; the
overlap_k are the metres of layer k above 0.30 m, from DZSOI. ELM writes
DZSOI only to the run's first h0 file (named in the global attribute
Time_constant_3Dvars_filename), so it is read from there; the 15-layer column
must be spatially uniform (asserted). Layer 6 straddles 0.30 m, so 0-30 cm
assumes uniform carbon density inside that layer, exactly like the poster's
extract_biomass_soc.py.

TOTSOMC_1m (ColumnDataType.F90, CNSummary): soil-pool carbon only (litter
`TOTLITC_1m` and CWD are separate), layers fully above 1 m counted whole, the
layer straddling 1 m counted by the share of its thickness above 1 m. The
same overlap integral of SOIL1-4C_vr to 1.00 m is computed here as a CHECK
(`soc_0_100_check`) and the maximum difference is printed; it is not used.

Each year is a day-weighted annual mean of the 12 monthly records
(time_bounds). h0 files are named by their first record's stamp
(h0.2000-02-01 holds Jan-Dec 2000); the bounds are checked to span the year.
Ocean/inactive cells are masked where TOTSOMC_1m is missing.

Output: compressed .npz, kg C m-2, dims (year, lat, lon), plus the year mean.
Must run through Slurm:
    sbatch --export=NONE -J elm_soc code/submit_py.sbatch \
        code/figure1/extract_elm_soc.py <case> <out.npz> [year ...]
Default years 2000-2023.
"""
import glob
import os
import resource
import sys

import netCDF4
import numpy as np

CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"
DEFAULT_YEARS = list(range(2000, 2024))
POOLS = ["SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr"]
GC_TO_KGC = 1.0e-3


def h0_file(run_dir, case, year):
    files = sorted(glob.glob(os.path.join(run_dir, f"{case}.elm.h0.{year:04d}-*.nc")))
    assert len(files) == 1, f"expected one h0 file for {year}, found {files}"
    return files[0]


def layer_overlap(dz, depth):
    """Metres of each layer above `depth` (m); dz = layer thicknesses (m)."""
    bottom = np.cumsum(dz)
    return np.clip(np.minimum(bottom, depth) - (bottom - dz), 0.0, None)


def read_dzsoi(run_dir, first_file):
    with netCDF4.Dataset(first_file) as ds:
        name = ds.getncattr("Time_constant_3Dvars_filename")
    path = os.path.normpath(os.path.join(run_dir, name))
    with netCDF4.Dataset(path) as ds:
        dz = np.ma.filled(ds["DZSOI"][:].astype("f8"), np.nan)  # (levgrnd, lat, lon), land only valid
    flat = dz.reshape(dz.shape[0], -1)
    valid = np.isfinite(flat).all(axis=0)
    assert valid.any(), "no valid DZSOI column"
    prof = flat[:, valid]
    assert np.allclose(prof, prof[:, :1], rtol=1e-6, atol=1e-9), "DZSOI is not spatially uniform"
    return prof[:, 0], path


def day_weights(tb):
    w = (tb[:, 1] - tb[:, 0]).astype("f8")
    return w / w.sum()


def main():
    case, out_npz = sys.argv[1], sys.argv[2]
    years = [int(y) for y in sys.argv[3:]] or DEFAULT_YEARS
    assert out_npz.endswith(".npz")
    assert not os.path.exists(out_npz), f"{out_npz} exists; refusing to overwrite"
    run_dir = os.path.join(CASE_ROOT, case, "run")

    dz, dz_path = read_dzsoi(run_dir, h0_file(run_dir, case, years[0]))
    w30, w100 = layer_overlap(dz, 0.30), layer_overlap(dz, 1.00)
    assert abs(w30.sum() - 0.30) < 1e-9 and abs(w100.sum() - 1.00) < 1e-9
    print(f"DZSOI from {dz_path}\n  dz (m): {np.round(dz[:9], 4).tolist()} ...\n"
          f"  0-30 cm weights (m): {np.round(w30[:8], 4).tolist()}  sum {w30.sum():.4f}\n"
          f"  0-100 cm weights (m): {np.round(w100[:9], 4).tolist()}  sum {w100.sum():.4f}", flush=True)

    soc30, soc100, soc100_chk = [], [], []
    lat = lon = landfrac = area = None
    for year in years:
        f = h0_file(run_dir, case, year)
        with netCDF4.Dataset(f) as ds:
            if lat is None:
                lat, lon = ds["lat"][:].filled(np.nan), ds["lon"][:].filled(np.nan)
                landfrac, area = ds["landfrac"][:].filled(np.nan), ds["area"][:].filled(np.nan)
                assert ds["SOIL1C_vr"].units.strip() == "gC/m^3", ds["SOIL1C_vr"].units
                assert ds["TOTSOMC_1m"].units.strip() == "gC/m^2", ds["TOTSOMC_1m"].units
                assert ds["SOIL1C_vr"].shape[1] == dz.size
            tb = np.ma.filled(ds["time_bounds"][:], np.nan)
            y0 = int(ds["time"].units.split("since")[1].strip()[:4])
            assert (tb[0, 0], tb[-1, 1]) == (365 * (year - y0), 365 * (year - y0 + 1)), \
                f"{os.path.basename(f)} time_bounds {tb[0, 0]}-{tb[-1, 1]} do not span {year}"
            w = day_weights(tb)
            tot = None
            for v in POOLS:
                a = np.ma.filled(ds[v][:].astype("f4"), np.nan)  # (time, lev, lat, lon)
                tot = a if tot is None else tot + a
                del a
            one_m = np.ma.filled(ds["TOTSOMC_1m"][:].astype("f8"), np.nan)  # (time, lat, lon)
        s30 = np.tensordot(w30, tot, axes=(0, 1))     # (time, lat, lon), gC/m2
        s100c = np.tensordot(w100, tot, axes=(0, 1))
        del tot
        soc30.append((np.tensordot(w, s30, axes=(0, 0)) * GC_TO_KGC).astype("f4"))
        soc100.append((np.tensordot(w, one_m, axes=(0, 0)) * GC_TO_KGC).astype("f4"))
        soc100_chk.append((np.tensordot(w, s100c, axes=(0, 0)) * GC_TO_KGC).astype("f4"))
        ok = np.isfinite(soc100[-1])
        d = np.abs(soc100[-1] - soc100_chk[-1])[ok]
        wgt = (area * landfrac)[ok]
        print(f"{year}: {os.path.basename(f)} land cells {int(ok.sum())}  "
              f"SOC0-30 mean {np.average(soc30[-1][ok], weights=wgt):.2f}  "
              f"SOC0-100 mean {np.average(soc100[-1][ok], weights=wgt):.2f} kg C m-2 (area x landfrac)  "
              f"max|TOTSOMC_1m - own 1 m integral| {d.max():.4f}  "
              f"peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.1f} GB", flush=True)

    soc30, soc100, soc100_chk = (np.stack(x) for x in (soc30, soc100, soc100_chk))
    mask = np.isfinite(soc100)
    soc30 = np.where(mask, soc30, np.nan).astype("f4")
    soc100_chk = np.where(mask, soc100_chk, np.nan).astype("f4")
    meta = {
        "units": "kg C m-2 per gridcell land area (soc_*); landfrac: 1; area: km^2",
        "definition": ("soc_0_30: sum of SOIL1C_vr..SOIL4C_vr x overlap with 0-0.30 m (DZSOI), annual day-weighted mean; "
                       "soc_0_100: TOTSOMC_1m annual day-weighted mean; soc_0_100_check: the same overlap integral of "
                       "SOIL1-4C_vr to 1.00 m (check only). Litter and CWD excluded. Masked where TOTSOMC_1m is missing."),
        "case": case, "run_dir": run_dir, "dzsoi_file": dz_path,
        "dz_m": ",".join(f"{x:.6f}" for x in dz),
    }
    tmp = out_npz + ".part"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, year=np.array(years, "i4"), lat=lat, lon=lon, landfrac=landfrac, area=area,
                            soc_0_30=soc30, soc_0_100=soc100, soc_0_100_check=soc100_chk,
                            soc_0_30_mean=np.nanmean(soc30, axis=0).astype("f4"),
                            soc_0_100_mean=np.nanmean(soc100, axis=0).astype("f4"),
                            **{k: np.array(v) for k, v in meta.items()})
    os.rename(tmp, out_npz)
    print(f"wrote {out_npz} ({os.path.getsize(out_npz) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
