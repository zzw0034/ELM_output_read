"""
Figure 2, first panel set: historical regional series of the SEUS domain, yearly,
ELM 4 km (solid blue) and ELM 0.5 deg (dashed orange) transient runs:
  (a) forest area (tree-PFT area, itype 1-8)           [10^3 km2]
  (b) regional GPP                                       [PgC / yr]
  (c) soil organic carbon, change relative to the first year [PgC]
  (d) regional NBP (positive = sink, includes fire, land use and harvest) [PgC / yr]

Inputs (pulled from Pathfinder `_cache/figure2/` into the local `_cache/figure2/`):
  transient_domain_totals_{4km,0p5deg}.npz   from extract_domain_totals.py
  transient_forest_area_{4km,0p5deg}.npz     from extract_forest_area.py
Domain totals are sums over each run's own land cells (area x landfrac; both cover
1.3562 Mkm2). SOC = TOTSOMC (soil organic matter pools only, full profile; litter
and CWD excluded), shown as a change since the first year.

Colours: slots 1 (blue, 4 km) and 2 (orange, 0.5 deg) of the dataviz reference
palette, line style as the second encoding (solid vs dashed). GPP and NBP show
thin annual lines and thick 11-year centred running means. One y-axis per panel.
(The per-scenario management figures use the 4 km runs only.)

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \
        code/figure2/plot_historical_regional_series.py [year_min year_max]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # analysis root
CACHE = os.path.join(ROOT, "_cache/figure2")
OUT_DIR = os.path.join(ROOT, "figures/figure2")
# (label, line colour, light colour for annual lines, line style, linewidth of the mean line)
RES = {"4km": ("4 km", "#2a78d6", "#a9c8ef", "-"), "0p5deg": ("0.5°", "#eb6834", "#f6c3ad", "--")}
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e9e8e4"
WIN = 11  # running-mean window (years, centred)


def running_mean(y, n=WIN):
    out = np.full(y.shape, np.nan)
    h = n // 2
    for i in range(h, len(y) - h):
        out[i] = y[i - h:i + h + 1].mean()
    return out


def style(ax, ylabel):
    ax.set_ylabel(ylabel, color=INK, fontsize=12)
    ax.grid(axis="y", color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("black")
        ax.spines[sp].set_linewidth(1.1)
    ax.tick_params(colors="black", labelcolor=INK, labelsize=11, length=4, width=1.0)
    ax.margins(x=0.035, y=0.06)


def note(ax, xy, text, xytext, ha="left", color=INK2):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=11, color=color, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9, shrinkA=0, shrinkB=3))


def main():
    data = {}
    for r in RES:
        t = np.load(os.path.join(CACHE, f"transient_domain_totals_{r}.npz"))
        f = np.load(os.path.join(CACHE, f"transient_forest_area_{r}.npz"))
        assert np.array_equal(t["year"], f["year"]), f"{r}: h0 and h1 years differ"
        data[r] = (t, f)
    years = data["4km"][0]["year"]
    assert np.array_equal(years, data["0p5deg"][0]["year"]), "4 km and 0.5 deg cover different years"
    y0 = int(sys.argv[1]) if len(sys.argv) > 1 else int(years[0])
    y1 = int(sys.argv[2]) if len(sys.argv) > 2 else int(years[-1])
    sel = (years >= y0) & (years <= y1)
    yr = years[sel]
    forest = {r: data[r][1]["tree_area_km2"][sel] / 1e3 for r in RES}
    gpp = {r: data[r][0]["GPP"][sel] for r in RES}
    soc = {r: data[r][0]["TOTSOMC"][sel] - data[r][0]["TOTSOMC"][sel][0] for r in RES}
    soc0 = {r: data[r][0]["TOTSOMC"][sel][0] for r in RES}
    nbp = {r: data[r][0]["NBP"][sel] for r in RES}
    last = yr >= yr[-1] - 23

    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    fig, axes = plt.subplots(2, 2, figsize=(14.5, 9.0), sharex=True)
    (axa, axb), (axc, axd) = axes

    def head(ax, title):
        ax.set_title(title, loc="left", fontsize=14, fontweight="semibold", pad=10)

    def stat(ax, lines, loc="tl"):
        ax.text(0.03 if loc == "tl" else 0.97, 0.96, "\n".join(lines), transform=ax.transAxes,
                ha="left" if loc == "tl" else "right", va="top", fontsize=12, color=INK, fontweight="semibold", linespacing=1.5)

    # (a) forest area: the two runs share the same land cover (0.5 deg = aggregate of 4 km)
    for r, (lab, c, cl, ls) in RES.items():
        axa.plot(yr, forest[r], color=c, ls=ls, lw=2.6 if r == "4km" else 2.2, label=lab, solid_capstyle="round")
    imin = int(np.argmin(forest["4km"]))
    axa.plot([yr[0], yr[imin], yr[-1]], [forest["4km"][0], forest["4km"][imin], forest["4km"][-1]], "o", color=RES["4km"][1],
             ms=6.5, mec="white", mew=1.5, zorder=5)
    note(axa, (yr[0], forest["4km"][0]), f"{forest['4km'][0]:.0f}", (yr[0] + 7, forest["4km"][0] + 2))
    note(axa, (yr[imin], forest["4km"][imin]), f"minimum {forest['4km'][imin]:.0f} ({yr[imin]})",
         (yr[imin] - 10, forest["4km"][imin] - 12), ha="right")
    note(axa, (yr[-1], forest["4km"][-1]), f"{forest['4km'][-1]:.0f}", (yr[-1] - 18, forest["4km"][-1] + 24), ha="right")
    stat(axa, [f"{100 * (forest['4km'][-1] / forest['4km'][0] - 1):+.0f}% since {y0}".replace("-", "−"),
               "identical in both runs"], loc="tr")
    axa.set_ylim(752, 990)
    head(axa, "Forest area (tree PFTs)")
    axa.legend(frameon=False, loc="lower left", fontsize=11, labelcolor=INK2, handlelength=2.2, bbox_to_anchor=(0.0, 0.0))
    style(axa, "10$^3$ km$^2$")

    # (b) GPP
    for r, (lab, c, cl, ls) in RES.items():
        axb.plot(yr, gpp[r], color=cl, lw=1.2, ls="-")
        axb.plot(yr, running_mean(gpp[r]), color=c, ls=ls, lw=2.6, label=lab, solid_capstyle="round")
    stat(axb, [f"{lab}: {gpp[r][0]:.2f} → {gpp[r][-1]:.2f} PgC yr$^{{-1}}$ ({100 * (gpp[r][-1] / gpp[r][0] - 1):+.0f}%)"
               for r, (lab, *_rest) in RES.items()])
    head(axb, "Gross primary production")
    axb.legend(frameon=False, loc="lower right", fontsize=11, labelcolor=INK2, handlelength=2.2, title="thin: annual; thick: 11-yr mean",
               title_fontsize=9.5)
    style(axb, "PgC yr$^{-1}$")

    # (c) SOC change
    for r, (lab, c, cl, ls) in RES.items():
        axc.plot(yr, soc[r], color=c, ls=ls, lw=2.6 if r == "4km" else 2.2, label=lab, solid_capstyle="round")
    axc.axhline(0, color="black", lw=0.9)
    stat(axc, [f"{lab}: {soc[r][-1]:+.2f} PgC by {y1} ({100 * soc[r][-1] / soc0[r]:+.1f}% of {soc0[r]:.1f} PgC)"
               for r, (lab, *_rest) in RES.items()])
    head(axc, f"Soil organic carbon, change since {y0}")
    axc.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.02, 0.80), fontsize=11, labelcolor=INK2, handlelength=2.2)
    style(axc, "PgC")

    # (d) NBP
    # annual values as side-by-side bars (4 km left, 0.5 deg right of each year), 11-yr means as lines
    off = {"4km": -0.24, "0p5deg": 0.24}
    for r, (lab, c, cl, ls) in RES.items():
        axd.bar(yr + off[r], nbp[r], width=0.48, color=c, alpha=0.75, lw=0, zorder=2)
    for r, (lab, c, cl, ls) in RES.items():
        axd.plot(yr, running_mean(nbp[r]), color=c, ls=ls, lw=2.6, label=lab, solid_capstyle="round", zorder=4)
    axd.axhline(0, color="black", lw=0.9, zorder=3)
    stat(axd, [f"mean {yr[-24]}–{yr[-1]}:"] + [f"{lab} {nbp[r][last].mean():+.3f} PgC yr$^{{-1}}$" for r, (lab, *_rest) in RES.items()])
    head(axd, "Net biome production (positive = sink)")
    axd.legend(frameon=False, loc="lower right", fontsize=11, labelcolor=INK2, handlelength=2.2, title="bars: annual; lines: 11-yr mean",
               title_fontsize=9.5)
    style(axd, "PgC yr$^{-1}$")

    axa.set_xlim(y0 - 6, y1 + 6)  # shared by all panels
    for ax in (axc, axd):
        ax.set_xlabel("year", color=INK, fontsize=12)
        ax.set_xticks(np.arange(int(np.ceil(y0 / 25) * 25), y1 + 1, 25))
    fig.suptitle(f"Southeastern U.S. {y0}–{y1}: ELM historical simulation, regional totals (4 km solid, 0.5° dashed)",
                 x=0.045, y=0.995, ha="left", fontsize=16, fontweight="semibold")
    fig.tight_layout(rect=(0, 0, 1, 0.965), h_pad=2.2, w_pad=3.0)
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"hist_regional_series_{y0}-{y1}.png")
    fig.savefig(out, dpi=200, facecolor="white")
    print(f"Saved {out}")
    for r, (lab, *_rest) in RES.items():
        print(f"  {lab}: forest {forest[r][0]:.1f} -> {forest[r][-1]:.1f}; GPP {gpp[r][0]:.2f} -> {gpp[r][-1]:.2f}; "
              f"SOC {soc[r][-1]:+.3f} PgC; NBP mean last 24 yr {nbp[r][last].mean():+.3f}")


if __name__ == "__main__":
    main()
