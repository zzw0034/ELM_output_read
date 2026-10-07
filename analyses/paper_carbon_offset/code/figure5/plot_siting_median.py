"""
Figure 5, poster method with median splits (user decisions 2026-10-06): 4 km only, the composite vulnerability of the
poster (carbon_offset_poster/outputs/panel4_siting_RF_4km_ABCD.png, ..._E_scatter.png) rebuilt from the two paper risk
components, and every split at this SSP's own area-weighted median over eligible land. RF, end state = mean of the window.

Main figure, three panels (user decisions 2026-10-06: the fire and water-stress maps are dropped; both components are
still computed and defined in the footnote; the scatter is an inset of the quadrant map): a and b on the left, c on the right:
  a  RF carbon benefit per eligible ha: window-mean TOTECOSYSC RF - Default (net of fire, user decision 2026-10-06;
     --benefit nofire adds the cumulative fire-loss difference back as in plot_priority_maps.py panel a, suffix _nofire);
     black line = median. The same benefit sets the quadrant split (c) and the scatter x axis (inset of c).
  b  composite vulnerability = mean of the percentile ranks (0-1) over eligible cells of
     fire risk  = (NEP - LAND_USE_FLUX - NBP) / TOTECOSYSC, RF run (%/yr), and
     water stress = 1 - BTRAN, April-October, RF run; black line = median
  c  siting quadrants: benefit >= its median x vulnerability < its median; inset: benefit vs composite vulnerability
     (also written as a standalone scatter, as on the poster)
Differences from the poster: two components instead of three (NBP variability dropped, notes 3.19), benefit per eligible
ha (MgC/ha) instead of per m2 of land (gC/m2), ranks and medians over eligible land
(RF 2060 forest fraction >= --floor) instead of all land, and (user decision 2026-10-06) ranks weighted by eligible area
(--rank area, default: a cell's rank is the share of eligible AREA with lower risk) instead of cell counts (--rank count, the
poster's way; outputs get the suffix _countrank). Medians are area-weighted in both cases. No 0.5 deg comparison.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_siting_median.py [--ssp SSP3-7.0]
Inputs: those of plot_priority_maps.py (annual maps, cumulative fire, pools, tree fraction).
Output: figures/figure5/fig5_siting_median_<SSP>_<window>.png, ..._scatter.png, ....csv
"""
import argparse
import contextlib
import csv
import io
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_priority_maps as pm  # noqa: E402

ps = pm.ps
BEN = {   # benefit choice -> (short name, panel a title, colour-bar label, footnote)
    "net": ("carbon benefit", "Carbon benefit of RF",
            "RF − Default, ecosystem carbon per eligible ha (MgC/ha), 2091–2100",
            "Benefit (a) = 2091–2100 mean TOTECOSYSC (total ecosystem carbon incl. wood products) of RF minus Default, per eligible hectare; "
            "it is net of fire (fire losses are not added back)."),
    "nofire": ("benefit without fire loss", "Carbon benefit of RF without fire loss",
               "RF − Default, MgC per eligible ha, fire loss added back",
               "Benefit (a) = TOTECOSYSC stock difference RF − Default plus the cumulative fire carbon loss difference since 2024 "
               "(fire = NEP − LAND_USE_FLUX − NBP), per eligible hectare; adding the fire loss back is an approximation."),
}
Q_COLS = ["#d9d9d9", "#9ecae1", "#fdae6b", "#238b45"]      # poster colours, quadrant codes 0-3
Q_NAMES = ["low benefit, high risk", "low benefit, low risk", "high benefit, high risk", "HIGH benefit, LOW risk"]
VULN_CMAP = LinearSegmentedColormap.from_list("vul", ["#fcfdbf", "#fc8961", "#b73779", "#51127c", "#000004"])


def rank01(x, keep, w=None):
    """Percentile rank in [0, 1] over the `keep` cells, NaN elsewhere (ties by order). w=None: share of cells below
    (poster); w = cell weights: share of the total weight below, each cell at the midpoint of its own weight
    (the convention of plot_priority_selection.wquantile)."""
    v = x[keep]
    order = np.argsort(v, kind="stable")
    r = np.empty(v.size)
    if w is None:
        r[order] = np.arange(v.size) / max(v.size - 1, 1)
    else:
        ws = w[keep][order]
        r[order] = (np.cumsum(ws) - 0.5 * ws) / ws.sum()
    out = np.full(x.shape, np.nan)
    out[keep] = r
    return out


