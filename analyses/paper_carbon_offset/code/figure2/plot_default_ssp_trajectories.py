"""
Figure 2, Default trajectories of the four SSPs from the ELM 4 km runs (results only):

  1. forest (tree-PFT) area change relative to 2023, four SSPs on one panel
  2. annual regional NBP, one panel per SSP (annual bars, 11-year running mean line)

The 2000-2023 historical years come from the 4 km transient run, 2024-2100 from the
four Default future runs with crit_dayl_stress = 36000 s (the Default of the RF/RH pairs,
blueprint A2/E2). All runs start from the same 2024 restart of the transient. NBP is
positive for a sink and includes fire, land use and harvest. Forest area = tree PFTs
(itype 1-8) from the h1 PFT weights.

Inputs (pulled from Pathfinder into the local `_cache/figure2/`): transient_*_4km.npz and
future_4km/<SSP>__{totals,forest}.npz, made by extract_domain_totals.py and
extract_forest_area.py.

Colours: categorical slots 1-4 of the dataviz reference palette in fixed SSP order (blue
SSP1-1.9, orange SSP2-4.5, aqua SSP3-7.0, yellow SSP5-8.5), direct end labels; history in
grey; black axes; one y axis per panel.

Runs locally, from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \\
        code/figure2/plot_default_ssp_trajectories.py [year_min]
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
SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
COLORS = {"SSP1-1.9": "#2a78d6", "SSP2-4.5": "#eb6834", "SSP3-7.0": "#1baf7a", "SSP5-8.5": "#eda100"}
HIST, HIST_DARK = "#b9b8b3", "#6f6e69"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e9e8e4"
WIN = 11


def running_mean(y, n=WIN):
    out = np.full(y.shape, np.nan)
    h = n // 2
    for i in range(h, len(y) - h):
        out[i] = y[i - h:i + h + 1].mean()
    return out


def style(ax, ylabel=None):
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=12)
    ax.grid(axis="y", color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("black")
        ax.spines[sp].set_linewidth(1.1)
    ax.tick_params(colors="black", labelcolor=INK, labelsize=11, length=4, width=1.0)
    ax.margins(y=0.06)


def load(y0):
    th = np.load(os.path.join(CACHE, "transient_domain_totals_4km.npz"))
    fh = np.load(os.path.join(CACHE, "transient_forest_area_4km.npz"))
    sel = (th["year"] >= y0) & (th["year"] <= 2023)
    hist = {"year": th["year"][sel], "NBP": th["NBP"][sel], "forest": fh["tree_area_km2"][sel] / 1e3}
    fut = {}
    for ssp in SSPS:
        t = np.load(os.path.join(CACHE, "future_4km", f"{ssp}__totals.npz"))
        f = np.load(os.path.join(CACHE, "future_4km", f"{ssp}__forest.npz"))
        assert np.array_equal(t["year"], f["year"])
        fut[ssp] = {"year": t["year"], "NBP": t["NBP"], "forest": f["tree_area_km2"] / 1e3}
        assert fut[ssp]["year"][0] == hist["year"][-1] + 1, "future must start the year after the history ends"
    return hist, fut


def main():
    y0 = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    hist, fut = load(y0)
    ref = hist["forest"][-1]  # 2023 forest area
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
    os.makedirs(OUT_DIR, exist_ok=True)

    # ---- 1. forest area change since 2023
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    ax.plot(hist["year"], hist["forest"] - ref, color=HIST_DARK, lw=2.6, solid_capstyle="round", label="historical")
    for ssp in SSPS:
        d = fut[ssp]
        yr = np.concatenate([[hist["year"][-1]], d["year"]])
        ch = np.concatenate([[0.0], d["forest"] - ref])
        ax.plot(yr, ch, color=COLORS[ssp], lw=2.6, solid_capstyle="round")
        ax.plot([yr[-1]], [ch[-1]], "o", color=COLORS[ssp], ms=6, mec="white", mew=1.4, zorder=4)
        ax.annotate(f"{ssp}  {ch[-1]:+.0f}", xy=(yr[-1], ch[-1]), xytext=(7, 0), textcoords="offset points", fontsize=12,
                    color=INK, va="center", fontweight="semibold", annotation_clip=False)
    ax.axhline(0, color="black", lw=0.9)
    ax.axvline(hist["year"][-1] + 0.5, color=HIST_DARK, lw=0.9, ls=(0, (4, 3)))
    ax.text(hist["year"][-1] + 0.5 - 1.2, ax.get_ylim()[1], "historical", ha="right", va="top", fontsize=11, color=INK2)
    ax.text(hist["year"][-1] + 0.5 + 1.2, ax.get_ylim()[1], "projections", ha="left", va="top", fontsize=11, color=INK2)
    ax.set_xlim(y0 - 2, 2100 + 2)
    style(ax, f"forest area change since 2023  (10$^3$ km$^2$)")
    ax.set_xlabel("year", color=INK, fontsize=12)
    ax.set_title("Forest (tree-PFT) area under the four SSPs, Default runs", loc="left", fontsize=14, fontweight="semibold", pad=12)
    fig.text(0.075, 0.005, f"ELM 4 km; 2023 forest area {ref:.0f} ×10³ km². SSP runs use crit_dayl_stress = 36000 s (the Default paired with RF and RH).",
             fontsize=9.5, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.03, 0.93, 1))
    out1 = os.path.join(OUT_DIR, f"ssp_forest_area_change_{y0}-2100_4km.png")
    fig.savefig(out1, dpi=200, facecolor="white")
    plt.close(fig)

    # ---- 2. annual NBP, one panel per SSP
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.4), sharex=True, sharey=True)
    allv = np.concatenate([hist["NBP"]] + [fut[s]["NBP"] for s in SSPS])
    lo = float(np.floor(allv.min() * 10) / 10)          # keeps the most negative year
    hi = float(np.ceil(allv.max() * 10) / 10 + 0.1)     # asymmetric: the largest sink year is ~0.45
    for ax, ssp in zip(axes.ravel(), SSPS):
        d = fut[ssp]
        yr = np.concatenate([hist["year"], d["year"]])
        nbp = np.concatenate([hist["NBP"], d["NBP"]])
        nh = len(hist["year"])
        ax.bar(hist["year"], hist["NBP"], width=0.8, color=HIST, lw=0, zorder=2)
        ax.bar(d["year"], d["NBP"], width=0.8, color=COLORS[ssp], alpha=0.65, lw=0, zorder=2)
        rm = running_mean(nbp)
        ax.plot(yr[:nh], rm[:nh], color=HIST_DARK, lw=2.6, solid_capstyle="round", zorder=4)
        ax.plot(yr[nh - 1:], rm[nh - 1:], color=INK, lw=2.6, solid_capstyle="round", zorder=4)
        ax.axhline(0, color="black", lw=0.9, zorder=3)
        ax.axvline(hist["year"][-1] + 0.5, color=HIST_DARK, lw=0.9, ls=(0, (4, 3)), zorder=1)
        ax.set_title(ssp, loc="left", fontsize=14, fontweight="semibold", pad=8, color=INK)
        m = d["NBP"].mean()
        ax.text(0.97, 0.05, f"2024–2100 mean {m:+.3f} PgC yr$^{{-1}}$", transform=ax.transAxes, ha="right", va="bottom",
                fontsize=11.5, color=INK, fontweight="semibold")
        style(ax, "PgC yr$^{-1}$" if ax in axes[:, 0] else None)
        ax.set_xlim(y0 - 2, 2102)
        ax.set_ylim(lo, hi)
    for ax in axes[1]:
        ax.set_xlabel("year", color=INK, fontsize=12)
    fig.suptitle("Annual regional NBP (positive = sink) under the four SSPs, ELM 4 km Default runs", x=0.045, y=0.995, ha="left",
                 fontsize=16, fontweight="semibold")
    fig.text(0.045, 0.005, "Grey bars: historical 2000–2023; coloured bars: projection (crit_dayl_stress = 36000 s). Lines: 11-year running mean. "
             "NBP includes fire, land use and harvest.", fontsize=9.5, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.03, 1, 0.965), h_pad=2.0, w_pad=2.5)
    out2 = os.path.join(OUT_DIR, f"ssp_nbp_annual_{y0}-2100_4km.png")
    fig.savefig(out2, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Saved {out1}\nSaved {out2}")

    print(f"\n2023 forest area {ref:.1f} x10^3 km2; hist NBP mean 2000-2023 {hist['NBP'].mean():+.3f} PgC/yr")
    print(f"{'SSP':9s} {'forest 2050':>12s} {'forest 2100':>12s} {'NBP 2024-50':>12s} {'NBP 2051-2100':>14s} {'NBP 2091-2100':>14s}  (change vs 2023, 10^3 km2 | PgC/yr)")
    for ssp in SSPS:
        d = fut[ssp]; yr = d["year"]
        i50 = int(np.where(yr == 2050)[0][0])
        print(f"{ssp:9s} {d['forest'][i50] - ref:+12.1f} {d['forest'][-1] - ref:+12.1f} {d['NBP'][:i50 + 1].mean():+12.3f} "
              f"{d['NBP'][i50 + 1:].mean():+14.3f} {d['NBP'][-10:].mean():+14.3f}")
    print("\njump check at the 2023 -> 2024 boundary (forest area, 10^3 km2; NBP, PgC/yr):")
    for ssp in SSPS:
        d = fut[ssp]
        print(f"  {ssp}: forest {hist['forest'][-1]:.2f} -> {d['forest'][0]:.2f} ({d['forest'][0] - hist['forest'][-1]:+.2f}); "
              f"NBP {hist['NBP'][-1]:+.3f} -> {d['NBP'][0]:+.3f}")


if __name__ == "__main__":
    main()
