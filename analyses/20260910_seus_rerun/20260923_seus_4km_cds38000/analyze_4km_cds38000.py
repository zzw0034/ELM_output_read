"""
4 km version of ../20260922_seus_halfdeg_DF_cds38000/analyze_df_cds38000.py:
did crit_dayl_stress 36000 s -> 38000 s remove the 30.833N GPP step from the
4 km future runs, and what did it cost?

Background: ../../CRIT_DAYL_STRESS_ARTIFACT.md. 38000 s (10.56 h) puts the
threshold latitude at 23.4N, south of the domain, so every cell crosses it each
winter instead of only the cells north of 30.833N.

Four runs per SSP:
  Default     20260917_seus_4km_fut_<ssp>                 36000 s
  oldDF       2026091{5,7}_seus_4km_fut_<ssp>_DF           36000 s
  newDF       20260922_seus_4km_fut_<ssp>_DF_cds38000      38000 s
  newDefault  20260922_seus_4km_fut_<ssp>_cds38000         38000 s
Each 38000 s run is a --keepexe clone of its 36000 s original: same executable,
finidat (2024 restart of the 20260911 transient), land use and forcing;
the effective lnd_in differs only in paramfile.

Same questions and methods as the 0.5 deg script (read that docstring for the
reasoning); what differs at 4 km:
  - the threshold rows are found from the latitudes (30.8125 / 30.854 N,
    rows 163/164) instead of being fixed at 30.75 / 31.25;
  - h1 has ~2.44 M PFTs and is ~7.5 GB per year, so GPP and NPP are read in
    one pass per file, and only the two decade windows are read from h1;
  - the full January transect is printed only for +-12 rows around the
    threshold (324 rows in total);
  - SSPs to process are chosen on the command line, so each Default/DF pair
    can be analysed as soon as it finishes:  analyze_4km_cds38000.py ssp585

Output conventions (unchanged): file <case>.elm.h?.YYYY-02-01-00000.nc holds
Jan..Dec of year YYYY (checked against mcdate); fluxes are day-weighted with
time_bounds; domain totals use area * landfrac (km^2).

Run through Slurm only (submit_py.sbatch), never on the login node.
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

WORKDIR = ("/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/"
           "20260910_seus_rerun/20260923_seus_4km_cds38000")
OUTDIR = os.path.join(WORKDIR, "outputs")
CASE_ROOT = "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun"

ALL_SSPS = ["ssp119", "ssp245", "ssp370", "ssp585"]
SSP_LABEL = {"ssp119": "SSP1-1.9", "ssp245": "SSP2-4.5",
             "ssp370": "SSP3-7.0", "ssp585": "SSP5-8.5"}
RUNS = ["Default", "oldDF", "newDF", "newDefault"]
RUN_STYLE = {
    "Default": dict(color="black", ls="-", label="Default, 36000 s"),
    "oldDF": dict(color="tab:red", ls="--", label="DF, 36000 s"),
    "newDF": dict(color="tab:blue", ls="--", label="DF, 38000 s"),
    "newDefault": dict(color="tab:green", ls="-", label="Default, 38000 s"),
}
PAIRS = {
    "both 36000": ("Default", "oldDF"),
    "DF only 38000": ("Default", "newDF"),
    "both 38000": ("newDefault", "newDF"),
}
PAIR_STYLE = {
    "both 36000": dict(color="tab:red", ls="--"),
    "DF only 38000": dict(color="tab:orange", ls=":"),
    "both 38000": dict(color="tab:blue", ls="-"),
}
PARAM_EFFECT = {"DF": ("oldDF", "newDF"), "Default": ("Default", "newDefault")}


def case_name(run, ssp):
    if run == "Default":
        return f"20260917_seus_4km_fut_{ssp}"
    if run == "oldDF":
        # ssp370 DF was built with the 2026-09-17 batch, the others on 09-15
        date = "20260917" if ssp == "ssp370" else "20260915"
        return f"{date}_seus_4km_fut_{ssp}_DF"
    if run == "newDF":
        return f"20260922_seus_4km_fut_{ssp}_DF_cds38000"
    if run == "newDefault":
        return f"20260922_seus_4km_fut_{ssp}_cds38000"
    raise ValueError(run)


YEARS_ALL = list(range(2024, 2101))
PERIODS = {"2024-2033": list(range(2024, 2034)),
           "2091-2100": list(range(2091, 2101))}
LATE = "2091-2100"

THRESHOLD_LAT_OLD = 30.833   # solstice daylength = 36000 s
JAN, JUL = 0, 6
TRANSECT_HALF_WIDTH = 12     # rows printed each side of the threshold

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
H1_VARS = ("GPP", "NPP")


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


def load_grid(ssp):
    ds = Dataset(hist_file(case_name("Default", ssp), "h0", 2100))
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
    stocks. For a stock, stock_month picks one monthly record (e.g. 11 = Dec)."""
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
    w = np.where(np.isfinite(field), weights, 0.0)
    num = np.nansum(np.where(w > 0, field, 0.0) * w, axis=1)
    den = w.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan)