def wcdf(x, w):
    """Area-weighted reference distribution: sorted values and midpoint cumulative weight (the wquantile convention)."""
    o = np.argsort(x, kind="stable")
    xs, ws = x[o], w[o]
    return xs, (np.cumsum(ws) - 0.5 * ws) / ws.sum()


def compute(a, ref=None):
    """ref=None: every split at this SSP's own area-weighted medians. ref = the "ref" entry returned for another SSP
    (user decision 2026-10-06, SSP3-7.0): fire and water ranks are read off that SSP's area-weighted distributions, and
    benefit and composite vulnerability are split at that SSP's medians, so thresholds are the same absolute values."""
    with contextlib.redirect_stdout(io.StringIO()):
        c = pm.compute(a)
    m, ok, a4, E = c["m"], c["ok"], c["a4"], c["E"]
    b = c["b_net"] if a.benefit == "net" else c["b_nf"]
    fire, water = m["R4"]["fire"], m["R4"]["water"]
    keep = ok & np.isfinite(b) & np.isfinite(fire) & np.isfinite(water)
    assert keep.sum() == ok.sum(), f"{ok.sum() - keep.sum()} eligible cells lack a benefit or risk value"
    rw = a4 if a.rank == "area" else None
    if ref is None:
        vuln = (rank01(fire, keep, rw) + rank01(water, keep, rw)) / 2
    else:
        assert a.rank == "area", "a fixed reference needs area-weighted ranks"
        vuln = np.full(b.shape, np.nan)
        vuln[keep] = (np.interp(fire[keep], *ref["fire"]) + np.interp(water[keep], *ref["water"])) / 2
    wmed = lambda x: ps.wquantile(x[keep], a4[keep], 0.5)
    med = dict(benefit=wmed(b), fire=wmed(fire), water=wmed(water), vuln=wmed(vuln))
    thr = dict(benefit=med["benefit"], vuln=med["vuln"]) if ref is None else dict(benefit=ref["benefit"], vuln=ref["vuln"])
    thr_label = "median" if ref is None else f"{ref['ssp']} median"
    hi_b, lo_v = b >= thr["benefit"], vuln < thr["vuln"]
    quad = np.select([hi_b & lo_v, hi_b & ~lo_v, ~hi_b & lo_v], [3, 2, 1], 0).astype("f8")
    quad = np.where(keep, quad, np.nan)
    rows = []
    for q in (3, 2, 1, 0):
        s = keep & (quad == q)
        area = float(a4[s].sum())
        pgc = float((a4[s] * b[s]).sum()) * 100 / 1e9
        rows.append(dict(quadrant=Q_NAMES[q], share_pct=100 * area / E, area_1e3km2=area / 1e3, benefit_PgC=pgc,
                         mean_benefit_MgCha=pgc * 1e9 / 100 / area if area else np.nan,
                         mean_fire_pctyr=float((a4[s] * fire[s]).sum() / area) if area else np.nan,
                         mean_water=float((a4[s] * water[s]).sum() / area) if area else np.nan))
    total = float((a4[keep] * b[keep]).sum()) * 100 / 1e9
    print(f"[{a.ssp}] eligible 4 km land {E / 1e3:.1f} x10^3 km2 in {keep.sum()} cells; {BEN[a.benefit][0]} {total:.3f} PgC")
    print(f"own medians (area-weighted, eligible land): benefit {med['benefit']:.2f} MgC/ha, fire {med['fire']:.4f} %/yr, "
          f"water {med['water']:.4f}, composite vulnerability {med['vuln']:.4f}")
    if ref is not None:
        print(f"fixed thresholds ({thr_label}): benefit {thr['benefit']:.2f} MgC/ha, vulnerability {thr['vuln']:.4f}; "
              f"high benefit {100 * a4[keep & hi_b].sum() / E:.1f}%, low risk {100 * a4[keep & lo_v].sum() / E:.1f}% of eligible land")
    for r in rows:
        print(f"  {r['quadrant']:24s} {r['share_pct']:5.1f}%  {r['benefit_PgC']:6.3f} PgC ({100 * r['benefit_PgC'] / total:4.1f}%)  "
              f"mean {r['mean_benefit_MgCha']:6.1f} MgC/ha, fire {r['mean_fire_pctyr']:.3f} %/yr, water {r['mean_water']:.4f}")
    hb = keep & hi_b
    print(f"high-benefit half: {100 * a4[hb & ~lo_v].sum() / a4[hb].sum():.1f}% high risk; of the high-benefit land, above the fire median "
          f"{100 * a4[hb & (fire > med['fire'])].sum() / a4[hb].sum():.1f}%, above the water median {100 * a4[hb & (water > med['water'])].sum() / a4[hb].sum():.1f}%")
    rk = lambda x: rank01(x, keep)[keep]
    print(f"rank correlations: fire-water {np.corrcoef(rk(fire), rk(water))[0, 1]:.2f}, benefit-vulnerability {np.corrcoef(rk(b), rk(vuln))[0, 1]:.2f}")
    own_ref = dict(ssp=a.ssp, fire=wcdf(fire[keep], a4[keep]), water=wcdf(water[keep], a4[keep]), benefit=med["benefit"], vuln=med["vuln"])
    return dict(m=m, keep=keep, a4=a4, E=E, b=b, fire=fire, water=water, vuln=vuln, med=med, thr=thr, thr_label=thr_label,
                fixed=ref is not None, ref=own_ref, quad=quad, rows=rows, total=total)


