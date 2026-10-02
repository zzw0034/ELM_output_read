"""
Figure 5 without the risk screen: panels a (where the budget goes, 4 km vs 0.5 deg selection) and
b (captured benefit and loss at 0.5 deg by area budget) of plot_priority_selection.py only, no
screen panels. RF, SSP3-7.0, end state = mean of 2091-2100.

Selection, scoring and eligibility are imported from plot_priority_selection.py, so the numbers match
Figure 5 exactly (equal area, 4 km field scoring, eligibility floor FLOOR).

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_priority_ab.py [--budget 20]
Output: figures/figure5/fig5_priority_ab_<SSP>_<window>.png
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_priority_selection as ps  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--floor", type=float, default=0.05)
    ap.add_argument("--pct", type=float, default=80, help="only used by the scoring helper; no screen is applied")
    ap.add_argument("--budgets", type=float, nargs="*", default=[20, 30], help="first one is mapped in panel a")
    ap.add_argument("--cache-4km", default=os.path.join(ps.ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(ps.ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--risk-cache", default=os.path.join(ps.ROOT, "_cache/figure5"))
    ap.add_argument("--out-dir", default=os.path.join(ps.ROOT, "figures/figure5"))
    a = ap.parse_args()
    m = ps.build(a)
    win = a.years
    elig = m["a4"] > 0
    T = {k: ps.wquantile(m["R4"][k][elig], m["a4"][elig], a.pct / 100) for k, _ in ps.COMPONENTS}

    p0 = a.budgets[0]
    w4, w5, _, _ = ps.select(m, p0 / 100 * m["E"])
    both, only4, only5 = ps.overlap(m, w4, w5)
    curve = []
    for p in np.arange(1, 101):
        c4, c5, _, _ = ps.select(m, p / 100 * m["E"])
        curve.append((p, ps.score(m, c4, T)["G_PgC"], ps.score(m, c5, T)["G_PgC"]))
    curve = np.array(curve)
    for p in a.budgets:
        g4, g5 = curve[int(p) - 1, 1:]
        print(f"budget {p:g}%: G 4 km {g4:.3f}, 0.5 deg {g5:.3f} PgC, loss {100 * (g4 - g5) / g4:.1f}%")
    print(f"{p0:g}% overlap: {100 * both / (both + only4):.0f}% of the 4 km selection is also selected at 0.5 deg")

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    fig = plt.figure(figsize=(17, 7.4), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(1, 12, wspace=2.0, left=0.05, right=0.985, top=0.88, bottom=0.17)

    ax = fig.add_subplot(gs[0, 0:6], projection=ccrs.PlateCarree())
    ax.set_facecolor(ps.BAD)
    ax.pcolormesh(m["lon4"], m["lat4"], np.ma.masked_invalid(ps.class_map(m, w4, w5)), cmap=ListedColormap(ps.CLS_COLS),
                  norm=Normalize(-0.5, 3.5), shading="auto", transform=ccrs.PlateCarree(), rasterized=True)
    ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                edgecolor="#777777", linewidth=0.3))
    ax.set_extent([m["lon4"].min(), m["lon4"].max(), m["lat4"].min(), m["lat4"].max()], crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 8}
    ps.ptitle(ax, "a", f"Where the {p0:g}% budget goes: 4 km vs 0.5° selection")
    handles = [plt.Rectangle((0, 0), 1, 1, color=ps.CLS_COLS[k]) for k in (3, 1, 2, 0)]
    ax.legend(handles, [ps.CLS_NAMES[k] for k in (3, 1, 2, 0)], loc="lower left", fontsize=8.5, framealpha=0.92, edgecolor="none")
    ax.text(0.98, 0.03, f"{100 * both / (both + only4):.0f}% of the 4 km selection\nis also selected at 0.5°", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9.5, color=ps.INK, bbox=dict(facecolor=ps.SURFACE, edgecolor="none", alpha=0.9, pad=3))

    sub = gs[0, 7:12].subgridspec(2, 1, height_ratios=[2, 1], hspace=0.12)
    axb, axl = fig.add_subplot(sub[0]), fig.add_subplot(sub[1])
    for col, key in ((1, "4km"), (2, "0.5deg")):
        axb.plot(curve[:, 0], curve[:, col], color=ps.RES_COL[key], lw=2.2, label=f"{ps.RES_LAB[key]} map")
    axl.plot(curve[:, 0], 100 * (curve[:, 1] - curve[:, 2]) / curve[:, 1], color=ps.INK, lw=2)
    for p in a.budgets:
        for axx in (axb, axl):
            axx.axvline(p, color=ps.INK2, lw=0.9, ls="--")
    ps.style(axb, "Captured benefit (PgC)")
    axb.legend(frameon=False, fontsize=9.5, loc="lower right")
    axb.tick_params(labelbottom=False)
    ps.style(axl, "Loss at 0.5° (%)", "Budget (% of eligible land)")
    axl.set_ylim(bottom=0)
    for axx in (axb, axl):
        axx.set_xlim(0, 100)
    ps.ptitle(axb, "b", "Captured benefit by area budget (scored on the 4 km field)")

    fig.suptitle(f"SEUS {a.ssp}, RF, {win}: does 4 km information change where to manage?", fontsize=13,
                 color=ps.INK, x=0.05, ha="left", y=0.975)
    fig.text(0.05, 0.015,
             f"Benefit = TOTECOSYSC stock difference RF − Default, per eligible hectare; eligible land = RF's 2060 forest fraction of each run (cells ≥ {a.floor:g} of the cell).\n"
             "Both selections cover the same physical area and are scored on the 4 km field; in sample the 4 km selection is best by construction (model-internal information loss).\n"
             "The 0.5° map is the native 0.5° run (separately configured). Dashed lines: the budgets in the text. RF is restoration plus a region-wide harvest ban.",
             fontsize=8.6, color=ps.INK2, va="bottom", ha="left")
    os.makedirs(a.out_dir, exist_ok=True)
    png = os.path.join(a.out_dir, f"fig5_priority_ab_{a.ssp}_{win}.png")
    fig.savefig(png, dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