# ---------------------------------------------------------------- h1 fields

def h1_pft_summary(case, years, weights, months=(JAN, JUL)):
    """One pass over the PFT-level h1 files of `years`, returning
      totals[var][itype]  domain total of var (PgC/yr), day-weighted annual,
                          for var in H1_VARS
      grass_rows[m]       per-row grass-only (GRASS) GPP in month m, weighted
                          by PFT area (gC/m2/yr annualised)
    """
    nlat, nlon = weights.shape
    totals = {v: {t: [] for t in PFT_NAMES} for v in H1_VARS}
    rnum = {m: np.zeros(nlat) for m in months}
    rden = {m: np.zeros(nlat) for m in months}
    for y in years:
        path = hist_file(case, "h1", y)
        print(f"    h1 {os.path.basename(path)}", flush=True)
        ds = Dataset(path)
        _check_year(ds, y, path)
        wt_m = _month_weights(ds)
        itype = np.asarray(ds.variables["pfts1d_itype_veg"][:]).astype(int)
        lunit = np.asarray(ds.variables["pfts1d_itype_lunit"][:]).astype(int)
        ixy = np.asarray(ds.variables["pfts1d_ixy"][:]).astype(int) - 1
        jxy = np.asarray(ds.variables["pfts1d_jxy"][:]).astype(int) - 1
        wtg = _read(ds, "pfts1d_wtgcell")
        vals = {}
        for var in H1_VARS:
            v = _read(ds, var)
            if _is_flux(ds, var):
                v = v * SEC_PER_YEAR
            vals[var] = v
        ds.close()
        # PFT area in km^2 = fraction of grid cell * grid-cell land area
        parea = np.where(np.isfinite(wtg), wtg, 0.0) * weights[jxy, ixy]
        veg = np.isin(lunit, VEG_LUNITS) & (parea > 0)
        for var in H1_VARS:
            ann = np.tensordot(wt_m, vals[var], axes=(0, 0))
            good = veg & np.isfinite(ann)
            contrib = np.where(good, ann * parea, 0.0)
            per_type = np.bincount(itype[good], weights=contrib[good], minlength=max(PFT_NAMES) + 1)
            for t in PFT_NAMES:
                totals[var][t].append(per_type[t] * 1e6 / 1e15)
        grass = veg & np.isin(itype, GRASS)
        for m in months:
            g = vals["GPP"][m]
            sel = grass & np.isfinite(g)
            rnum[m] += np.bincount(jxy[sel], weights=g[sel] * parea[sel], minlength=nlat)
            rden[m] += np.bincount(jxy[sel], weights=parea[sel], minlength=nlat)
        del vals
    totals = {var: {t: float(np.mean(totals[var][t])) for t in PFT_NAMES} for var in H1_VARS}
    grass_rows = {}
    for m in months:
        with np.errstate(invalid="ignore", divide="ignore"):
            grass_rows[m] = np.where(rden[m] > 0, rnum[m] / rden[m], np.nan)
    return totals, grass_rows


# ---------------------------------------------------------------- main

def pair_profile(rows, pair, ssp, m):
    a, b = PAIRS[pair]
    return rows[(a, ssp, m)] - rows[(b, ssp, m)]


