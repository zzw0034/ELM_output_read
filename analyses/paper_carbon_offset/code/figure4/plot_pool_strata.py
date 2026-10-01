"""
Main Figure 4 / Results 3.3 (blueprint E4): which carbon pools carry the management
benefit, and when they move.

Panels (one SSP, 4 km; defaults SSP3-7.0):
  a  Default stock composition by pool, PgC (mean of 2091-2100)
  b  signed pool contributions to RF - Default and RH - Default, PgC (mean of 2091-2100)
  c  RF - Default, living vegetation, 2024-2100 (annual domain totals, PgC)
  d  RH - Default, living vegetation, 2024-2100
  e  RF - Default, the other pools (dead wood + litter, soil, wood products), 2024-2100
  f  RH - Default, the other pools, 2024-2100
The three-boundary panel and the land-cover increment bins were removed from the figure on
2026-10-01 (user decision); the boundary numbers are still printed and written to the pool CSV,
and the bins are recorded in notes 3.16 (made by this script at commit f850ac1).

Pools (D4), four, adding up to TOTECOSYSC (grouping chosen by the user 2026-10-01):
living vegetation = TOTVEGC; dead wood and litter = CWDC + TOTLITC; soil organic carbon over the
whole column = TOTSOMC; wood products = TOTECOSYSC - (TOTVEGC + CWDC + TOTLITC + TOTSOMC), derived
because TOTPRODC is not in h0 (must be >= 0 in Default). Two finer quantities are kept in the
printout, the CSVs and the note: aboveground vegetation (TOTVEGC_ABG, panel c's narrowest
boundary) and SOC 0-100 cm (TOTSOMC_1m, comparable to field studies).

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python \\
        code/figure4/plot_pool_strata.py --res 4km [--ssp SSP3-7.0]
Inputs (pulled from proj-shared, git-ignored): in _cache/figure4/<res>/, made by
extract_pool_maps.py and extract_soc1m.py:
    <SSP>[_RF|_RH]__pools_2091-2100.npz   <SSP>[_RF|_RH]__soc1m_2024-2100.npz
and, for panels c-f (4 km), the annual domain totals of extract_domain_totals.py in
_cache/figure2/future_4km/<SSP>[_RF|_RH]__totals.npz.
Outputs: figures/figure4/fig4_pools_<res>_<SSP>_<y0>-<y1>.png, the pool CSV and the trajectory CSV.
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # analysis root

# dataviz reference palette (light). Management uses slots 1-2 (as in Figure 2);
# pools use slots 3-8 so a pool colour never repeats a management colour.
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e9e8e4", "#fcfcfb"
MGMT = {"RF": "#2a78d6", "RH": "#eb6834"}
POOLS = [("veg", "Living vegetation", "#1baf7a"),
         ("dead", "Dead wood and litter", "#e87ba4"),
         ("soil", "Soil organic carbon (whole column)", "#4a3aa7"),
         ("prod", "Wood products (derived)", "#e34948")]
POOL_SHORT = {"veg": "Living\nvegetation", "dead": "Dead wood\n+ litter", "soil": "Soil\n(whole column)", "prod": "Wood\nproducts"}
POOL_LINE = {"veg": "Living vegetation", "dead": "Dead wood + litter", "soil": "Soil (whole column)", "prod": "Wood products"}
GC_M2_TO_MGC_HA = 0.01
FLUX_VARS = ["NBP", "NEP", "LAND_USE_FLUX", "WOOD_HARVESTC"]


# ------------------------------------------------------------------- numbers

def load(path):
    assert os.path.exists(path), f"missing input {path}"
    z = np.load(path)
    return {k: z[k] for k in z.files}


def pools_of(m):
    """Four pools in gC/m2 from the h0 stock maps (D4 closure, products derived)."""
    prod = m["TOTECOSYSC"] - (m["TOTVEGC"] + m["CWDC"] + m["TOTLITC"] + m["TOTSOMC"])
    return {"veg": m["TOTVEGC"], "dead": m["CWDC"] + m["TOTLITC"], "soil": m["TOTSOMC"], "prod": prod}


def pg(field, area, mask):
    """Domain total in PgC (or PgC/yr) of a gC/m2 field over mask: gC/m2 x km2 x 1e6 m2/km2 / 1e15."""
    return float(np.sum(field[mask].astype("f8") * area[mask]) * 1e6 / 1e15)


def style(ax, ylabel=None, grid_axis="y"):
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=10.5)
    ax.grid(axis=grid_axis, color=GRID, lw=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("black")
        ax.spines[sp].set_linewidth(1.0)
    ax.tick_params(colors="black", labelcolor=INK, labelsize=9.5, length=3.5, width=0.9)
    ax.axhline(0, color="black", lw=0.9, zorder=1)


def ptitle(ax, letter, text):
    ax.set_title(f"{letter}  {text}", loc="left", fontsize=11, color=INK, fontweight="bold")


def spread(ys, gap):
    """Push label y-positions apart so neighbours are >= gap apart (order kept)."""
    order = np.argsort(ys)
    out = np.array(ys, float)
    for a, b in zip(order[:-1], order[1:]):
        if out[b] - out[a] < gap:
            out[b] = out[a] + gap
    return out


def panel_a(ax, P_def, area, valid):
    tot = {k: pg(P_def[k], area, valid) for k, _, _ in POOLS}
    total = sum(tot.values())
    bottom, ys = 0.0, []
    for k, name, c in POOLS:
        ax.bar(0, tot[k], 0.55, bottom=bottom, color=c, edgecolor=SURFACE, linewidth=1.5, zorder=3)
        ys.append(bottom + tot[k] / 2)
        bottom += tot[k]
    ly = spread(ys, total * 0.06)
    for (k, name, c), y0, y1 in zip(POOLS, ys, ly):
        ax.text(0.34, y1, f"{POOL_SHORT[k].replace(chr(10), ' ')} {tot[k]:.2f} ({100 * tot[k] / total:.0f}%)",
                va="center", fontsize=8.6, color=INK2)
    ax.set_xlim(-0.45, 2.3)
    ax.set_xticks([])
    style(ax, "Default stock (PgC)")
    ax.grid(False)
    ax.set_ylim(0, total * 1.04)
    ptitle(ax, "a", "Default stock by pool")
    return tot


def panel_b(ax, P, area, valid):
    keys = [k for k, _, _ in POOLS]
    vals = {mg: [pg(P[mg][k] - P["Def"][k], area, valid) for k in keys] for mg in ("RF", "RH")}
    for mg in vals:
        vals[mg].append(sum(vals[mg]))
    x = np.arange(len(keys) + 1)
    w = 0.36
    for i, mg in enumerate(("RF", "RH")):
        ax.bar(x + (i - 0.5) * w, vals[mg], w, color=MGMT[mg], edgecolor=SURFACE, linewidth=1.2, zorder=3, label=mg)
    for xi, v in zip(x[-1:], vals["RF"][-1:]):
        ax.text(xi - 0.5 * w, v, f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=8.8, color=INK2)
    for xi, v in zip(x[-1:], vals["RH"][-1:]):
        ax.text(xi + 0.5 * w, v, f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=8.8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([POOL_SHORT[k] for k in keys] + ["Total"], fontsize=8.4)
    style(ax, "Change vs Default (PgC)")
    lo, hi = min(0, min(vals["RF"] + vals["RH"])), max(0, max(vals["RF"] + vals["RH"]))
    ax.set_ylim(lo - 0.08 * (hi - lo), hi + 0.22 * (hi - lo))
    ax.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=2)
    ptitle(ax, "b", "Signed pool contributions")
    return vals


# ------------------------------------------------------------- trajectories

def traj_pools(tot):
    """Four pools as annual domain totals (PgC) from the Figure 2 totals."""
    prod = tot["TOTECOSYSC"] - (tot["TOTVEGC"] + tot["CWDC"] + tot["TOTLITC"] + tot["TOTSOMC"])
    return {"veg": tot["TOTVEGC"], "dead": tot["CWDC"] + tot["TOTLITC"], "soil": tot["TOTSOMC"], "prod": prod}


def traj_deltas(fig2_dir, soc_dir, ssp):
    """{'year', mgmt: (pool deltas, total delta, extras)} vs the 36000 s Default, 2024-2100.
    extras: aboveground vegetation and SOC 0-100 cm differences (from the soc1m extract)."""
    ld = lambda sfx: (np.load(os.path.join(fig2_dir, f"{ssp}{sfx}__totals.npz"), allow_pickle=True),
                      np.load(os.path.join(soc_dir, f"{ssp}{sfx}__soc1m_2024-2100.npz"), allow_pickle=True))
    (tD, sD), runs = ld(""), {"RF": ld("_RF"), "RH": ld("_RH")}
    assert np.array_equal(tD["year"], sD["year"]), "year axes of totals and soc1m differ"
    assert (tD["TOTSOMC"] - sD["total_PgC"] >= -1e-6).all(), "TOTSOMC_1m exceeds TOTSOMC"
    PD = traj_pools(tD)
    out = {"year": tD["year"]}
    for nm, (t, s1) in runs.items():
        assert np.array_equal(t["year"], tD["year"]) and np.array_equal(s1["year"], tD["year"]), f"{nm}: year axis differs"
        PR = traj_pools(t)
        delta = {k: PR[k] - PD[k] for k, _, _ in POOLS}
        total = t["TOTECOSYSC"] - tD["TOTECOSYSC"]
        assert np.allclose(sum(delta.values()), total, atol=1e-9), f"{nm}: pools do not add up to TOTECOSYSC"
        extras = {"abg": t["TOTVEGC_ABG"] - tD["TOTVEGC_ABG"], "soc_0_100": s1["total_PgC"] - sD["total_PgC"]}
        out[nm] = (delta, total, extras)
    return out


def panel_traj(ax, yr, delta, keys, letter, title, label_ends=True):
    """Annual differences of the chosen pools (no total line), each pool in its Figure 4 colour."""
    col = {k: c for k, _, c in POOLS}
    for k in keys:
        ax.plot(yr, delta[k], color=col[k], lw=2.2)
    if label_ends:
        ends = [delta[k][-1] for k in keys]
        span = max(max(abs(v) for v in ends), 1e-6)
        for k, y1 in zip(keys, spread(ends, span * 0.12)):
            ax.text(2101.5, y1, POOL_LINE[k], color=INK2, fontsize=9, va="center", clip_on=False)
    ax.set_xlim(2024, 2100)
    style(ax, "Difference vs Default (PgC)")
    ptitle(ax, letter, title)


# ---------------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="4km", choices=["4km", "0.5deg"])
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100", help="end-state window of the maps (as extracted)")
    ap.add_argument("--cache-root", default=os.path.join(ROOT, "_cache/figure4"))
    ap.add_argument("--fig2-cache", default=os.path.join(ROOT, "_cache/figure2/future_4km"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "figures/figure4"))
    a = ap.parse_args()

    cdir = os.path.join(a.cache_root, a.res)
    win = a.years
    y0, y1 = (int(v) for v in win.split("-"))
    runs = {"Def": a.ssp, "RF": f"{a.ssp}_RF", "RH": f"{a.ssp}_RH"}
    maps = {k: load(os.path.join(cdir, f"{t}__pools_{win}.npz")) for k, t in runs.items()}
    soc1 = {k: load(os.path.join(cdir, f"{t}__soc1m_2024-2100.npz")) for k, t in runs.items()}
    for k in maps:
        for g in ("lat", "lon", "area_km2"):
            assert np.array_equal(soc1[k][g], maps["Def"][g]), f"{k} soc1m: {g} differs from the Default pools grid"
        assert tuple(int(v) for v in soc1[k]["map_years"]) == (y0, y1), f"{k}: soc1m map window is not {win}"
        maps[k]["TOTSOMC_1m"] = soc1[k]["mean_map"]
    lat, lon, area = maps["Def"]["lat"], maps["Def"]["lon"], maps["Def"]["area_km2"].astype("f8")
    lon = np.where(lon > 180, lon - 360, lon)

    STK = ("TOTECOSYSC", "TOTVEGC", "TOTVEGC_ABG", "CWDC", "TOTLITC", "TOTSOMC", "TOTSOMC_1m")
    # float32 stocks of ~3e4 gC/m2 carry ~2e-3 gC/m2 rounding: add them in float64
    P = {k: pools_of({v: m[v].astype("f8") for v in STK}) for k, m in maps.items()}
    F = {k: {v: m[v] for v in FLUX_VARS} for k, m in maps.items()}

    valid = area > 0
    for k in P:
        for v in P[k].values():
            valid &= np.isfinite(v)
    for k in F:
        for v in F[k].values():
            valid &= np.isfinite(v)
    print(f"{a.res} {a.ssp} {win}: {int(valid.sum())} valid land cells, {area[valid].sum() / 1e3:.1f} x10^3 km2 "
          f"(of {int((area > 0).sum())} land cells)")

    # ---- checks, all printed
    for k in P:
        closure = np.abs(sum(P[k].values())[valid] - maps[k]["TOTECOSYSC"][valid].astype("f8")).max()
        assert closure < 1e-6, f"{k}: pools do not sum to TOTECOSYSC (max {closure})"
        deep = maps[k]["TOTSOMC"].astype("f8") - maps[k]["TOTSOMC_1m"].astype("f8")
        assert float(deep[valid].min()) > -0.01, f"{k}: TOTSOMC_1m exceeds TOTSOMC in a cell by {-float(deep[valid].min())} gC/m2"
        print(f"  derived product pool {k:3s}: {pg(P[k]['prod'], area, valid):+.4f} PgC (min per cell {P[k]['prod'][valid].min():+.2f} gC/m2); "
              f"soil whole column {pg(P[k]['soil'], area, valid):.2f}, of which 0-100 cm {pg(maps[k]['TOTSOMC_1m'], area, valid):.2f} PgC")
    assert pg(P["Def"]["prod"], area, valid) >= -1e-3, \
        "derived product pool of Default is negative: TOTPRODC is not in TOTECOSYSC here, re-check D4"
    dom_total = {mg: pg(maps[mg]["TOTECOSYSC"].astype("f8") - maps["Def"]["TOTECOSYSC"].astype("f8"), area, valid)
                 for mg in ("RF", "RH")}

    # ---- pool table (always): stocks, signed contributions, three boundaries
    print(f"\nDefault stock {win} (PgC): " + ", ".join(f"{POOL_LINE[k]} {pg(P['Def'][k], area, valid):.2f}" for k, _, _ in POOLS))
    print(f"{'pool':36s}{'RF-Def PgC':>11s}{'RH-Def PgC':>11s}")
    d_pool = {mg: {k: pg(P[mg][k] - P["Def"][k], area, valid) for k, _, _ in POOLS} for mg in ("RF", "RH")}
    for k, name, _ in POOLS:
        print(f"{name:36s}{d_pool['RF'][k]:+11.3f}{d_pool['RH'][k]:+11.3f}")
    for mg in ("RF", "RH"):
        assert abs(sum(d_pool[mg].values()) - dom_total[mg]) < 1e-6 * max(1.0, abs(dom_total[mg]))
    print(f"{'Total (= TOTECOSYSC difference)':36s}{dom_total['RF']:+11.3f}{dom_total['RH']:+11.3f}")
    insitu = {mg: dom_total[mg] - d_pool[mg]["prod"] for mg in ("RF", "RH")}
    diff = lambda mg, v: pg(maps[mg][v].astype("f8") - maps["Def"][v].astype("f8"), area, valid)
    d_extra = {mg: {"abg": diff(mg, "TOTVEGC_ABG"), "soc_0_100": diff(mg, "TOTSOMC_1m")} for mg in ("RF", "RH")}
    def_extra = {"abg": pg(maps["Def"]["TOTVEGC_ABG"], area, valid), "soc_0_100": pg(maps["Def"]["TOTSOMC_1m"], area, valid)}
    print(f"{'  of which aboveground vegetation':36s}{d_extra['RF']['abg']:+11.3f}{d_extra['RH']['abg']:+11.3f}")
    print(f"{'  of which SOC 0-100 cm':36s}{d_extra['RF']['soc_0_100']:+11.3f}{d_extra['RH']['soc_0_100']:+11.3f}")
    print("Boundaries (PgC)   aboveground | in-situ (excl. products) | ecosystem + products")
    for mg in ("RF", "RH"):
        print(f"  {mg}-Def  {d_extra[mg]['abg']:+.3f} | {insitu[mg]:+.3f} | {dom_total[mg]:+.3f}")
    print(f"  RF/RH ratio  {d_extra['RF']['abg'] / d_extra['RH']['abg']:.2f} | {insitu['RF'] / insitu['RH']:.2f} "
          f"| {dom_total['RF'] / dom_total['RH']:.2f}")
    print("  (RF = restoration + harvest ban everywhere; its difference also holds the SSP's own land-use drift)")

    # ---- trajectories 2024-2100 (4 km only: the Figure 2 totals exist at 4 km)
    have_traj = a.res == "4km" and all(os.path.exists(os.path.join(a.fig2_cache, f"{a.ssp}{s}__totals.npz")) for s in ("", "_RF", "_RH"))
    T = None
    if have_traj:
        T = traj_deltas(a.fig2_cache, cdir, a.ssp)
        end = T["year"] >= y0
        print(f"\nCross-check, mean {win} of the annual totals vs the maps (PgC):")
        for mg in ("RF", "RH"):
            dlt, tot, ext = T[mg]
            print(f"  {mg}: total {tot[end].mean():+.3f} vs {dom_total[mg]:+.3f}; soil {dlt['soil'][end].mean():+.3f} vs {d_pool[mg]['soil']:+.3f}; "
                  f"SOC 0-100 cm {ext['soc_0_100'][end].mean():+.3f} vs {d_extra[mg]['soc_0_100']:+.3f}")
            if abs(tot[end].mean() - dom_total[mg]) > 0.02:
                print(f"  WARNING: {mg} totals differ by more than 0.02 PgC between the two sources")
        print(f"{'RF - Default, PgC':24s}" + "".join(f"{y:>8d}" for y in (2030, 2050, 2075, 2100)))
        for k, _, _ in POOLS:
            print(f"  {POOL_LINE[k]:22s}" + "".join(f"{T['RF'][0][k][list(T['year']).index(y)]:+8.2f}" for y in (2030, 2050, 2075, 2100)))
        print(f"  {'Total':22s}" + "".join(f"{T['RF'][1][list(T['year']).index(y)]:+8.2f}" for y in (2030, 2050, 2075, 2100)))
        print(f"  {'(SOC 0-100 cm)':22s}" + "".join(f"{T['RF'][2]['soc_0_100'][list(T['year']).index(y)]:+8.2f}" for y in (2030, 2050, 2075, 2100)))
    else:
        print("\nNo 2024-2100 trajectories (needs 4 km and the Figure 2 totals); panels d-e skipped")

    os.makedirs(a.out_dir, exist_ok=True)
    base_name = f"fig4_pools_{a.res}_{a.ssp}_{win}"
    with open(os.path.join(a.out_dir, f"fig4_pools_{a.res}_{a.ssp}_{win}.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["pool", "Default_PgC", "RF_minus_Default_PgC", "RH_minus_Default_PgC"])
        for k, name, _ in POOLS:
            w.writerow([name, f"{pg(P['Def'][k], area, valid):.5f}", f"{d_pool['RF'][k]:.5f}", f"{d_pool['RH'][k]:.5f}"])
        w.writerow(["Total", f"{sum(pg(P['Def'][k], area, valid) for k, _, _ in POOLS):.5f}",
                    f"{dom_total['RF']:.5f}", f"{dom_total['RH']:.5f}"])
        for k, name in (("abg", "of which: aboveground vegetation (TOTVEGC_ABG)"), ("soc_0_100", "of which: SOC 0-100 cm (TOTSOMC_1m)")):
            w.writerow([name, f"{def_extra[k]:.5f}", f"{d_extra['RF'][k]:.5f}", f"{d_extra['RH'][k]:.5f}"])
    if have_traj:
        with open(os.path.join(a.out_dir, f"fig4_pool_trajectories_{a.res}_{a.ssp}.csv"), "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["mgmt", "pool", "year", "diff_vs_Default_PgC"])
            for mg in ("RF", "RH"):
                dlt, tot, ext = T[mg]
                for k in [p[0] for p in POOLS]:
                    w.writerows([[mg, k, int(y), f"{v:.5f}"] for y, v in zip(T["year"], dlt[k])])
                for k in ("abg", "soc_0_100"):
                    w.writerows([[mg, f"of_which_{k}", int(y), f"{v:.5f}"] for y, v in zip(T["year"], ext[k])])
                w.writerows([[mg, "total", int(y), f"{v:.5f}"] for y, v in zip(T["year"], tot)])

    foot = ("Four pools add up to TOTECOSYSC: living vegetation (TOTVEGC), dead wood and litter (CWDC + TOTLITC), soil organic carbon over the whole column (TOTSOMC), "
            "wood products derived as TOTECOSYSC − (TOTVEGC + CWDC + TOTLITC + TOTSOMC).\n"
            f"Within these: SOC 0–100 cm (TOTSOMC_1m) RF {d_extra['RF']['soc_0_100']:+.2f}, RH {d_extra['RH']['soc_0_100']:+.2f} PgC; "
            f"aboveground vegetation RF {d_extra['RF']['abg']:+.2f}, RH {d_extra['RH']['abg']:+.2f} PgC.\n"
            "RF sets harvest to zero everywhere (restoration plus a region-wide harvest ban); its difference to Default also contains the SSP's own land-use drift.\n"
            f"Panels a-b: mean of {win}; c-f: annual domain totals, each panel with its own y axis. All sums are area × landfrac weighted.")
    nrows = 3 if have_traj else 1
    heights = [1.0, 0.8, 0.8] if have_traj else [1.0]
    fig = plt.figure(figsize=(16, 4.6 + (7.0 if have_traj else 0) + 1.0), facecolor=SURFACE)
    top, bottom = 1 - 0.75 / fig.get_figheight(), 1.15 / fig.get_figheight()
    gs = fig.add_gridspec(nrows, 12, height_ratios=heights, hspace=0.45, wspace=2.2, left=0.06, right=0.985, top=top, bottom=bottom)
    panel_a(fig.add_subplot(gs[0, 0:4]), P["Def"], area, valid)
    panel_b(fig.add_subplot(gs[0, 5:12]), P, area, valid)
    if have_traj:
        others = [k for k, _, _ in POOLS if k != "veg"]
        ax_c = fig.add_subplot(gs[1, 0:5])
        ax_d = fig.add_subplot(gs[1, 6:11])
        ax_e = fig.add_subplot(gs[2, 0:5], sharex=ax_c)
        ax_f = fig.add_subplot(gs[2, 6:11], sharex=ax_d)
        panel_traj(ax_c, T["year"], T["RF"][0], ["veg"], "c", "RF − Default: living vegetation", label_ends=False)
        panel_traj(ax_d, T["year"], T["RH"][0], ["veg"], "d", "RH − Default: living vegetation (own y axis)", label_ends=False)
        panel_traj(ax_e, T["year"], T["RF"][0], others, "e", "RF − Default: other pools")
        panel_traj(ax_f, T["year"], T["RH"][0], others, "f", "RH − Default: other pools (own y axis)")
        for ax in (ax_c, ax_d):
            ax.tick_params(labelbottom=False)
    fig.suptitle(f"SEUS {a.res} {a.ssp}: which pools carry the management benefit, and when (RF, RH − Default)",
                 fontsize=13, color=INK, x=0.05, y=1 - 0.2 / fig.get_figheight(), ha="left")
    fig.text(0.05, 0.12 / fig.get_figheight(), foot, fontsize=8.6, color=INK2, va="bottom", ha="left")
    png = os.path.join(a.out_dir, base_name + ".png")
    fig.savefig(png, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    print(f"\nwrote {png}")


if __name__ == "__main__":
    main()
