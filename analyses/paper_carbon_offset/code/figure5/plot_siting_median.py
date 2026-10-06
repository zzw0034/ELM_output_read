"""
Figure 5, poster method with median splits (user decisions 2026-10-06): 4 km only, the composite vulnerability of the
poster (carbon_offset_poster/outputs/panel4_siting_RF_4km_ABCD.png, ..._E_scatter.png) rebuilt from the two paper risk
components, and every split at this SSP's own area-weighted median over eligible land. RF, end state = mean of the window.

  a  RF benefit without fire loss per eligible ha (as plot_priority_maps.py panel a); black line = median
  b  fire risk: (NEP - LAND_USE_FLUX - NBP) / TOTECOSYSC, RF run (%/yr)
  c  water stress: 1 - BTRAN, April-October, RF run
  d  composite vulnerability = mean of the percentile ranks (0-1) of b and c over eligible cells; black line = median
  e  siting quadrants: benefit >= its median x vulnerability < its median
  f  benefit vs composite vulnerability (also written as a standalone scatter, as on the poster)
Differences from the poster: two components instead of three (NBP variability dropped, notes 3.19), benefit without
fire loss per eligible ha instead of the net stock difference per m2 of land, ranks and medians over eligible land
(RF 2060 forest fraction >= --floor) instead of all land. Ranks are unweighted (4 km cells have nearly equal area,
as on the poster); medians are area-weighted. No 0.5 deg comparison.

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
Q_COLS = ["#d9d9d9", "#9ecae1", "#fdae6b", "#238b45"]      # poster colours, quadrant codes 0-3
Q_NAMES = ["low benefit, high risk", "low benefit, low risk", "high benefit, high risk", "HIGH benefit, LOW risk"]
VULN_CMAP = LinearSegmentedColormap.from_list("vul", ["#fcfdbf", "#fc8961", "#b73779", "#51127c", "#000004"])


def rank01(x, keep):
    """Percentile rank in [0, 1] over the `keep` cells (unweighted, ties by order), NaN elsewhere."""
    v = x[keep]
    order = np.argsort(v, kind="stable")
    r = np.empty(v.size)
    r[order] = np.arange(v.size) / max(v.size - 1, 1)
    out = np.full(x.shape, np.nan)
    out[keep] = r
    return out


def compute(a):
    with contextlib.redirect_stdout(io.StringIO()):
        c = pm.compute(a)
    m, ok, a4, E, b = c["m"], c["ok"], c["a4"], c["E"], c["b_nf"]
    fire, water = m["R4"]["fire"], m["R4"]["water"]
    keep = ok & np.isfinite(b) & np.isfinite(fire) & np.isfinite(water)
    assert keep.sum() == ok.sum(), f"{ok.sum() - keep.sum()} eligible cells lack a benefit or risk value"
    vuln = (rank01(fire, keep) + rank01(water, keep)) / 2
    wmed = lambda x: ps.wquantile(x[keep], a4[keep], 0.5)
    med = dict(benefit=wmed(b), fire=wmed(fire), water=wmed(water), vuln=wmed(vuln))
    hi_b, lo_v = b >= med["benefit"], vuln < med["vuln"]
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
    print(f"[{a.ssp}] eligible 4 km land {E / 1e3:.1f} x10^3 km2 in {keep.sum()} cells; benefit without fire loss {total:.3f} PgC")
    print(f"medians (area-weighted, eligible land): benefit {med['benefit']:.2f} MgC/ha, fire {med['fire']:.4f} %/yr, "
          f"water {med['water']:.4f}, composite vulnerability {med['vuln']:.4f}")
    for r in rows:
        print(f"  {r['quadrant']:24s} {r['share_pct']:5.1f}%  {r['benefit_PgC']:6.3f} PgC ({100 * r['benefit_PgC'] / total:4.1f}%)  "
              f"mean {r['mean_benefit_MgCha']:6.1f} MgC/ha, fire {r['mean_fire_pctyr']:.3f} %/yr, water {r['mean_water']:.4f}")
    hb = keep & hi_b
    print(f"high-benefit half: {100 * a4[hb & ~lo_v].sum() / a4[hb].sum():.1f}% high risk; of the high-benefit land, above the fire median "
          f"{100 * a4[hb & (fire > med['fire'])].sum() / a4[hb].sum():.1f}%, above the water median {100 * a4[hb & (water > med['water'])].sum() / a4[hb].sum():.1f}%")
    rk = lambda x: rank01(x, keep)[keep]
    print(f"rank correlations: fire-water {np.corrcoef(rk(fire), rk(water))[0, 1]:.2f}, benefit-vulnerability {np.corrcoef(rk(b), rk(vuln))[0, 1]:.2f}")
    return dict(m=m, keep=keep, a4=a4, E=E, b=b, fire=fire, water=water, vuln=vuln, med=med, quad=quad, rows=rows, total=total)


def colorbar(fig, mm, ax, label, line, extend):
    cb = fig.colorbar(mm, ax=ax, orientation="horizontal", fraction=0.05, pad=0.08, shrink=0.85, extend=extend)
    cb.ax.axvline(line, color="black", lw=2.4)
    cb.set_label(label, fontsize=8.6)
    cb.ax.tick_params(labelsize=8)


def scatter(ax, c, small=False):
    k, a4 = c["keep"], c["a4"]
    x, y, w, q = c["b"][k], c["vuln"][k], a4[k], c["quad"][k].astype(int)
    sz = np.clip(w / w.max() * (5 if small else 12), 0.5, None)
    ax.scatter(x, y, s=sz, c=np.array(Q_COLS)[q], alpha=0.6, linewidths=0, rasterized=True)
    ax.axvline(c["med"]["benefit"], color="k", lw=0.9, ls="--")
    ax.axhline(c["med"]["vuln"], color="k", lw=0.9, ls="--")
    # a few cells with a small eligible fraction have large negative values per eligible ha; clip the axis at the area-weighted p0.1
    xlo = ps.wquantile(x, w, 0.001)
    span = x.max() - xlo
    ax.set_xlim(xlo - 0.03 * span, x.max() + 0.03 * span)
    out = 100 * w[x < xlo].sum() / w.sum()
    ax.text(0.01, 0.01, f"{out:.1f}% of eligible area left of the axis (down to {x.min():.0f})", transform=ax.transAxes,
            fontsize=7 if small else 8.5, color=ps.INK2, ha="left", va="bottom")
    ax.set_xlabel("RF benefit without fire loss (MgC/ha per eligible ha)", fontsize=9 if small else 11)
    ax.set_ylabel("Composite vulnerability (0–1)", fontsize=9 if small else 11)
    ax.set_ylim(-0.03, 1.03)
    ax.grid(alpha=0.3)
    ax.tick_params(labelsize=8 if small else 10)


def draw(a, c):
    import cartopy.crs as ccrs
    m, keep, med = c["m"], c["keep"], c["med"]
    lon4, lat4 = m["lon4"], m["lat4"]
    land4 = np.isfinite(m["g4"]) & np.isfinite(m["R4"]["water"])
    inel = np.where(land4 & ~keep, 1.0, np.nan)
    vmax = [float(np.nanpercentile(c[k][keep], 98)) for k in ("b", "fire", "water")]
    fig = plt.figure(figsize=(21, 12.6), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(2, 3, hspace=0.26, wspace=0.1, left=0.03, right=0.985, top=0.93, bottom=0.12)

    def map_ax(pos, letter, ttl):
        ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
        pm.base_map(ax, lon4, lat4)
        pm.mesh(ax, lon4, lat4, inel, ListedColormap([pm.INELIGIBLE]), Normalize(0, 1))
        pm.title(ax, letter, ttl)
        return ax

    ax = map_ax(gs[0, 0], "a", "Carbon benefit of RF without fire loss")
    mm = pm.mesh(ax, lon4, lat4, np.where(keep, c["b"], np.nan), pm.BENEFIT_CMAP, Normalize(0, vmax[0]))
    colorbar(fig, mm, ax, f"RF − Default, MgC per eligible ha, fire loss added back; black line = median {med['benefit']:.1f}", med["benefit"], "both")
    for pos, key, cmap, letter, ttl, lab, vm in (
            (gs[0, 1], "fire", pm.FIRE_CMAP, "b", "Fire risk", "Fire carbon loss / ecosystem carbon (%/yr)", vmax[1]),
            (gs[0, 2], "water", pm.WATER_CMAP, "c", "Water stress risk", "1 − BTRAN, April–October", vmax[2])):
        ax = map_ax(pos, letter, ttl)
        mm = pm.mesh(ax, lon4, lat4, np.where(keep, c[key], np.nan), cmap, Normalize(0, vm))
        colorbar(fig, mm, ax, f"{lab}; black line = median {med[key]:.3g}", med[key], "max")
    ax = map_ax(gs[1, 0], "d", "Composite vulnerability (fire + water stress)")
    mm = pm.mesh(ax, lon4, lat4, c["vuln"], VULN_CMAP, Normalize(0, 1))
    colorbar(fig, mm, ax, f"Mean of the percentile ranks of b and c; black line = median {med['vuln']:.3f}", med["vuln"], "neither")
    ax = map_ax(gs[1, 1], "e", "Siting quadrants (split at medians)")
    pm.mesh(ax, lon4, lat4, c["quad"], ListedColormap(Q_COLS), Normalize(-0.5, 3.5))
    share = {r["quadrant"]: r["share_pct"] for r in c["rows"]}
    handles = [plt.Rectangle((0, 0), 1, 1, color=Q_COLS[q]) for q in (3, 2, 1, 0)]
    ax.legend(handles, [f"{Q_NAMES[q]} ({share[Q_NAMES[q]]:.0f}%)" for q in (3, 2, 1, 0)], loc="lower left", fontsize=8.2,
              framealpha=0.93, edgecolor="none", title="share of eligible land", title_fontsize=8)
    axf = fig.add_subplot(gs[1, 2])
    axf.set_facecolor(ps.SURFACE)
    scatter(axf, c, small=True)
    pm.title(axf, "f", "Benefit vs vulnerability")
    fig.suptitle(f"Where to restore and protect forest for carbon (SEUS, {a.ssp}, RF, {a.years}, 4 km)", fontsize=14, color=ps.INK,
                 x=0.03, ha="left", y=0.975)
    fig.text(0.03, 0.012,
             "Benefit (a) = TOTECOSYSC stock difference RF − Default plus the cumulative fire carbon loss difference since 2024 (fire = NEP − LAND_USE_FLUX − NBP), "
             "per eligible hectare; adding the fire loss back is an approximation.\n"
             f"Eligible land = RF's 2060 forest fraction ≥ {a.floor:g} (near-white: not eligible). All medians are area-weighted over eligible land of this SSP. "
             "Vulnerability (d) is rank-based, so half of the eligible land is high risk by construction.\n"
             "Fire has ~0.5° effective resolution at 4 km (population-density input interpolated from 0.5°). RF is restoration plus a region-wide harvest ban. "
             f"Colour scales a–c: 0 to the 98th percentile ({vmax[0]:.3g}, {vmax[1]:.3g}, {vmax[2]:.3g}). Point size in f = cell eligible area.",
             fontsize=8.4, color=ps.INK2, va="bottom", ha="left")
    os.makedirs(a.out_dir, exist_ok=True)
    stem = os.path.join(a.out_dir, f"fig5_siting_median_{a.ssp}_{a.years}")
    fig.savefig(stem + ".png", dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)

    fs, ax = plt.subplots(figsize=(8, 7), facecolor=ps.SURFACE)
    ax.set_facecolor(ps.SURFACE)
    scatter(ax, c)
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


def main():
    a = pm.parser().parse_args()
    draw(a, compute(a))


if __name__ == "__main__":
    main()
