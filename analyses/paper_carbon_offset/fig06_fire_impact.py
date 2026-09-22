"""
Legacy asset fig06 -- modeled fire-loss diagnostics for the supplement.

Supports new Main Figures 4/5 and Results 3.3/3.4; see FIGURE_PLAN.md.
PFT_FIRE_CLOSS is patch fire loss, not complete COL_FIRE_CLOSS. Its ratio
to ecosystem stock is loss intensity, not a project reversal probability.
The existing case cohort and known phenology artifact need provenance and
sensitivity checks; this script does not independently validate fire physics.

Supports the proposal's climate-risk argument (Aim 3 "assess the
vulnerability of forest and soil carbon to climate change" and Aim 5
"identify areas with lower vulnerabilities ... to provide guidance on where
carbon offset projects would be best located"), which leans on Anderegg et
al. (2020, 2022) on climate-driven disturbance risk to forest carbon.

Products:
  A. Time series, 2024-2100, all scenarios: annual burned-area fraction and
     fire carbon loss, plus fire loss as a fraction of standing ecosystem
     carbon -- a modeled loss-intensity proxy with explicit pool boundaries.
  B. Maps: mean annual burned fraction and fire C loss for the historical
     decade (from the transient run) and end-of-century, and the change.

UNIT TRAPS in this output, both verified empirically 2026-09-14 rather than
assumed -- do not "simplify" these away:
  * `FIRE` is NOT wildfire. Its long_name is "emitted infrared (longwave)
    radiation". The fire variables are FAREA_BURNED, PFT_FIRE_CLOSS,
    PFT_FIRE_NLOSS, NFIRE, LFC2.
  * FAREA_BURNED's units attribute says "proportion" but the values are a
    per-second rate: the domain mean 1.95e-10 becomes 0.61%/yr when
    multiplied by seconds-per-year, versus a nonsensical 4e-7 %/yr under a
    per-timestep reading. NFIRE ("counts/km2/sec") is likewise per-second.
    common.py only auto-annualises variables whose units are exactly
    "gC/m^2/s", so these two are converted explicitly here.
  * LFC2 (fire-driven deforestation conversion) is identically zero
    everywhere in this configuration -- not plotted.

Usage inside an approved Slurm allocation:
    python fig06_fire_impact.py [0.5deg|4km]
"""
import os
import sys

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from common import (HALFDEG, HALFDEG_SUBDIR, FOURKM, FOURKM_SUBDIR, OUTDIR,
                    SEC_PER_YEAR_NOLEAP, h0_files, year_of, area_weights,
                    day_weighted_annual_mean, domain_mean, domain_total_PgC,
                    save_cache, load_cache, cache_exists)

# Variables whose units attribute does not say gC/m^2/s but which are still
# per-second rates that must be annualised (see the docstring).
RATE_VARS = ["FAREA_BURNED", "NFIRE"]
FIRE_VARS = ["FAREA_BURNED", "PFT_FIRE_CLOSS", "NFIRE"]
CTX_VARS = ["TOTECOSYSC"]

SCEN_ORDER = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5",
              "SSP3-7.0 RF", "SSP3-7.0 DF", "SSP3-7.0 RH"]
STYLE = {
    "SSP1-1.9": dict(color="tab:green", ls="-"),
    "SSP2-4.5": dict(color="tab:olive", ls="-"),
    "SSP3-7.0": dict(color="tab:orange", ls="-"),
    "SSP5-8.5": dict(color="tab:brown", ls="-"),
    "SSP3-7.0 RF": dict(color="tab:blue", ls="--"),
    "SSP3-7.0 DF": dict(color="tab:red", ls="--"),
    "SSP3-7.0 RH": dict(color="tab:purple", ls="--"),
}


def load_fire_series(case, subdir, res, year_min=None):
    key = f"{res}__{case}__fire"
    if cache_exists(key):
        print(f"  cache hit: {case}")
        return load_cache(key)
    print(f"  loading {case} ...")
    files = h0_files(case, subdir)
    if year_min is not None:
        files = [f for f in files if year_of(f) >= year_min]

    out = {"year": []}
    for v in FIRE_VARS + CTX_VARS:
        out[v] = []
    out["PFT_FIRE_CLOSS_PgC"] = []

    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        w = area_weights(ds)
        tb = ds["time_bounds"].values if "time_bounds" in ds else None
        out["year"].append(year_of(f))
        for v in FIRE_VARS + CTX_VARS:
            vals = day_weighted_annual_mean(ds[v], tb)
            units = ds[v].attrs.get("units", "").strip()
            if units == "gC/m^2/s" or v in RATE_VARS:
                vals = vals * SEC_PER_YEAR_NOLEAP
            out[v].append(domain_mean(vals, w))
            if v == "PFT_FIRE_CLOSS":
                out["PFT_FIRE_CLOSS_PgC"].append(domain_total_PgC(vals, w))
        ds.close()

    s = {k: np.array(v) for k, v in out.items()}
    save_cache(s, key)
    return s