def step_and_noise(profile, i_s, i_n):
    """Step across the threshold rows, and the median |adjacent-row change|
    of the same profile excluding that pair (its own row-to-row noise)."""
    d = np.diff(profile)
    step = profile[i_n] - profile[i_s]
    others = np.delete(d, i_s)
    return step, float(np.nanmedian(np.abs(others)))


def main(ssps):
    os.makedirs(OUTDIR, exist_ok=True)
    tag = "_".join(ssps)
    report = []

    def say(s=""):
        print(s, flush=True)
        report.append(s)

    lat, lon, W = load_grid(ssps[0])
    i_s = int(np.max(np.where(lat < THRESHOLD_LAT_OLD)[0]))
    i_n = i_s + 1
    assert lat[i_n] > THRESHOLD_LAT_OLD
    say(f"SSPs: {', '.join(SSP_LABEL[s] for s in ssps)}")
    say(f"grid {len(lat)} x {len(lon)}; threshold rows {lat[i_s]:.4f} (i={i_s}) -> "
        f"{lat[i_n]:.4f} (i={i_n})")
    say(f"domain land area (area*landfrac) = {W.sum():.0f} km^2")

    for r in RUNS:
        for s in ssps:
            c = case_name(r, s)
            missing = [y for y in YEARS_ALL for t in ("h0", "h1")
                       if not os.path.exists(hist_file(c, t, y))]
            if missing:
                raise RuntimeError(f"{c}: {len(missing)} missing history files")
    say(f"all {len(RUNS) * len(ssps)} cases x 77 years x h0/h1 present")

    # ---------------------------------------------------- read everything
    rows, grass_rows, pft_tot, maps = {}, {}, {}, {}
    for s in ssps:
        for r in RUNS:
            c = case_name(r, s)
            print(f"== {c}", flush=True)
            ann, mon = h0_climatology(c, "GPP", PERIODS[LATE])
            rows[(r, s, JAN)] = row_means(mon[JAN], W)
            rows[(r, s, JUL)] = row_means(mon[JUL], W)
            rows[(r, s, "ann")] = row_means(ann, W)
            maps[(r, s, JAN)] = mon[JAN]
            maps[(r, s, "ann")] = ann
            del mon
            for per, yrs in PERIODS.items():
                tot, grows = h1_pft_summary(c, yrs, W, months=(JAN, JUL) if per == LATE else ())
                for var in H1_VARS:
                    pft_tot[(r, s, per, var)] = tot[var]
                if per == LATE:
                    grass_rows[(r, s, JAN)] = grows[JAN]
                    grass_rows[(r, s, JUL)] = grows[JUL]

    # ---------------------------------------------------- 1a. per-run row step
    say("\n" + "=" * 78)
    say(f"1a. ROW STEP {lat[i_s]:.4f}N -> {lat[i_n]:.4f}N per run, GPP {LATE} mean "
        "(gC/m2/yr, monthly values annualised)")
    say("=" * 78)
    step_csv = []
    for s in ssps:
        say(f"\n--- {SSP_LABEL[s]} ---")
        say(f"{'':34s}{'Jan south':>10s}{'Jan north':>10s}{'step':>9s}{'%':>7s}"
            f"{'Jul south':>11s}{'Jul north':>10s}{'step':>9s}{'%':>7s}")
        for label, src in (("grid cell", rows), ("grass PFTs 13/14 only", grass_rows)):
            for r in RUNS:
                vals = []
                for m in (JAN, JUL):
                    a, b = src[(r, s, m)][i_s], src[(r, s, m)][i_n]
                    pct = 100 * (b - a) / a if abs(a) > 1e-9 else np.nan
                    vals += [a, b, b - a, pct]
                    step_csv.append(dict(ssp=s, run=r, level=label,
                                         month="Jan" if m == JAN else "Jul",
                                         south=a, north=b, step=b - a, step_pct=pct))
                say(f"  {label:20s} {r:10s}  "
                    f"{vals[0]:10.0f}{vals[1]:10.0f}{vals[2]:+9.0f}{vals[3]:+7.1f}"
                    f" {vals[4]:10.0f}{vals[5]:10.0f}{vals[6]:+9.0f}{vals[7]:+7.1f}")
    say("\n(% steps on values near 0 -- e.g. 38000 s grass in January -- are not meaningful)")

    # ---------------------------------------------------- 1b. Default - DF step
    say("\n" + "=" * 78)
    say("1b. STEP IN THE Default - DF DIFFERENCE PROFILE across the threshold rows")
    say("    noise = median |adjacent-row change| of the same profile, other rows")
    say("=" * 78)
    pair_csv = []
    for m, mname in ((JAN, "Jan"), (JUL, "Jul"), ("ann", "annual")):
        say(f"\n{mname} GPP, {LATE}")
        say(f"{'':10s}" + "".join(f"{p:>24s}" for p in PAIRS))
        say(f"{'':10s}" + "".join(f"{'step':>12s}{'noise':>12s}" for _ in PAIRS))
        for s in ssps:
            line = f"{SSP_LABEL[s]:10s}"
            for p in PAIRS:
                st, nz = step_and_noise(pair_profile(rows, p, s, m), i_s, i_n)
                line += f"{st:+12.0f}{nz:12.0f}"
                pair_csv.append(dict(ssp=s, month=mname, pairing=p, step=st, noise=nz))
            say(line)

    # ---------------------------------------------------- 1c. transect near the threshold
    lo, hi = max(i_s - TRANSECT_HALF_WIDTH, 1), min(i_n + TRANSECT_HALF_WIDTH, len(lat) - 1)
    for s in ssps:
        say(f"\n{SSP_LABEL[s]}: January grid-cell GPP, rows {lo}-{hi}, {LATE} "
            f"(d = change from the row to the south)")
        say(f"{'lat':>8s}" + "".join(f"{r:>11s}{'d':>7s}" for r in RUNS))
        for i in range(lo, hi + 1):
            line = f"{lat[i]:8.3f}"
            for r in RUNS:
                prof = rows[(r, s, JAN)]
                line += f"{prof[i]:11.0f}{prof[i] - prof[i - 1]:+7.0f}"
            say(line + ("   <== old threshold" if i == i_n else ""))
    say("")
    for s in ssps:
        for r in RUNS:
            d = np.diff(rows[(r, s, JAN)])
            k = int(np.nanargmin(d))
            say(f"  {SSP_LABEL[s]} {r:10s}: largest adjacent-row DROP in Jan GPP (whole domain) is "
                f"{d[k]:+.0f} between {lat[k]:.3f} and {lat[k + 1]:.3f}N")

    # ---------------------------------------------------- 2. parameter effect by PFT
    say("\n" + "=" * 78)
    say("2. PARAMETER EFFECT BY PFT (new - old, same land use), domain total PgC/yr, h1")
    say("=" * 78)
    for landuse, (old, new) in PARAM_EFFECT.items():
        for var in H1_VARS:
            for per in PERIODS:
                say(f"\n{landuse}: {new} - {old}, {var}, {per} mean   (* = stress-deciduous)")
                say(f"{'PFT':>22s}" + "".join(f"{SSP_LABEL[s]:>22s}" for s in ssps))
                say(f"{'':>22s}" + "".join(f"{'old':>8s}{'new-old':>9s}{'%':>5s}" for _ in ssps))
                for t in PFT_NAMES:
                    olds = [pft_tot[(old, s, per, var)][t] for s in ssps]
                    news = [pft_tot[(new, s, per, var)][t] for s in ssps]
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
                    for s in ssps:
                        o = sum(pft_tot[(old, s, per, var)][t] for t in sel)
                        n = sum(pft_tot[(new, s, per, var)][t] for t in sel)
                        line += f"{o:8.4f}{n - o:+9.4f}{100 * (n - o) / o:+5.0f}"
                    say(line)
    pft_csv = []
    for var in H1_VARS:
        for per in PERIODS:
            for s in ssps:
                for t in PFT_NAMES:
                    row = dict(var=var, period=per, ssp=s, itype=t, pft=PFT_NAMES[t],
                               stress_decid=int(t in STRESS_DECID))
                    for r in RUNS:
                        row[f"{r}_PgC_per_yr"] = pft_tot[(r, s, per, var)][t]
                    pft_csv.append(row)

    # ---------------------------------------------------- 3. carbon benefit
    say("\n" + "=" * 78)
    say("3. CARBON BENEFIT Default - DF under the three pairings (h0, area*landfrac)")
    say("=" * 78)
    series = {}
    for s in ssps:
        for r in RUNS:
            c = case_name(r, s)
            print(f"== series {c}", flush=True)
            series[(r, s, "NBP")] = h0_domain_series(c, "NBP", W)
            series[(r, s, "GPP")] = h0_domain_series(c, "GPP", W)
            series[(r, s, "TOTECOSYSC_dec")] = h0_domain_series(c, "TOTECOSYSC", W, stock_month=11)
    late = np.isin(YEARS_ALL, PERIODS[LATE])
    say(f"{'':10s}{'':15s}{'dGPP ' + LATE:>15s}{'cum dNBP':>15s}{'dTOTECOSYSC':>13s}")
    say(f"{'':10s}{'':15s}{'PgC/yr':>15s}{'2024-2100 PgC':>15s}{'Dec2100 PgC':>13s}")
    ben_csv = []
    for s in ssps:
        res = {}
        for p, (a, b) in PAIRS.items():
            dg = series[(a, s, "GPP")] - series[(b, s, "GPP")]
            dn = series[(a, s, "NBP")] - series[(b, s, "NBP")]
            de = series[(a, s, "TOTECOSYSC_dec")] - series[(b, s, "TOTECOSYSC_dec")]
            res[p] = (dg[late].mean(), dn.sum(), de[-1])
            ref = res["both 36000"]
            chg = "" if p == "both 36000" else (
                f"   vs both 36000: cum NBP {100 * (res[p][1] - ref[1]) / ref[1]:+.1f}%, "
                f"TOTECOSYSC {100 * (res[p][2] - ref[2]) / ref[2]:+.1f}%")
            say(f"{SSP_LABEL[s]:10s}{p:15s}{res[p][0]:15.4f}{res[p][1]:15.3f}{res[p][2]:13.3f}{chg}")
            ben_csv.append(dict(ssp=s, pairing=p, default_run=a, df_run=b,
                                dGPP_late=res[p][0], cumNBP_2024_2100=res[p][1],
                                dTOTECOSYSC_dec2100=res[p][2]))

    say("\nCheck: h1 exact PFT sum vs h0 area*landfrac total, GPP " + LATE)
    for s in ssps:
        for r in RUNS:
            h1sum = sum(pft_tot[(r, s, LATE, "GPP")].values())
            h0sum = series[(r, s, "GPP")][late].mean()
            say(f"  {SSP_LABEL[s]} {r:10s} h1 {h1sum:.4f}  h0 {h0sum:.4f}  ratio {h1sum / h0sum:.4f}")

    # ---------------------------------------------------- write tables
    with open(os.path.join(OUTDIR, f"summary_{tag}.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    for name, rowsout in ((f"row_step_{tag}.csv", step_csv), (f"pair_step_{tag}.csv", pair_csv),
                          (f"pft_totals_{tag}.csv", pft_csv), (f"carbon_benefit_{tag}.csv", ben_csv)):
        with open(os.path.join(OUTDIR, name), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(rowsout[0].keys()))
            wr.writeheader()
            wr.writerows(rowsout)

    # ---------------------------------------------------- figures
    ncol = len(ssps)
    zoom = (lat[i_s] - 3.0, lat[i_n] + 3.0)   # +-3 deg around the threshold

    # Fig 1: per-run transects (whole domain, and zoomed on the threshold)
    for suffix, xlim in (("", None), ("_zoom", zoom)):
        fig, axes = plt.subplots(3, ncol, figsize=(5 * ncol + 1, 13), sharex=True, squeeze=False)
        panels = [("Jan GPP, grid cell", rows, JAN), ("Jul GPP, grid cell", rows, JUL),
                  ("Jan GPP, grass PFTs 13/14 only", grass_rows, JAN)]
        for i, (title, src, m) in enumerate(panels):
            for j, s in enumerate(ssps):
                ax = axes[i, j]
                for r in RUNS:
                    ax.plot(lat, src[(r, s, m)], lw=1, **RUN_STYLE[r])
                ax.axvline(THRESHOLD_LAT_OLD, color="gray", ls=":", lw=1)
                if xlim:
                    ax.set_xlim(*xlim)
                ax.set_title(f"{SSP_LABEL[s]} - {title}", fontsize=10)
                if j == 0:
                    ax.set_ylabel("gC m$^{-2}$ yr$^{-1}$")
                if i == 2:
                    ax.set_xlabel("latitude (row centre, N)")
        axes[0, 0].legend(fontsize=9, loc="upper right")
        fig.suptitle(f"4 km row-mean GPP across the old 30.833N threshold (dotted), {LATE} mean",
                     fontsize=13)
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR, f"row_transect_gpp_{tag}{suffix}.png"), dpi=130)
        plt.close(fig)

    # Fig 2: Default - DF difference transects, the three pairings
    for suffix, xlim in (("", None), ("_zoom", zoom)):
        fig, axes = plt.subplots(3, ncol, figsize=(5 * ncol + 1, 13), sharex=True, squeeze=False)
        for i, (m, mname) in enumerate(((JAN, "Jan"), (JUL, "Jul"), ("ann", "annual"))):
            for j, s in enumerate(ssps):
                ax = axes[i, j]
                for p in PAIRS:
                    ax.plot(lat, pair_profile(rows, p, s, m), lw=1,
                            label=f"Default - DF, {p}", **PAIR_STYLE[p])
                ax.axvline(THRESHOLD_LAT_OLD, color="gray", ls=":", lw=1)
                ax.axhline(0, color="gray", lw=0.6)
                if xlim:
                    ax.set_xlim(*xlim)
                ax.set_title(f"{SSP_LABEL[s]} - {mname} GPP, Default - DF", fontsize=10)
                if j == 0:
                    ax.set_ylabel("gC m$^{-2}$ yr$^{-1}$")
                if i == 2:
                    ax.set_xlabel("latitude (row centre, N)")
        axes[0, 0].legend(fontsize=9)
        fig.suptitle(f"4 km row-mean Default - DF GPP difference, {LATE} mean", fontsize=13)
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR, f"pair_transect_gpp_{tag}{suffix}.png"), dpi=130)
        plt.close(fig)

    land = W > 0

    # Fig 3a: old vs new per land use, 1x4 (same layout as the 0.5 deg maps)
    def old_new_maps(old_fld, new_fld, titles, fname, suptitle, fourth):
        old_fld = np.where(land, old_fld, np.nan)
        new_fld = np.where(land, new_fld, np.nan)
        diff = new_fld - old_fld
        vmax = np.nanmax([np.nanmax(old_fld), np.nanmax(new_fld)])
        dmax = np.nanpercentile(np.abs(diff), 99.5)
        if isinstance(fourth, str) and fourth == "pct":
            with np.errstate(invalid="ignore", divide="ignore"):
                f4 = np.where(np.abs(old_fld) > 1e-9, 100 * diff / old_fld, np.nan)
            f4max, f4label = np.nanpercentile(np.abs(f4), 99.5), "%"
        else:
            f4 = np.where(land, fourth, np.nan)
            f4max, f4label = np.nanpercentile(np.abs(f4), 99.5), "gC m$^{-2}$ yr$^{-1}$"
        specs = [(old_fld, "viridis", 0, vmax, "gC m$^{-2}$ yr$^{-1}$"),
                 (new_fld, "viridis", 0, vmax, "gC m$^{-2}$ yr$^{-1}$"),
                 (diff, "RdBu", -dmax, dmax, "gC m$^{-2}$ yr$^{-1}$"),
                 (f4, "RdBu", -f4max, f4max, f4label)]
        fig, axes = plt.subplots(1, 4, figsize=(22, 5))
        for ax, title, (fld, cmap, vmin, vmx, lab) in zip(axes, titles, specs):
            pc = ax.pcolormesh(lon, lat, fld, cmap=cmap, vmin=vmin, vmax=vmx, shading="auto")
            ax.axhline(THRESHOLD_LAT_OLD, color="k", ls="--", lw=0.8)
            ax.set_title(title, fontsize=11)
            ax.set_aspect("equal")
            fig.colorbar(pc, ax=ax, shrink=0.8, label=lab)
        fig.suptitle(suptitle, fontsize=13)
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR, fname), dpi=130)
        plt.close(fig)

    for s in ssps:
        for landuse, (old, new) in PARAM_EFFECT.items():
            old_new_maps(maps[(old, s, JAN)], maps[(new, s, JAN)],
                         [f"old {landuse}, Jan GPP", f"new {landuse}, Jan GPP",
                          f"new - old {landuse}, Jan GPP", f"new - old {landuse}, annual GPP"],
                         f"maps_{s}_gpp_jan_{landuse}.png",
                         f"4 km {SSP_LABEL[s]} {landuse}, {LATE} mean, 36000 s (old) vs 38000 s (new) "
                         f"(dashed = old threshold 30.833N)",
                         maps[(new, s, "ann")] - maps[(old, s, "ann")])
            old_new_maps(maps[(old, s, "ann")], maps[(new, s, "ann")],
                         [f"old {landuse}, annual GPP", f"new {landuse}, annual GPP",
                          f"new - old {landuse}, annual GPP", f"new - old {landuse}, annual GPP (%)"],
                         f"maps_{s}_gpp_annual_{landuse}.png",
                         f"4 km {SSP_LABEL[s]} {landuse}, {LATE} mean, 36000 s (old) vs 38000 s (new) "
                         f"(dashed = old threshold 30.833N)",
                         "pct")

        # Fig 3b: Default - DF difference maps, the three pairings
        fig, axes = plt.subplots(2, 3, figsize=(20, 9))
        for i, key in enumerate((JAN, "ann")):
            flds = [np.where(land, maps[(a, s, key)] - maps[(b, s, key)], np.nan)
                    for a, b in PAIRS.values()]
            vmax = np.nanmax([np.nanpercentile(np.abs(f), 99.5) for f in flds])
            for j, (p, fld) in enumerate(zip(PAIRS, flds)):
                ax = axes[i, j]
                pc = ax.pcolormesh(lon, lat, fld, cmap="RdBu", vmin=-vmax, vmax=vmax, shading="auto")
                ax.axhline(THRESHOLD_LAT_OLD, color="k", ls="--", lw=0.8)
                ax.set_title(f"Default - DF, {p}: {'Jan' if key == JAN else 'annual'} GPP", fontsize=11)
                ax.set_aspect("equal")
                fig.colorbar(pc, ax=ax, shrink=0.8, label="gC m$^{-2}$ yr$^{-1}$")
        fig.suptitle(f"4 km {SSP_LABEL[s]}, {LATE} mean (dashed = old threshold 30.833N)", fontsize=13)
        fig.tight_layout()
        fig.savefig(os.path.join(OUTDIR, f"maps_{s}_default_minus_df.png"), dpi=130)
        plt.close(fig)

    # Fig 4: carbon benefit
    fig, axes = plt.subplots(2, ncol, figsize=(5 * ncol + 1, 8), sharex=True, squeeze=False)
    yrs = np.array(YEARS_ALL)
    for j, s in enumerate(ssps):
        for p, (a, b) in PAIRS.items():
            dn = series[(a, s, "NBP")] - series[(b, s, "NBP")]
            axes[0, j].plot(yrs, dn, label=f"Default - DF, {p}", **PAIR_STYLE[p])
            axes[1, j].plot(yrs, np.cumsum(dn), label=f"Default - DF, {p}", **PAIR_STYLE[p])
        axes[0, j].axhline(0, color="gray", lw=0.6)
        axes[0, j].set_title(f"{SSP_LABEL[s]}: annual NBP benefit", fontsize=10)
        axes[1, j].set_title(f"{SSP_LABEL[s]}: cumulative NBP benefit", fontsize=10)
        axes[1, j].set_xlabel("year")
    axes[0, 0].set_ylabel("PgC yr$^{-1}$")
    axes[1, 0].set_ylabel("PgC")
    axes[1, 0].legend(fontsize=8)
    fig.suptitle("4 km avoided-deforestation carbon benefit (Default - DF), three crit_dayl_stress pairings",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, f"carbon_benefit_nbp_{tag}.png"), dpi=130)
    plt.close(fig)

    print(f"\nwrote outputs to {OUTDIR}")


if __name__ == "__main__":
    args = sys.argv[1:] or ALL_SSPS
    bad = [a for a in args if a not in ALL_SSPS]
    if bad:
        sys.exit(f"unknown SSP(s): {bad}; choose from {ALL_SSPS}")
    main([s for s in ALL_SSPS if s in args])
