"""
Where do the square GPP patches in south Florida come from?

The 4 km SSP5-8.5 DF GPP maps (both crit_dayl_stress = 36000 and 38000 s) show
straight-edged rectangular patches in south Florida, e.g. east of Lake
Okeechobee. They are identical in the 36000 s and 38000 s runs, so they are
not the phenology threshold. This script compares GPP with every candidate
input over south Florida and measures, for each field, whether its sharp
edges sit on a coarse grid.

Grid facts used: the 4 km grid is 1/24 deg with cell EDGES on round numbers
(lon -95 + k/24, lat 24 + k/24; see memory seus_4km_grid_and_boundary). So a
0.5 deg source grid puts an edge every 12 cells, 0.25 deg every 6, 0.125 deg
every 3.

Metric per field (on the south-Florida box, land cells only):
  ratio_S = mean |difference between neighbouring cells| across edges that lie
            on the S-deg grid (and not on a coarser listed grid)
            / the same mean across edges on none of the listed grids.
  ~1 means no preference for that grid; >> 1 means blocks of that size.
  edge_corr = correlation between the field's |neighbour difference| and
            GPP's, over all interior edges: high = its edges are GPP's edges.

Fields:
  model output (h0, 2091-2100 mean): GPP, TLAI, FPG, FPG_P, BTRAN, and the
    forcing / deposition the model actually used: TBOT, RAIN, FSDS, FLDS,
    QBOT, WIND, NDEP_TO_SMINN, PDEP_TO_SMINP
  land use (DF file, year 2100): tree, grass, C4-share, crop fractions
  surface data: APATITE_P, LABILE_P, OCCLUDED_P, SECONDARY_P, PCT_SAND,
    PCT_CLAY, ORGANIC (top layer), SOIL_ORDER, SOIL_COLOR, FMAX
Runs: oldDF (36000 s) for everything; GPP also for newDF and old Default.

Run through Slurm:  sbatch -J sfl_blocks submit_py.sbatch diagnose_sfl_blocks.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

from analyze_4km_cds38000 import (OUTDIR, PERIODS, LATE, JAN, _read, case_name,
                                  h0_climatology, load_grid)

SSP = "ssp585"
BOX_LAT = (24.9, 28.8)
BOX_LON = (-82.9, -79.9)
LANDUSE = ("/projects/hpcl-cli185/proj-shared/zw5/ELM_Futu_landuseInput/outputs/processed/"
           "harvest_scenarios/landuse.timeseries_SEUS_1_24deg_nlcd2elm_SSP5_RCP85_DF_simyr2024-2100.nc")
FSURDAT = ("/projects/hpcl-cli185/proj-shared/zw5/20260910_seus_rerun_inputs/"
           "surfdata_UpdatedsoilP_SEUS_1_24deg_simyr1850_c260712.nc")
H0_VARS = ["TLAI", "FPG", "FPG_P", "BTRAN", "TBOT", "RAIN", "FSDS", "FLDS", "QBOT", "WIND",
           "NDEP_TO_SMINN", "PDEP_TO_SMINP"]
SURF_2D = ["APATITE_P", "LABILE_P", "OCCLUDED_P", "SECONDARY_P", "SOIL_ORDER", "SOIL_COLOR", "FMAX"]
SURF_3D = ["PCT_SAND", "PCT_CLAY", "ORGANIC"]          # top soil layer
GRIDS = [(1.0, 24), (0.5, 12), (0.25, 6), (0.125, 3)]  # (deg, cells between edges)


def edge_stats(fld, land, ref=None):
    """ratio per grid spacing (lon and lat edges pooled) and correlation of
    |neighbour difference| with the reference field's."""
    dx = np.abs(np.diff(fld, axis=1)); okx = land[:, 1:] & land[:, :-1] & np.isfinite(dx)
    dy = np.abs(np.diff(fld, axis=0)); oky = land[1:, :] & land[:-1, :] & np.isfinite(dy)
    # global edge index of the edge between column i and i+1 is i+1 (edges at -95 + k/24)
    kx = np.broadcast_to(np.arange(1, fld.shape[1]) + COL0, dx.shape)
    ky = np.broadcast_to((np.arange(1, fld.shape[0]) + ROW0)[:, None], dy.shape)
    d = np.concatenate([dx[okx], dy[oky]])
    k = np.concatenate([kx[okx], ky[oky]])
    level = np.full(k.shape, -1)
    for n, (_, step) in enumerate(GRIDS):          # coarsest first
        level[(level == -1) & (k % step == 0)] = n
    off = d[level == -1].mean()
    ratios = {deg: (d[level == n].mean() / off if off > 0 and (level == n).any() else np.nan)
              for n, (deg, _) in enumerate(GRIDS)}
    corr = np.nan
    if ref is not None:
        rx = np.abs(np.diff(ref, axis=1)); ry = np.abs(np.diff(ref, axis=0))
        both_x = okx & np.isfinite(rx); both_y = oky & np.isfinite(ry)
        a = np.concatenate([dx[both_x], dy[both_y]]); b = np.concatenate([rx[both_x], ry[both_y]])
        if a.std() > 0 and b.std() > 0:
            corr = float(np.corrcoef(a, b)[0, 1])
    return ratios, corr


