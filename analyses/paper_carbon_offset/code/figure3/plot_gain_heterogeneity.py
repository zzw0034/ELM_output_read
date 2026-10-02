"""
Main Figure 3 / Results 3.3 (blueprint E3): how the management gain differs between the
native 4 km run and the native 0.5 deg run. RF is the main example, RH the consistency
check. SSP3-7.0, end state = mean of 2091-2100, gain = TOTECOSYSC difference to the
(36000 s) Default, in MgC/ha of land. TOTECOSYSC is the total ecosystem carbon STOCK (vegetation + CWD +
litter + whole soil column + wood products), so the gain is a stock difference, not a flux such as NBP.

Only two versions are compared (user decision 2026-10-01; no 4 km-averaged-to-0.5 deg
comparator):
  C   native 4 km run
  A   native 0.5 deg run, copied to its 12 x 12 = 144 4 km children
Both are compared on the 4 km grid and on common support (4 km land cells inside a valid
0.5 deg cell; weights area x landfrac of the 4 km cell). A is a separately configured
run, so C - A is the combined effect of resolution and configuration, not of aggregation
alone.

Reported on common support (all, with the 0.5 deg row 30.5-31.0 N excluded because it holds
the 30.833 N crit_dayl_stress line, and for 0.5 deg cells with >= 72 of 144 children):
area-weighted mean, SD and quantiles of C and A, SD(A)/SD(C), weighted Pearson and Spearman
correlation, mean absolute and RMS difference, mean A - C, and the top-/bottom-decile area
overlap (the share of the area in C's top/bottom decile that is also in A's).

Panels h-i map the top-10 % overlap (RF and RH): each 4 km cell is "both" (in the top 10 % of
the land area by gain in C and in A), "C only" (a top-decile cell of the 4 km run that the 0.5 deg
run misses), "A only" or "neither". Top 10 % = the cells with the largest gain holding 10 % of the
common-support land area in that run; A's top decile is made of whole 0.5 deg cells.

Descriptive map (panel d): the area-weighted SD of C inside each 0.5 deg cell (about that
cell's own mean), the 4 km variation that a 0.5 deg cell cannot represent. It is also used,
only, to choose the zoom windows by a rule fixed before looking at the maps: among 0.5 deg
cells with >= 100 common children, zoom 1 is the cell with the largest within-cell SD and
zoom 2 the cell whose SD is closest to the median; each window is 3 x 3 coarse cells.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure3/plot_gain_heterogeneity.py [--ssp SSP3-7.0]
Inputs (git-ignored, from figure4/extract_pool_maps.py): <SSP>[_RF|_RH]__pools_2091-2100.npz in
_cache/figure4/4km/ and _cache/figure3/0.5deg/.
Outputs: figures/figure3/fig3_gain_heterogeneity_<SSP>_<window>.png and CSVs (statistics, per-cell).
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # analysis root
N = 12                      # 4 km cells per 0.5 deg cell along each axis
MIN_CHILD, ZOOM_MIN_CHILD = 72, 100
BAND_LAT = 30.833           # crit_dayl_stress line; its 0.5 deg row is 30.5-31.0 N
GC_M2_TO_MGC_HA = 0.01
INK, INK2, GRID, SURFACE, BAD = "#0b0b0b", "#52514e", "#e9e8e4", "#fcfcfb", "#dfe3e8"
MGMT = {"RF": "#2a78d6", "RH": "#eb6834"}
SERIES = {"C": ("#1baf7a", "4 km run"), "A": ("#e87ba4", "0.5° run")}
DIV = LinearSegmentedColormap.from_list("div", ["#e34948", "#f0efec", "#1c5cab"])
SEQ = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
QS = (0.05, 0.25, 0.5, 0.75, 0.95)


# ------------------------------------------------------------ weighted statistics

def wmean(x, w):
    return float((x * w).sum() / w.sum())


def wvar(x, w):
    mu = wmean(x, w)
    return float(((x - mu) ** 2 * w).sum() / w.sum())


def wquantile(x, w, qs):
    o = np.argsort(x, kind="stable")
    xs, ws = x[o], w[o]
    c = (np.cumsum(ws) - 0.5 * ws) / ws.sum()
    return np.interp(qs, c, xs)


def wrank(x, w):
    """Area-weighted mid-rank in (0,1): the weighted Spearman is the weighted Pearson of these."""
    o = np.argsort(x, kind="stable")
    r = np.empty(len(x))
    r[o] = (np.cumsum(w[o]) - 0.5 * w[o]) / w.sum()
    return r


def wcorr(x, y, w):
    mx, my = wmean(x, w), wmean(y, w)
    cov = ((x - mx) * (y - my) * w).sum() / w.sum()
    return float(cov / np.sqrt(wvar(x, w) * wvar(y, w)))


def decile_overlap(x, y, w, top=True):
    """Share of the area in x's top (bottom) decile that is also in y's top (bottom) decile."""
    q = 0.9 if top else 0.1
    qx, qy = wquantile(x, w, [q])[0], wquantile(y, w, [q])[0]
    ix, iy = (x >= qx, y >= qy) if top else (x <= qx, y <= qy)
    return float(w[ix & iy].sum() / w[ix].sum())


def stats(c, a, w):
    """Distribution and agreement statistics of C and A (arrays of valid cells, MgC/ha)."""
    out = {}
    for key, v in (("C", c), ("A", a)):
        out[f"{key}_mean"], out[f"{key}_sd"] = wmean(v, w), float(np.sqrt(wvar(v, w)))
        for q, val in zip(QS, wquantile(v, w, QS)):
            out[f"{key}_q{int(q * 100):02d}"] = float(val)
    out["sd_ratio_A_over_C"] = out["A_sd"] / out["C_sd"]
    out["r"] = wcorr(c, a, w)
    out["rho"] = wcorr(wrank(c, w), wrank(a, w), w)
    out["mad"] = float((np.abs(c - a) * w).sum() / w.sum())
    out["rmse"] = float(np.sqrt(((c - a) ** 2 * w).sum() / w.sum()))
    out["mean_diff_A_minus_C"] = wmean(a - c, w)
    out["top10_overlap"] = decile_overlap(c, a, w, True)
    out["bottom10_overlap"] = decile_overlap(c, a, w, False)
    return out


# --------------------------------------------------------------------- grid ops

def block_sum(x):
    ny, nx = x.shape[0] // N, x.shape[1] // N
    return x.reshape(ny, N, nx, N).sum(axis=(1, 3))


def to_children(x):
    return np.repeat(np.repeat(x, N, axis=0), N, axis=1)


def load_gain(cdir, ssp, mg, win):
    d = np.load(os.path.join(cdir, f"{ssp}__pools_{win}.npz"))
    m = np.load(os.path.join(cdir, f"{ssp}_{mg}__pools_{win}.npz"))
    for g in ("lat", "lon", "area_km2"):
        assert np.array_equal(d[g], m[g]), f"{mg}: {g} differs between Default and management run"
    gain = (m["TOTECOSYSC"].astype("f8") - d["TOTECOSYSC"].astype("f8")) * GC_M2_TO_MGC_HA  # MgC/ha of land
    lon = np.where(d["lon"] > 180, d["lon"] - 360, d["lon"])
    return d["lat"].astype("f8"), lon.astype("f8"), d["area_km2"].astype("f8"), gain


def build(c4dir, c05dir, ssp, mg, win):
    """C and A of one management run on the 4 km grid and on common support."""
    lat4, lon4, A4, g4 = load_gain(c4dir, ssp, mg, win)
    lat5, lon5, A5, g5 = load_gain(c05dir, ssp, mg, win)
    ny, nx = A4.shape
    assert (ny, nx) == (len(lat5) * N, len(lon5) * N), f"grids do not nest: {A4.shape} vs {A5.shape}"
    assert np.allclose(lat4.reshape(-1, N).mean(1), lat5, atol=1e-4) and np.allclose(lon4.reshape(-1, N).mean(1), lon5, atol=1e-4), \
        "0.5 deg cell centres are not the means of their 4 km children"
    valid5 = (A5 > 0) & np.isfinite(g5)
    common = (A4 > 0) & np.isfinite(g4) & to_children(valid5)
    w = np.where(common, A4, 0.0)
    a = to_children(np.where(valid5, g5, 0.0))
    # within-cell SD of C (about each 0.5 deg cell's own mean): description of the 4 km variation only
    wb = block_sum(w)
    gz = np.where(common, g4, 0.0)
    mean_in = np.divide(block_sum(gz * w), wb, out=np.zeros(wb.shape), where=wb > 0)
    within_var = np.divide(block_sum(w * (gz - to_children(mean_in)) ** 2), wb, out=np.full(wb.shape, np.nan), where=wb > 0)
    return dict(lat4=lat4, lon4=lon4, lat5=lat5, lon5=lon5, w=w, common=common, c=g4, a=a,
                a5=np.where(valid5, g5, np.nan), within_sd=np.sqrt(within_var), nch=block_sum(common.astype("f8")), wb=wb)


def subsets(b):
    """Weight arrays of the three subsets reported."""
    row = int(np.floor((BAND_LAT - (b["lat5"][0] - 0.25)) / 0.5))  # 0.5 deg row index of the 30.833 N line
    band = np.zeros(b["w"].shape[0], bool)
    band[row * N:(row + 1) * N] = True
    return {"all common support": b["w"],
            "excl. 30.5-31.0N row": np.where(band[:, None], 0.0, b["w"]),
            f">= {MIN_CHILD} children": np.where(to_children(b["nch"] >= MIN_CHILD), b["w"], 0.0)}, row


def pick_zooms(b):
    ok = (b["nch"] >= ZOOM_MIN_CHILD) & np.isfinite(b["within_sd"])
    idx = np.argwhere(ok)
    sd = b["within_sd"][ok]
    i1 = idx[int(np.argmax(sd))]
    i2 = idx[int(np.argmin(np.abs(sd - np.median(sd))))]
    return [tuple(int(v) for v in i1), tuple(int(v) for v in i2)], float(np.median(sd))


# ---------------------------------------------------------------------- drawing

def style(ax, ylabel=None, xlabel=None):
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=10.5)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK, fontsize=10.5)
    ax.grid(axis="y", color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("black")
        ax.spines[sp].set_linewidth(1.0)
    ax.tick_params(colors="black", labelcolor=INK, labelsize=9.5, length=3.5, width=0.9)


def ptitle(ax, letter, text):
    ax.set_title(f"{letter}  {text}", loc="left", fontsize=11, color=INK, fontweight="bold")


def draw_map(ax, lon, lat, field, cmap, norm, title, extent):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    ax.set_facecolor(BAD)
    mesh = ax.pcolormesh(lon, lat, np.ma.masked_invalid(field), cmap=cmap, norm=norm, shading="auto",
                         transform=ccrs.PlateCarree(), rasterized=True)
    ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m",
                                                facecolor="none", edgecolor="#777777", linewidth=0.3))
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 8}
    ptitle(ax, *title)
    return mesh


def draw_zoom(ax, lon, lat, field, norm, label, lon_edges, lat_edges):
    ax.pcolormesh(lon, lat, np.ma.masked_invalid(field), cmap=DIV, norm=norm, shading="auto", rasterized=True)
    for x in lon_edges:
        ax.axvline(x, color="#0b0b0b", lw=0.6, alpha=0.55)
    for y in lat_edges:
        ax.axhline(y, color="#0b0b0b", lw=0.6, alpha=0.55)
    ax.set_xlim(lon_edges[0], lon_edges[-1])
    ax.set_ylim(lat_edges[0], lat_edges[-1])
    ax.set_aspect("equal")
    ax.text(0.04, 0.96, label, transform=ax.transAxes, va="top", fontsize=9.5, color=INK,
            bbox=dict(facecolor=SURFACE, edgecolor="none", alpha=0.85, pad=2))
    ax.set_xticks(lon_edges[::2])
    ax.set_yticks(lat_edges[::2])
    ax.tick_params(labelsize=8, length=2.5)
    ax.set_facecolor(BAD)
    for sp in ax.spines.values():
        sp.set_color(INK2)


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--cache-4km", default=os.path.join(ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "figures/figure3"))
    a = ap.parse_args()
    win = a.years
    B = {mg: build(a.cache_4km, a.cache_05, a.ssp, mg, win) for mg in ("RF", "RH")}
    os.makedirs(a.out_dir, exist_ok=True)

    # ---- statistics for both managements and the three subsets
    rows, S = [], {}
    for mg, b in B.items():
        sub, row = subsets(b)
        for sname, w in sub.items():
            m = w > 0
            st = stats(b["c"][m], b["a"][m], w[m])
            st["n_cells_4km"], st["area_1e3km2"] = int(m.sum()), float(w[m].sum() / 1e3)
            S[(mg, sname)] = st
            rows += [[mg, sname, k, f"{v:.6g}"] for k, v in st.items()]
    with open(os.path.join(a.out_dir, f"fig3_stats_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows([["mgmt", "subset", "metric", "value"]] + rows)
    print(f"{a.ssp} {win}: gain = TOTECOSYSC difference to Default, MgC/ha of land; 0.5 deg band row {row} (30.5-31.0 N)")
    for mg in B:
        st = S[(mg, "all common support")]
        print(f"\n{mg} - Default on common support: {st['n_cells_4km']} 4 km cells, {st['area_1e3km2']:.1f} x10^3 km2")
        print(f"{'':4s}{'mean':>7s}{'sd':>7s}" + "".join(f"{'q%02d' % (q * 100):>7s}" for q in QS))
        for key in ("C", "A"):
            print(f"{key:4s}{st[key + '_mean']:7.1f}{st[key + '_sd']:7.1f}" + "".join(f"{st[f'{key}_q{int(q * 100):02d}']:7.1f}" for q in QS))
        print(f"SD(A)/SD(C) {st['sd_ratio_A_over_C']:.2f}; r {st['r']:.3f}, Spearman {st['rho']:.3f}; MAD {st['mad']:.2f}, RMSE {st['rmse']:.2f} MgC/ha; "
              f"mean A - C {st['mean_diff_A_minus_C']:+.2f}; top-10% overlap {100 * st['top10_overlap']:.0f}%, bottom-10% {100 * st['bottom10_overlap']:.0f}%")
        for sn in ("excl. 30.5-31.0N row", f">= {MIN_CHILD} children"):
            s2 = S[(mg, sn)]
            print(f"  {sn:22s} SD(A)/SD(C) {s2['sd_ratio_A_over_C']:.2f}; r {s2['r']:.3f}; top-10% overlap {100 * s2['top10_overlap']:.0f}%")

    # ---- per 0.5 deg cell table (RF)
    b = B["RF"]
    with open(os.path.join(a.out_dir, f"fig3_cells_RF_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["lat", "lon", "n_common_children", "area_km2", "A_MgC_ha", "within_cell_sd_of_C_MgC_ha"])
        for j, i in np.argwhere(b["wb"] > 0):
            wr.writerow([f"{b['lat5'][j]:.2f}", f"{b['lon5'][i]:.2f}", int(b["nch"][j, i]), f"{b['wb'][j, i]:.1f}",
                         f"{b['a5'][j, i]:.3f}", f"{b['within_sd'][j, i]:.3f}"])

    zooms, med_sd = pick_zooms(b)
    print(f"\nZoom rule: >= {ZOOM_MIN_CHILD} common children; zoom 1 = largest within-cell SD of C, zoom 2 = SD closest to the median ({med_sd:.1f})")
    for k, (j, i) in enumerate(zooms, 1):
        print(f"  zoom {k}: 0.5 deg cell lat {b['lat5'][j]:.2f}, lon {b['lon5'][i]:.2f}, within-cell SD of C {b['within_sd'][j, i]:.1f} MgC/ha, "
              f"A {b['a5'][j, i]:.1f}")

    # ---- figure
    import cartopy.crs as ccrs
    m = b["w"] > 0
    vmax = float(np.ceil(wquantile(np.abs(b["c"][m]), b["w"][m], [0.98])[0] / 10) * 10)
    norm = Normalize(-vmax, vmax)
    diff = np.where(b["common"], b["a"] - b["c"], np.nan)
    dmax = float(np.ceil(wquantile(np.abs(diff[m]), b["w"][m], [0.98])[0] / 10) * 10)
    c_map = np.where(b["common"], b["c"], np.nan)
    a_map = np.where(np.isfinite(b["a5"]) & (b["wb"] > 0), b["a5"], np.nan)
    extent = [float(b["lon4"].min()), float(b["lon4"].max()), float(b["lat4"].min()), float(b["lat4"].max())]

    fig = plt.figure(figsize=(17, 16), facecolor=SURFACE)
    gs = fig.add_gridspec(3, 12, height_ratios=[1, 1, 0.9], hspace=0.42, wspace=1.7, left=0.05, right=0.985, top=0.935, bottom=0.115)
    axs = [fig.add_subplot(gs[0, 4 * k:4 * k + 4], projection=ccrs.PlateCarree()) for k in range(3)]
    mesh = draw_map(axs[0], b["lon4"], b["lat4"], c_map, DIV, norm, ("a", "4 km run"), extent)
    draw_map(axs[1], b["lon5"], b["lat5"], a_map, DIV, norm, ("b", "0.5° run"), extent)
    cb = fig.colorbar(mesh, ax=axs[:2], orientation="horizontal", fraction=0.04, pad=0.09, shrink=0.55, extend="both")
    cb.set_label("Δ ecosystem carbon stock, RF − Default (TOTECOSYSC, MgC/ha of land), mean 2091–2100", fontsize=9.5, color=INK)
    cb.ax.tick_params(labelsize=9)
    meshx = draw_map(axs[2], b["lon4"], b["lat4"], diff, DIV, Normalize(-dmax, dmax), ("c", "0.5° run − 4 km run, on the 4 km cells"), extent)
    cbx = fig.colorbar(meshx, ax=axs[2], orientation="horizontal", fraction=0.04, pad=0.09, shrink=0.8, extend="both")
    cbx.set_label("0.5° run − 4 km run, Δ ecosystem carbon stock (MgC/ha of land)", fontsize=9.5, color=INK)
    cbx.ax.tick_params(labelsize=9)

    axd = fig.add_subplot(gs[1, 0:4], projection=ccrs.PlateCarree())
    sd_max = float(np.ceil(np.nanpercentile(b["within_sd"], 98) / 5) * 5)
    meshd = draw_map(axd, b["lon5"], b["lat5"], np.where(b["wb"] > 0, b["within_sd"], np.nan), SEQ, Normalize(0, sd_max),
                     ("d", "SD of the 4 km run inside each 0.5° cell"), extent)
    cbd = fig.colorbar(meshd, ax=axd, orientation="horizontal", fraction=0.045, pad=0.09, shrink=0.8, extend="max")
    cbd.set_label("MgC/ha (area-weighted SD of the 4 km gain)", fontsize=9, color=INK)
    cbd.ax.tick_params(labelsize=9)
    for k, ((j, i), letter) in enumerate(zip(zooms, ("e", "f"))):
        j0, j1 = max(j - 1, 0), min(j + 2, len(b["lat5"]))
        i0, i1 = max(i - 1, 0), min(i + 2, len(b["lon5"]))
        axd.add_patch(Rectangle((b["lon5"][i0] - 0.25, b["lat5"][j0] - 0.25), 0.5 * (i1 - i0), 0.5 * (j1 - j0), fill=False,
                                edgecolor="black", lw=1.4, transform=ccrs.PlateCarree()))
        axd.text(b["lon5"][i0] - 0.25, b["lat5"][j1 - 1] + 0.3, letter, transform=ccrs.PlateCarree(), fontsize=10,
                 fontweight="bold", color=INK)
        sub = gs[1, 4 + 4 * k:8 + 4 * k].subgridspec(1, 2, wspace=0.12)
        r0, r1, q0, q1 = j0 * N, j1 * N, i0 * N, i1 * N
        ax1, ax2 = fig.add_subplot(sub[0]), fig.add_subplot(sub[1])
        lon_e = np.append(b["lon5"][i0:i1] - 0.25, b["lon5"][i1 - 1] + 0.25)
        lat_e = np.append(b["lat5"][j0:j1] - 0.25, b["lat5"][j1 - 1] + 0.25)
        draw_zoom(ax1, b["lon4"][q0:q1], b["lat4"][r0:r1], c_map[r0:r1, q0:q1], norm, "4 km run", lon_e, lat_e)
        draw_zoom(ax2, b["lon5"][i0:i1], b["lat5"][j0:j1], a_map[j0:j1, i0:i1], norm, "0.5° run", lon_e, lat_e)
        ax2.set_yticklabels([])
        ptitle(ax1, letter, f"Zoom {k + 1}: 4 km SD in the centre cell {b['within_sd'][j, i]:.0f}" + (" MgC/ha" if k == 0 else " (median)"))

    # g: area-weighted cumulative distributions of C and A
    axg = fig.add_subplot(gs[2, 0:4])
    w = b["w"][m]
    for key, (col, lab) in SERIES.items():
        v = {"C": b["c"], "A": b["a"]}[key][m]
        o = np.argsort(v)
        cdf = np.cumsum(w[o]) / w.sum()
        axg.plot(v[o][::25], 100 * cdf[::25], color=col, lw=2.2, label=lab)
    axg.set_xlim(float(np.min(b["c"][m])) - 5, float(np.percentile(b["c"][m], 99.9)) + 5)
    axg.legend(frameon=False, fontsize=9.5, loc="lower right")
    style(axg, "Share of land area with gain ≤ x (%)", "Δ ecosystem carbon stock, RF − Default (MgC/ha of land)")
    ptitle(axg, "g", "Area-weighted distribution of the gain")
    axg.grid(axis="x", color=GRID, lw=0.9)

    # h-i: where the top-10 % land area of the 4 km run is, and whether the 0.5 deg run finds it
    cls_cols = ["#e1e0dc", "#eb6834", "#1baf7a", "#2a78d6"]     # neither, C only, A only, both
    cls_names = ["Neither", "4 km only (missed by 0.5°)", "0.5° only", "Both"]
    cmap_cls = matplotlib.colors.ListedColormap(cls_cols)
    for letter, mg, col in (("h", "RF", slice(4, 8)), ("i", "RH", slice(8, 12))):
        bm = B[mg]
        wm = bm["w"] > 0
        wv = bm["w"][wm]
        qc = wquantile(bm["c"][wm], wv, [0.9])[0]
        qa = wquantile(bm["a"][wm], wv, [0.9])[0]
        topc, topa = bm["c"] >= qc, bm["a"] >= qa
        cls = np.where(topc & topa, 3, np.where(topc, 1, np.where(topa, 2, 0))).astype("f8")
        cls = np.where(bm["common"], cls, np.nan)
        tot = bm["w"].sum()
        share = {k: 100 * bm["w"][(cls == k)].sum() / tot for k in (0, 1, 2, 3)}
        ov = S[(mg, "all common support")]["top10_overlap"]
        print(f"{mg} top-10% maps: C top decile {100 * bm['w'][topc].sum() / tot:.1f}% of land, A top decile {100 * bm['w'][topa].sum() / tot:.1f}%; "
              f"both {share[3]:.1f}%, C only {share[1]:.1f}%, A only {share[2]:.1f}% of land; overlap {100 * ov:.0f}% of C's top-decile area")
        axm = fig.add_subplot(gs[2, col], projection=ccrs.PlateCarree())
        draw_map(axm, bm["lon4"], bm["lat4"], cls, cmap_cls, Normalize(-0.5, 3.5),
                 (letter, f"{mg}: top 10% of the gain, 4 km vs 0.5°"), extent)
        handles = [plt.Rectangle((0, 0), 1, 1, color=cls_cols[k]) for k in (3, 1, 2, 0)]
        axm.legend(handles, [cls_names[k] for k in (3, 1, 2, 0)], loc="lower left", fontsize=8.2, frameon=True, framealpha=0.92, edgecolor="none")
        axm.text(0.98, 0.03, f"0.5° finds {100 * ov:.0f}%\nof the 4 km top 10%", transform=axm.transAxes, ha="right", va="bottom",
                 fontsize=9.5, color=INK, bbox=dict(facecolor=SURFACE, edgecolor="none", alpha=0.9, pad=3))

    st = S[("RF", "all common support")]
    fig.suptitle(f"SEUS {a.ssp}, {win}: the management gain at 4 km and at 0.5°", fontsize=13, color=INK, x=0.05, y=0.985, ha="left")
    fig.text(0.05, 0.006,
             "Gain = change in the total ecosystem carbon STOCK, management run − Default, mean of the window (TOTECOSYSC = vegetation + CWD + litter + soil, whole column, + wood products; "
             "MgC/ha of land). A stock difference, not a flux: it is not NBP.\n"
             "C = native 4 km run, A = native 0.5° run (Methods notation). Common support of the two runs; weights area × landfrac. "
             "A is a separately configured run, so A − C combines resolution and configuration. "
             f"RF: SD(A)/SD(C) = {st['sd_ratio_A_over_C']:.2f}, mean A − C = {st['mean_diff_A_minus_C']:+.1f} MgC/ha.\n"
             "RF is restoration plus a region-wide harvest ban; its gain contains the SSP's own land-use drift. Panel d: SD of the 4 km gain inside each 0.5° cell, about that cell's own mean.\n"
             "h-i: top 10% = the cells with the largest gain holding 10% of the common-support land area in each run (the 0.5° top decile is made of whole 0.5° cells).",
             fontsize=8.6, color=INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, f"fig3_gain_heterogeneity_{a.ssp}_{win}.png")
    fig.savefig(png, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    print(f"\nwrote {png}")


if __name__ == "__main__":
    main()