def colorbar(fig, mm, ax, label, line, extend):
    cb = fig.colorbar(mm, ax=ax, orientation="horizontal", fraction=0.05, pad=0.08, shrink=0.85, extend=extend)
    cb.ax.axvline(line, color="black", lw=2.4)
    cb.set_label(label, fontsize=8.6)
    cb.ax.tick_params(labelsize=8)
    return cb


def scatter(ax, c, a, small=False, note=True):
    """Benefit vs composite vulnerability; returns the note on the clipped x axis (drawn inside the axes when note=True)."""
    k, a4 = c["keep"], c["a4"]
    x, y, w, q = c["b"][k], c["vuln"][k], a4[k], c["quad"][k].astype(int)
    sz = np.clip(w / w.max() * (5 if small else 12), 0.5, None)
    ax.scatter(x, y, s=sz, c=np.array(Q_COLS)[q], alpha=0.6, linewidths=0, rasterized=True)
    ax.axvline(c["thr"]["benefit"], color="k", lw=0.9, ls="--")
    ax.axhline(c["thr"]["vuln"], color="k", lw=0.9, ls="--")
    # a few cells with a small eligible fraction have large negative values per eligible ha; clip the axis at the area-weighted p0.1
    xlo = ps.wquantile(x, w, 0.001)
    span = x.max() - xlo
    ax.set_xlim(xlo - 0.03 * span, x.max() + 0.03 * span)
    out = 100 * w[x < xlo].sum() / w.sum()
    txt = f"{out:.1f}% of eligible area left of the axis (down to {x.min():.0f})"
    if note:
        ax.text(0.01, 0.01, txt, transform=ax.transAxes, fontsize=7 if small else 8.5, color=ps.INK2, ha="left", va="bottom")
    if small:   # inset: short labels
        ax.set_xlabel(f"{BEN[a.benefit][0].capitalize()} (MgC/ha)", fontsize=8.5, labelpad=1)
        ax.set_ylabel("Vulnerability (0–1)", fontsize=8.5, labelpad=1)
    else:
        ax.set_xlabel(f"RF {BEN[a.benefit][0]} (MgC/ha per eligible ha)", fontsize=11)
        ax.set_ylabel("Composite vulnerability (0–1)", fontsize=11)
    ax.set_ylim(-0.03, 1.03)
    ax.grid(alpha=0.3)
    ax.tick_params(labelsize=8 if small else 10)
    return txt


