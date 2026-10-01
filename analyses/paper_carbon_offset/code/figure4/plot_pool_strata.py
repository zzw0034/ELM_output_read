"""
Main Figure 4 / Results 3.3 (blueprint E4): which carbon pools carry the
management benefit, when they move, and (with --strata) what part of the RF
benefit comes from cells where RF restores forest versus cells where it only
stops harvest.

Panels (one SSP, 4 km; defaults SSP3-7.0, end state = mean of 2091-2100):
  a  Default stock composition by pool, PgC
  b  signed pool contributions to RF - Default and RH - Default, PgC
  c  the same benefits at three boundaries: aboveground vegetation, in-situ
     ecosystem (excl. products), ecosystem + products (= TOTECOSYSC)
  d  RF - Default pool contributions over 2024-2100 (domain totals, PgC)
  e  the same for RH - Default
  f-h  (--strata) restoration / protection strata of RF: map, area and benefit
     per stratum, signed pool response per stratum (MgC/ha of stratum land)

Pools (D4), four, adding up to TOTECOSYSC (grouping chosen by the user 2026-10-01):
living vegetation = TOTVEGC; dead wood and litter = CWDC + TOTLITC; soil organic carbon over the
whole column = TOTSOMC; wood products = TOTECOSYSC - (TOTVEGC + CWDC + TOTLITC + TOTSOMC), derived
because TOTPRODC is not in h0 (must be >= 0 in Default). Two finer quantities are kept in the
printout, the CSVs and the note: aboveground vegetation (TOTVEGC_ABG, panel c's narrowest
boundary) and SOC 0-100 cm (TOTSOMC_1m, comparable to field studies).

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \\
        code/figure4/plot_pool_strata.py --res 4km [--ssp SSP3-7.0] [--strata]
Inputs (pulled from proj-shared, git-ignored): in _cache/figure4/<res>/, made by
extract_pool_maps.py, extract_soc1m.py and extract_tree_fraction.py:
    <SSP>[_RF|_RH]__pools_2091-2100.npz   <SSP>[_RF|_RH]__soc1m_2024-2100.npz
    transient__treefrac_2023.npz  <SSP>_RF__treefrac_<rf-year>.npz   (--strata)
and, for panels d-e (4 km), the annual domain totals of extract_domain_totals.py in
_cache/figure2/future_4km/<SSP>[_RF|_RH]__totals.npz.
Outputs: figures/figure4/fig4_pools_<res>_<SSP>_<y0>-<y1>.png (+ pool CSV and trajectory
CSV), or fig4_pool_strata_... with --strata (+ strata and sensitivity CSVs).
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # analysis root

# dataviz reference palette (light). Management uses slots 1-2 (as in Figure 2);
# pools use slots 3-8 so a pool colour never repeats a management colour.
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e9e8e4", "#fcfcfb"
MGMT = {"RF": "#2a78d6", "RH": "#eb6834"}
STRATA = [(1, "Restoration\n(+ harvest ban)", "#2a78d6"),
          (2, "Protection only\n(harvest ban)", "#9ec5f4"),
          (0, "No change", "#cfcdc6")]
POOLS = [("veg", "Living vegetation", "#1baf7a"),
         ("dead", "Dead wood and litter", "#e87ba4"),
         ("soil", "Soil organic carbon (whole column)", "#4a3aa7"),
         ("prod", "Wood products (derived)", "#e34948")]
POOL_SHORT = {"veg": "Living\nvegetation", "dead": "Dead wood\n+ litter", "soil": "Soil\n(whole column)", "prod": "Wood\nproducts"}
POOL_LINE = {"veg": "Living vegetation", "dead": "Dead wood + litter", "soil": "Soil (whole column)", "prod": "Wood products"}
BAD = "#dfe3e8"
GC_M2_TO_MGC_HA = 0.01
REST_SENS = (0.005, 0.01, 0.05, 0.10)
HARV_SENS = (0.01, 0.1, 1.0)
FLUX_VARS = ["NBP", "NEP", "LAND_USE_FLUX", "WOOD_HARVESTC"]


# ------------------------------------------------------------------- numbers

def load(path):
    assert os.path.exists(path), f"missing input {path}"
    z = np.load(path)
    return {k: z[k] for k in z.files}


def pools_of(m):
    """Four pools in gC/m2 from the h0 stock maps (D4 closure, products derived)."""
    prod = m["TOTECOSYSC"] - (m["TOTVEGC"] + m["CWDC"] + m["TOTLITC"] + m["TOTSOMC"])
    return {"veg": m["TOTVEGC"], "dead": m["CWDC"] + m["TOTLITC"], "soil": m["TOTSOMC"], "prod": prod}


def pg(field, area, mask):
    """Domain total in PgC (or PgC/yr) of a gC/m2 field over mask: gC/m2 x km2 x 1e6 m2/km2 / 1e15."""
    return float(np.sum(field[mask].astype("f8") * area[mask]) * 1e6 / 1e15)


def classify(inc, harv, rest_thr, harv_thr):
    s = np.zeros(inc.shape, dtype=int)
    rest = inc >= rest_thr
    s[rest] = 1
    s[(~rest) & (harv >= harv_thr)] = 2
    return s


def stratum_rows(P, F, strata, area, valid):
    """Per stratum: area, RF-Default and RH-Default pool sums (PgC) and total, flux differences (PgC/yr)."""
    rows = []
    for code, label, _ in STRATA:
        m = valid & (strata == code)
        row = {"code": code, "label": label.replace("\n", " "), "area_km2": float(area[m].sum())}
        for mg in ("RF", "RH"):
            d = {k: pg(P[mg][k] - P["Def"][k], area, m) for k, _, _ in POOLS}
            row[f"{mg}_pools"] = d
            row[f"{mg}_total"] = sum(d.values())
            row[f"{mg}_fluxes"] = {v: pg(F[mg][v] - F["Def"][v], area, m) for v in FLUX_VARS}
        rows.append(row)
    return rows


def density(pgc, area_km2):
    """PgC over area_km2 of land -> MgC/ha."""
    return pgc * 1e15 / (area_km2 * 1e6) * GC_M2_TO_MGC_HA if area_km2 > 0 else np.nan


# ---------------------------------------------------------------------- plot

def style(ax, ylabel=None, grid_axis="y"):
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=10.5)
    ax.grid(axis=grid_axis, color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("black")
        ax.spines[sp].set_linewidth(1.0)
    ax.tick_params(colors="black", labelcolor=INK, labelsize=9.5, length=3.5, width=0.9)
    ax.axhline(0, color="black", lw=0.9, zorder=1)


def ptitle(ax, letter, text):
    ax.set_title(f"{letter}  {text}", loc="left", fontsize=11, color=INK, fontweight="bold")


def spread(ys, gap):
    """Push label y-positions apart so neighbours are >= gap apart (order kept)."""
    order = np.argsort(ys)
    out = np.array(ys, float)
    for a, b in zip(order[:-1], order[1:]):
        if out[b] - out[a] < gap:
            out[b] = out[a] + gap
    return out


def stacked_signed(ax, x, values, width, colors, edge=SURFACE):
    """One stacked bar with positive parts upward and negative parts downward from 0."""
    pos = neg = 0.0
    for v, c in zip(values, colors):
        if v >= 0:
            ax.bar(x, v, width, bottom=pos, color=c, edgecolor=edge, linewidth=1.2, zorder=3)
            pos += v
        else:
            ax.bar(x, v, width, bottom=neg, color=c, edgecolor=edge, linewidth=1.2, zorder=3)
            neg += v


def panel_a(ax, P_def, area, valid):
    tot = {k: pg(P_def[k], area, valid) for k, _, _ in POOLS}
    total = sum(tot.values())
    bottom, ys = 0.0, []
    for k, name, c in POOLS:
        ax.bar(0, tot[k], 0.55, bottom=bottom, color=c, edgecolor=SURFACE, linewidth=1.5, zorder=3)
        ys.append(bottom + tot[k] / 2)
        bottom += tot[k]
    ly = spread(ys, total * 0.06)
    for (k, name, c), y0, y1 in zip(POOLS, ys, ly):
        ax.text(0.34, y1, f"{POOL_SHORT[k].replace(chr(10), ' ')} {tot[k]:.2f} ({100 * tot[k] / total:.0f}%)",
                va="center", fontsize=8.6, color=INK2)
    ax.set_xlim(-0.45, 2.3)
    ax.set_xticks([])
    style(ax, "Default stock (PgC)")
    ax.grid(False)
    ax.set_ylim(0, total * 1.04)
    ptitle(ax, "a", "Default stock by pool")
    return tot


def panel_b(ax, P, area, valid):
    keys = [k for k, _, _ in POOLS]
    vals = {mg: [pg(P[mg][k] - P["Def"][k], area, valid) for k in keys] for mg in ("RF", "RH")}
    for mg in vals:
        vals[mg].append(sum(vals[mg]))
    x = np.arange(len(keys) + 1)
    w = 0.36
    for i, mg in enumerate(("RF", "RH")):
        ax.bar(x + (i - 0.5) * w, vals[mg], w, color=MGMT[mg], edgecolor=SURFACE, linewidth=1.2, zorder=3, label=mg)
    for xi, v in zip(x[-1:], vals["RF"][-1:]):
        ax.text(xi - 0.5 * w, v, f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=8.8, color=INK2)
    for xi, v in zip(x[-1:], vals["RH"][-1:]):
        ax.text(xi + 0.5 * w, v, f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=8.8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([POOL_SHORT[k] for k in keys] + ["Total"], fontsize=8.4)
    style(ax, "Change vs Default (PgC)")
    lo, hi = min(0, min(vals["RF"] + vals["RH"])), max(0, max(vals["RF"] + vals["RH"]))
    ax.set_ylim(lo - 0.08 * (hi - lo), hi + 0.22 * (hi - lo))
    ax.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=2)
    ptitle(ax, "b", "Signed pool contributions")
    return vals


def panel_c(ax, P, area, valid, abg):
    """abg: {mgmt: aboveground-vegetation difference, PgC} (TOTVEGC_ABG, not one of the four pools)."""
    def bounds(mg):
        d = {k: pg(P[mg][k] - P["Def"][k], area, valid) for k, _, _ in POOLS}
        return [abg[mg], sum(d.values()) - d["prod"], sum(d.values())]
    b = {mg: bounds(mg) for mg in ("RF", "RH")}
    x = np.arange(3)
    w = 0.36
    for i, mg in enumerate(("RF", "RH")):
        ax.bar(x + (i - 0.5) * w, b[mg], w, color=MGMT[mg], edgecolor=SURFACE, linewidth=1.2, zorder=3, label=mg)
    top = max(max(b["RF"]), max(b["RH"]), 0)
    for xi in range(3):
        r = b["RF"][xi] / b["RH"][xi] if abs(b["RH"][xi]) > 1e-9 else np.nan
        ax.text(xi, max(b["RF"][xi], b["RH"][xi], 0) + 0.04 * max(top, 1e-9),
                f"RF/RH = {r:.1f}" if np.isfinite(r) else "RF/RH = n/a", ha="center", fontsize=8.8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels(["Aboveground\nvegetation", "In-situ\necosystem", "Ecosystem\n+ products"], fontsize=8.8)
    style(ax, "Benefit (PgC)")
    ax.set_ylim(min(0, min(b["RF"] + b["RH"])) * 1.15, top * 1.18)
    ptitle(ax, "c", "Benefit at three boundaries")
    return b


def panel_map(ax_proj, lon, lat, strata, valid, extent):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    field = np.where(valid, strata, np.nan).astype("f8")
    cmap = ListedColormap([c for code, _, c in sorted(STRATA, key=lambda s: s[0])])
    cmap.set_bad(BAD)
    ax_proj.set_facecolor(BAD)
    ax_proj.pcolormesh(lon, lat, field, cmap=cmap, vmin=-0.5, vmax=2.5, shading="auto",
                       transform=ccrs.PlateCarree(), rasterized=True)
    ax_proj.coastlines(resolution="10m", linewidth=0.5, color="#555555")
    ax_proj.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m",
                                                     facecolor="none", edgecolor="#777777", linewidth=0.3))
    ax_proj.set_extent(extent, crs=ccrs.PlateCarree())
    gl = ax_proj.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 8}
    ptitle(ax_proj, "f", "RF strata")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in STRATA]
    ax_proj.legend(handles, [l.replace("\n", " ") for _, l, _ in STRATA], loc="lower left", fontsize=8.2,
                   frameon=True, framealpha=0.9, edgecolor="none")


def panel_strata_bars(ax_area, ax_ben, rows):
    x = np.arange(len(rows))
    colors = [c for _, _, c in STRATA]
    area = [r["area_km2"] / 1e3 for r in rows]
    ben = [r["RF_total"] for r in rows]
    ax_area.bar(x, area, 0.62, color=colors, edgecolor=SURFACE, linewidth=1.2, zorder=3)
    ax_ben.bar(x, ben, 0.62, color=colors, edgecolor=SURFACE, linewidth=1.2, zorder=3)
    tot_area, tot_ben = sum(area), sum(ben)
    for xi, a in zip(x, area):
        ax_area.text(xi, a, f"{a:.0f}\n({100 * a / tot_area:.0f}%)", ha="center", va="bottom", fontsize=8.5, color=INK2)
    for xi, b in zip(x, ben):
        pct = 100 * b / tot_ben if tot_ben else np.nan
        ax_ben.text(xi, b, f"{b:+.2f}\n({pct:.0f}%)", ha="center", va="bottom" if b >= 0 else "top",
                    fontsize=8.5, color=INK2)
    for ax, ylab in ((ax_area, "Area (10³ km²)"), (ax_ben, "RF − Default (PgC)")):
        style(ax, ylab)
        ax.set_xticks(x)
    ax_area.set_xticklabels([])
    ax_ben.set_xticklabels([l for _, l, _ in STRATA], fontsize=8.2)
    ax_area.set_ylim(0, max(area) * 1.3)
    lo, hi = min(0, min(ben)), max(0, max(ben))
    ax_ben.set_ylim(lo - 0.25 * (hi - lo + 1e-9) if lo < 0 else 0, hi * 1.35 if hi > 0 else 1)
    ptitle(ax_area, "g", "Area and benefit by stratum")


def panel_strata_pools(ax, rows):
    x = np.arange(len(rows))
    colors = [c for _, _, c in POOLS]
    totals = []
    for xi, r in zip(x, rows):
        dens = [density(r["RF_pools"][k], r["area_km2"]) for k, _, _ in POOLS]
        stacked_signed(ax, xi, dens, 0.55, colors)
        totals.append(density(r["RF_total"], r["area_km2"]))
    ax.scatter(x, totals, s=46, marker="o", color="black", zorder=5, label="RF total")
    ax.scatter(x, [density(r["RH_total"], r["area_km2"]) for r in rows], s=52, marker="D",
               facecolor=SURFACE, edgecolor=MGMT["RH"], linewidth=1.8, zorder=5, label="RH total")
    for xi, t in zip(x, totals):
        ax.text(xi + 0.33, t, f"{t:+.1f}", va="center", fontsize=8.8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([l for _, l, _ in STRATA], fontsize=8.2)
    style(ax, "RF − Default (MgC/ha of stratum)")
    stacks = [[density(r["RF_pools"][k], r["area_km2"]) for k, _, _ in POOLS] for r in rows]
    top = max(sum(v for v in st if v > 0) for st in stacks)
    bot = min(sum(v for v in st if v < 0) for st in stacks)
    ax.set_ylim(bot - 0.06 * (top - bot), top + 0.55 * (top - bot))
    ax.set_xlim(-0.6, len(rows) - 0.1)
    pool_handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors]
    h2, l2 = ax.get_legend_handles_labels()
    ax.legend(pool_handles + h2, [n for _, n, _ in POOLS] + l2, ncol=2, fontsize=8, frameon=False,
              loc="upper right", handlelength=1.2, columnspacing=1.0)
    ptitle(ax, "h", "Pool response by stratum")


# ------------------------------------------------------------- trajectories

def traj_pools(tot):
    """Four pools as annual domain totals (PgC) from the Figure 2 totals."""
    prod = tot["TOTECOSYSC"] - (tot["TOTVEGC"] + tot["CWDC"] + tot["TOTLITC"] + tot["TOTSOMC"])
    return {"veg": tot["TOTVEGC"], "dead": tot["CWDC"] + tot["TOTLITC"], "soil": tot["TOTSOMC"], "prod": prod}


def traj_deltas(fig2_dir, soc_dir, ssp):
    """{'year', mgmt: (pool deltas, total delta, extras)} vs the 36000 s Default, 2024-2100.
    extras: aboveground vegetation and SOC 0-100 cm differences (from the soc1m extract)."""
    ld = lambda sfx: (np.load(os.path.join(fig2_dir, f"{ssp}{sfx}__totals.npz"), allow_pickle=True),
                      np.load(os.path.join(soc_dir, f"{ssp}{sfx}__soc1m_2024-2100.npz"), allow_pickle=True))
    (tD, sD), runs = ld(""), {"RF": ld("_RF"), "RH": ld("_RH")}
    assert np.array_equal(tD["year"], sD["year"]), "year axes of totals and soc1m differ"
    assert (tD["TOTSOMC"] - sD["total_PgC"] >= -1e-6).all(), "TOTSOMC_1m exceeds TOTSOMC"
    PD = traj_pools(tD)
    out = {"year": tD["year"]}
    for nm, (t, s1) in runs.items():
        assert np.array_equal(t["year"], tD["year"]) and np.array_equal(s1["year"], tD["year"]), f"{nm}: year axis differs"
        PR = traj_pools(t)
        delta = {k: PR[k] - PD[k] for k, _, _ in POOLS}
        total = t["TOTECOSYSC"] - tD["TOTECOSYSC"]
        assert np.allclose(sum(delta.values()), total, atol=1e-9), f"{nm}: pools do not add up to TOTECOSYSC"
        extras = {"abg": t["TOTVEGC_ABG"] - tD["TOTVEGC_ABG"], "soc_0_100": s1["total_PgC"] - sD["total_PgC"]}
        out[nm] = (delta, total, extras)
    return out


def panel_traj(ax, yr, delta, total, letter, title):
    for k, _, col in POOLS:
        ax.plot(yr, delta[k], color=col, lw=2)
    ax.plot(yr, total, color="black", lw=2.6)
    ends = [delta[k][-1] for k, _, _ in POOLS] + [total[-1]]
    span = max(abs(max(ends)), abs(min(ends)), 1e-6)
    ly = spread(ends, span * 0.065)
    for lab, y1 in zip([POOL_LINE[k] for k, _, _ in POOLS] + ["Total"], ly):
        ax.text(2101.5, y1, lab, color=INK2, fontsize=9, va="center", clip_on=False)
    ax.set_xlim(2024, 2100)
    style(ax, "Difference vs Default (PgC)")
    ptitle(ax, letter, title)


# ---------------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="4km", choices=["4km", "0.5deg"])
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100", help="end-state window of the maps (as extracted)")
    ap.add_argument("--strata", action="store_true",
                    help="add the restoration/protection strata (panels f-h); needs the tree-fraction extracts")
    ap.add_argument("--rf-year", type=int, default=2060, help="plateau year of the RF run for the land-cover increment")
    ap.add_argument("--rest-thr", type=float, default=0.01)
    ap.add_argument("--harv-thr", type=float, default=0.1)
    ap.add_argument("--cache-root", default=os.path.join(ROOT, "_cache/figure4"))
    ap.add_argument("--fig2-cache", default=os.path.join(ROOT, "_cache/figure2/future_4km"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "figures/figure4"))
    a = ap.parse_args()

    cdir = os.path.join(a.cache_root, a.res)
    win = a.years
    y0, y1 = (int(v) for v in win.split("-"))
    runs = {"Def": a.ssp, "RF": f"{a.ssp}_RF", "RH": f"{a.ssp}_RH"}
    maps = {k: load(os.path.join(cdir, f"{t}__pools_{win}.npz")) for k, t in runs.items()}
    soc1 = {k: load(os.path.join(cdir, f"{t}__soc1m_2024-2100.npz")) for k, t in runs.items()}
    for k in maps:
        for g in ("lat", "lon", "area_km2"):
            assert np.array_equal(soc1[k][g], maps["Def"][g]), f"{k} soc1m: {g} differs from the Default pools grid"
        assert tuple(int(v) for v in soc1[k]["map_years"]) == (y0, y1), f"{k}: soc1m map window is not {win}"
        maps[k]["TOTSOMC_1m"] = soc1[k]["mean_map"]
    extra = {}
    if a.strata:
        extra = {"base": load(os.path.join(cdir, "transient__treefrac_2023.npz")),
                 "rfcov": load(os.path.join(cdir, f"{a.ssp}_RF__treefrac_{a.rf_year}.npz"))}
    for k, m in extra.items():
        for g in ("lat", "lon", "area_km2"):
            assert np.array_equal(m[g], maps["Def"][g]), f"{k}: {g} differs from the Default run's grid"
    lat, lon, area = maps["Def"]["lat"], maps["Def"]["lon"], maps["Def"]["area_km2"].astype("f8")
    lon = np.where(lon > 180, lon - 360, lon)

    STK = ("TOTECOSYSC", "TOTVEGC", "TOTVEGC_ABG", "CWDC", "TOTLITC", "TOTSOMC", "TOTSOMC_1m")
    # float32 stocks of ~3e4 gC/m2 carry ~2e-3 gC/m2 rounding: add them in float64
    P = {k: pools_of({v: m[v].astype("f8") for v in STK}) for k, m in maps.items()}
    F = {k: {v: m[v] for v in FLUX_VARS} for k, m in maps.items()}

    valid = area > 0
    for k in P:
        for v in P[k].values():
            valid &= np.isfinite(v)
    for k in F:
        for v in F[k].values():
            valid &= np.isfinite(v)
    if a.strata:
        inc = extra["rfcov"]["tree_frac"].astype("f8") - extra["base"]["tree_frac"].astype("f8")
        harv = maps["Def"]["WOOD_HARVESTC"].astype("f8")
        valid &= np.isfinite(inc) & np.isfinite(harv)
    print(f"{a.res} {a.ssp} {win}: {int(valid.sum())} valid land cells, {area[valid].sum() / 1e3:.1f} x10^3 km2 "
          f"(of {int((area > 0).sum())} land cells)")

    # ---- checks, all printed
    for k in P:
        closure = np.abs(sum(P[k].values())[valid] - maps[k]["TOTECOSYSC"][valid].astype("f8")).max()
        assert closure < 1e-6, f"{k}: pools do not sum to TOTECOSYSC (max {closure})"
        deep = maps[k]["TOTSOMC"].astype("f8") - maps[k]["TOTSOMC_1m"].astype("f8")
        assert float(deep[valid].min()) > -0.01, f"{k}: TOTSOMC_1m exceeds TOTSOMC in a cell by {-float(deep[valid].min())} gC/m2"
        print(f"  derived product pool {k:3s}: {pg(P[k]['prod'], area, valid):+.4f} PgC (min per cell {P[k]['prod'][valid].min():+.2f} gC/m2); "
              f"soil whole column {pg(P[k]['soil'], area, valid):.2f}, of which 0-100 cm {pg(maps[k]['TOTSOMC_1m'], area, valid):.2f} PgC")
    assert pg(P["Def"]["prod"], area, valid) >= -1e-3, \
        "derived product pool of Default is negative: TOTPRODC is not in TOTECOSYSC here, re-check D4"
    dom_total = {mg: pg(maps[mg]["TOTECOSYSC"].astype("f8") - maps["Def"]["TOTECOSYSC"].astype("f8"), area, valid)
                 for mg in ("RF", "RH")}

    # ---- pool table (always): stocks, signed contributions, three boundaries
    print(f"\nDefault stock {win} (PgC): " + ", ".join(f"{POOL_LINE[k]} {pg(P['Def'][k], area, valid):.2f}" for k, _, _ in POOLS))
    print(f"{'pool':36s}{'RF-Def PgC':>11s}{'RH-Def PgC':>11s}")
    d_pool = {mg: {k: pg(P[mg][k] - P["Def"][k], area, valid) for k, _, _ in POOLS} for mg in ("RF", "RH")}
    for k, name, _ in POOLS:
        print(f"{name:36s}{d_pool['RF'][k]:+11.3f}{d_pool['RH'][k]:+11.3f}")
    for mg in ("RF", "RH"):
        assert abs(sum(d_pool[mg].values()) - dom_total[mg]) < 1e-6 * max(1.0, abs(dom_total[mg]))
    print(f"{'Total (= TOTECOSYSC difference)':36s}{dom_total['RF']:+11.3f}{dom_total['RH']:+11.3f}")
    insitu = {mg: dom_total[mg] - d_pool[mg]["prod"] for mg in ("RF", "RH")}
    diff = lambda mg, v: pg(maps[mg][v].astype("f8") - maps["Def"][v].astype("f8"), area, valid)
    d_extra = {mg: {"abg": diff(mg, "TOTVEGC_ABG"), "soc_0_100": diff(mg, "TOTSOMC_1m")} for mg in ("RF", "RH")}
    def_extra = {"abg": pg(maps["Def"]["TOTVEGC_ABG"], area, valid), "soc_0_100": pg(maps["Def"]["TOTSOMC_1m"], area, valid)}
    print(f"{'  of which aboveground vegetation':36s}{d_extra['RF']['abg']:+11.3f}{d_extra['RH']['abg']:+11.3f}")
    print(f"{'  of which SOC 0-100 cm':36s}{d_extra['RF']['soc_0_100']:+11.3f}{d_extra['RH']['soc_0_100']:+11.3f}")
    print("Boundaries (PgC)   aboveground | in-situ (excl. products) | ecosystem + products")
    for mg in ("RF", "RH"):
        print(f"  {mg}-Def  {d_extra[mg]['abg']:+.3f} | {insitu[mg]:+.3f} | {dom_total[mg]:+.3f}")
    print(f"  RF/RH ratio  {d_extra['RF']['abg'] / d_extra['RH']['abg']:.2f} | {insitu['RF'] / insitu['RH']:.2f} "
          f"| {dom_total['RF'] / dom_total['RH']:.2f}")
    print("  (RF = restoration + harvest ban everywhere; its difference also holds the SSP's own land-use drift)")

    # ---- trajectories 2024-2100 (4 km only: the Figure 2 totals exist at 4 km)
    have_traj = a.res == "4km" and all(os.path.exists(os.path.join(a.fig2_cache, f"{a.ssp}{s}__totals.npz")) for s in ("", "_RF", "_RH"))
    T = None
    if have_traj:
        T = traj_deltas(a.fig2_cache, cdir, a.ssp)
        end = T["year"] >= y0
        print(f"\nCross-check, mean {win} of the annual totals vs the maps (PgC):")
        for mg in ("RF", "RH"):
            dlt, tot, ext = T[mg]
            print(f"  {mg}: total {tot[end].mean():+.3f} vs {dom_total[mg]:+.3f}; soil {dlt['soil'][end].mean():+.3f} vs {d_pool[mg]['soil']:+.3f}; "
                  f"SOC 0-100 cm {ext['soc_0_100'][end].mean():+.3f} vs {d_extra[mg]['soc_0_100']:+.3f}")
            if abs(tot[end].mean() - dom_total[mg]) > 0.02:
                print(f"  WARNING: {mg} totals differ by more than 0.02 PgC between the two sources")
        print(f"{'RF - Default, PgC':24s}" + "".join(f"{y:>8d}" for y in (2030, 2050, 2075, 2100)))
        for k, _, _ in POOLS:
            print(f"  {POOL_LINE[k]:22s}" + "".join(f"{T['RF'][0][k][list(T['year']).index(y)]:+8.2f}" for y in (2030, 2050, 2075, 2100)))
        print(f"  {'Total':22s}" + "".join(f"{T['RF'][1][list(T['year']).index(y)]:+8.2f}" for y in (2030, 2050, 2075, 2100)))
        print(f"  {'(SOC 0-100 cm)':22s}" + "".join(f"{T['RF'][2]['soc_0_100'][list(T['year']).index(y)]:+8.2f}" for y in (2030, 2050, 2075, 2100)))
    else:
        print("\nNo 2024-2100 trajectories (needs 4 km and the Figure 2 totals); panels d-e skipped")

    os.makedirs(a.out_dir, exist_ok=True)
    tag = "pool_strata" if a.strata else "pools"
    base_name = f"fig4_{tag}_{a.res}_{a.ssp}_{win}"
    with open(os.path.join(a.out_dir, f"fig4_pools_{a.res}_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pool", "Default_PgC", "RF_minus_Default_PgC", "RH_minus_Default_PgC"])
        for k, name, _ in POOLS:
            w.writerow([name, f"{pg(P['Def'][k], area, valid):.5f}", f"{d_pool['RF'][k]:.5f}", f"{d_pool['RH'][k]:.5f}"])
        w.writerow(["Total", f"{sum(pg(P['Def'][k], area, valid) for k, _, _ in POOLS):.5f}",
                    f"{dom_total['RF']:.5f}", f"{dom_total['RH']:.5f}"])
        for k, name in (("abg", "of which: aboveground vegetation (TOTVEGC_ABG)"), ("soc_0_100", "of which: SOC 0-100 cm (TOTSOMC_1m)")):
            w.writerow([name, f"{def_extra[k]:.5f}", f"{d_extra['RF'][k]:.5f}", f"{d_extra['RH'][k]:.5f}"])
    if have_traj:
        with open(os.path.join(a.out_dir, f"fig4_pool_trajectories_{a.res}_{a.ssp}.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["mgmt", "pool", "year", "diff_vs_Default_PgC"])
            for mg in ("RF", "RH"):
                dlt, tot, ext = T[mg]
                for k in [p[0] for p in POOLS]:
                    w.writerows([[mg, k, int(y), f"{v:.5f}"] for y, v in zip(T["year"], dlt[k])])
                for k in ("abg", "soc_0_100"):
                    w.writerows([[mg, f"of_which_{k}", int(y), f"{v:.5f}"] for y, v in zip(T["year"], ext[k])])
                w.writerows([[mg, "total", int(y), f"{v:.5f}"] for y, v in zip(T["year"], tot)])

    foot = ("Four pools add up to TOTECOSYSC: living vegetation (TOTVEGC), dead wood and litter (CWDC + TOTLITC), soil organic carbon over the whole column (TOTSOMC), "
            "wood products derived as TOTECOSYSC − (TOTVEGC + CWDC + TOTLITC + TOTSOMC).\n"
            f"Within these: SOC 0–100 cm (TOTSOMC_1m) RF {d_extra['RF']['soc_0_100']:+.2f}, RH {d_extra['RH']['soc_0_100']:+.2f} PgC; "
            f"aboveground vegetation (panel c) RF {d_extra['RF']['abg']:+.2f}, RH {d_extra['RH']['abg']:+.2f} PgC. "
            "In-situ ecosystem = TOTECOSYSC − wood products.\n"
            "RF sets harvest to zero everywhere (restoration plus a region-wide harvest ban); its difference to Default also contains the SSP's own land-use drift. "
            f"Panels a-c: mean of {win}; d-e: annual domain totals. All sums are area × landfrac weighted.")
    nrows = 1 + int(have_traj) + int(a.strata)
    heights = [1.0] + ([1.0] if have_traj else []) + ([1.1] if a.strata else [])
    fig = plt.figure(figsize=(17, 5.0 * nrows + 0.9), facecolor=SURFACE)
    top, bottom = 1 - 0.75 / fig.get_figheight(), 1.2 / fig.get_figheight()
    gs = fig.add_gridspec(nrows, 12, height_ratios=heights, hspace=0.4, wspace=2.2, left=0.05, right=0.985, top=top, bottom=bottom)
    panel_a(fig.add_subplot(gs[0, 0:3]), P["Def"], area, valid)
    panel_b(fig.add_subplot(gs[0, 3:8]), P, area, valid)
    panel_c(fig.add_subplot(gs[0, 8:12]), P, area, valid, {mg: d_extra[mg]['abg'] for mg in ('RF', 'RH')})
    r = 1
    if have_traj:
        panel_traj(fig.add_subplot(gs[r, 0:5]), T["year"], T["RF"][0], T["RF"][1], "d", "RF − Default, 2024–2100")
        panel_traj(fig.add_subplot(gs[r, 6:11]), T["year"], T["RH"][0], T["RH"][1], "e", "RH − Default, 2024–2100 (own y axis)")
        r += 1
    if a.strata:
        import cartopy.crs as ccrs
        d_area = float(np.sum(inc[valid] * area[valid]))
        print(f"\n  RF tree-area increment ({a.rf_year} vs transient 2023): {d_area / 1e3:+.1f} x10^3 km2 "
              f"(4 km tree-PFT run output gave +142.3, notes 3.9)")
        n_neg = int((inc[valid] < -1e-3).sum())
        if n_neg:
            print(f"  WARNING: {n_neg} cells lose tree fraction (< -0.001) between 2023 and RF {a.rf_year}")
        strata = classify(inc, harv, a.rest_thr, a.harv_thr)
        rows = stratum_rows(P, F, strata, area, valid)
        for mg in ("RF", "RH"):
            sm = sum(rw[f"{mg}_total"] for rw in rows)
            assert abs(sm - dom_total[mg]) < 1e-6 * max(1.0, abs(dom_total[mg])), f"strata do not close for {mg}: {sm} vs {dom_total[mg]}"
        print(f"  closure: strata sum to the domain total (RF {dom_total['RF']:+.3f}, RH {dom_total['RH']:+.3f} PgC)")
        print(f"\nStrata (rest_thr {a.rest_thr}, harv_thr {a.harv_thr} gC/m2/yr), RF/RH - Default, window mean {win}:")
        print(f"{'stratum':26s}{'area 10^3km2':>13s}{'RF PgC':>9s}{'RF %':>6s}{'RF MgC/ha':>10s}{'RH PgC':>9s}{'RH MgC/ha':>10s}")
        for rw in rows:
            print(f"{rw['label']:26s}{rw['area_km2'] / 1e3:13.1f}{rw['RF_total']:+9.3f}{100 * rw['RF_total'] / dom_total['RF']:6.0f}"
                  f"{density(rw['RF_total'], rw['area_km2']):10.2f}{rw['RH_total']:+9.3f}{density(rw['RH_total'], rw['area_km2']):10.2f}")
        print("\nStratum fluxes RF - Default (PgC/yr; implied fire = NEP - LAND_USE_FLUX - NBP, D4 identity):")
        for rw in rows:
            f = rw["RF_fluxes"]
            print(f"  {rw['label']:26s} NBP {f['NBP']:+.4f}  NEP {f['NEP']:+.4f}  LUF {f['LAND_USE_FLUX']:+.4f}  "
                  f"harvest {f['WOOD_HARVESTC']:+.4f}  implied fire {f['NEP'] - f['LAND_USE_FLUX'] - f['NBP']:+.4f}")
        sens = []
        print("\nThreshold sensitivity (area 10^3 km2 | RF benefit share %) restoration / protection only / no change:")
        for rt in REST_SENS:
            for ht in HARV_SENS:
                rr = stratum_rows(P, F, classify(inc, harv, rt, ht), area, valid)
                sens.append((rt, ht, rr))
                print(f"  rest {rt:5.3f} harv {ht:5.2f}: " + " | ".join(
                    f"{x['area_km2'] / 1e3:6.1f} {100 * x['RF_total'] / dom_total['RF']:4.0f}%" for x in rr))
        extent = [float(lon.min()), float(lon.max()), float(lat.min()), float(lat.max())]
        panel_map(fig.add_subplot(gs[r, 0:4], projection=ccrs.PlateCarree()), lon, lat, strata, valid, extent)
        sub = gs[r, 4:7].subgridspec(2, 1, hspace=0.25)
        panel_strata_bars(fig.add_subplot(sub[0]), fig.add_subplot(sub[1]), rows)
        panel_strata_pools(fig.add_subplot(gs[r, 7:12]), rows)
        foot += (f"\nStrata from RF land cover (tree fraction {a.rf_year} − 2023 ≥ {a.rest_thr:g}) and Default harvest "
                 f"(≥ {a.harv_thr:g} gC/m²/yr); the restoration stratum is restoration plus the harvest ban, not restoration alone.")
        with open(os.path.join(a.out_dir, base_name + "_strata.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["stratum", "area_km2", "mgmt", "total_PgC", "MgC_per_ha"] + [k for k, _, _ in POOLS] + [f"d{v}_PgC_per_yr" for v in FLUX_VARS])
            for rw in rows:
                for mg in ("RF", "RH"):
                    w.writerow([rw["label"], f"{rw['area_km2']:.1f}", mg, f"{rw[mg + '_total']:.5f}",
                                f"{density(rw[mg + '_total'], rw['area_km2']):.4f}"]
                               + [f"{rw[mg + '_pools'][k]:.5f}" for k, _, _ in POOLS]
                               + [f"{rw[mg + '_fluxes'][v]:.5f}" for v in FLUX_VARS])
        with open(os.path.join(a.out_dir, base_name + "_sensitivity.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rest_thr", "harv_thr_gC_m2_yr", "stratum", "area_km2", "RF_PgC", "RF_share_pct", "RH_PgC"])
            for rt, ht, rr in sens:
                for x in rr:
                    w.writerow([rt, ht, x["label"], f"{x['area_km2']:.1f}", f"{x['RF_total']:.5f}",
                                f"{100 * x['RF_total'] / dom_total['RF']:.2f}", f"{x['RH_total']:.5f}"])

    fig.suptitle(f"SEUS {a.res} {a.ssp}: which pools carry the management benefit, and when (RF, RH − Default)",
                 fontsize=13, color=INK, x=0.05, y=1 - 0.2 / fig.get_figheight(), ha="left")
    fig.text(0.05, 0.12 / fig.get_figheight(), foot, fontsize=8.6, color=INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, base_name + ".png")
    fig.savefig(png, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    print(f"\nwrote {png}")


if __name__ == "__main__":
    main()
