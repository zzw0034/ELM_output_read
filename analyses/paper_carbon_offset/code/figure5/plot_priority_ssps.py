"""
Figure 5 across the four SSPs (user decision 2026-10-02): one colour scale and one pair of absolute risk thresholds
for every SSP, so that differences between the SSP maps come from the scenarios and not from re-ranking.

  thresholds  the SSP3-7.0 area-weighted p<pct> (default p80) of the 4 km fire and water-stress components over
              eligible land (the main-figure thresholds), applied unchanged to every SSP
  colour      shared maxima for the benefit, fire and water panels = the 98th percentile of the eligible cells of
              all four SSPs pooled

Writes, for each SSP, the four-panel figure of plot_priority_maps.py (fig5_priority_maps_<SSP>_<window>.png, the
SSP3-7.0 one included, so the main figure carries the shared scale), and one cross-SSP summary:
  a  how many of the four SSPs select each 4 km cell (screened 4 km siting, top BUDGET % by the benefit without
     fire loss) -- the robust priority land is selected in all four
  b  benefit without fire loss captured by the unscreened and the screened selection (PgC), screen cost in %
  c  share of eligible land above each fixed threshold (20 % in SSP3-7.0 by construction)
  d  loss of captured benefit when the native 0.5 deg map chooses the land instead of the 4 km map (net benefit,
     the supplement convention of plot_priority_selection.py), without screen and with the fire + water screen
fig5_ssp_summary_<window>.png plus a CSV of the numbers and of the pairwise overlap of the screened selections.
The 4 km vs 0.5 deg supplement figure per SSP is plot_priority_selection.py with --thresholds (run separately).

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_priority_ssps.py [--budget 20 --pct 80]
Inputs: those of plot_priority_maps.py for SSP1-1.9, SSP2-4.5, SSP3-7.0 and SSP5-8.5.
"""
import copy
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_priority_maps as pm  # noqa: E402
import plot_priority_selection as ps  # noqa: E402

SSPS = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
REF = "SSP3-7.0"
COUNT_COLS = ["#e1e0dc", "#cfe8d8", "#8fcfa8", "#3fa874", "#0b6e4a"]     # selected in 0..4 SSPs
SSP_COL = {"SSP1-1.9": "#3987e5", "SSP2-4.5": "#1baf7a", "SSP3-7.0": "#eb6834", "SSP5-8.5": "#7a2a0c"}


