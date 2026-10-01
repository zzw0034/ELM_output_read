"""
Main Figure 3 / Results 3.3 (blueprint E3, D8): the spatial heterogeneity of the
management gain that averaging to 0.5 deg removes. RF is the main example, RH the
consistency check. SSP3-7.0, end state = mean of 2091-2100, gain = TOTECOSYSC difference
to the (36000 s) Default, shown in MgC/ha of land.

Three versions of the gain (blueprint A4), compared on the 4 km grid and on common
support (cells valid at both resolutions):
  C   native 4 km run
  C'  the 4 km run area-averaged to 0.5 deg and copied back to its 144 children
      (the same simulation with coarse information: the clean test of what aggregation loses)
  A   native 0.5 deg run, copied to its 144 children (a separately configured run, so
      A - C' mixes aggregation with configuration differences; only C - C' is pure)
Weights are area x landfrac of the 4 km cell; C' is the weighted mean of the common-support
children of each 0.5 deg cell, so the identity  var(C) = var(C') + mean within-cell variance
holds exactly and is asserted.

Headline statistic (D8): share of the area-weighted spatial variance of the gain that lies
within 0.5 deg cells, 1 - var(C')/var(C). It is reported for all common support, with the
0.5 deg row 30.5-31.0 N excluded (it holds the 30.833 N crit_dayl_stress line), and for
0.5 deg cells with >= 72 of 144 children. Also reported on common support: area-weighted
quantiles, weighted Pearson and Spearman correlations, mean absolute and RMS differences,
and the top-/bottom-decile area overlap (C against C' and against A).

Zoom rule, fixed before looking at the maps: among 0.5 deg cells with >= 100 common
children, zoom 1 is the cell with the largest within-cell SD and zoom 2 the cell whose
within-cell SD is closest to the median; each window is 3 x 3 coarse cells.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure3/plot_gain_heterogeneity.py [--ssp SSP3-7.0]
Inputs (git-ignored, from extract_pool_maps.py): <SSP>[_RF|_RH]__pools_2091-2100.npz in
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
SERIES = {"C": ("#1baf7a", "C  native 4 km"), "Cp": ("#eda100", "C′  4 km averaged to 0.5°"),
          "A": ("#e87ba4", "A  native 0.5°")}
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


def stats(c, cp, a, w):
    """Distribution and agreement statistics of the three gains (arrays of valid cells, MgC/ha)."""
    out = {}
    for key, v in (("C", c), ("Cp", cp), ("A", a)):
        out[f"{key}_mean"], out[f"{key}_sd"] = wmean(v, w), float(np.sqrt(wvar(v, w)))
        for q, val in zip(QS, wquantile(v, w, QS)):
            out[f"{key}_q{int(q * 100):02d}"] = float(val)
    out["within_share"] = 1 - wvar(cp, w) / wvar(c, w)
    out["A_var_share_of_C"] = wvar(a, w) / wvar(c, w)
    for nm, y in (("Cp", cp), ("A", a)):
        out[f"r_C_{nm}"] = wcorr(c, y, w)
        out[f"rho_C_{nm}"] = wcorr(wrank(c, w), wrank(y, w), w)
        out[f"mad_C_{nm}"] = float((np.abs(c - y) * w).sum() / w.sum())
        out[f"rmse_C_{nm}"] = float(np.sqrt(((c - y) ** 2 * w).sum() / w.sum()))
        out[f"top10_overlap_C_{nm}"] = decile_overlap(c, y, w, True)
        out[f"bottom10_overlap_C_{nm}"] = decile_overlap(c, y, w, False)
    out["r_Cp_A"] = wcorr(cp, a, w)
    out["mean_diff_A_minus_Cp"] = wmean(a - cp, w)
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
    """All fields of one management run on the 4 km grid and on common support."""
    lat4, lon4, A4, g4 = load_gain(c4dir, ssp, mg, win)
    lat5, lon5, A5, g5 = load_gain(c05dir, ssp, mg, win)
    ny, nx = A4.shape
    assert (ny, nx) == (len(lat5) * N, len(lon5) * N), f"grids do not nest: {A4.shape} vs {A5.shape}"
    assert np.allclose(lat4.reshape(-1, N).mean(1), lat5, atol=1e-4) and np.allclose(lon4.reshape(-1, N).mean(1), lon5, atol=1e-4), \
        "0.5 deg cell centres are not the means of their 4 km children"
    valid5c = to_children((A5 > 0) & np.isfinite(g5))
    common = (A4 > 0) & np.isfinite(g4) & valid5c
    w = np.where(common, A4, 0.0)
    wb = block_sum(w)
    gz = np.where(common, g4, 0.0)
    cb = np.divide(block_sum(gz * w), wb, out=np.full(wb.shape, np.nan), where=wb > 0)   # C' on the 0.5 deg grid
    cp = to_children(np.where(np.isnan(cb), 0.0, cb))
    a = to_children(np.where(np.isfinite(g5), g5, 0.0))
    within_var = np.divide(block_sum(w * (gz - cp) ** 2), wb, out=np.full(wb.shape, np.nan), where=wb > 0)
    nch = block_sum(common.astype("f8"))
    return dict(lat4=lat4, lon4=lon4, lat5=lat5, lon5=lon5, A4=A4, w=w, common=common, c=g4, cp=cp, a=a,
                cb=cb, a5=np.where((A5 > 0) & np.isfinite(g5), g5, np.nan), within_sd=np.sqrt(within_var),
                nch=nch, wb=wb, within_var=within_var)


def subsets(b):
    """Weight arrays of the three subsets reported."""
    row_lo = np.floor((BAND_LAT - (b["lat5"][0] - 0.25)) / 0.5)  # 0.5 deg row index of the 30.833 N line
    band = np.zeros(b["w"].shape[0], bool)
    band[int(row_lo) * N:(int(row_lo) + 1) * N] = True
    return {"all common support": b["w"],
            "excl. 30.5-31.0N row": np.where(band[:, None], 0.0, b["w"]),
            f">= {MIN_CHILD} children": np.where(to_children(b["nch"] >= MIN_CHILD), b["w"], 0.0)}, int(row_lo)


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
    letter, text = title
    ptitle(ax, letter, text)
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
        sub, row_lo = subsets(b)
        for sname, w in sub.items():
            m = w > 0
            st = stats(b["c"][m], b["cp"][m], b["a"][m], w[m])
            # identity check: var(C) = var(C') + mean within-cell variance (exact for C' = weighted block mean)
            within = float((w[m] * (b["c"][m] - b["cp"][m]) ** 2).sum() / w[m].sum())
            assert abs(wvar(b["c"][m], w[m]) - wvar(b["cp"][m], w[m]) - within) < 1e-6 * wvar(b["c"][m], w[m]), "variance identity fails"
            st["n_cells_4km"], st["area_1e3km2"] = int(m.sum()), float(w[m].sum() / 1e3)
            S[(mg, sname)] = st
            rows += [[mg, sname, k, f"{v:.6g}"] for k, v in st.items()]
    with open(os.path.join(a.out_dir, f"fig3_stats_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows([["mgmt", "subset", "metric", "value"]] + rows)
    print(f"{a.ssp} {win}: gain = TOTECOSYSC difference to Default, MgC/ha of land; band row {row_lo} (0.5 deg row 30.5-31.0 N)")
    for mg in B:
        st = S[(mg, "all common support")]
        print(f"\n{mg} - Default on common support: {st['n_cells_4km']} 4 km cells, {st['area_1e3km2']:.1f} x10^3 km2")
        print(f"{'':6s}{'mean':>7s}{'sd':>7s}" + "".join(f"{'q%02d' % (q * 100):>7s}" for q in QS))
        for key in ("C", "Cp", "A"):
            print(f"{key:6s}{st[key + '_mean']:7.1f}{st[key + '_sd']:7.1f}" + "".join(f"{st[f'{key}_q{int(q * 100):02d}']:7.1f}" for q in QS))
        print(f"within-0.5deg share of variance 1 - var(C')/var(C): " + ", ".join(
            f"{sn} {100 * S[(mg, sn)]['within_share']:.1f}%" for sn in subsets(B[mg])[0]))
        print(f"var(A)/var(C) {st['A_var_share_of_C']:.2f}; corr C-C' r {st['r_C_Cp']:.3f} rho {st['rho_C_Cp']:.3f}; "
              f"C-A r {st['r_C_A']:.3f} rho {st['rho_C_A']:.3f}; C'-A r {st['r_Cp_A']:.3f}")
        print(f"MAD C-C' {st['mad_C_Cp']:.2f}, C-A {st['mad_C_A']:.2f}; RMSE C-C' {st['rmse_C_Cp']:.2f}, C-A {st['rmse_C_A']:.2f} MgC/ha; "
              f"top-10% overlap C-C' {100 * st['top10_overlap_C_Cp']:.0f}%, C-A {100 * st['top10_overlap_C_A']:.0f}%; "
              f"bottom-10% overlap {100 * st['bottom10_overlap_C_Cp']:.0f}%, {100 * st['bottom10_overlap_C_A']:.0f}%; "
              f"mean A - C' {st['mean_diff_A_minus_Cp']:+.2f}")

    # ---- per 0.5 deg cell table (RF)
    b = B["RF"]
    with open(os.path.join(a.out_dir, f"fig3_cells_RF_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["lat", "lon", "n_common_children", "area_km2", "Cprime_MgC_ha", "A_MgC_ha", "within_cell_sd_MgC_ha"])
        for j, i in np.argwhere(b["wb"] > 0):
            wr.writerow([f"{b['lat5'][j]:.2f}", f"{b['lon5'][i]:.2f}", int(b["nch"][j, i]), f"{b['wb'][j, i]:.1f}",
                         f"{b['cb'][j, i]:.3f}", f"{b['a5'][j, i]:.3f}", f"{b['within_sd'][j, i]:.3f}"])

    zooms, med_sd = pick_zooms(b)
    print(f"\nZoom rule: >= {ZOOM_MIN_CHILD} common children; zoom 1 = largest within-cell SD, zoom 2 = SD closest to the median ({med_sd:.1f})")
    for k, (j, i) in enumerate(zooms, 1):
        print(f"  zoom {k}: 0.5 deg cell lat {b['lat5'][j]:.2f}, lon {b['lon5'][i]:.2f}, within-cell SD {b['within_sd'][j, i]:.1f} MgC/ha, "
              f"C' {b['cb'][j, i]:.1f}")

    # ---- figure
    import cartopy.crs as ccrs
    m = b["w"] > 0
    vmax = float(np.ceil(wquantile(np.abs(b["c"][m]), b["w"][m], [0.98])[0] / 10) * 10)
    norm = Normalize(-vmax, vmax)
    c_map = np.where(b["common"], b["c"], np.nan)
    cp_map = b["cb"]
    a_map = np.where(np.isfinite(b["a5"]) & (b["wb"] > 0), b["a5"], np.nan)
    extent = [float(b["lon4"].min()), float(b["lon4"].max()), float(b["lat4"].min()), float(b["lat4"].max())]

    fig = plt.figure(figsize=(17, 16), facecolor=SURFACE)
    gs = fig.add_gridspec(3, 12, height_ratios=[1, 1, 0.9], hspace=0.42, wspace=1.7, left=0.05, right=0.985, top=0.935, bottom=0.115)
    axs = [fig.add_subplot(gs[0, 4 * k:4 * k + 4], projection=ccrs.PlateCarree()) for k in range(3)]
    mesh = draw_map(axs[0], b["lon4"], b["lat4"], c_map, DIV, norm, ("a", "C  native 4 km"), extent)
    draw_map(axs[1], b["lon5"], b["lat5"], cp_map, DIV, norm, ("b", "C′  4 km averaged to 0.5°"), extent)
    draw_map(axs[2], b["lon5"], b["lat5"], a_map, DIV, norm, ("c", "A  native 0.5° run"), extent)
    cb = fig.colorbar(mesh, ax=axs, orientation="horizontal", fraction=0.03, pad=0.09, shrink=0.42, extend="both")
    cb.set_label("RF − Default, total ecosystem carbon (MgC/ha of land), mean 2091–2100", fontsize=9.5, color=INK)
    cb.ax.tick_params(labelsize=9)

    axd = fig.add_subplot(gs[1, 0:4], projection=ccrs.PlateCarree())
    sd_max = float(np.ceil(np.nanpercentile(b["within_sd"], 98) / 5) * 5)
    meshd = draw_map(axd, b["lon5"], b["lat5"], np.where(b["wb"] > 0, b["within_sd"], np.nan), SEQ, Normalize(0, sd_max),
                     ("d", "Within-cell SD of C inside each 0.5° cell"), extent)
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
        draw_zoom(ax1, b["lon4"][q0:q1], b["lat4"][r0:r1], c_map[r0:r1, q0:q1], norm, "C  4 km", lon_e, lat_e)
        draw_zoom(ax2, b["lon4"][q0:q1], b["lat4"][r0:r1], np.where(b["common"], b["cp"], np.nan)[r0:r1, q0:q1], norm,
                  "C′  0.5° mean", lon_e, lat_e)
        ax2.set_yticklabels([])
        ptitle(ax1, letter, f"Zoom {k + 1}: within-cell SD {b['within_sd'][j, i]:.0f}" + (" MgC/ha" if k == 0 else " (median)"))

    # g: area-weighted cumulative distributions
    axg = fig.add_subplot(gs[2, 0:6])
    w = b["w"][m]
    xs = np.linspace(-vmax, 2.2 * vmax, 600)
    ends = []
    for key, (col, lab) in SERIES.items():
        v = {"C": b["c"], "Cp": b["cp"], "A": b["a"]}[key][m]
        o = np.argsort(v)
        cdf = np.cumsum(w[o]) / w.sum()
        axg.plot(v[o][::25], 100 * cdf[::25], color=col, lw=2.2, label=lab)
        ends.append((key, v[o][-1], lab, col))
    axg.set_xlim(max(-vmax, float(np.min(b["c"][m])) - 5), float(np.percentile(b["c"][m], 99.9)) + 5)
    axg.legend(frameon=False, fontsize=9.5, loc="lower right")
    style(axg, "Share of land area with gain ≤ x (%)", "RF − Default, total ecosystem carbon (MgC/ha of land)")
    ptitle(axg, "g", "Area-weighted distribution of the gain")
    axg.grid(axis="x", color=GRID, lw=0.9)

    # h: within-cell variance share
    axh = fig.add_subplot(gs[2, 7:12])
    names = list(subsets(b)[0])
    xh = np.arange(len(names))
    wd = 0.36
    for k, mg in enumerate(("RF", "RH")):
        vals = [100 * S[(mg, sn)]["within_share"] for sn in names]
        axh.bar(xh + (k - 0.5) * wd, vals, wd, color=MGMT[mg], edgecolor=SURFACE, linewidth=1.2, zorder=3, label=mg)
        for xi, v in zip(xh, vals):
            axh.text(xi + (k - 0.5) * wd, v, f"{v:.0f}%", ha="center", va="bottom", fontsize=9, color=INK2)
    axh.set_xticks(xh)
    axh.set_xticklabels([n.replace(" ", "\n", 1) if len(n) > 14 else n for n in names], fontsize=8.8)
    axh.set_ylim(0, 100)
    axh.legend(frameon=False, fontsize=9.5, loc="upper right")
    style(axh, "Variance within 0.5° cells (%)")
    ptitle(axh, "h", "Share of the gain's variance lost by 0.5° averaging")

    st = S[("RF", "all common support")]
    fig.suptitle(f"SEUS {a.ssp}, {win}: what averaging to 0.5° removes from the management gain", fontsize=13, color=INK,
                 x=0.05, y=0.985, ha="left")
    fig.text(0.05, 0.012,
             "Gain = TOTECOSYSC (RF or RH) − Default, mean of the window, MgC/ha of land, on the common support of the 4 km and 0.5° runs; weights area × landfrac. "
             "C′ is the area-weighted mean of the 4 km cells in each 0.5° cell,\nso C − C′ isolates information lost by aggregation; A is a separately configured run. "
             f"Variance share = 1 − var(C′)/var(C). A − C′ mean {st['mean_diff_A_minus_Cp']:+.1f} MgC/ha, r(C′, A) = {st['r_Cp_A']:.2f}. "
             "RF is restoration plus a region-wide harvest ban and its gain contains the SSP's own land-use drift.",
             fontsize=8.6, color=INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, f"fig3_gain_heterogeneity_{a.ssp}_{win}.png")
    fig.savefig(png, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    print(f"\nwrote {png}")


if __name__ == "__main__":
    main()