def draw(a, c):
    import cartopy.crs as ccrs
    m, keep, med = c["m"], c["keep"], c["med"]
    lon4, lat4 = m["lon4"], m["lat4"]
    land4 = np.isfinite(m["g4"]) & np.isfinite(m["R4"]["water"])
    inel = np.where(land4 & ~keep, 1.0, np.nan)
    vmax = getattr(a, "vmax_b", None) or float(np.nanpercentile(c["b"][keep], 98))   # shared across SSPs when set by the driver
    fig = plt.figure(figsize=(21, 12.4), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.9], hspace=0.28, wspace=0.08, left=0.03, right=0.99, top=0.93, bottom=0.11)

    def map_ax(pos, letter, ttl):
        ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
        pm.base_map(ax, lon4, lat4)
        pm.mesh(ax, lon4, lat4, inel, ListedColormap([pm.INELIGIBLE]), Normalize(0, 1))
        pm.title(ax, letter, ttl)
        return ax

    ax = map_ax(gs[0, 0], "a", BEN[a.benefit][1])
    mm = pm.mesh(ax, lon4, lat4, np.where(keep, c["b"], np.nan), pm.BENEFIT_CMAP, Normalize(0, vmax))
    colorbar(fig, mm, ax, f"{BEN[a.benefit][2]}; black line = {c['thr_label']} {c['thr']['benefit']:.1f}", c["thr"]["benefit"], "both")
    ax = map_ax(gs[1, 0], "b", "Composite vulnerability (fire + water stress)")
    mm = pm.mesh(ax, lon4, lat4, c["vuln"], VULN_CMAP, Normalize(0, 1))
    rdesc = "area-weighted percentile ranks" if a.rank == "area" else "percentile ranks (by cell count)"
    colorbar(fig, mm, ax, f"Mean of the {rdesc} of fire risk and water stress; black line = {c['thr_label']} {c['thr']['vuln']:.3f}", c["thr"]["vuln"], "neither")
    ax = map_ax(gs[:, 1], "c", f"Siting quadrants (split at {c['thr_label']}s), with benefit vs vulnerability")
    pm.mesh(ax, lon4, lat4, c["quad"], ListedColormap(Q_COLS), Normalize(-0.5, 3.5))
    share = {r["quadrant"]: r["share_pct"] for r in c["rows"]}
    handles = [plt.Rectangle((0, 0), 1, 1, color=Q_COLS[q]) for q in (3, 2, 1, 0)]
    ax.legend(handles, [f"{Q_NAMES[q]} ({share[Q_NAMES[q]]:.0f}%)" for q in (3, 2, 1, 0)], loc="lower right", fontsize=9.5,
              framealpha=0.93, edgecolor="none", title="share of eligible land", title_fontsize=9)
    # scatter as an inset over the open Gulf of Mexico (lower left of the map); the legend sits over the Atlantic
    # square in physical units: as tall as the open Gulf allows (lat ~25.5-29.1, below the Louisiana coast), width from the map aspect
    fig.canvas.draw()
    bb = ax.get_position()
    W, H = bb.width * fig.get_figwidth(), bb.height * fig.get_figheight()
    hi = 0.275
    axi = ax.inset_axes([0.07, 0.10, hi * H / W, hi])
    axi.set_facecolor("white")
    clip_note = scatter(axi, c, a, small=True, note=False)
    fig.suptitle(f"Where to restore and protect forest for carbon (SEUS, {a.ssp}, RF, {a.years}, 4 km)", fontsize=13.5, color=ps.INK,
                 x=0.04, ha="left", y=0.975)
    rank_txt = (f"ranks are {rdesc} over eligible land, so half of the eligible land is high risk by construction. " if not c["fixed"] else
                f"ranks are read off the area-weighted {c['thr_label'].split()[0]} distributions of fire risk and water stress, "
                f"and both splits are fixed at the {c['thr_label']}s. ")
    split_txt = "All medians are area-weighted over eligible land of this SSP.\n" if not c["fixed"] else "Class shares therefore differ between SSPs.\n"
    scale_txt = "98th percentile of the four SSPs pooled" if getattr(a, "vmax_b", None) else "98th percentile"
    fig.text(0.04, 0.012,
             BEN[a.benefit][3] + "\n"
             "Vulnerability (b) = mean of the percentile ranks of fire risk (fire carbon loss NEP − LAND_USE_FLUX − NBP over ecosystem carbon, %/yr) and "
             "water stress (1 − BTRAN, April–October), both 2091–2100 means of the RF run;\n"
             + rank_txt + f"Eligible land = RF's 2060 forest fraction ≥ {a.floor:g} (near-white: not eligible). " + split_txt +
             "Fire has ~0.5° effective resolution at 4 km (population-density input interpolated from 0.5°). RF is restoration plus a region-wide harvest ban. "
             f"Colour scale a: 0 to {vmax:.3g} ({scale_txt}). Inset in c: each point = one eligible 4 km cell, size = its eligible area, "
             f"dashed = the two splits; " + clip_note + ".",
             fontsize=8.4, color=ps.INK2, va="bottom", ha="left")
    os.makedirs(a.out_dir, exist_ok=True)
    stem = os.path.join(a.out_dir, f"fig5_siting_median_{a.ssp}_{a.years}" + ("_countrank" if a.rank == "count" else "") + ("_nofire" if a.benefit == "nofire" else "") + getattr(a, "suffix", ""))
    fig.savefig(stem + ".png", dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)

    fs, ax = plt.subplots(figsize=(8, 7), facecolor=ps.SURFACE)
    ax.set_facecolor(ps.SURFACE)
    scatter(ax, c, a)
    ax.set_title(f"Benefit vs composite vulnerability ({a.ssp}, {a.years}, 4 km)\npoint size = eligible area; dashed = medians", fontsize=12)
    ax.legend([plt.Rectangle((0, 0), 1, 1, color=Q_COLS[q]) for q in (3, 2, 1, 0)],
              [f"{Q_NAMES[q]} ({share[Q_NAMES[q]]:.0f}%)" for q in (3, 2, 1, 0)], loc="upper right", fontsize=8.5, framealpha=0.93)
    fs.tight_layout()
    fs.savefig(stem + "_scatter.png", dpi=170, facecolor=ps.SURFACE)
    plt.close(fs)

    with open(stem + ".csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["ssp", "window", "median_benefit_MgCha", "median_fire_pctyr", "median_water", "median_vuln", "total_benefit_PgC"])
        wr.writerow([a.ssp, a.years] + [f"{med[k]:.6g}" for k in ("benefit", "fire", "water", "vuln")] + [f"{c['total']:.4f}"])
        wr.writerow([])
        cols = list(c["rows"][0])
        wr.writerow(cols)
        for r in c["rows"]:
            wr.writerow([r[k] if isinstance(r[k], str) else f"{r[k]:.6g}" for k in cols])
    print(f"wrote {stem}.png, {stem}_scatter.png, {stem}.csv")


def draw_ppt(a, c):
    """Slide version (--ppt, user request 2026-10-06): 16 x 9 in, fonts sized to stay legible when the PNG fills a 16:9 slide
    (about 0.83x), short labels, legend under map c, no footnote (user request). Same panels and numbers as draw()."""
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    F = dict(sup=20, title=16, tick=12.5, cbar=13, legend=13, inset_lab=12.5, inset_tick=11, foot=11.5)
    m, keep, med = c["m"], c["keep"], c["med"]
    lon4, lat4 = m["lon4"], m["lat4"]
    land4 = np.isfinite(m["g4"]) & np.isfinite(m["R4"]["water"])
    inel = np.where(land4 & ~keep, 1.0, np.nan)
    vmax = getattr(a, "vmax_b", None) or float(np.nanpercentile(c["b"][keep], 98))   # shared across SSPs when set by the driver
    fig = plt.figure(figsize=(16, 9), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.75], hspace=0.42, wspace=0.07, left=0.035, right=0.99, top=0.9, bottom=0.15)

    def map_ax(pos, letter, ttl):
        ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
        ax.set_facecolor(ps.BAD)
        ax.coastlines(resolution="10m", linewidth=0.6, color="#555555")
        ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                    edgecolor="#777777", linewidth=0.35))
        ax.set_extent([lon4.min(), lon4.max(), lat4.min(), lat4.max()], crs=ccrs.PlateCarree())
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--",
                          xlocs=range(-93, -73, 4), ylocs=range(26, 38, 4))
        gl.top_labels = gl.right_labels = False
        gl.xlabel_style = gl.ylabel_style = {"size": F["tick"]}
        pm.mesh(ax, lon4, lat4, inel, ListedColormap([pm.INELIGIBLE]), Normalize(0, 1))
        ax.set_title(f"{letter}  {ttl}", loc="left", fontsize=F["title"], color=ps.INK, fontweight="bold")
        return ax

    def cbar(mm, ax, label, line, extend):
        cb = fig.colorbar(mm, ax=ax, orientation="horizontal", fraction=0.06, pad=0.1, shrink=0.9, extend=extend)
        cb.ax.axvline(line, color="black", lw=3)
        cb.set_label(label, fontsize=F["cbar"])
        cb.ax.tick_params(labelsize=F["tick"])

    ax = map_ax(gs[0, 0], "a", "Carbon benefit of RF" + ("" if a.benefit == "net" else " w/o fire loss"))
    mm = pm.mesh(ax, lon4, lat4, np.where(keep, c["b"], np.nan), pm.BENEFIT_CMAP, Normalize(0, vmax))
    cbar(mm, ax, f"MgC/ha of eligible land; {c['thr_label']} {c['thr']['benefit']:.1f}", c["thr"]["benefit"], "both")
    ax = map_ax(gs[1, 0], "b", "Vulnerability (fire + water)")
    mm = pm.mesh(ax, lon4, lat4, c["vuln"], VULN_CMAP, Normalize(0, 1))
    cbar(mm, ax, f"Mean area-weighted rank; {c['thr_label']} {c['thr']['vuln']:.3f}", c["thr"]["vuln"], "neither")

    ax = map_ax(gs[:, 1], "c", f"Siting quadrants (split at {c['thr_label']}s)")
    pm.mesh(ax, lon4, lat4, c["quad"], ListedColormap(Q_COLS), Normalize(-0.5, 3.5))
    share = {r["quadrant"]: r["share_pct"] for r in c["rows"]}
    handles = [plt.Rectangle((0, 0), 1, 1, color=Q_COLS[q]) for q in (3, 2, 1, 0)]
    ax.legend(handles, [f"{Q_NAMES[q]} ({share[Q_NAMES[q]]:.0f}%)" for q in (3, 2, 1, 0)], loc="upper center",
              bbox_to_anchor=(0.5, -0.045), ncol=2, fontsize=F["legend"], frameon=False, handlelength=1.6, columnspacing=1.6,
              title="share of eligible land", title_fontsize=F["legend"] - 1)
    fig.canvas.draw()
    bb = ax.get_position()
    W, H = bb.width * fig.get_figwidth(), bb.height * fig.get_figheight()
    hi = 0.255
    axi = ax.inset_axes([0.085, 0.115, hi * H / W, hi])
    axi.set_facecolor("white")
    clip_note = scatter(axi, c, a, small=True, note=False)
    axi.set_xlabel("Benefit (MgC/ha)", fontsize=F["inset_lab"], labelpad=1)
    axi.set_ylabel("Vulnerability", fontsize=F["inset_lab"], labelpad=1)
    axi.tick_params(labelsize=F["inset_tick"])
    axi.set_yticks([0, 0.5, 1])

    fig.suptitle(f"Where to restore and protect forest for carbon (SEUS, {a.ssp}, RF, 4 km)", fontsize=F["sup"],
                 color=ps.INK, x=0.035, ha="left", y=0.975)
    os.makedirs(a.out_dir, exist_ok=True)
    stem = os.path.join(a.out_dir, f"fig5_siting_median_{a.ssp}_{a.years}" + ("_countrank" if a.rank == "count" else "")
                        + ("_nofire" if a.benefit == "nofire" else "") + getattr(a, "suffix", "") + "_ppt")
    fig.savefig(stem + ".png", dpi=200, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"wrote {stem}.png")


def main():
    ap = pm.parser()
    ap.add_argument("--benefit", choices=("net", "nofire"), default="net",
                    help="net stock difference (default) or with the cumulative fire-loss difference added back")
    ap.add_argument("--rank", choices=("area", "count"), default="area",
                    help="percentile ranks of the risk components by eligible area (default) or by cell count (poster)")
    ap.add_argument("--ppt", action="store_true", help="also write the 16:9 slide version with large fonts (..._ppt.png)")
    a = ap.parse_args()
    c = compute(a)
    draw(a, c)
    if a.ppt:
        draw_ppt(a, c)


if __name__ == "__main__":
    main()
