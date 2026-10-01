"""
Main Figure 4 / Results 3.3 (blueprint E4): which carbon pools carry the
management benefit, and what part of the RF benefit comes from cells where RF
restores forest versus cells where it only stops harvest.

Panels (one SSP, one resolution, one window; defaults SSP3-7.0, 2091-2100):
  a  Default stock composition by pool, PgC (existing stocks)
  b  signed pool contributions to RF - Default and RH - Default, PgC
  c  the same benefits at three boundaries: aboveground vegetation, in-situ
     ecosystem (excl. products), ecosystem + products (= TOTECOSYSC)
  d  restoration / protection strata of RF: map, area and benefit per stratum,
     and the signed pool response per stratum (MgC/ha of stratum land)

Pools (D4): aboveground vegetation = TOTVEGC_ABG; other vegetation = TOTVEGC -
TOTVEGC_ABG (roots plus storage/transfer pools); CWDC; TOTLITC; TOTSOMC;
wood products = TOTECOSYSC - (TOTVEGC + CWDC + TOTLITC + TOTSOMC), derived because
TOTPRODC is not in h0. The six pools sum to TOTECOSYSC by construction, so the
check that matters is that the derived product term is plausible: it is printed
for every run and must be >= 0 in Default.

Strata, fixed from RF's land cover and Default's harvest BEFORE any carbon
benefit is looked at (user decision 2026-10-01: scheme 1, no NH run):
  increment  = RF tree fraction in a plateau year (default 2060)
               - transient 2023 tree fraction            (fraction of gridcell land)
  restoration     increment >= REST_THR  (default 0.01 of the cell)
  protection only increment <  REST_THR and Default WOOD_HARVESTC >= HARV_THR
                  (default 0.1 gC/m2/yr, window mean)
  no change       everything else (should show benefit ~0: the null control)
CAVEAT, repeated on the figure: RF also sets harvest to zero everywhere, so the
restoration stratum is restoration PLUS the harvest ban, not restoration alone.
A pure split needs the NH run (PCT_NAT_PFT = Default, HARVEST = 0): then
NH - Default is the ban and RF - NH the restoration under protection. RF - Default
also absorbs the SSP's own land-use drift (RF replaces the land trajectory).
Mixed cells (part restored) are classified by the threshold only; the printed
sensitivity table varies both thresholds.

All sums are area x landfrac weighted (never cell counts, never bare means).

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \\
        code/figure4/plot_pool_strata.py --res 4km [--ssp SSP3-7.0] [--years 2091-2100]
Inputs (pulled from proj-shared, git-ignored), made by extract_pool_maps.py and
extract_tree_fraction.py, in _cache/figure4/<res>/ :
    <SSP>__pools_<y0>-<y1>.npz  <SSP>_RF__pools_...  <SSP>_RH__pools_...
    transient__treefrac_2023.npz  <SSP>_RF__treefrac_<rf-year>.npz
Outputs: figures/figure4/fig4_pool_strata_<res>_<SSP>_<y0>-<y1>.png and three
CSVs (strata, threshold sensitivity, strata fluxes) next to it.
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
POOLS = [("abg", "Aboveground vegetation", "#1baf7a"),
         ("veg_other", "Other vegetation (roots, storage)", "#eda100"),
         ("cwd", "Coarse woody debris", "#e87ba4"),
         ("lit", "Litter", "#008300"),
         ("soc", "Soil organic carbon", "#4a3aa7"),
         ("prod", "Wood products (derived)", "#e34948")]
POOL_SHORT = {"abg": "Aboveground\nvegetation", "veg_other": "Other\nvegetation", "cwd": "CWD",
              "lit": "Litter", "soc": "SOC", "prod": "Products"}
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
    """Six pools in gC/m2 from the h0 stock maps (D4 closure, products derived)."""
    prod = m["TOTECOSYSC"] - (m["TOTVEGC"] + m["CWDC"] + m["TOTLITC"] + m["TOTSOMC"])
    return {"abg": m["TOTVEGC_ABG"], "veg_other": m["TOTVEGC"] - m["TOTVEGC_ABG"], "cwd": m["CWDC"],
            "lit": m["TOTLITC"], "soc": m["TOTSOMC"], "prod": prod}


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
    ax.set_xticklabels([POOL_SHORT[k] for k in keys] + ["Total"], fontsize=8.8)
    style(ax, "Change vs Default (PgC)")
    lo, hi = min(0, min(vals["RF"] + vals["RH"])), max(0, max(vals["RF"] + vals["RH"]))
    ax.set_ylim(lo - 0.08 * (hi - lo), hi + 0.22 * (hi - lo))
    ax.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=2)
    ptitle(ax, "b", "Signed pool contributions")
    return vals


def panel_c(ax, P, area, valid):
    def bounds(mg):
        d = {k: pg(P[mg][k] - P["Def"][k], area, valid) for k, _, _ in POOLS}
        return [d["abg"], d["abg"] + d["veg_other"] + d["cwd"] + d["lit"] + d["soc"], sum(d.values())]
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
    ptitle(ax_proj, "d", "RF strata")
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
    ptitle(ax_area, "e", "Area and benefit by stratum")


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
    ptitle(ax, "f", "Pool response by stratum")


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="4km", choices=["4km", "0.5deg"])
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--strata", action="store_true",
                    help="add the restoration/protection strata (panels d-f); needs the tree-fraction extracts")
    ap.add_argument("--rf-year", type=int, default=2060, help="plateau year of the RF run for the land-cover increment")
    ap.add_argument("--rest-thr", type=float, default=0.01)
    ap.add_argument("--harv-thr", type=float, default=0.1)
    ap.add_argument("--cache-root", default=os.path.join(ROOT, "_cache/figure4"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "figures/figure4"))
    a = ap.parse_args()

    cdir = os.path.join(a.cache_root, a.res)
    win = a.years
    runs = {"Def": a.ssp, "RF": f"{a.ssp}_RF", "RH": f"{a.ssp}_RH"}
    maps = {k: load(os.path.join(cdir, f"{t}__pools_{win}.npz")) for k, t in runs.items()}
    extra = {}
    if a.strata:
        extra = {"base": load(os.path.join(cdir, "transient__treefrac_2023.npz")),
                 "rfcov": load(os.path.join(cdir, f"{a.ssp}_RF__treefrac_{a.rf_year}.npz"))}
    for k, m in list(maps.items()) + list(extra.items()):
        for g in ("lat", "lon", "area_km2"):
            assert np.array_equal(m[g], maps["Def"][g]), f"{k}: {g} differs from the Default run's grid"
    lat, lon, area = maps["Def"]["lat"], maps["Def"]["lon"], maps["Def"]["area_km2"].astype("f8")
    lon = np.where(lon > 180, lon - 360, lon)

    # float32 stocks of ~3e4 gC/m2 carry ~2e-3 gC/m2 rounding: add them in float64
    P = {k: pools_of({v: m[v].astype("f8") for v in ("TOTECOSYSC", "TOTVEGC", "TOTVEGC_ABG", "CWDC", "TOTLITC", "TOTSOMC")})
         for k, m in maps.items()}
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
        pr = pg(P[k]["prod"], area, valid)
        print(f"  derived product pool {k:3s}: {pr:+.4f} PgC  (min per cell {P[k]['prod'][valid].min():+.2f} gC/m2)")
    assert pg(P["Def"]["prod"], area, valid) >= -1e-3, \
        "derived product pool of Default is negative: TOTPRODC is not in TOTECOSYSC here, re-check D4"
    dom_total = {mg: pg(maps[mg]["TOTECOSYSC"].astype("f8") - maps["Def"]["TOTECOSYSC"].astype("f8"), area, valid)
                 for mg in ("RF", "RH")}

    # ---- pool table (always): stocks, signed contributions, three boundaries
    print(f"\nDefault stock {win} (PgC): " + ", ".join(f"{n.split(' (')[0]} {pg(P['Def'][k], area, valid):.2f}" for k, n, _ in POOLS))
    print(f"{'pool':36s}{'RF-Def PgC':>11s}{'RH-Def PgC':>11s}")
    pool_rows = []
    for k, name, _ in POOLS:
        d = {mg: pg(P[mg][k] - P["Def"][k], area, valid) for mg in ("RF", "RH")}
        pool_rows.append((name, d["RF"], d["RH"]))
        print(f"{name:36s}{d['RF']:+11.3f}{d['RH']:+11.3f}")
    for mg in ("RF", "RH"):
        assert abs(sum(r[1 if mg == 'RF' else 2] for r in pool_rows) - dom_total[mg]) < 1e-6 * max(1.0, abs(dom_total[mg]))
    agb = {mg: pool_rows[0][1 if mg == "RF" else 2] for mg in ("RF", "RH")}
    prod = {mg: pool_rows[5][1 if mg == "RF" else 2] for mg in ("RF", "RH")}
    print(f"{'Total (= TOTECOSYSC difference)':36s}{dom_total['RF']:+11.3f}{dom_total['RH']:+11.3f}")
    print("Boundaries (PgC)   aboveground | in-situ (excl. products) | ecosystem + products")
    for mg in ("RF", "RH"):
        print(f"  {mg}-Def  {agb[mg]:+.3f} | {dom_total[mg] - prod[mg]:+.3f} | {dom_total[mg]:+.3f}")
    print(f"  RF/RH ratio  {agb['RF'] / agb['RH']:.2f} | {(dom_total['RF'] - prod['RF']) / (dom_total['RH'] - prod['RH']):.2f} "
          f"| {dom_total['RF'] / dom_total['RH']:.2f}")
    print("  (RF = restoration + harvest ban everywhere; its difference also holds the SSP's own land-use drift)")

    os.makedirs(a.out_dir, exist_ok=True)
    tag = "pool_strata" if a.strata else "pools"
    base_name = f"fig4_{tag}_{a.res}_{a.ssp}_{win}"
    with open(os.path.join(a.out_dir, f"fig4_pools_{a.res}_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pool", "Default_PgC", "RF_minus_Default_PgC", "RH_minus_Default_PgC"])
        for (name, rf, rh), (k, _, _) in zip(pool_rows, POOLS):
            w.writerow([name, f"{pg(P['Def'][k], area, valid):.5f}", f"{rf:.5f}", f"{rh:.5f}"])
        w.writerow(["Total", f"{sum(pg(P['Def'][k], area, valid) for k, _, _ in POOLS):.5f}",
                    f"{dom_total['RF']:.5f}", f"{dom_total['RH']:.5f}"])

    foot_pools = ("Pools sum to TOTECOSYSC; wood products derived as TOTECOSYSC − (TOTVEGC + CWDC + TOTLITC + TOTSOMC). "
                  "Other vegetation = TOTVEGC − TOTVEGC_ABG (roots plus storage/transfer pools).\n"
                  "RF sets harvest to zero everywhere (restoration plus a region-wide harvest ban) and its difference to Default "
                  "also contains the SSP's own land-use drift. All sums are area × landfrac weighted.")
    import cartopy.crs as ccrs

    if not a.strata:
        fig = plt.figure(figsize=(17, 5.6), facecolor=SURFACE)
        gs = fig.add_gridspec(1, 12, wspace=2.2, left=0.05, right=0.985, top=0.84, bottom=0.2)
        panel_a(fig.add_subplot(gs[0, 0:3]), P["Def"], area, valid)
        panel_b(fig.add_subplot(gs[0, 3:8]), P, area, valid)
        panel_c(fig.add_subplot(gs[0, 8:12]), P, area, valid)
        fig.suptitle(f"SEUS {a.res} {a.ssp}, {win}: which pools carry the management benefit (RF, RH − Default)",
                     fontsize=13, color=INK, x=0.05, ha="left")
        fig.text(0.05, 0.015, foot_pools, fontsize=8.6, color=INK2, va="bottom", ha="left")
        png = os.path.join(a.out_dir, base_name + ".png")
        fig.savefig(png, dpi=170, facecolor=SURFACE)
        plt.close(fig)
        print(f"\nwrote {png} and the pool CSV")
        return

    # ---- strata (restoration / protection), panels d-f
    d_area = float(np.sum(inc[valid] * area[valid]))
    print(f"\n  RF tree-area increment ({a.rf_year} vs transient 2023): {d_area / 1e3:+.1f} x10^3 km2 "
          f"(4 km tree-PFT run output gave +142.3, notes 3.9)")
    n_neg = int((inc[valid] < -1e-3).sum())
    if n_neg:
        print(f"  WARNING: {n_neg} cells lose tree fraction (< -0.001) between 2023 and RF {a.rf_year}")
    strata = classify(inc, harv, a.rest_thr, a.harv_thr)
    rows = stratum_rows(P, F, strata, area, valid)
    for mg in ("RF", "RH"):
        sm = sum(r[f"{mg}_total"] for r in rows)
        assert abs(sm - dom_total[mg]) < 1e-6 * max(1.0, abs(dom_total[mg])), f"strata do not close for {mg}: {sm} vs {dom_total[mg]}"
    print(f"  closure: strata sum to the domain total (RF {dom_total['RF']:+.3f}, RH {dom_total['RH']:+.3f} PgC)")

    print(f"\nStrata (rest_thr {a.rest_thr}, harv_thr {a.harv_thr} gC/m2/yr), RF/RH - Default, window mean {win}:")
    print(f"{'stratum':26s}{'area 10^3km2':>13s}{'RF PgC':>9s}{'RF %':>6s}{'RF MgC/ha':>10s}{'RH PgC':>9s}{'RH MgC/ha':>10s}")
    for r in rows:
        print(f"{r['label']:26s}{r['area_km2'] / 1e3:13.1f}{r['RF_total']:+9.3f}{100 * r['RF_total'] / dom_total['RF']:6.0f}"
              f"{density(r['RF_total'], r['area_km2']):10.2f}{r['RH_total']:+9.3f}{density(r['RH_total'], r['area_km2']):10.2f}")

    print("\nStratum fluxes RF - Default (PgC/yr; implied fire = NEP - LAND_USE_FLUX - NBP, D4 identity):")
    for r in rows:
        f = r["RF_fluxes"]
        print(f"  {r['label']:26s} NBP {f['NBP']:+.4f}  NEP {f['NEP']:+.4f}  LUF {f['LAND_USE_FLUX']:+.4f}  "
              f"harvest {f['WOOD_HARVESTC']:+.4f}  implied fire {f['NEP'] - f['LAND_USE_FLUX'] - f['NBP']:+.4f}")

    sens = []
    print("\nThreshold sensitivity (area 10^3 km2 | RF benefit share %) restoration / protection only / no change:")
    for rt in REST_SENS:
        for ht in HARV_SENS:
            rr = stratum_rows(P, F, classify(inc, harv, rt, ht), area, valid)
            sens.append((rt, ht, rr))
            print(f"  rest {rt:5.3f} harv {ht:5.2f}: " + " | ".join(
                f"{r['area_km2'] / 1e3:6.1f} {100 * r['RF_total'] / dom_total['RF']:4.0f}%" for r in rr))

    fig = plt.figure(figsize=(17, 10.2), facecolor=SURFACE)
    gs = fig.add_gridspec(2, 12, hspace=0.42, wspace=2.2, left=0.05, right=0.985, top=0.93, bottom=0.12)
    panel_a(fig.add_subplot(gs[0, 0:3]), P["Def"], area, valid)
    panel_b(fig.add_subplot(gs[0, 3:8]), P, area, valid)
    panel_c(fig.add_subplot(gs[0, 8:12]), P, area, valid)
    extent = [float(lon.min()), float(lon.max()), float(lat.min()), float(lat.max())]
    panel_map(fig.add_subplot(gs[1, 0:4], projection=ccrs.PlateCarree()), lon, lat, strata, valid, extent)
    sub = gs[1, 4:7].subgridspec(2, 1, hspace=0.25)
    panel_strata_bars(fig.add_subplot(sub[0]), fig.add_subplot(sub[1]), rows)
    panel_strata_pools(fig.add_subplot(gs[1, 7:12]), rows)
    fig.suptitle(f"SEUS {a.res} {a.ssp}, {win}: where the management benefit sits (RF, RH − Default)",
                 fontsize=13, color=INK, x=0.05, ha="left")
    fig.text(0.05, 0.015,
             foot_pools + f"\nStrata from RF land cover (tree fraction {a.rf_year} − 2023 ≥ {a.rest_thr:g}) and Default harvest "
             f"(≥ {a.harv_thr:g} gC/m²/yr); the restoration stratum is restoration plus the harvest ban, not restoration alone.",
             fontsize=8.6, color=INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, base_name + ".png")
    fig.savefig(png, dpi=170, facecolor=SURFACE)
    plt.close(fig)

    with open(os.path.join(a.out_dir, base_name + "_strata.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stratum", "area_km2", "mgmt", "total_PgC", "MgC_per_ha"] + [k for k, _, _ in POOLS] + [f"d{v}_PgC_per_yr" for v in FLUX_VARS])
        for r in rows:
            for mg in ("RF", "RH"):
                w.writerow([r["label"], f"{r['area_km2']:.1f}", mg, f"{r[mg + '_total']:.5f}",
                            f"{density(r[mg + '_total'], r['area_km2']):.4f}"]
                           + [f"{r[mg + '_pools'][k]:.5f}" for k, _, _ in POOLS]
                           + [f"{r[mg + '_fluxes'][v]:.5f}" for v in FLUX_VARS])
    with open(os.path.join(a.out_dir, base_name + "_sensitivity.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rest_thr", "harv_thr_gC_m2_yr", "stratum", "area_km2", "RF_PgC", "RF_share_pct", "RH_PgC"])
        for rt, ht, rr in sens:
            for r in rr:
                w.writerow([rt, ht, r["label"], f"{r['area_km2']:.1f}", f"{r['RF_total']:.5f}",
                            f"{100 * r['RF_total'] / dom_total['RF']:.2f}", f"{r['RH_total']:.5f}"])
    print(f"\nwrote {png} and three CSVs")


if __name__ == "__main__":
    main()