def check_coords(ds, lat, lon, path):
    """Input grids must be the model grid in the same orientation (a
    south-north flip would put patterns in the wrong place)."""
    la = _read(ds, "LATIXY")[:, 0]
    lo = _read(ds, "LONGXY")[0, :]
    lo = np.where(lo > 180, lo - 360, lo)
    if not (np.allclose(la, lat, atol=1e-4) and np.allclose(lo, lon, atol=1e-4)):
        raise RuntimeError(f"{path}: LATIXY/LONGXY do not match the model lat/lon")


def main():
    global COL0, ROW0
    os.makedirs(OUTDIR, exist_ok=True)
    lat, lon, W = load_grid(SSP)
    jj = np.where((lat >= BOX_LAT[0]) & (lat <= BOX_LAT[1]))[0]
    ii = np.where((lon >= BOX_LON[0]) & (lon <= BOX_LON[1]))[0]
    ROW0, COL0 = jj[0], ii[0]
    sub = (slice(jj[0], jj[-1] + 1), slice(ii[0], ii[-1] + 1))
    land = (W > 0)[sub]
    slat, slon = lat[jj], lon[ii]
    # sanity: the grid edges really are on round numbers
    assert abs((lon[0] - 1 / 48) - (-95.0)) < 1e-6 and abs((lat[0] - 1 / 48) - 24.0) < 1e-6

    fields = {}
    old = case_name("oldDF", SSP)
    print(f"reading {old}", flush=True)
    ann, mon = h0_climatology(old, "GPP", PERIODS[LATE])
    fields["GPP oldDF (annual)"] = ann[sub]
    fields["GPP oldDF (Jan)"] = mon[JAN][sub]
    for v in H0_VARS:
        a, _ = h0_climatology(old, v, PERIODS[LATE])
        fields[f"{v} oldDF"] = a[sub]
    for run in ("newDF", "Default"):
        a, _ = h0_climatology(case_name(run, SSP), "GPP", PERIODS[LATE])
        fields[f"GPP {run} (annual)"] = a[sub]

    with Dataset(LANDUSE) as ds:
        check_coords(ds, lat, lon, LANDUSE)
        yrs = np.asarray(ds.variables["YEAR"][:]).astype(int) if "YEAR" in ds.variables else None
        t = int(np.where(yrs == 2100)[0][0]) if yrs is not None else -1
        p = _read(ds, "PCT_NAT_PFT")[t]                 # (natpft, lat, lon), % of natveg
        tree = p[1:9].sum(0); grass = p[12:15].sum(0)
        with np.errstate(invalid="ignore", divide="ignore"):
            c4 = np.where(grass > 0, p[14] / grass, np.nan)
        fields["LU2100 tree %"] = tree[sub]
        fields["LU2100 grass %"] = grass[sub]
        fields["LU2100 C4 share of grass"] = c4[sub]
        for v in ("PCT_CROP", "PCT_NATVEG"):
            if v in ds.variables:
                x = _read(ds, v)
                fields[f"LU {v}"] = (x[t] if x.ndim == 3 else x)[sub]
    with Dataset(FSURDAT) as ds:
        check_coords(ds, lat, lon, FSURDAT)
        for v in SURF_2D:
            fields[f"surf {v}"] = _read(ds, v)[sub]
        for v in SURF_3D:
            fields[f"surf {v} (top)"] = _read(ds, v)[0][sub]

    ref = fields["GPP oldDF (annual)"]
    lines = [f"South Florida box {BOX_LAT[0]}-{BOX_LAT[1]}N, {BOX_LON[0]}-{BOX_LON[1]}E, "
             f"{land.sum()} land cells; output fields = {LATE} mean",
             "ratio_S = mean |neighbour diff| on S-deg grid edges / on off-grid edges  (~1 = no blocks)",
             "edge_corr = corr of |neighbour diff| with that of annual GPP (oldDF)", "",
             f"{'field':34s}" + "".join(f"{'r_' + str(g):>9s}" for g, _ in GRIDS) + f"{'edge_corr':>11s}"]
    rows = []
    for name, fld in fields.items():
        fld = np.where(land, fld, np.nan)
        fields[name] = fld
        ratios, corr = edge_stats(fld, land, ref)
        rows.append((name, ratios, corr))
        lines.append(f"{name:34s}" + "".join(f"{ratios[g]:9.2f}" for g, _ in GRIDS) + f"{corr:11.2f}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(OUTDIR, "sfl_blocks_summary.txt"), "w") as f:
        f.write(txt + "\n")

    # panel figure, no overlays
    names = list(fields)
    ncol = 6
    nrow = int(np.ceil(len(names) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 4.6 * nrow))
    for ax, name in zip(axes.flat, names):
        fld = fields[name]
        lo, hi = np.nanpercentile(fld, [1, 99])
        pc = ax.pcolormesh(slon, slat, fld, cmap="viridis", vmin=lo, vmax=hi, shading="auto")
        ax.set_aspect("equal")
        ax.set_title(name, fontsize=9)
        ax.tick_params(labelsize=7)
        fig.colorbar(pc, ax=ax, shrink=0.7).ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(names):]:
        ax.axis("off")
    fig.suptitle(f"South Florida, 4 km {SSP}: GPP and candidate inputs ({LATE} mean for model fields; "
                 "land use year 2100; no overlays)", fontsize=13)
    fig.tight_layout()
    out = os.path.join(OUTDIR, "sfl_blocks_panels.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
