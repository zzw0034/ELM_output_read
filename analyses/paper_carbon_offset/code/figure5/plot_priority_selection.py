"""
Main Figure 5 / Results 3.4 (blueprint E5, D9): does finer information change where management
is prioritized, and at what risk? Equal-area selection with the native 4 km map against the
native 0.5 deg map (user decision 2026-10-01: no 4 km-averaged comparator), before and after a
risk screen. RF, SSP3-7.0, end state = mean of 2091-2100.

Benefit (Figure 3/4): TOTECOSYSC difference RF - Default (36000 s), MgC/ha of land. It is a stock
difference, not NBP. RF is restoration plus a region-wide harvest ban and contains the SSP's own
land-use drift.

Eligible land, fixed before looking at benefits: RF's plateau forest, i.e. the RF tree fraction in
2060 of each cell (existing forest plus restorable grass), from each run's own h1 output. Cells
with an eligible fraction below FLOOR (default 0.05) are not eligible, because the benefit per
eligible hectare b = benefit / eligible fraction blows up there. Eligible area a = area x landfrac x
eligible fraction.

Selection for a budget of p % of the total 4 km eligible area E (common support: 4 km cells inside
valid 0.5 deg land cells):
  4 km     rank eligible 4 km cells by b, take cells until the budget is met, the last one fractionally.
  0.5 deg  rank eligible 0.5 deg cells by the 0.5 deg run's own b, take whole cells; a cell's area is
           the 4 km eligible area inside it (so both selections are the same physical area); the last
           cell is taken fractionally (all its 4 km cells scaled), never by choosing pixels inside it.
  Ties: stable sort by grid index (row-major), fixed before looking.
Scoring, always on the 4 km field: captured benefit G = sum w a b (w = selected fraction); loss from
coarse information (G_4km - G_0.5)/G_4km; benefit per selected hectare; area overlap (both / 4 km
only / 0.5 deg only); 4 km risk of the selected land. In sample the 4 km selection is best by
construction: the result measures model-internal information lost at 0.5 deg, not a real-world gain.

Risk components (D7), from the RF run, 2091-2100, used separately (no composite). Only fire loss and water
stress are used (user decision 2026-10-01): NBP variability was dropped because about half of it is fire
(rank correlation 0.83 with the fire component, notes 3.18).
  fire          mean(NEP - LAND_USE_FLUX - NBP) / mean(TOTECOSYSC), %/yr (complete column fire loss from
                the D4 identity; 4 km fire has ~0.5 deg effective resolution, blueprint A3)
  water stress  1 - BTRAN averaged over April-October (user decision 2026-10-01)
Screen (D9 B): one absolute threshold per component, the area-weighted PCT-th percentile (default 80,
user decision 2026-10-01; 90 and 95 as sensitivity) of the 4 km component over all eligible land,
shared by both resolutions. 4 km excludes 4 km cells above it, 0.5 deg excludes 0.5 deg cells whose
0.5 deg run value is above it; both then fill the same budget and are scored with 4 km benefit and
4 km risk. If the screened land cannot fill the budget, the shortfall is reported, the threshold is
not relaxed. Screens: each component alone, and both together.

Fixed thresholds (--thresholds FIRE WATER, user decision 2026-10-02 for the cross-SSP set: the SSP3-7.0 p80
applied to every SSP) replace the main percentile thresholds; the --sens percentiles stay each SSP's own.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_priority_selection.py [--ssp SSP3-7.0]
        [--thresholds FIRE WATER --threshold-label "SSP3-7.0 p80"]
Inputs (git-ignored):
    _cache/figure4/4km/SSP3-7.0{,_RF}__pools_2091-2100.npz, _cache/figure3/0.5deg/SSP3-7.0{,_RF}__pools_2091-2100.npz
    _cache/figure4/4km/SSP3-7.0_RF__treefrac_2060.npz, _cache/figure5/0.5deg/SSP3-7.0_RF__treefrac_2060.npz
    _cache/figure5/{4km,0.5deg}/SSP3-7.0_RF__annual_2091-2100.npz          (extract_annual_maps.py)
Outputs: figures/figure5/fig5_priority_<SSP>_<window>.png and CSVs (selections, budget curve, per-cell classes).
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, Normalize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # analysis root
N = 12
INK, INK2, GRID, SURFACE, BAD = "#0b0b0b", "#52514e", "#e9e8e4", "#fcfcfb", "#dfe3e8"
RES_COL = {"4km": "#1baf7a", "0.5deg": "#e87ba4"}          # as C and A in Figure 3
RES_LAB = {"4km": "4 km", "0.5deg": "0.5°"}
CLS_COLS = ["#e1e0dc", "#1baf7a", "#e87ba4", "#4a3aa7"]     # neither, 4 km only (4 km colour), 0.5 deg only (0.5 deg colour), both
CLS_NAMES = ["Eligible, not selected", "4 km only", "0.5° only", "Both"]
COMPONENTS = [("fire", "Fire loss (%/yr)"), ("water", "Water stress (1 − BTRAN, Apr–Oct)")]
SCREENS = [("none", "No screen"), ("fire", "Fire"), ("water", "Water stress"), ("all", "Fire + water")]


# ---------------------------------------------------------------------- helpers

def load(path):
    assert os.path.exists(path), f"missing input {path}"
    z = np.load(path, allow_pickle=True)
    return {k: z[k] for k in z.files}


def block_sum(x):
    ny, nx = x.shape[0] // N, x.shape[1] // N
    return x.reshape(ny, N, nx, N).sum(axis=(1, 3))


def to_children(x):
    return np.repeat(np.repeat(x, N, axis=0), N, axis=1)


def wquantile(x, w, q):
    o = np.argsort(x, kind="stable")
    xs, ws = x[o], w[o]
    c = (np.cumsum(ws) - 0.5 * ws) / ws.sum()
    return float(np.interp(q, c, xs))


def take(order_vals, areas, budget):
    """Selected fraction per item: rank by value (descending, stable), fill `budget` area, last item fractional.
    Returns (fraction array, selected area)."""
    frac = np.zeros(len(areas))
    order = np.argsort(-order_vals, kind="stable")
    cum = np.cumsum(areas[order])
    k = int(np.searchsorted(cum, budget))
    frac[order[:k]] = 1.0
    if k < len(order):
        prev = cum[k - 1] if k > 0 else 0.0
        frac[order[k]] = (budget - prev) / areas[order[k]]
    return frac, float(min(budget, cum[-1] if len(cum) else 0.0))


def risk_components(ann):
    """fire (%/yr) and water stress from an annual-map extract (year, lat, lon)."""
    fire = (ann["NEP"] - ann["LAND_USE_FLUX"] - ann["NBP"]).astype("f8").mean(0) / ann["TOTECOSYSC"].astype("f8").mean(0) * 100
    water = 1 - ann["BTRAN_GS"].astype("f8").mean(0)
    return {"fire": fire, "water": water}


# ------------------------------------------------------------------- the model

def build(a):
    win = a.years
    p4 = {k: load(os.path.join(a.cache_4km, f"{a.ssp}{s}__pools_{win}.npz")) for k, s in (("Def", ""), ("RF", "_RF"))}
    p5 = {k: load(os.path.join(a.cache_05, f"{a.ssp}{s}__pools_{win}.npz")) for k, s in (("Def", ""), ("RF", "_RF"))}
    t4 = load(os.path.join(a.cache_4km, f"{a.ssp}_RF__treefrac_2060.npz"))
    t5 = load(os.path.join(a.risk_cache, "0.5deg", f"{a.ssp}_RF__treefrac_2060.npz"))
    r4 = load(os.path.join(a.risk_cache, "4km", f"{a.ssp}_RF__annual_{win}.npz"))
    r5 = load(os.path.join(a.risk_cache, "0.5deg", f"{a.ssp}_RF__annual_{win}.npz"))
    for z in (p4["RF"], t4, r4):
        assert np.array_equal(z["area_km2"], p4["Def"]["area_km2"]), "4 km grids differ"
    for z in (p5["RF"], t5, r5):
        assert np.array_equal(z["area_km2"], p5["Def"]["area_km2"]), "0.5 deg grids differ"
    lat4, lat5 = p4["Def"]["lat"].astype("f8"), p5["Def"]["lat"].astype("f8")
    lon4 = np.where(p4["Def"]["lon"] > 180, p4["Def"]["lon"] - 360, p4["Def"]["lon"]).astype("f8")
    lon5 = np.where(p5["Def"]["lon"] > 180, p5["Def"]["lon"] - 360, p5["Def"]["lon"]).astype("f8")
    A4, A5 = p4["Def"]["area_km2"].astype("f8"), p5["Def"]["area_km2"].astype("f8")
    assert A4.shape == (len(lat5) * N, len(lon5) * N), "grids do not nest"
    assert np.allclose(lat4.reshape(-1, N).mean(1), lat5, atol=1e-4) and np.allclose(lon4.reshape(-1, N).mean(1), lon5, atol=1e-4)

    g4 = (p4["RF"]["TOTECOSYSC"].astype("f8") - p4["Def"]["TOTECOSYSC"].astype("f8")) * 0.01   # MgC/ha of land
    g5 = (p5["RF"]["TOTECOSYSC"].astype("f8") - p5["Def"]["TOTECOSYSC"].astype("f8")) * 0.01
    e4, e5 = t4["tree_frac"].astype("f8"), t5["tree_frac"].astype("f8")
    R4, R5 = risk_components(r4), risk_components(r5)

    land5 = (A5 > 0) & np.isfinite(g5)
    ok5 = land5 & np.isfinite(e5) & (e5 >= a.floor) & np.all([np.isfinite(R5[k]) for k, _ in COMPONENTS], axis=0)
    ok4 = (A4 > 0) & np.isfinite(g4) & np.isfinite(e4) & (e4 >= a.floor) & to_children(land5) \
        & np.all([np.isfinite(R4[k]) for k, _ in COMPONENTS], axis=0)
    a4 = np.where(ok4, A4 * e4, 0.0)                                  # eligible km2
    b4 = np.where(ok4, g4 / np.where(ok4, e4, 1.0), np.nan)           # MgC/ha of eligible land
    b5 = np.where(ok5, g5 / np.where(ok5, e5, 1.0), np.nan)
    ac = np.where(ok5, block_sum(a4), 0.0)                            # 4 km eligible area inside each 0.5 deg cell
    return dict(lat4=lat4, lon4=lon4, lat5=lat5, lon5=lon5, a4=a4, b4=b4, b5=b5, ac=ac, ok4=ok4, ok5=ok5 & (ac > 0),
                R4=R4, R5=R5, E=float(a4.sum()), g4=g4, e4=e4)


def select(m, budget, screen=None, T=None):
    """4 km and 0.5 deg selection weights on the 4 km grid for one budget (km2) and optional screen."""
    keep4, keep5 = m["ok4"].copy(), m["ok5"].copy()
    if screen and screen != "none":
        comps = [k for k, _ in COMPONENTS] if screen == "all" else [screen]
        for k in comps:
            keep4 &= m["R4"][k] <= T[k]
            keep5 &= m["R5"][k] <= T[k]
    i4 = np.flatnonzero(keep4.ravel())
    f4, s4 = take(m["b4"].ravel()[i4], m["a4"].ravel()[i4], budget)
    w4 = np.zeros(m["a4"].size)
    w4[i4] = f4
    i5 = np.flatnonzero(keep5.ravel())
    f5, s5 = take(m["b5"].ravel()[i5], m["ac"].ravel()[i5], budget)
    wc = np.zeros(m["ac"].size)
    wc[i5] = f5
    w5 = to_children(wc.reshape(m["ac"].shape)) * m["ok4"]
    return w4.reshape(m["a4"].shape), w5, s4, s5


def score(m, w, T):
    a, b = m["a4"], np.nan_to_num(m["b4"])
    area = float((w * a).sum())
    G = float((w * a * b).sum()) * 100 / 1e9                # km2 x MgC/ha x 100 ha/km2 -> MgC -> PgC
    out = {"area_km2": area, "G_PgC": G, "per_ha": G * 1e9 / (area * 100) if area > 0 else np.nan}
    for k, _ in COMPONENTS:
        r = np.nan_to_num(m["R4"][k])
        out[f"mean_{k}"] = float((w * a * r).sum() / area) if area > 0 else np.nan
        out[f"exceed_{k}"] = float((w * a * (m["R4"][k] > T[k])).sum() / area) if area > 0 else np.nan
    anyx = np.any([m["R4"][k] > T[k] for k, _ in COMPONENTS], axis=0)
    out["exceed_any"] = float((w * a * anyx).sum() / area) if area > 0 else np.nan
    return out


def overlap(m, w4, w5):
    both = np.minimum(w4, w5)
    a = m["a4"]
    return float((both * a).sum()), float(((w4 - both) * a).sum()), float(((w5 - both) * a).sum())


# ---------------------------------------------------------------------- drawing

def style(ax, ylabel=None, xlabel=None):
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=10)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK, fontsize=10)
    ax.grid(axis="y", color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=9, length=3.5)


def ptitle(ax, letter, text):
    ax.set_title(f"{letter}  {text}", loc="left", fontsize=11, color=INK, fontweight="bold")


def class_map(m, w4, w5):
    sel4, sel5 = w4 > 0, w5 > 0
    cls = np.where(sel4 & sel5, 3, np.where(sel4, 1, np.where(sel5, 2, 0))).astype("f8")
    return np.where(m["ok4"], cls, np.nan)


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--floor", type=float, default=0.05, help="minimum eligible fraction of a cell")
    ap.add_argument("--pct", type=float, default=80, help="threshold percentile (main)")
    ap.add_argument("--sens", type=float, nargs="*", default=[90, 95], help="threshold percentiles (sensitivity)")
    ap.add_argument("--budgets", type=float, nargs="*", default=[20, 30])
    ap.add_argument("--thresholds", type=float, nargs=2, metavar=("FIRE", "WATER"),
                    help="fixed absolute main thresholds instead of this SSP's own p<pct> (sensitivity percentiles stay this SSP's own)")
    ap.add_argument("--threshold-label", default=None, help="how the fixed thresholds were derived, e.g. 'SSP3-7.0 p80'")
    ap.add_argument("--cache-4km", default=os.path.join(ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--risk-cache", default=os.path.join(ROOT, "_cache/figure5"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "figures/figure5"))
    a = ap.parse_args()
    m = build(a)
    win = a.years
    os.makedirs(a.out_dir, exist_ok=True)
    elig_all = m["a4"] > 0
    print(f"{a.ssp} {win}: eligible 4 km land {m['E'] / 1e3:.1f} x10^3 km2 in {int(elig_all.sum())} cells (floor {a.floor}); "
          f"eligible 0.5 deg cells {int(m['ok5'].sum())}")
    tot = float((m["a4"] * np.nan_to_num(m["b4"])).sum()) * 100 / 1e9
    print(f"total benefit on eligible 4 km land {tot:.3f} PgC")

    def thresholds(pct):
        if a.thresholds and pct == a.pct:
            return dict(zip(("fire", "water"), a.thresholds))
        return {k: wquantile(m["R4"][k][elig_all], m["a4"][elig_all], pct / 100) for k, _ in COMPONENTS}

    T = thresholds(a.pct)
    tlab = (a.threshold_label or "fixed") if a.thresholds else f"p{a.pct:g}"
    print(f"thresholds ({'fixed: ' + tlab if a.thresholds else f'4 km eligible, area-weighted p{a.pct:g}'}): "
          + ", ".join(f"{k} {v:.4g}" for k, v in T.items()) + "; eligible land above: "
          + ", ".join(f"{k} {100 * m['a4'][elig_all & (m['R4'][k] > T[k])].sum() / m['E']:.1f}%" for k, _ in COMPONENTS))

    # ---- selections for every budget, screen and threshold percentile
    rows = []
    res = {}
    for pct in [a.pct] + list(a.sens):
        Tp = thresholds(pct)
        for p in a.budgets:
            budget = p / 100 * m["E"]
            base = {}
            for sname, _ in SCREENS:
                w4, w5, s4, s5 = select(m, budget, sname, Tp)
                sc4, sc5 = score(m, w4, Tp), score(m, w5, Tp)
                both, only4, only5 = overlap(m, w4, w5)
                if sname == "none":
                    base = {"4km": sc4["G_PgC"], "0.5deg": sc5["G_PgC"]}
                for res_name, sc, sel_area in (("4km", sc4, s4), ("0.5deg", sc5, s5)):
                    row = {"pct": pct, "budget_pct": p, "screen": sname, "res": res_name, "budget_km2": budget,
                           "shortfall_km2": budget - sel_area, **sc,
                           "forgone_vs_noscreen": (base[res_name] - sc["G_PgC"]) / base[res_name] if base else np.nan,
                           "overlap_both_km2": both, "only_4km_km2": only4, "only_05_km2": only5}
                    rows.append(row)
                res[(pct, p, sname)] = (w4, w5, sc4, sc5, both, only4, only5)
    with open(os.path.join(a.out_dir, f"fig5_selections_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)

    for p in a.budgets:
        print(f"\n--- budget {p:g}% of eligible land ({p / 100 * m['E'] / 1e3:.1f} x10^3 km2), thresholds p{a.pct:g} ---")
        print(f"{'screen':13s}{'res':>7s}{'G PgC':>8s}{'MgC/ha':>8s}{'loss %':>8s}{'forgone %':>10s}{'short km2':>10s}"
              f"{'>fire':>7s}{'>water':>7s}{'>any':>7s}")
        for sname, _ in SCREENS:
            w4, w5, sc4, sc5, both, only4, only5 = res[(a.pct, p, sname)]
            loss = 100 * (sc4["G_PgC"] - sc5["G_PgC"]) / sc4["G_PgC"]
            for rn, sc in (("4km", sc4), ("0.5deg", sc5)):
                r = next(x for x in rows if x["pct"] == a.pct and x["budget_pct"] == p and x["screen"] == sname and x["res"] == rn)
                print(f"{sname:13s}{RES_LAB[rn]:>7s}{sc['G_PgC']:8.3f}{sc['per_ha']:8.1f}{(loss if rn == '0.5deg' else 0):8.1f}"
                      f"{100 * r['forgone_vs_noscreen']:10.1f}{r['shortfall_km2']:10.0f}"
                      + "".join(f"{100 * sc[f'exceed_{k}']:7.1f}" for k in ("fire", "water", "any")))
            if sname == "none":
                sel = both + only4
                print(f"{'':13s} overlap: both {both / 1e3:.1f}, 4 km only {only4 / 1e3:.1f}, 0.5 deg only {only5 / 1e3:.1f} x10^3 km2 "
                      f"({100 * both / sel:.0f}% of the 4 km selection is also chosen at 0.5 deg)")
    print("\nSensitivity of the 20% screens to the threshold percentile (loss %, 4 km exposure to the screened component after screening, 4 km | 0.5 deg):")
    for pct in [a.pct] + list(a.sens):
        for sname, _ in SCREENS[1:]:
            w4, w5, sc4, sc5, *_ = res[(pct, a.budgets[0], sname)]
            key = "exceed_any" if sname == "all" else f"exceed_{sname}"
            print(f"  p{pct:g} {sname:12s} loss {100 * (sc4['G_PgC'] - sc5['G_PgC']) / sc4['G_PgC']:5.1f}%  "
                  f"exposure {100 * sc4[key]:5.1f}% | {100 * sc5[key]:5.1f}%")

    # ---- budget curve (no screen)
    budgets = np.arange(1, 101)
    curve = []
    for p in budgets:
        w4, w5, *_ = select(m, p / 100 * m["E"])
        curve.append((p, score(m, w4, T)["G_PgC"], score(m, w5, T)["G_PgC"]))
    curve = np.array(curve)
    with open(os.path.join(a.out_dir, f"fig5_budget_curve_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["budget_pct", "G_4km_PgC", "G_05deg_PgC", "loss_pct"])
        for p, g4, g5 in curve:
            wr.writerow([int(p), f"{g4:.5f}", f"{g5:.5f}", f"{100 * (g4 - g5) / g4:.3f}"])
    print(f"0.5 deg side can reach {100 * m['ac'][m['ok5']].sum() / m['E']:.1f}% of the 4 km eligible area "
          f"(the rest lies in 0.5 deg cells below the eligibility floor); at 100% budget G = {curve[-1, 1]:.3f} (4 km) vs {curve[-1, 2]:.3f} PgC (0.5 deg)")

    # ---- figure
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    p0 = a.budgets[0]
    w4, w5, sc4, sc5, both, only4, only5 = res[(a.pct, p0, "none")]
    fig = plt.figure(figsize=(17, 12.2), facecolor=SURFACE)
    gs = fig.add_gridspec(2, 12, height_ratios=[1.15, 1], hspace=0.38, wspace=2.0, left=0.05, right=0.985, top=0.93, bottom=0.12)

    ax = fig.add_subplot(gs[0, 0:6], projection=ccrs.PlateCarree())
    ax.set_facecolor(BAD)
    ax.pcolormesh(m["lon4"], m["lat4"], np.ma.masked_invalid(class_map(m, w4, w5)), cmap=ListedColormap(CLS_COLS),
                  norm=Normalize(-0.5, 3.5), shading="auto", transform=ccrs.PlateCarree(), rasterized=True)
    ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                edgecolor="#777777", linewidth=0.3))
    ax.set_extent([m["lon4"].min(), m["lon4"].max(), m["lat4"].min(), m["lat4"].max()], crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 8}
    ptitle(ax, "a", f"Where the {p0:g}% budget goes: 4 km vs 0.5° selection")
    handles = [plt.Rectangle((0, 0), 1, 1, color=CLS_COLS[k]) for k in (3, 1, 2, 0)]
    ax.legend(handles, [CLS_NAMES[k] for k in (3, 1, 2, 0)], loc="lower left", fontsize=8.5, framealpha=0.92, edgecolor="none")
    ax.text(0.98, 0.03, f"{100 * both / (both + only4):.0f}% of the 4 km selection\nis also selected at 0.5°", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9.5, color=INK, bbox=dict(facecolor=SURFACE, edgecolor="none", alpha=0.9, pad=3))

    sub = gs[0, 7:12].subgridspec(2, 1, height_ratios=[2, 1], hspace=0.12)
    axb, axl = fig.add_subplot(sub[0]), fig.add_subplot(sub[1])
    for col, key in ((1, "4km"), (2, "0.5deg")):
        axb.plot(curve[:, 0], curve[:, col], color=RES_COL[key], lw=2.2, label=f"{RES_LAB[key]} map")
    axl.plot(curve[:, 0], 100 * (curve[:, 1] - curve[:, 2]) / curve[:, 1], color=INK, lw=2)
    for p in a.budgets:
        for axx in (axb, axl):
            axx.axvline(p, color=INK2, lw=0.9, ls="--")
    style(axb, "Captured benefit (PgC)")
    axb.legend(frameon=False, fontsize=9.5, loc="lower right")
    axb.tick_params(labelbottom=False)
    style(axl, "Loss at 0.5° (%)", "Budget (% of eligible land)")
    axl.set_ylim(bottom=0)
    for axx in (axb, axl):
        axx.set_xlim(0, 100)
    ptitle(axb, "b", "Captured benefit by area budget (scored on the 4 km field)")

    axc = fig.add_subplot(gs[1, 0:4])
    x = np.arange(len(SCREENS))
    wd = 0.38
    for k, rn in enumerate(("4km", "0.5deg")):
        vals = [res[(a.pct, p0, s)][2 + k]["G_PgC"] for s, _ in SCREENS]
        axc.bar(x + (k - 0.5) * wd, vals, wd, color=RES_COL[rn], edgecolor=SURFACE, linewidth=1.2, zorder=3, label=f"{RES_LAB[rn]} map")
        for xi, v in zip(x, vals):
            axc.text(xi + (k - 0.5) * wd, v, f"{v:.2f}", ha="center", va="bottom", fontsize=7.8, color=INK2)
    axc.set_xticks(x)
    axc.set_xticklabels([n.replace(" ", "\n", 1) for _, n in SCREENS], fontsize=8.6)
    style(axc, "Captured benefit (PgC)")
    axc.legend(frameon=False, fontsize=9, loc="upper right")
    axc.set_ylim(0, axc.get_ylim()[1] * 1.15)
    ptitle(axc, "c", f"Benefit at {p0:g}%, before and after the screen")

    axd = fig.add_subplot(gs[1, 4:8])
    x = np.arange(len(COMPONENTS))
    wd = 0.2
    bars = [("4km", "none", "4 km, no screen", None), ("0.5deg", "none", "0.5°, no screen", None),
            ("4km", "comp", "4 km, screened", "//"), ("0.5deg", "comp", "0.5°, screened", "//")]
    for k, (rn, mode, lab, hatch) in enumerate(bars):
        vals = []
        for comp, _ in COMPONENTS:
            sc = res[(a.pct, p0, "none" if mode == "none" else comp)][2 if rn == "4km" else 3]
            vals.append(100 * sc[f"exceed_{comp}"])
        axd.bar(x + (k - 1.5) * wd, vals, wd, color=RES_COL[rn] if hatch is None else SURFACE, edgecolor=RES_COL[rn],
                hatch=hatch, linewidth=1.4, zorder=3, label=lab)
    axd.set_xticks(x)
    axd.set_xticklabels(["Fire", "Water stress"], fontsize=9)
    style(axd, "Selected land above the threshold (%)")
    axd.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
    axd.set_ylim(0, max(axd.get_ylim()[1], 10) * 1.25)
    ptitle(axd, "d", "True 4 km risk of the selected land")

    axe = fig.add_subplot(gs[1, 8:12])
    cls = class_map(m, w4, w5)
    rng = np.random.default_rng(0)
    for k in (0, 2, 1, 3):
        idx = np.flatnonzero((cls == k).ravel())
        if len(idx) > 6000:
            idx = rng.choice(idx, 6000, replace=False)
        axe.scatter(m["b4"].ravel()[idx], m["R4"]["water"].ravel()[idx], s=3, color=CLS_COLS[k], alpha=0.55, lw=0,
                    label=CLS_NAMES[k], rasterized=True)
    cut = np.nanmin(m["b4"][w4 >= 1]) if (w4 >= 1).any() else np.nan
    axe.axvline(cut, color=INK, lw=1, ls="--")
    axe.axhline(T["water"], color=INK, lw=1, ls=":")
    axe.text(cut, axe.get_ylim()[1], " budget cutoff", fontsize=8, color=INK2, va="top")
    axe.text(axe.get_xlim()[0], T["water"], f" threshold {tlab}", fontsize=8, color=INK2, ha="left", va="bottom")
    style(axe, "Water stress (1 − BTRAN, Apr–Oct)", "Benefit per eligible ha, 4 km (MgC/ha)")
    axe.legend(frameon=True, framealpha=0.92, edgecolor="none", fontsize=7.8, loc="upper left", markerscale=3)
    ptitle(axe, "e", f"Benefit vs water stress, {p0:g}% budget")

    fig.suptitle(f"SEUS {a.ssp}, RF, {win}: does 4 km information change where to manage, and at what risk?", fontsize=13,
                 color=INK, x=0.05, ha="left", y=0.985)
    fig.text(0.05, 0.012,
             f"Benefit = TOTECOSYSC stock difference RF − Default, per eligible hectare; eligible land = RF's 2060 forest fraction of each run (cells ≥ {a.floor:g} of the cell). "
             "Both selections cover the same physical area and are scored on the 4 km field;\n"
             "in sample the 4 km selection is best by construction (model-internal information loss). The 0.5° map is the native 0.5° run (separately configured). "
             + (f"Screen thresholds: fixed at the {tlab} (fire {T['fire']:.3g} %/yr, water {T['water']:.3g}), shared by both maps;\n" if a.thresholds else
              f"Screen thresholds: area-weighted p{a.pct:g} of the 4 km component over eligible land, shared by both maps;\n")
             + "the 0.5° side screens with its own 0.5° risk. Fire = (NEP − LAND_USE_FLUX − NBP)/TOTECOSYSC, ~0.5° effective resolution at 4 km; water stress = 1 − BTRAN, Apr–Oct "
             "(NBP variability not used: about half of it is fire). RF is restoration plus a region-wide harvest ban.",
             fontsize=8.4, color=INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, f"fig5_priority_{a.ssp}_{win}.png")
    fig.savefig(png, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    print(f"\nwrote {png}")


if __name__ == "__main__":
    main()