def main():
    ap = pm.parser()
    ap.description = __doc__
    base = ap.parse_args()
    assert not base.thresholds and not base.vmax, "thresholds and colour scales are derived here"

    # thresholds: the reference SSP's own p<pct>
    ref = copy.copy(base)
    ref.ssp = REF
    T = pm.compute(ref)["T"]
    tlab = f"{REF} p{base.pct:g}"
    print(f"\n=== fixed thresholds ({tlab}): fire {T['fire']:.4f} %/yr, water {T['water']:.4f}\n")

    args, C = {}, {}
    for ssp in SSPS:
        a = copy.copy(base)
        a.ssp, a.thresholds, a.threshold_label = ssp, (T["fire"], T["water"]), tlab
        args[ssp], C[ssp] = a, pm.compute(a)
        print()

    pool = lambda f: np.concatenate([f(c)[c["ok"]] for c in C.values()])
    vmax = (float(np.nanpercentile(pool(lambda c: c["b_nf"]), 98)),
            float(np.nanpercentile(pool(lambda c: c["m"]["R4"]["fire"]), 98)),
            float(np.nanpercentile(pool(lambda c: c["m"]["R4"]["water"]), 98)))
    print(f"shared colour maxima (p98 of the four SSPs pooled): benefit {vmax[0]:.2f} MgC/ha, fire {vmax[1]:.3f} %/yr, water {vmax[2]:.3f}")
    for ssp in SSPS:
        pm.draw(args[ssp], C[ssp], vmax)

    # 4 km vs native 0.5 deg loss (net benefit, as in the supplement), fixed thresholds
    loss = {}
    for ssp in SSPS:
        m = C[ssp]["m"]
        budget = base.budget / 100 * m["E"]
        for scr in ("none", "all"):
            w4, w5, *_ = ps.select(m, budget, scr, T)
            g4, g5 = ps.score(m, w4, T)["G_PgC"], ps.score(m, w5, T)["G_PgC"]
            loss[(ssp, scr)] = (g4, g5, 100 * (g4 - g5) / g4)
        print(f"[{ssp}] loss at 0.5 deg, net benefit, {base.budget:g}%: no screen {loss[(ssp, 'none')][2]:.1f}%, "
              f"fire + water {loss[(ssp, 'all')][2]:.1f}%")

    # agreement of the screened 4 km selections
    ref_c = C[REF]
    for c in C.values():
        assert np.array_equal(c["m"]["a4"].shape, ref_c["m"]["a4"].shape)
    sel = {s: C[s]["wS"] for s in SSPS}
    area = {s: float((sel[s] * C[s]["a4"]).sum()) for s in SSPS}
    ov = {}
    for i in SSPS:
        for j in SSPS:
            both = float((np.minimum(sel[i], sel[j]) * np.minimum(C[i]["a4"], C[j]["a4"])).sum())
            ov[(i, j)] = 100 * both / area[i]
    count = sum((sel[s] > 0).astype("f8") for s in SSPS)
    ok_any = np.any([C[s]["ok"] for s in SSPS], axis=0)
    a_any = np.max([C[s]["a4"] for s in SSPS], axis=0)
    count = np.where(ok_any, count, np.nan)
    E_any = float(a_any.sum())
    cshare = {k: 100 * float(a_any[count == k].sum()) / E_any for k in range(5)}
    sel_any = float(a_any[count >= 1].sum())
    print("pairwise overlap of the screened selections (% of the row SSP's selection):")
    for i in SSPS:
        print(f"  {i}: " + ", ".join(f"{j} {ov[(i, j)]:.0f}" for j in SSPS))
    print("eligible land selected in k SSPs: " + ", ".join(f"{k}: {cshare[k]:.1f}%" for k in range(5))
          + f"; of the land selected in any SSP, {100 * float(a_any[count == 4].sum()) / sel_any:.0f}% is selected in all four")

    win = base.years
    os.makedirs(base.out_dir, exist_ok=True)
    with open(os.path.join(base.out_dir, f"fig5_ssp_summary_{win}.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["ssp", "threshold_fire_pct_per_yr", "threshold_water", "eligible_km2", "benefit_nf_eligible_PgC",
                     "benefit_net_eligible_PgC", "above_fire_pct", "above_water_pct", "G_nf_unscreened_PgC", "G_nf_screened_PgC",
                     "screen_cost_pct", "unscreened_top_above_fire_pct", "unscreened_top_above_water_only_pct",
                     "G4_net_noscreen_PgC", "G05_net_noscreen_PgC", "loss05_noscreen_pct", "G4_net_screened_PgC",
                     "G05_net_screened_PgC", "loss05_screened_pct"] + [f"overlap_with_{j}_pct" for j in SSPS])
        for s in SSPS:
            c = C[s]
            wr.writerow([s, f"{T['fire']:.5f}", f"{T['water']:.5f}", f"{c['E']:.1f}", f"{c['benefit_nf_PgC']:.4f}",
                         f"{c['benefit_net_PgC']:.4f}", f"{c['above']['fire']:.2f}", f"{c['above']['water']:.2f}",
                         f"{c['G_unscreened']:.4f}", f"{c['G_screened']:.4f}", f"{100 * (1 - c['G_screened'] / c['G_unscreened']):.2f}",
                         f"{100 * c['excl_fire']:.2f}", f"{100 * c['excl_water']:.2f}"]
                        + [f"{v:.4f}" if k < 2 else f"{v:.2f}" for k, v in enumerate(loss[(s, 'none')])]
                        + [f"{v:.4f}" if k < 2 else f"{v:.2f}" for k, v in enumerate(loss[(s, 'all')])]
                        + [f"{ov[(s, j)]:.1f}" for j in SSPS])

    # ---- summary figure
    import cartopy.crs as ccrs
    m = ref_c["m"]
    lon4, lat4 = m["lon4"], m["lat4"]
    land4 = np.isfinite(m["g4"]) & np.isfinite(m["R4"]["water"])
    inel = np.where(land4 & ~ok_any, 1.0, np.nan)
    fig = plt.figure(figsize=(16.5, 8.6), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(3, 2, width_ratios=[1.25, 1], hspace=0.55, wspace=0.16, left=0.04, right=0.985, top=0.9, bottom=0.17)

    ax = fig.add_subplot(gs[:, 0], projection=ccrs.PlateCarree())
    pm.base_map(ax, lon4, lat4)
    pm.mesh(ax, lon4, lat4, inel, ListedColormap([pm.INELIGIBLE]), Normalize(0, 1))
    pm.mesh(ax, lon4, lat4, count, ListedColormap(COUNT_COLS), Normalize(-0.5, 4.5))
    pm.title(ax, "a", f"Robust priority land: selected in how many SSPs (top {base.budget:g}%, screened)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=COUNT_COLS[k]) for k in (4, 3, 2, 1, 0)]
    labels = [f"{k} of 4 SSPs ({cshare[k]:.0f}%)" if k else f"none ({cshare[0]:.0f}%)" for k in (4, 3, 2, 1, 0)]
    ax.legend(handles, labels, loc="lower left", fontsize=8.6, framealpha=0.93, edgecolor="none",
              title="share of eligible land", title_fontsize=8)
    others = [s for s in SSPS if s != REF]
    ax.text(0.98, 0.03, f"overlap with the {REF} selection:\n" + "\n".join(f"{s}  {ov[(REF, s)]:.0f}%" for s in others),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=9, color=ps.INK,
            bbox=dict(facecolor=ps.SURFACE, edgecolor="none", alpha=0.9, pad=3))

    x = np.arange(len(SSPS))
    axb = fig.add_subplot(gs[0, 1])
    wd = 0.38
    for k, (key, lab, hatch) in enumerate((("G_unscreened", "unscreened", None), ("G_screened", "screened (fire + water)", "//"))):
        vals = [C[s][key] for s in SSPS]
        axb.bar(x + (k - 0.5) * wd, vals, wd, color=[SSP_COL[s] if hatch is None else ps.SURFACE for s in SSPS],
                edgecolor=[SSP_COL[s] for s in SSPS], hatch=hatch, linewidth=1.4, zorder=3, label=lab)
    for xi, s in zip(x, SSPS):
        c = C[s]
        axb.text(xi + 0.5 * wd, c["G_screened"], f"−{100 * (1 - c['G_screened'] / c['G_unscreened']):.1f}%",
                 ha="center", va="bottom", fontsize=8, color=ps.INK2)
    axb.set_xticks(x)
    axb.set_xticklabels(SSPS, fontsize=9)
    ps.style(axb, "PgC")
    axb.set_ylim(0, axb.get_ylim()[1] * 1.18)
    leg = axb.legend(frameon=False, fontsize=8.4, loc="upper left", ncol=2)
    for h in leg.legend_handles:
        h.set_facecolor("#bbbbbb" if h.get_hatch() is None else ps.SURFACE)
        h.set_edgecolor("#777777")
    ps.ptitle(axb, "b", f"Benefit without fire loss captured by the top {base.budget:g}%")

    axc = fig.add_subplot(gs[1, 1])
    wd = 0.36
    for k, (key, lab, col) in enumerate((("fire", "fire", pm.FIRE_CMAP(0.6)), ("water", "water stress", pm.WATER_CMAP(0.6)))):
        vals = [C[s]["above"][key] for s in SSPS]
        axc.bar(x + (k - 0.5) * wd, vals, wd, color=col, edgecolor=ps.SURFACE, linewidth=1.2, zorder=3, label=lab)
        for xi, v in zip(x, vals):
            axc.text(xi + (k - 0.5) * wd, v, f"{v:.0f}", ha="center", va="bottom", fontsize=7.8, color=ps.INK2)
    axc.axhline(100 - base.pct, color=ps.INK, lw=0.9, ls="--")
    axc.set_xticks(x)
    axc.set_xticklabels(SSPS, fontsize=9)
    ps.style(axc, "% of eligible land")
    axc.set_ylim(0, axc.get_ylim()[1] * 1.2)
    axc.legend(frameon=False, fontsize=8.4, loc="upper left", ncol=2)
    ps.ptitle(axc, "c", f"Eligible land above the fixed {tlab} thresholds")

    axd = fig.add_subplot(gs[2, 1])
    for k, (scr, lab, hatch) in enumerate((("none", "no screen", None), ("all", "fire + water screen", "//"))):
        vals = [loss[(s, scr)][2] for s in SSPS]
        axd.bar(x + (k - 0.5) * wd, vals, wd, color=ps.RES_COL["0.5deg"] if hatch is None else ps.SURFACE,
                edgecolor=ps.RES_COL["0.5deg"], hatch=hatch, linewidth=1.4, zorder=3, label=lab)
        for xi, v in zip(x, vals):
            axd.text(xi + (k - 0.5) * wd, v, f"{v:.1f}", ha="center", va="bottom", fontsize=7.8, color=ps.INK2)
    axd.set_xticks(x)
    axd.set_xticklabels(SSPS, fontsize=9)
    ps.style(axd, "% of the 4 km benefit")
    axd.set_ylim(0, axd.get_ylim()[1] * 1.2)
    axd.legend(frameon=False, fontsize=8.4, loc="upper left", ncol=2)
    ps.ptitle(axd, "d", "Benefit lost when the 0.5° map chooses the land")

    fig.suptitle(f"Is the 4 km siting robust across scenarios? SEUS, RF, {win}, four SSPs", fontsize=13.5, color=ps.INK,
                 x=0.04, ha="left", y=0.975)
    fig.text(0.04, 0.012,
             f"Every SSP uses the same absolute thresholds, the {tlab} (fire {T['fire']:.3g} %/yr, water stress {T['water']:.3g}), so (c) shows how much "
             "land each scenario puts at risk.\nSelection (a, b) = top {0:g}% of eligible land by the benefit without fire loss after removing land above "
             "either threshold; percentages in (b) = benefit given up by the screen.\n(d) uses the net benefit (fire loss not added back) and the native "
             "0.5° run's own benefit and risk to choose the same area, scored on the 4 km field (supplement convention).\nEligible land = each SSP's RF "
             "2060 forest fraction (cells ≥ {1:g}). Adding the fire loss back is an approximation; fire has ~0.5° effective resolution at 4 km. "
             "RF is restoration plus a region-wide harvest ban.".format(base.budget, base.floor),
             fontsize=8.4, color=ps.INK2, va="bottom", ha="left")
    png = os.path.join(base.out_dir, f"fig5_ssp_summary_{win}.png")
    fig.savefig(png, dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
