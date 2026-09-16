"""
Compare the 6 future (2024-2100) SEUS 0.5-deg scenarios: SSP1-1.9, SSP2-4.5,
SSP3-7.0 (+ RF reforest / DF deforest-counterfactual / RH reduced-harvest
management variants), SSP5-8.5.

Prepends the transient-run 2014-2023 decade as a shared historical baseline
so all scenario lines start from the same point in 2023/2024.

Runs directly on Pathfinder. Figures written to OUTDIR_ROOT.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import TRANSIENT, FUTURE, FUTURE_STYLE, OUTDIR_ROOT, load_annual_domain_series

OUTDIR = OUTDIR_ROOT
os.makedirs(OUTDIR, exist_ok=True)

VARS = ["GPP", "NPP", "NBP", "TOTVEGC", "TOTSOMC"]


def main():
    print(f"Loading transient tail (2014-2023) for baseline context...")
    hist = load_annual_domain_series(TRANSIENT, VARS)
    tail = hist["year"] >= 2014

    series_by_scenario = {}
    for label, case in FUTURE.items():
        print(f"Loading {label} ({case})...")
        series_by_scenario[label] = load_annual_domain_series(case, VARS)

    panels = [
        ("GPP", "GPP (domain-mean, gC m$^{-2}$ yr$^{-1}$)"),
        ("NPP", "NPP (domain-mean, gC m$^{-2}$ yr$^{-1}$)"),
        ("NBP", "NBP (domain-mean, gC m$^{-2}$ yr$^{-1}$; +ve = sink)"),
        ("TOTVEGC", "Vegetation C (domain-mean, gC m$^{-2}$)"),
        ("TOTSOMC", "Soil organic C (domain-mean, gC m$^{-2}$)"),
    ]

    fig, axes = plt.subplots(3, 2, figsize=(14, 12), sharex=True)
    axes = axes.flat
    for ax, (var, ylabel) in zip(axes, panels):
        ax.plot(hist["year"][tail], hist[var][tail], color="k", lw=1.5, label="historical (2014-2023)")
        for label, d in series_by_scenario.items():
            style = FUTURE_STYLE[label]
            ax.plot(d["year"], d[var], lw=1.3, label=label, **style)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.grid(alpha=0.3)
        if var == "NBP":
            ax.axhline(0, color="gray", lw=0.6)
    axes[0].legend(fontsize=7, loc="best")
    for ax in list(axes)[-2:]:
        ax.set_xlabel("year")

    fig.suptitle("SEUS 0.5° future scenarios (2024–2100): domain-mean carbon fluxes/pools", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, "future_scenario_comparison_timeseries.png"), dpi=150)
    plt.close(fig)

    # Cumulative domain NBP (PgC) by scenario -- net carbon balance trajectory.
    # Split into two panels (2026-09-15): the 4 SSP baselines vs the 3
    # SSP3-7.0 management practices. Each line is that CASE'S OWN raw
    # cumulative NBP (cumsum of its own domain-total NBP since 2024) --
    # NOT a difference from Default. RF/RH/DF are all drawn the same way (no
    # special-casing DF's sign), so DF shows up as its own steep, deeply
    # negative trajectory (a rapidly-deforested world's actual net carbon
    # balance), not a pre-computed "avoided loss" curve. SSP3-7.0 Default is
    # included in the management panel as the shared reference line. A
    # separate, explicitly-labeled *derived offset* figure (Default-DF,
    # RF-Default, RH-Default) is a different, complementary product -- see
    # ../../paper_carbon_offset/fig01_offset_potential_timeseries.py, which
    # does this for the TOTECOSYSC stock (not the NBP flux); don't conflate
    # the two kinds of figure.
    SSP_GROUP = ["SSP1-1.9", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]
    MGMT_GROUP = ["SSP3-7.0", "SSP3-7.0 RF (reforest)", "SSP3-7.0 DF (deforest counterfactual)",
                  "SSP3-7.0 RH (reduced harvest)"]

    fig2, (axA, axB) = plt.subplots(1, 2, figsize=(15, 6), sharey=False)
    for ax, group, title in [(axA, SSP_GROUP, "A. Four SSP baselines"),
                              (axB, MGMT_GROUP, "B. SSP3-7.0 management practices\n"
                                                "(Default shown as reference)")]:
        for label in group:
            if label not in series_by_scenario:
                continue
            d = series_by_scenario[label]
            style = dict(FUTURE_STYLE[label])
            if label == "SSP3-7.0" and group is MGMT_GROUP:
                style = dict(color="k", ls="-")  # reference line, not a management practice
            cum = np.cumsum(np.nan_to_num(d["NBP_domaintotal"]))
            lw = 2.0 if (label == "SSP3-7.0" and group is MGMT_GROUP) else 1.5
            ax.plot(d["year"], cum, lw=lw, label=label, **style)
        ax.axhline(0, color="gray", lw=0.6)
        ax.set_xlabel("year")
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    axA.set_ylabel("Cumulative domain NBP since 2024 (PgC)\n(each case's own trajectory, not a difference)")

    fig2.suptitle("SEUS 0.5°: cumulative net carbon balance, 2024–2100", fontsize=13)
    fig2.tight_layout()
    fig2.savefig(os.path.join(OUTDIR, "future_scenario_cumulative_nbp_split.png"), dpi=150)
    plt.close(fig2)

    # 2091-2100 end-of-century summary bar chart for TOTVEGC and TOTSOMC deltas
    # relative to 2024.
    fig3, axs3 = plt.subplots(1, 2, figsize=(12, 5))
    labels = list(FUTURE.keys())
    for ax, var, title in zip(axs3, ["TOTVEGC", "TOTSOMC"],
                                ["Vegetation C change (2091-2100 mean vs 2024)",
                                 "Soil organic C change (2091-2100 mean vs 2024)"]):
        deltas = []
        colors = []
        for label in labels:
            d = series_by_scenario[label]
            end_mean = np.nanmean(d[var][d["year"] >= 2091])
            start = d[var][d["year"] == 2024]
            start = start[0] if len(start) else np.nan
            deltas.append(end_mean - start)
            colors.append(FUTURE_STYLE[label]["color"])
        ax.barh(labels, deltas, color=colors)
        ax.axvline(0, color="k", lw=0.8)
        ax.set_xlabel("gC m$^{-2}$")
        ax.set_title(title, fontsize=10)
        ax.grid(alpha=0.3, axis="x")
    fig3.tight_layout()
    fig3.savefig(os.path.join(OUTDIR, "future_scenario_endofcentury_pool_change.png"), dpi=150)
    plt.close(fig3)

    print("\nEnd-of-century (2091-2100 mean) summary:")
    for label, d in series_by_scenario.items():
        end = d["year"] >= 2091
        print(f"  {label}: GPP={np.nanmean(d['GPP'][end]):.1f} NBP={np.nanmean(d['NBP'][end]):+.2f} "
              f"TOTVEGC={np.nanmean(d['TOTVEGC'][end]):.1f} TOTSOMC={np.nanmean(d['TOTSOMC'][end]):.1f}")

    print(f"\nFigures written to {OUTDIR}")


if __name__ == "__main__":
    main()
