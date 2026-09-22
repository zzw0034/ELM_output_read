"""
Did raising crit_dayl_stress 36000 s -> 38000 s remove the 30.833N GPP step
from the 0.5-deg DF runs, and what did it cost?

Background: ../../CRIT_DAYL_STRESS_ARTIFACT.md. With crit_dayl_stress = 36000 s
(10.0 h) every stress-deciduous PFT is force-dormant each winter north of
30.833N and never south of it. 38000 s (10.56 h) moves that latitude to 23.4N,
south of the whole domain, so every cell crosses the threshold each winter.

Only the four DF cases were rerun (2026-09-22). Default keeps 36000 s. The
old and new DF runs share executable, finidat, land use and forcing; the
paramfile is the ONLY difference (lnd_in diff = one line). Hence:

    (Default - newDF) - (Default - oldDF) = oldDF - newDF

i.e. the change in the DF "carbon benefit" caused by the parameter is exactly
oldDF - newDF, and it can be split by PFT from h1.

Crops are NOT an isolated control: create_crop_landunit = .false., so crop
PFT 15 shares the natural-vegetation soil column with the grass that DF adds.
Default - DF on crops is therefore not zero even with identical parameters;
use newDF - oldDF, not newDF - Default, to isolate the parameter.

Three questions, all for 4 SSPs:
  1. Row step 30.75 -> 31.25N in January / July GPP, gridcell (h0) and
     grass-only (h1): old DF vs new DF vs Default. Plus the full transect, to
     check no new step appeared elsewhere.
  2. newDF - oldDF domain-total GPP / NPP split by PFT type (h1), for an
     early decade and the last decade.
  3. Carbon benefit Default - DF (NBP annual, cumulative 2024-2100, and
     TOTECOSYSC at end of 2100), old vs new.

Output conventions:
  - Monthly h0/h1 files: file "<case>.elm.h?.YYYY-02-01-00000.nc" holds the
    12 months Jan..Dec of year YYYY (checked against mcdate below).
  - Fluxes are day-weighted with time_bounds before annual averaging
    (see memory: plain 12-record means bias fluxes ~0.3% low).
  - Domain totals use area * landfrac (km^2). Grid-cell h0 fluxes are ELM's
    p2g averages over the vegetated PFTs, so an h0-based total can differ from
    the exact h1 sum (sum_p v * wtgcell * area * landfrac); the ratio is
    printed as a check and only differences between runs are interpreted.

Run through Slurm only (submit_py.sbatch), never on the login node.
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

WORKDIR = ("/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/"
           "20260910_seus_rerun/20260922_seus_halfdeg_DF_cds38000")
OUTDIR = os.path.join(WORKDIR, "outputs")
CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"

SSPS = ["ssp119", "ssp245", "ssp370", "ssp585"]
SSP_LABEL = {"ssp119": "SSP1-1.9", "ssp245": "SSP2-4.5",
             "ssp370": "SSP3-7.0", "ssp585": "SSP5-8.5"}
RUNS = ["Default", "oldDF", "newDF"]
RUN_STYLE = {
    "Default": dict(color="black", ls="-", label="Default (36000 s)"),
    "oldDF": dict(color="tab:red", ls="--", label="DF, crit_dayl_stress 36000 s"),
    "newDF": dict(color="tab:blue", ls="-", label="DF, crit_dayl_stress 38000 s"),
}


def case_name(run, ssp):
    if run == "Default":
        return f"20260911_seus_halfdeg_future_{ssp}_dt3600"
    if run == "oldDF":
        # ssp370 DF was built with the 2026-09-11 batch, the others on 09-15
        date = "20260911" if ssp == "ssp370" else "20260915"
        return f"{date}_seus_halfdeg_future_{ssp}_DF_dt3600"
    if run == "newDF":
        return f"20260922_seus_halfdeg_future_{ssp}_DF_cds38000_dt3600"
    raise ValueError(run)


YEARS_ALL = list(range(2024, 2101))
PERIODS = {"2024-2033": list(range(2024, 2034)),
           "2091-2100": list(range(2091, 2101))}
LATE = "2091-2100"

THRESHOLD_LAT_OLD = 30.833   # solstice daylength = 36000 s
LAT_SOUTH, LAT_NORTH = 30.75, 31.25   # 0.5-deg rows bracketing it
JAN, JUL = 0, 6

SEC_PER_YEAR = 365 * 86400.0
FLUX_UNITS = "gC/m^2/s"

# stress_decid = 1 in clm_params_SEUS_c260712.nc (checked 2026-09-22)
STRESS_DECID = {6, 10, 13, 14, 15, 16}
GRASS = [13, 14]   # C3 / C4 grass; 12 (arctic C3) is season-deciduous
PFT_NAMES = {
    0: "bare", 1: "NET_temp", 2: "NET_boreal", 3: "NDT_boreal", 4: "BET_trop",
    5: "BET_temp", 6: "BDT_trop", 7: "BDT_temp", 8: "BDT_boreal",
    9: "BES_temp", 10: "BDS_temp", 11: "BDS_boreal",
    12: "C3_arctic_grass", 13: "C3_grass", 14: "C4_grass",
    15: "crop", 16: "crop_irr",
}
VEG_LUNITS = (1, 2)   # istsoil, istcrop


# ---------------------------------------------------------------- file access

def hist_file(case, tape, year):
    return os.path.join(CASE_ROOT, case, "run",
                        f"{case}.elm.{tape}.{year}-02-01-00000.nc")


def _read(ds, var):
    v = ds.variables[var][:]
    return np.ma.filled(v.astype(float), np.nan) if np.ma.isMaskedArray(v) else np.asarray(v, float)


def _check_year(ds, year, path):
    mcdate = np.asarray(ds.variables["mcdate"][:]).astype(int)
    expected = [year * 10000 + m * 100 + 1 for m in range(2, 13)] + [(year + 1) * 10000 + 101]
    if list(mcdate) != expected:
        raise RuntimeError(f"{path}: mcdate {list(mcdate)} is not Jan..Dec {year}")


def _month_weights(ds):
    tb = _read(ds, "time_bounds")
    dt = tb[:, 1] - tb[:, 0]
    if len(dt) != 12:
        raise RuntimeError(f"expected 12 monthly records, got {len(dt)}")
    return dt / dt.sum()


def _is_flux(ds, var):
    return ds.variables[var].getncattr("units").strip() == FLUX_UNITS


def load_grid():
    ds = Dataset(hist_file(case_name("Default", "ssp585"), "h0", 2100))
    lat = _read(ds, "lat")
    lon = _read(ds, "lon")
    area = _read(ds, "area")          # km^2
    landfrac = _read(ds, "landfrac")
    ds.close()
    w = area * landfrac
    w = np.where(np.isfinite(w) & (w > 0), w, 0.0)
    return lat, lon, w


# ---------------------------------------------------------------- h0 fields

def h0_climatology(case, var, years):
    """Return (annual, monthly[12]) multi-year means on the 2-D grid.
    Fluxes are converted to gC/m2/yr (monthly values = annualised rates)."""
    ann = []
    mon = []
    for y in years:
        path = hist_file(case, "h0", y)
        ds = Dataset(path)
        _check_year(ds, y, path)
        wt = _month_weights(ds)
        v = _read(ds, var)
        if _is_flux(ds, var):
            v = v * SEC_PER_YEAR
        ds.close()
        mon.append(v)
        ann.append(np.tensordot(wt, v, axes=(0, 0)))
    return np.nanmean(ann, axis=0), np.nanmean(mon, axis=0)


def h0_domain_series(case, var, weights, stock_month=None):
    """Annual domain total per year, PgC/yr for fluxes (day-weighted), PgC for
    stocks. For a stock, stock_month picks one monthly record (e.g. 11 = Dec)
    instead of the within-year mean."""
    out = []
    for y in YEARS_ALL:
        path = hist_file(case, "h0", y)
        ds = Dataset(path)
        _check_year(ds, y, path)
        v = _read(ds, var)
        if _is_flux(ds, var):
            field = np.tensordot(_month_weights(ds), v, axes=(0, 0)) * SEC_PER_YEAR
        elif stock_month is not None:
            field = v[stock_month]
        else:
            field = np.tensordot(_month_weights(ds), v, axes=(0, 0))
        ds.close()
        m = np.isfinite(field) & (weights > 0)
        out.append(np.sum(field[m] * weights[m]) * 1e6 / 1e15)
    return np.array(out)


def row_means(field, weights):
    """Land-area-weighted mean of each latitude row."""
    out = np.full(field.shape[0], np.nan)
    for i in range(field.shape[0]):
        m = np.isfinite(field[i]) & (weights[i] > 0)
        if m.any():
            out[i] = np.sum(field[i][m] * weights[i][m]) / np.sum(weights[i][m])
    return out


# ---------------------------------------------------------------- h1 fields

def h1_pft_summary(case, years, weights, var, months=(JAN, JUL)):
    """From PFT-level h1 output, averaged over `years`:
      totals[itype]   domain total of `var` (PgC/yr), day-weighted annual
      grass_rows[m]   per-row grass-only (GRASS) mean of `var` in month m,
                      weighted by PFT area (gC/m2/yr annualised)
      grass_map[m]    same, per grid cell
    """
    nlat, nlon = weights.shape
    totals = {t: [] for t in PFT_NAMES}
    num = {m: np.zeros((nlat, nlon)) for m in months}
    den = {m: np.zeros((nlat, nlon)) for m in months}
    for y in years:
        path = hist_file(case, "h1", y)
        ds = Dataset(path)
        _check_year(ds, y, path)
        wt_m = _month_weights(ds)
        itype = np.asarray(ds.variables["pfts1d_itype_veg"][:]).astype(int)
        lunit = np.asarray(ds.variables["pfts1d_itype_lunit"][:]).astype(int)
        ixy = np.asarray(ds.variables["pfts1d_ixy"][:]).astype(int) - 1
        jxy = np.asarray(ds.variables["pfts1d_jxy"][:]).astype(int) - 1
        wtg = _read(ds, "pfts1d_wtgcell")
        v = _read(ds, var)
        flux = _is_flux(ds, var)
        ds.close()
        if flux:
            v = v * SEC_PER_YEAR
        # PFT area in km^2 = fraction of grid cell * grid-cell land area
        parea = np.where(np.isfinite(wtg), wtg, 0.0) * weights[jxy, ixy]
        veg = np.isin(lunit, VEG_LUNITS) & (parea > 0)
        ann = np.tensordot(wt_m, v, axes=(0, 0))
        for t in PFT_NAMES:
            sel = veg & (itype == t) & np.isfinite(ann)
            totals[t].append(np.sum(ann[sel] * parea[sel]) * 1e6 / 1e15)
        for m in months:
            sel = veg & np.isin(itype, GRASS) & np.isfinite(v[m])
            np.add.at(num[m], (jxy[sel], ixy[sel]), v[m][sel] * parea[sel])
            np.add.at(den[m], (jxy[sel], ixy[sel]), parea[sel])
    totals = {t: float(np.mean(totals[t])) for t in totals}
    grass_map, grass_rows = {}, {}
    for m in months:
        with np.errstate(invalid="ignore", divide="ignore"):
            grass_map[m] = np.where(den[m] > 0, num[m] / den[m], np.nan)
        rn, rd = num[m].sum(axis=1), den[m].sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            grass_rows[m] = np.where(rd > 0, rn / rd, np.nan)
    return totals, grass_rows, grass_map


# ---------------------------------------------------------------- main

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    report = []

    def say(s=""):
        print(s, flush=True)
        report.append(s)

    lat, lon, W = load_grid()
    i_s = int(np.argmin(np.abs(lat - LAT_SOUTH)))
    i_n = int(np.argmin(np.abs(lat - LAT_NORTH)))
    assert abs(lat[i_s] - LAT_SOUTH) < 1e-6 and abs(lat[i_n] - LAT_NORTH) < 1e-6
    say(f"grid {len(lat)} x {len(lon)}; threshold rows {lat[i_s]} (i={i_s}) -> {lat[i_n]} (i={i_n})")
    say(f"domain land area (area*landfrac) = {W.sum():.0f} km^2")

    for r in RUNS:
        for s in SSPS:
            c = case_name(r, s)
            missing = [y for y in YEARS_ALL for t in ("h0", "h1")
                       if not os.path.exists(hist_file(c, t, y))]
            if missing:
                raise RuntimeError(f"{c}: {len(missing)} missing history files")
    say("all 12 cases x 77 years x h0/h1 present")

    # ---------------------------------------------------- 1. row step
    say("\n" + "=" * 78)
    say(f"1. ROW STEP {LAT_SOUTH}N -> {LAT_NORTH}N, GPP {LATE} mean (gC/m2/yr, monthly values annualised)")
    say("=" * 78)
    rows = {}        # (run, ssp, month) -> row-mean profile, h0 grid cell
    grass_rows = {}  # (run, ssp, month) -> row profile, grass PFTs only
    pft_tot = {}     # (run, ssp, period) -> {itype: PgC/yr}
    maps585 = {}
    step_csv = []
    for s in SSPS:
        for r in RUNS:
            c = case_name(r, s)
            ann, mon = h0_climatology(c, "GPP", PERIODS[LATE])
            rows[(r, s, JAN)] = row_means(mon[JAN], W)
            rows[(r, s, JUL)] = row_means(mon[JUL], W)
            rows[(r, s, "ann")] = row_means(ann, W)
            if s == "ssp585":
                maps585[(r, JAN)] = mon[JAN]
                maps585[(r, "ann")] = ann
            for per, yrs in PERIODS.items():
                tot, grows, _gmap = h1_pft_summary(c, yrs, W, "GPP")
                pft_tot[(r, s, per, "GPP")] = tot
                if per == LATE:
                    grass_rows[(r, s, JAN)] = grows[JAN]
                    grass_rows[(r, s, JUL)] = grows[JUL]
                ntot, _, _ = h1_pft_summary(c, yrs, W, "NPP", months=())
                pft_tot[(r, s, per, "NPP")] = ntot

        say(f"\n--- {SSP_LABEL[s]} ---")
        say(f"{'':34s}{'Jan south':>10s}{'Jan north':>10s}{'step':>9s}{'%':>7s}"
            f"{'Jul south':>11s}{'Jul north':>10s}{'step':>9s}{'%':>7s}")
        for label, src in (("grid cell", rows), ("grass PFTs 13/14 only", grass_rows)):
            for r in RUNS:
                vals = []
                for m in (JAN, JUL):
                    a, b = src[(r, s, m)][i_s], src[(r, s, m)][i_n]
                    vals += [a, b, b - a, 100 * (b - a) / a]
                    step_csv.append(dict(ssp=s, run=r, level=label,
                                         month="Jan" if m == JAN else "Jul",
                                         south=a, north=b, step=b - a,
                                         step_pct=100 * (b - a) / a))
                say(f"  {label:20s} {r:8s}    "
                    f"{vals[0]:10.0f}{vals[1]:10.0f}{vals[2]:+9.0f}{vals[3]:+7.1f}"
                    f" {vals[4]:10.0f}{vals[5]:10.0f}{vals[6]:+9.0f}{vals[7]:+7.1f}")

    # full January transect for the new DF: is there a new step anywhere?
    for s in SSPS:
        say(f"\n{SSP_LABEL[s]}: January grid-cell GPP transect, {LATE} "
            f"(d = change from the row to the south)")
        say(f"{'lat':>7s}{'old DF':>9s}{'d':>7s}{'new DF':>9s}{'d':>7s}{'Default':>9s}{'d':>7s}")
        for i in range(len(lat)):
            line = f"{lat[i]:7.2f}"
            for r in ("oldDF", "newDF", "Default"):
                prof = rows[(r, s, JAN)]
                d = f"{prof[i] - prof[i - 1]:+7.0f}" if i > 0 else f"{'':7s}"
                line += f"{prof[i]:9.0f}{d}"
            say(line + ("   <== old threshold" if i == i_n else ""))
    say("")
    for s in SSPS:
        for r in ("oldDF", "newDF"):
            prof = rows[(r, s, JAN)]
            d = np.diff(prof)
            k = int(np.nanargmin(d))
            say(f"  {SSP_LABEL[s]} {r}: largest adjacent-row DROP in Jan GPP is "
                f"{d[k]:+.0f} between {lat[k]:.2f} and {lat[k + 1]:.2f}N")

    # ---------------------------------------------------- 2. newDF - oldDF by PFT
    say("\n" + "=" * 78)
    say("2. newDF - oldDF DOMAIN TOTAL BY PFT (PgC/yr), from h1")
    say("   = the change in the DF carbon benefit caused by the parameter alone")
    say("=" * 78)
    for var in ("GPP", "NPP"):
        for per in PERIODS:
            say(f"\n{var}, {per} mean   (* = stress-deciduous)")
            say(f"{'PFT':>22s}" + "".join(f"{SSP_LABEL[s]:>22s}" for s in SSPS))
            say(f"{'':>22s}" + "".join(f"{'old':>8s}{'new-old':>9s}{'%':>5s}" for _ in SSPS))
            for t in PFT_NAMES:
                olds = [pft_tot[("oldDF", s, per, var)][t] for s in SSPS]
                news = [pft_tot[("newDF", s, per, var)][t] for s in SSPS]
                if max(abs(x) for x in olds + news) < 5e-5:
                    continue
                star = "*" if t in STRESS_DECID else " "
                line = f"{star}{t:2d} {PFT_NAMES[t]:>18s}"
                for o, n in zip(olds, news):
                    pct = 100 * (n - o) / o if abs(o) > 1e-9 else np.nan
                    line += f"{o:8.4f}{n - o:+9.4f}{pct:+5.0f}"
                say(line)
            for label, sel in (("stress-decid total", STRESS_DECID),
                               ("all PFTs", set(PFT_NAMES))):
                line = f"{label:>22s}"
                for s in SSPS:
                    o = sum(pft_tot[("oldDF", s, per, var)][t] for t in sel)
                    n = sum(pft_tot[("newDF", s, per, var)][t] for t in sel)
                    line += f"{o:8.4f}{n - o:+9.4f}{100 * (n - o) / o:+5.0f}"
                say(line)
    pft_csv = []
    for var in ("GPP", "NPP"):
        for per in PERIODS:
            for s in SSPS:
                for t in PFT_NAMES:
                    row = dict(var=var, period=per, ssp=s, itype=t, pft=PFT_NAMES[t],
                               stress_decid=int(t in STRESS_DECID))
                    for r in RUNS:
                        row[f"{r}_PgC_per_yr"] = pft_tot[(r, s, per, var)][t]
                    pft_csv.append(row)

    # ---------------------------------------------------- 3. carbon benefit
    say("\n" + "=" * 78)
    say("3. CARBON BENEFIT Default - DF (h0, area*landfrac)")
    say("=" * 78)
    series = {}
    for s in SSPS:
        for r in RUNS:
            c = case_name(r, s)
            series[(r, s, "NBP")] = h0_domain_series(c, "NBP", W)
            series[(r, s, "GPP")] = h0_domain_series(c, "GPP", W)
            series[(r, s, "TOTECOSYSC_dec")] = h0_domain_series(c, "TOTECOSYSC", W, stock_month=11)
    late = np.isin(YEARS_ALL, PERIODS[LATE])
    say(f"{'':10s}{'':8s}{'GPP ' + LATE:>14s}{'NBP ' + LATE:>14s}{'cum NBP':>12s}{'dTOTECOSYSC':>13s}")
    say(f"{'':10s}{'':8s}{'PgC/yr':>14s}{'PgC/yr':>14s}{'2024-2100 PgC':>14s}{'Dec2100 PgC':>11s}")
    ben_csv = []
    for s in SSPS:
        res = {}
        for r in ("oldDF", "newDF"):
            dg = series[("Default", s, "GPP")] - series[(r, s, "GPP")]
            dn = series[("Default", s, "NBP")] - series[(r, s, "NBP")]
            de = series[("Default", s, "TOTECOSYSC_dec")] - series[(r, s, "TOTECOSYSC_dec")]
            res[r] = (dg[late].mean(), dn[late].mean(), dn.sum(), de[-1])
            say(f"{SSP_LABEL[s]:10s}{r:8s}{res[r][0]:14.4f}{res[r][1]:14.4f}{res[r][2]:14.3f}{res[r][3]:11.3f}")
        chg = [100 * (res["newDF"][k] - res["oldDF"][k]) / res["oldDF"][k] for k in range(4)]
        say(f"{'':10s}{'change':8s}" + "".join(f"{c:+13.1f}%" for c in chg[:2])
            + f"{chg[2]:+13.1f}%{chg[3]:+10.1f}%")
        for r in ("oldDF", "newDF"):
            ben_csv.append(dict(ssp=s, df_run=r, dGPP_late=res[r][0], dNBP_late=res[r][1],
                                cumNBP_2024_2100=res[r][2], dTOTECOSYSC_dec2100=res[r][3]))

    # h0 vs h1 consistency check for the domain totals
    say("\nCheck: h1 exact PFT sum vs h0 area*landfrac total, GPP " + LATE)
    for s in SSPS:
        for r in RUNS:
            h1sum = sum(pft_tot[(r, s, LATE, "GPP")].values())
            h0sum = series[(r, s, "GPP")][late].mean()
            say(f"  {SSP_LABEL[s]} {r:8s} h1 {h1sum:.4f}  h0 {h0sum:.4f}  ratio {h1sum / h0sum:.4f}")

    # ---------------------------------------------------- write tables
    with open(os.path.join(OUTDIR, "summary.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    for name, rowsout in (("row_step.csv", step_csv), ("pft_totals.csv", pft_csv),
                          ("carbon_benefit.csv", ben_csv)):
        with open(os.path.join(OUTDIR, name), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(rowsout[0].keys()))
            wr.writeheader()
            wr.writerows(rowsout)

    # ---------------------------------------------------- figures
    # Fig 1: transects
    fig, axes = plt.subplots(3, 4, figsize=(20, 13), sharex=True)
    panels = [("Jan GPP, grid cell", rows, JAN), ("Jul GPP, grid cell", rows, JUL),
              ("Jan GPP, grass PFTs 13/14 only", grass_rows, JAN)]
    for i, (title, src, m) in enumerate(panels):
        for j, s in enumerate(SSPS):
            ax = axes[i, j]
            for r in RUNS:
                ax.plot(lat, src[(r, s, m)], marker="o", ms=3, **RUN_STYLE[r])
            ax.axvline(THRESHOLD_LAT_OLD, color="gray", ls=":", lw=1)
            ax.set_title(f"{SSP_LABEL[s]} - {title}", fontsize=10)
            if j == 0:
                ax.set_ylabel("gC m$^{-2}$ yr$^{-1}$")
            if i == 2:
                ax.set_xlabel("latitude (row centre, N)")
    axes[0, 0].legend(fontsize=9, loc="lower left")
    fig.suptitle(f"Row-mean GPP across the old 30.833N threshold (dotted), {LATE} mean", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "row_transect_gpp.png"), dpi=130)
    plt.close(fig)

    # Fig 2: SSP5-8.5 maps
    land = W > 0
    fig, axes = plt.subplots(1, 4, figsize=(22, 5))
    jan_max = np.nanmax([np.nanmax(maps585[("oldDF", JAN)]), np.nanmax(maps585[("newDF", JAN)])])
    d_jan = np.where(land, maps585[("newDF", JAN)] - maps585[("oldDF", JAN)], np.nan)
    d_ann = np.where(land, maps585[("newDF", "ann")] - maps585[("oldDF", "ann")], np.nan)
    specs = [
        (np.where(land, maps585[("oldDF", JAN)], np.nan), "old DF, Jan GPP", "viridis", 0, jan_max),
        (np.where(land, maps585[("newDF", JAN)], np.nan), "new DF, Jan GPP", "viridis", 0, jan_max),
        (d_jan, "new - old DF, Jan GPP", "RdBu", -np.nanmax(np.abs(d_jan)), np.nanmax(np.abs(d_jan))),
        (d_ann, "new - old DF, annual GPP", "RdBu", -np.nanmax(np.abs(d_ann)), np.nanmax(np.abs(d_ann))),
    ]
    for ax, (fld, title, cmap, vmin, vmax) in zip(axes, specs):
        pc = ax.pcolormesh(lon, lat, fld, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto")
        ax.axhline(THRESHOLD_LAT_OLD, color="k", ls="--", lw=0.8)
        ax.set_title(title, fontsize=11)
        ax.set_aspect("equal")
        fig.colorbar(pc, ax=ax, shrink=0.8, label="gC m$^{-2}$ yr$^{-1}$")
    fig.suptitle(f"SSP5-8.5 DF, {LATE} mean (dashed = old threshold 30.833N)", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "maps_ssp585_gpp.png"), dpi=130)
    plt.close(fig)

    # Fig 3: carbon benefit
    fig, axes = plt.subplots(2, 4, figsize=(20, 8), sharex=True)
    yrs = np.array(YEARS_ALL)
    for j, s in enumerate(SSPS):
        for r in ("oldDF", "newDF"):
            dn = series[("Default", s, "NBP")] - series[(r, s, "NBP")]
            st = dict(RUN_STYLE[r])
            st["label"] = "Default - " + st["label"]
            axes[0, j].plot(yrs, dn, **st)
            axes[1, j].plot(yrs, np.cumsum(dn), **st)
        axes[0, j].axhline(0, color="gray", lw=0.6)
        axes[0, j].set_title(f"{SSP_LABEL[s]}: annual NBP benefit", fontsize=10)
        axes[1, j].set_title(f"{SSP_LABEL[s]}: cumulative NBP benefit", fontsize=10)
        axes[1, j].set_xlabel("year")
    axes[0, 0].set_ylabel("PgC yr$^{-1}$")
    axes[1, 0].set_ylabel("PgC")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Avoided-deforestation carbon benefit (Default - DF), old vs new crit_dayl_stress", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "carbon_benefit_nbp.png"), dpi=130)
    plt.close(fig)

    print(f"\nwrote outputs to {OUTDIR}")


if __name__ == "__main__":
    main()
