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

    # Historical context line for panel A only (2026-09-16): the transient
    # run's own cumulative NBP over its last decade (2014-2023), same "tail"
    # window used for the historical line in the first figure above. Panel
    # A's four SSP-baseline lines are then OFFSET to start from where this
    # historical line ends in 2024, so panel A reads as one continuous
    # accumulation (2014-2100) rather than four lines that visually reset to
    # zero at 2024. Panel B is left as-is (each management practice's own
    # cumsum since 2024, no history splice) -- SSP3-7.0's management
    # variants don't diverge before 2024 anyway, and splicing history in
    # would just duplicate panel A's black line with no new information.
    hist_tail_mask = hist["year"] >= 2014
    hist_tail_years = hist["year"][hist_tail_mask]
    hist_cum = np.cumsum(np.nan_to_num(hist["NBP_domaintotal"][hist_tail_mask]))
    hist_cum_end = float(hist_cum[-1])

    fig2, (axA, axB) = plt.subplots(1, 2, figsize=(15, 6), sharey=False)
    for ax, group, title in [(axA, SSP_GROUP, "A. Four SSP baselines"),
                              (axB, MGMT_GROUP, "B. SSP3-7.0 management practices\n"
                                                "(Default shown as reference)")]:
        if group is SSP_GROUP:
            ax.plot(hist_tail_years, hist_cum, color="k", lw=1.8,
                     label="Historical (2014-2023)", zorder=10)
        offset = hist_cum_end if group is SSP_GROUP else 0.0
        for label in group:
            if label not in series_by_scenario:
                continue
            d = series_by_scenario[label]
            style = dict(FUTURE_STYLE[label])
            if label == "SSP3-7.0" and group is MGMT_GROUP:
                style = dict(color="k", ls="-")  # reference line, not a management practice
            cum = offset + np.cumsum(np.nan_to_num(d["NBP_domaintotal"]))
            lw = 2.0 if (label == "SSP3-7.0" and group is MGMT_GROUP) else 1.5
            ax.plot(d["year"], cum, lw=lw, label=label, **style)
        ax.axhline(0, color="gray", lw=0.6)
        ax.set_xlabel("year")
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    axA.set_ylabel("Cumulative domain NBP since 2014 (PgC)\n"
                    "(historical 2014-2023, then each scenario's own future trajectory)")
    axB.set_ylabel("Cumulative domain NBP since 2024 (PgC)\n(each case's own trajectory, not a difference)")

    fig2.suptitle("SEUS 0.5°: cumulative net carbon balance, 2024–2100", fontsize=13)
    fig2.tight_layout()
    fig2.savefig(os.path.join(OUTDIR, "future_scenario_cumulative_nbp_split.png"), dpi=150)
    plt.close(fig2)

    # Full-history variant (2026-09-16, user request): a SEPARATE figure
    # using the ENTIRE 1850-2023 historical trajectory instead of just the
    # 2014-2023 tail, both panels this time (not just A) -- a complete
    # "since the model's beginning" picture. Kept as its own file, not a
    # replacement for future_scenario_cumulative_nbp_split.png above (the
    # poster-ready version): the full record is a genuinely different
    # story (SEUS was a net carbon SOURCE for most of 1850-2023, bottoming
    # out around -4.6 PgC circa 1956 from historical land clearing, and had
    # only recovered to -1.3 PgC by 2023 -- it does not cross back to being
    # a net sink until partway through the future period), and forcing it
    # onto the same clean axis as the poster panel would misrepresent both.
    hist_full_cum = np.cumsum(np.nan_to_num(hist["NBP_domaintotal"]))
    hist_full_end = float(hist_full_cum[-1])

    fig2b, (axA3, axB3) = plt.subplots(1, 2, figsize=(15, 6), sharey=False)
    for ax, group, title in [(axA3, SSP_GROUP, "A. Four SSP baselines"),
                              (axB3, MGMT_GROUP, "B. SSP3-7.0 management practices\n"
                                                 "(Default shown as reference)")]:
        ax.plot(hist["year"], hist_full_cum, color="k", lw=1.3,
                 label="Historical (1850-2023)", zorder=10)
        for label in group:
            if label not in series_by_scenario:
                continue
            d = series_by_scenario[label]
            style = dict(FUTURE_STYLE[label])
            if label == "SSP3-7.0" and group is MGMT_GROUP:
                style = dict(color="k", ls="-")
            cum = hist_full_end + np.cumsum(np.nan_to_num(d["NBP_domaintotal"]))
            lw = 2.0 if (label == "SSP3-7.0" and group is MGMT_GROUP) else 1.5
            ax.plot(d["year"], cum, lw=lw, label=label, **style)
        ax.axhline(0, color="gray", lw=0.6)
        ax.set_xlabel("year")
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc="lower right")
    axA3.set_ylabel("Cumulative domain NBP since 1850 (PgC)\n"
                     "(historical 1850-2023, then each scenario's own future trajectory)")
    axB3.set_ylabel("Cumulative domain NBP since 1850 (PgC)\n"
                     "(historical 1850-2023, then each management practice's own future trajectory)")
    fig2b.suptitle("SEUS 0.5°: cumulative net carbon balance, full history 1850–2100", fontsize=13)
    fig2b.tight_layout()
    fig2b.savefig(os.path.join(OUTDIR, "future_scenario_cumulative_nbp_full_history.png"), dpi=150)
    plt.close(fig2b)
    print(f"\nFull 1850-2023 cumulative NBP: {hist_full_end:+.3f} PgC "
          f"(min {hist_full_cum.min():+.3f} PgC at year {int(hist['year'][np.argmin(hist_full_cum)])})")

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

    # Historical vs. future accumulated carbon, for the poster's Panel-3
    # bullet points (2026-09-16). "Accumulated" = sum of domain-total NBP
    # (PgC) over the window; "rate" = mean of the domain-MEAN NBP
    # (gC/m2/yr) over the same window, in kgC/m2/yr (+ve = sink).
    print(f"\nHistorical accumulated carbon (2014-2023, {hist_tail_years.size} yr):")
    hist_rate_gm2yr = np.nanmean(hist["NBP"][hist_tail_mask])
    print(f"  cumulative NBP = {hist_cum_end:+.3f} PgC   "
          f"mean rate = {hist_rate_gm2yr/1000.0:+.4f} kgC/m^2/yr")

    print("\nFuture accumulated carbon (2024-2100, per scenario):")
    for label, d in series_by_scenario.items():
        cum_2100 = float(np.cumsum(np.nan_to_num(d["NBP_domaintotal"]))[-1])
        rate_gm2yr = np.nanmean(d["NBP"])
        print(f"  {label}: cumulative NBP = {cum_2100:+.3f} PgC   "
              f"mean rate = {rate_gm2yr/1000.0:+.4f} kgC/m^2/yr")

    print(f"\nFigures written to {OUTDIR}")


if __name__ == "__main__":
    main()