def load_fire_map(case, var, y0, y1, subdir):
    files = [f for f in h0_files(case, subdir) if y0 <= year_of(f) <= y1]
    stack, lat, lon = [], None, None
    for f in files:
        ds = xr.open_dataset(f, decode_times=False)
        tb = ds["time_bounds"].values if "time_bounds" in ds else None
        vals = day_weighted_annual_mean(ds[var], tb)
        units = ds[var].attrs.get("units", "").strip()
        if units == "gC/m^2/s" or var in RATE_VARS:
            vals = vals * SEC_PER_YEAR_NOLEAP
        stack.append(vals)
        if lat is None:
            lat, lon, w = ds["lat"].values, ds["lon"].values, area_weights(ds)
        ds.close()
    return lon, lat, np.nanmean(np.stack(stack, axis=0), axis=0), w


def make_axes(ax):
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="gray", linewidth=0.5)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.6)
    ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())


def main():
    res = sys.argv[1] if len(sys.argv) > 1 else "0.5deg"
    cases, subdir = (HALFDEG, HALFDEG_SUBDIR) if res == "0.5deg" else (FOURKM, FOURKM_SUBDIR)
    os.makedirs(OUTDIR, exist_ok=True)

    hist = load_fire_series(cases["transient"], subdir, res, year_min=1950)
    fut = {s: load_fire_series(cases[s], subdir, res) for s in SCEN_ORDER}

    # ---- Panel figure A: time series -------------------------------------
    fig, axes = plt.subplots(3, 1, figsize=(11, 12), sharex=True)

    ax = axes[0]
    ax.plot(hist["year"], 100 * hist["FAREA_BURNED"], color="k", lw=1.2,
            label="historical (transient)")
    for s in SCEN_ORDER:
        ax.plot(fut[s]["year"], 100 * fut[s]["FAREA_BURNED"], lw=1.2, label=s, **STYLE[s])
    ax.set_ylabel("Burned area (% of land area yr$^{-1}$)")
    ax.set_title("Annual burned-area fraction", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, ncol=2)

    ax = axes[1]
    ax.plot(hist["year"], hist["PFT_FIRE_CLOSS"], color="k", lw=1.2)
    for s in SCEN_ORDER:
        ax.plot(fut[s]["year"], fut[s]["PFT_FIRE_CLOSS"], lw=1.2, **STYLE[s])
    ax.set_ylabel("PFT fire C loss (gC m$^{-2}$ yr$^{-1}$)")
    ax.set_title("Patch-level fire carbon loss", fontsize=10)
    ax.grid(alpha=0.3)

    # Patch fire loss normalized by ecosystem stock: loss intensity, not a
    # reversal probability. The numerator excludes decomposition-pool fire.
    ax = axes[2]
    ax.plot(hist["year"], 100 * hist["PFT_FIRE_CLOSS"] / hist["TOTECOSYSC"],
            color="k", lw=1.2)
    for s in SCEN_ORDER:
        ax.plot(fut[s]["year"],
                100 * fut[s]["PFT_FIRE_CLOSS"] / fut[s]["TOTECOSYSC"],
                lw=1.2, **STYLE[s])
    ax.set_ylabel("PFT fire loss (% of ecosystem C yr$^{-1}$)")
    ax.set_title("PFT fire-loss intensity relative to ecosystem carbon "
                 "(not a reversal probability)", fontsize=10)
    ax.set_xlabel("year")
    ax.grid(alpha=0.3)

    fig.suptitle(f"SEUS {res}: modeled burned area and PFT fire carbon loss", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, f"fig06a_fire_timeseries_{res}.png"), dpi=150)
    plt.close(fig)

    # ---- Panel figure B: maps --------------------------------------------
    lon, lat, hist_ba, w = load_fire_map(cases["transient"], "FAREA_BURNED", 2014, 2023, subdir)
    _, _, fut_ba, _ = load_fire_map(cases["SSP3-7.0"], "FAREA_BURNED", 2091, 2100, subdir)
    _, _, hist_cl, _ = load_fire_map(cases["transient"], "PFT_FIRE_CLOSS", 2014, 2023, subdir)
    _, _, fut_cl, _ = load_fire_map(cases["SSP3-7.0"], "PFT_FIRE_CLOSS", 2091, 2100, subdir)
    land = w > 0

    fig2, axs = plt.subplots(2, 3, figsize=(17, 9),
                             subplot_kw={"projection": ccrs.PlateCarree()})
    panels = [
        (100 * hist_ba, "Burned area 2014-2023", "% yr$^{-1}$", "YlOrRd", False),
        (100 * fut_ba, "Burned area 2091-2100 (SSP3-7.0)", "% yr$^{-1}$", "YlOrRd", False),
        (100 * (fut_ba - hist_ba), "Change in burned area", "% yr$^{-1}$", "RdBu_r", True),
        (hist_cl, "PFT fire C loss 2014-2023", "gC m$^{-2}$ yr$^{-1}$", "YlOrRd", False),
        (fut_cl, "PFT fire C loss 2091-2100 (SSP3-7.0)", "gC m$^{-2}$ yr$^{-1}$", "YlOrRd", False),
        (fut_cl - hist_cl, "Change in PFT fire C loss", "gC m$^{-2}$ yr$^{-1}$", "RdBu_r", True),
    ]
    # Shared scales within each row so the before/after panels are comparable.
    ba_max = np.nanpercentile(np.concatenate([(100 * hist_ba)[land], (100 * fut_ba)[land]]), 99)
    cl_max = np.nanpercentile(np.concatenate([hist_cl[land], fut_cl[land]]), 99)

    for ax, (field, title, unit, cmap, diverging) in zip(axs.flat, panels):
        make_axes(ax)
        if diverging:
            v = np.nanpercentile(np.abs(field[land]), 99)
            kw = dict(cmap=cmap, vmin=-v, vmax=v)
        else:
            kw = dict(cmap=cmap, vmin=0, vmax=(ba_max if "Burned" in title else cl_max))
        pc = ax.pcolormesh(lon, lat, field, transform=ccrs.PlateCarree(),
                           shading="auto", **kw)
        cb = fig2.colorbar(pc, ax=ax, orientation="horizontal", pad=0.05, shrink=0.85)
        cb.set_label(unit, fontsize=8)
        ax.set_title(title, fontsize=9)

    fig2.suptitle(f"SEUS {res}: modeled fire patterns, present vs end of century", fontsize=13)
    fig2.savefig(os.path.join(OUTDIR, f"fig06b_fire_maps_{res}.png"), dpi=150,
                 bbox_inches="tight")
    plt.close(fig2)

    # ---- numbers ----------------------------------------------------------
    def wmean_land(field):
        f, ww = field[land], w[land]
        g = np.isfinite(f)
        return float(np.nansum(f[g] * ww[g]) / np.nansum(ww[g]))

    print("\n--- Burned area and PFT fire carbon loss (domain, land-area weighted) ---")
    h = hist["year"] >= 2014
    print(f"historical 2014-2023: burned {100*np.nanmean(hist['FAREA_BURNED'][h]):.3f} %/yr, "
          f"PFT fire C loss {np.nanmean(hist['PFT_FIRE_CLOSS'][h]):.2f} gC/m2/yr "
          f"({np.nanmean(hist['PFT_FIRE_CLOSS_PgC'][h]):.4f} PgC/yr)")
    print(f"{'scenario':14s} {'burned %/yr':>12} {'PFT fire gC/m2/yr':>17} {'PgC/yr':>9} "
          f"{'% of stock/yr':>14}")
    for s in SCEN_ORDER:
        e = fut[s]["year"] >= 2091
        ba = 100 * np.nanmean(fut[s]["FAREA_BURNED"][e])
        cl = np.nanmean(fut[s]["PFT_FIRE_CLOSS"][e])
        pg = np.nanmean(fut[s]["PFT_FIRE_CLOSS_PgC"][e])
        frac = 100 * cl / np.nanmean(fut[s]["TOTECOSYSC"][e])
        print(f"{s:14s} {ba:12.3f} {cl:17.2f} {pg:9.4f} {frac:14.3f}")

    print(f"\nMaps (land-weighted means): burned area 2014-2023 "
          f"{100*wmean_land(hist_ba):.3f} %/yr -> 2091-2100 {100*wmean_land(fut_ba):.3f} %/yr; "
          f"PFT fire C loss {wmean_land(hist_cl):.2f} -> {wmean_land(fut_cl):.2f} gC/m2/yr")
    print(f"\nFigures written to {OUTDIR}")


if __name__ == "__main__":
    main()
