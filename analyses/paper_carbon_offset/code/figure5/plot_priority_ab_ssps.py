"""
plot_priority_ab.py for all four SSPs in one figure (user request 2026-10-02): no risk screen.

  a-d  where the BUDGET % goes in each SSP: 4 km vs native 0.5 deg selection (both / 4 km only / 0.5 deg only /
       eligible, not selected), with the share of the 4 km selection also chosen at 0.5 deg and the loss at 0.5 deg
  e    captured benefit by area budget, 4 km map (solid) and 0.5 deg map (dashed), one colour per SSP
  f    loss of captured benefit at 0.5 deg by area budget, one colour per SSP; dots at the mapped budget (values in a-d)

Selection, scoring and eligibility are imported from plot_priority_selection.py (net benefit = TOTECOSYSC RF - Default per
eligible ha, equal area, scored on the 4 km field), so the SSP3-7.0 numbers equal those of plot_priority_ab.py.
SSP colours: blue, yellow, red, violet (categorical slots validated together; yellow is below 3:1 contrast, so the
SSPs are named in the legend of e and the loss values are printed in a-d).

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_priority_ab_ssps.py [--budget 20]
Inputs: those of plot_priority_selection.py for SSP1-1.9, SSP2-4.5, SSP3-7.0 and SSP5-8.5.
Output: figures/figure5/fig5_priority_ab_ssps_<window>.png and a CSV of the per-SSP curves.
"""
import argparse
import copy
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_priority_selection as ps  # noqa: E402

SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
SSP_COL = {"SSP1-1.9": "#2a78d6", "SSP2-4.5": "#eda100", "SSP3-7.0": "#e34948", "SSP5-8.5": "#4a3aa7"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--floor", type=float, default=0.05)
    ap.add_argument("--pct", type=float, default=80, help="only used by the scoring helper; no screen is applied")
    ap.add_argument("--budget", type=float, default=20, help="budget mapped in a-d (% of eligible land)")
    ap.add_argument("--cache-4km", default=os.path.join(ps.ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(ps.ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--risk-cache", default=os.path.join(ps.ROOT, "_cache/figure5"))
    ap.add_argument("--out-dir", default=os.path.join(ps.ROOT, "figures/figure5"))
    base = ap.parse_args()
    win, p0 = base.years, base.budget

    R = {}
    for ssp in SSPS:
        a = copy.copy(base)
        a.ssp = ssp
        m = ps.build(a)
        elig = m["a4"] > 0
        T = {k: ps.wquantile(m["R4"][k][elig], m["a4"][elig], a.pct / 100) for k, _ in ps.COMPONENTS}
        w4, w5, _, _ = ps.select(m, p0 / 100 * m["E"])
        both, only4, only5 = ps.overlap(m, w4, w5)
        curve = []
        for p in np.arange(1, 101):
            c4, c5, _, _ = ps.select(m, p / 100 * m["E"])
            curve.append((p, ps.score(m, c4, T)["G_PgC"], ps.score(m, c5, T)["G_PgC"]))
        curve = np.array(curve)
        g4, g5 = curve[int(p0) - 1, 1:]
        R[ssp] = dict(m=m, cls=ps.class_map(m, w4, w5), agree=100 * both / (both + only4), curve=curve,
                      g4=g4, g5=g5, loss=100 * (g4 - g5) / g4)
        print(f"[{ssp}] budget {p0:g}%: G 4 km {g4:.3f}, 0.5 deg {g5:.3f} PgC, loss {R[ssp]['loss']:.1f}%; "
              f"{R[ssp]['agree']:.0f}% of the 4 km selection also selected at 0.5 deg")

    os.makedirs(base.out_dir, exist_ok=True)
    with open(os.path.join(base.out_dir, f"fig5_priority_ab_ssps_{win}.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["ssp", "budget_pct", "G_4km_PgC", "G_05deg_PgC", "loss_pct"])
        for ssp in SSPS:
            for p, g4, g5 in R[ssp]["curve"]:
                wr.writerow([ssp, int(p), f"{g4:.5f}", f"{g5:.5f}", f"{100 * (g4 - g5) / g4:.3f}"])

    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    fig = plt.figure(figsize=(24, 13.5), facecolor=ps.SURFACE)
    outer = fig.add_gridspec(1, 2, width_ratios=[2.05, 1], wspace=0.12, left=0.035, right=0.985, top=0.92, bottom=0.15)
    gm = outer[0].subgridspec(2, 2, hspace=0.2, wspace=0.06)
    for k, ssp in enumerate(SSPS):
        r, m = R[ssp], R[ssp]["m"]
        ax = fig.add_subplot(gm[k // 2, k % 2], projection=ccrs.PlateCarree())
        ax.set_facecolor(ps.BAD)
        ax.pcolormesh(m["lon4"], m["lat4"], np.ma.masked_invalid(r["cls"]), cmap=ListedColormap(ps.CLS_COLS),
                      norm=Normalize(-0.5, 3.5), shading="auto", transform=ccrs.PlateCarree(), rasterized=True)
        ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
        ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                    edgecolor="#777777", linewidth=0.3))
        ax.set_extent([m["lon4"].min(), m["lon4"].max(), m["lat4"].min(), m["lat4"].max()], crs=ccrs.PlateCarree())
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
        gl.top_labels = gl.right_labels = False
        gl.left_labels = k % 2 == 0
        gl.bottom_labels = k // 2 == 1
        gl.xlabel_style = gl.ylabel_style = {"size": 8}
        ps.ptitle(ax, "abcd"[k], ssp)
        ax.set_title(f"{r['agree']:.0f}% of the 4 km selection also at 0.5°  ·  loss at 0.5° {r['loss']:.1f}%",
                     loc="right", fontsize=10, color=ps.INK2)
    handles = [plt.Rectangle((0, 0), 1, 1, color=ps.CLS_COLS[c]) for c in (3, 1, 2, 0)]
    fig.legend(handles, [ps.CLS_NAMES[c] for c in (3, 1, 2, 0)], loc="upper center", bbox_to_anchor=(0.345, 0.135), ncol=4,
               fontsize=10.5, frameon=False, handlelength=2.2, columnspacing=2.2)

    gr = outer[1].subgridspec(2, 1, height_ratios=[1.35, 1], hspace=0.28)
    axb, axl = fig.add_subplot(gr[0]), fig.add_subplot(gr[1])
    for ssp in SSPS:
        c, col = R[ssp]["curve"], SSP_COL[ssp]
        axb.plot(c[:, 0], c[:, 1], color=col, lw=2)
        axb.plot(c[:, 0], c[:, 2], color=col, lw=2, ls=(0, (4, 2.5)))
        axl.plot(c[:, 0], 100 * (c[:, 1] - c[:, 2]) / c[:, 1], color=col, lw=2)
        axl.plot([p0], [R[ssp]["loss"]], "o", ms=8, color=col, mec=ps.SURFACE, mew=2, zorder=4)
    for axx in (axb, axl):
        axx.axvline(p0, color=ps.INK2, lw=0.9, ls="--")
        axx.set_xlim(0, 100)
    ps.style(axb, "Captured benefit (PgC)")
    axb.tick_params(labelbottom=False)
    handles = [Line2D([], [], color=SSP_COL[s_], lw=2.6) for s_ in SSPS[::-1]] + \
        [Line2D([], [], color=ps.INK2, lw=2), Line2D([], [], color=ps.INK2, lw=2, ls=(0, (4, 2.5)))]
    axb.legend(handles, SSPS[::-1] + ["4 km map", "0.5° map"], frameon=False, fontsize=9.3, loc="lower right", ncol=2,
               columnspacing=1.4, handlelength=2.6)
    ps.ptitle(axb, "e", "Captured benefit by area budget")
    ps.style(axl, "Loss at 0.5° (%)", "Budget (% of eligible land)")
    axl.set_ylim(bottom=0)
    ps.ptitle(axl, "f", "Benefit lost when the 0.5° map chooses the land")

    fig.suptitle(f"SEUS, RF, {win}: does 4 km information change where to manage? Four SSPs, top {p0:g}% of eligible land, no risk screen",
                 fontsize=13, color=ps.INK, x=0.035, ha="left", y=0.975)
    fig.text(0.035, 0.015,
             f"Benefit = TOTECOSYSC stock difference RF − Default, per eligible hectare; eligible land = RF's 2060 forest fraction of each run (cells ≥ {base.floor:g} of the cell).\n"
             "Both selections cover the same physical area and are scored on the 4 km field; in sample the 4 km selection is best by construction (model-internal information loss).\n"
             f"The 0.5° map is the native 0.5° run (separately configured). Dashed vertical line: the {p0:g}% budget mapped in a–d. RF is restoration plus a region-wide harvest ban.",
             fontsize=8.6, color=ps.INK2, va="bottom", ha="left")
    png = os.path.join(base.out_dir, f"fig5_priority_ab_ssps_{win}.png")
    fig.savefig(png, dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
