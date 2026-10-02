"""
Main Figure 5, poster-style (user decisions 2026-10-01/02): benefit without fire loss, the two risks, and the
4 km siting. RF, SSP3-7.0, end state = mean of 2091-2100, 4 km.

  a  RF benefit WITHOUT fire loss, per eligible hectare: the window-mean TOTECOSYSC difference RF - Default plus
     the cumulative fire-loss difference RF - Default from 2024 (window mean of the cumulative sum to each year;
     fire = NEP - LAND_USE_FLUX - NBP, extract_fire_cumulative.py). Adding the fire loss back is an approximation:
     unburnt carbon would partly have been respired later, and fire also changes stand dynamics.
  b  fire risk: (NEP - LAND_USE_FLUX - NBP) / TOTECOSYSC, RF run, 2091-2100 mean (%/yr), with the threshold
  c  water stress: 1 - BTRAN, April-October, RF run, 2091-2100 mean, with the threshold
  d  4 km siting: rank eligible land by the benefit of panel a, remove land above either threshold, fill BUDGET %
     of the eligible area. Classes: selected; high benefit but excluded for fire risk; high benefit but excluded
     for water stress only ("high benefit" = inside the unscreened top BUDGET %); eligible, not selected.
Thresholds: area-weighted PCT-th percentile of each 4 km component over eligible land (default p80), or fixed
absolute values (--thresholds FIRE WATER, e.g. the SSP3-7.0 p80 applied to every SSP; user decision 2026-10-02).
Colour-scale maxima default to the 98th percentile of each panel; --vmax BENEFIT FIRE WATER fixes them so that
several SSPs share one scale (plot_priority_ssps.py). Eligible land and the selection machinery are those of
plot_priority_selection.py (imported), which keeps the 4 km vs 0.5 deg comparison for the supplement.

Runs locally (cartopy venv), from the analysis root:
    /Users/zw5/ORNL_workplace/ELM_output_read/.venv/bin/python code/figure5/plot_priority_maps.py [--ssp SSP3-7.0 --budget 20 --pct 80]
        [--thresholds FIRE WATER --threshold-label "SSP3-7.0 p80"] [--vmax BENEFIT FIRE WATER]
Extra inputs: _cache/figure5/4km/<SSP>{,_RF}__firecum_2024-2100.npz
Output: figures/figure5/fig5_priority_maps_<SSP>_<window>.png
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plot_priority_selection as ps  # noqa: E402

D_COLS = ["#d9d7d0", "#3987e5", "#e34948", "#008300"]      # eligible not selected, excluded water, excluded fire, selected
D_NAMES = ["Eligible, not selected", "High benefit, excluded: water stress", "High benefit, excluded: fire risk", "Selected"]
INELIGIBLE = "#f3f2ee"
BENEFIT_CMAP = LinearSegmentedColormap.from_list("ben", ["#f0efec", "#b5dfc6", "#5fbf8e", "#1baf7a", "#0b6e4a"])
FIRE_CMAP = LinearSegmentedColormap.from_list("fire", ["#fdeee6", "#f6b48f", "#eb6834", "#b8461b", "#7a2a0c"])
WATER_CMAP = LinearSegmentedColormap.from_list("wat", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])


def base_map(ax, lon, lat):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    ax.set_facecolor(ps.BAD)
    ax.coastlines(resolution="10m", linewidth=0.5, color="#555555")
    ax.add_feature(cfeature.NaturalEarthFeature("cultural", "admin_1_states_provinces_lakes", "10m", facecolor="none",
                                                edgecolor="#777777", linewidth=0.3))
    ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=ccrs.PlateCarree())
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="#999999", alpha=0.6, linestyle="--")
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 8}


def mesh(ax, lon, lat, field, cmap, norm):
    import cartopy.crs as ccrs
    return ax.pcolormesh(lon, lat, np.ma.masked_invalid(field), cmap=cmap, norm=norm, shading="auto",
                         transform=ccrs.PlateCarree(), rasterized=True, zorder=1)


def title(ax, letter, text):
    ax.set_title(f"{letter}  {text}", loc="left", fontsize=11.5, color=ps.INK, fontweight="bold")


def take_mask(vals, areas, keep, budget):
    """Selected fraction (4 km grid) when ranking `vals` over the `keep` cells and filling `budget` area."""
    idx = np.flatnonzero(keep.ravel())
    f, s = ps.take(vals.ravel()[idx], areas.ravel()[idx], budget)
    w = np.zeros(areas.size)
    w[idx] = f
    return w.reshape(areas.shape), s


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssp", default="SSP3-7.0")
    ap.add_argument("--years", default="2091-2100")
    ap.add_argument("--floor", type=float, default=0.05)
    ap.add_argument("--pct", type=float, default=80)
    ap.add_argument("--budget", type=float, default=20)
    ap.add_argument("--thresholds", type=float, nargs=2, metavar=("FIRE", "WATER"),
                    help="fixed absolute thresholds instead of this SSP's own p<pct>")
    ap.add_argument("--threshold-label", default=None, help="how the fixed thresholds were derived, for the figure text")
    ap.add_argument("--vmax", type=float, nargs=3, metavar=("BENEFIT", "FIRE", "WATER"), help="fixed colour-scale maxima")
    ap.add_argument("--cache-4km", default=os.path.join(ps.ROOT, "_cache/figure4/4km"))
    ap.add_argument("--cache-05", default=os.path.join(ps.ROOT, "_cache/figure3/0.5deg"))
    ap.add_argument("--risk-cache", default=os.path.join(ps.ROOT, "_cache/figure5"))
    ap.add_argument("--out-dir", default=os.path.join(ps.ROOT, "figures/figure5"))
    return ap


def compute(a):
    """Benefit without fire loss, thresholds, screened 4 km siting and the printed summary for one SSP."""
    m = ps.build(a)
    w0, w1 = (int(v) for v in a.years.split("-"))

    # benefit without fire loss (4 km)
    fc = {k: ps.load(os.path.join(a.risk_cache, "4km", f"{a.ssp}{s}__firecum_2024-2100.npz")) for k, s in (("Def", ""), ("RF", "_RF"))}
    for z in fc.values():
        assert np.array_equal(z["area_km2"], fc["Def"]["area_km2"]) and tuple(int(v) for v in z["window"]) == (w0, w1)
    dfire = (fc["RF"]["fire_cum_endmean"].astype("f8") - fc["Def"]["fire_cum_endmean"].astype("f8")) * 0.01   # MgC/ha of land
    ok = m["ok4"] & np.isfinite(dfire)
    a4 = np.where(ok, m["a4"], 0.0)
    e4 = np.where(ok, m["e4"], 1.0)
    g_net = m["g4"]
    g_nf = g_net + dfire                                                    # MgC/ha of land, without fire loss
    b_nf = np.where(ok, g_nf / e4, np.nan)                                 # per eligible ha
    b_net = np.where(ok, g_net / e4, np.nan)
    E = float(a4.sum())
    pg = lambda per_land: float(np.nansum(np.where(ok, per_land, 0) * a4 / e4) * 100 / 1e9)   # PgC on eligible cells
    print(f"[{a.ssp}] eligible 4 km land {E / 1e3:.1f} x10^3 km2; benefit on eligible cells: net {pg(g_net):.3f} PgC, "
          f"fire-loss difference added back {pg(dfire):+.3f} PgC, without fire loss {pg(g_nf):.3f} PgC")
    print(f"domain cumulative fire 2024-2100: RF {fc['RF']['fire_domain_PgC'].sum():.2f}, Default {fc['Def']['fire_domain_PgC'].sum():.2f} PgC")

    own = {k: ps.wquantile(m["R4"][k][ok], a4[ok], a.pct / 100) for k in ("fire", "water")}
    T = dict(zip(("fire", "water"), a.thresholds)) if a.thresholds else own
    budget = a.budget / 100 * E
    hi_f = m["R4"]["fire"] > T["fire"]
    hi_w = m["R4"]["water"] > T["water"]
    above = {k: 100 * float(a4[ok & (m["R4"][k] > T[k])].sum()) / E for k in ("fire", "water")}
    wU, _ = take_mask(b_nf, a4, ok, budget)                              # unscreened top BUDGET %
    wS, sS = take_mask(b_nf, a4, ok & ~hi_f & ~hi_w, budget)            # screened selection
    U, S = wU > 0, wS > 0
    cls = np.where(S, 3, np.where(U & hi_f, 2, np.where(U & hi_w, 1, 0))).astype("f8")
    cls = np.where(ok, cls, np.nan)
    share = {k: 100 * a4[ok & (cls == k)].sum() / E for k in range(4)}
    G = lambda w, b: float((w * a4 * np.nan_to_num(b)).sum()) * 100 / 1e9
    tsrc = a.threshold_label or "fixed" if a.thresholds else f"own p{a.pct:g}"
    print(f"thresholds ({tsrc}): fire {T['fire']:.4f} %/yr, water {T['water']:.4f} (this SSP's own p{a.pct:g}: fire {own['fire']:.4f}, "
          f"water {own['water']:.4f}); eligible land above: fire {above['fire']:.1f}%, water {above['water']:.1f}%; "
          f"budget {a.budget:g}% = {budget / 1e3:.1f} x10^3 km2 (screened land filled {sS / 1e3:.1f})")
    print("classes (% of eligible land): " + ", ".join(f"{D_NAMES[k]} {share[k]:.1f}" for k in (3, 2, 1, 0)))
    GU, GS = G(wU, b_nf), G(wS, b_nf)
    print(f"captured, benefit without fire loss: unscreened {GU:.3f}, screened {GS:.3f} PgC "
          f"(screen gives up {100 * (1 - GS / GU):.1f}%); same land scored on the net benefit: "
          f"unscreened {G(wU, b_net):.3f}, screened {G(wS, b_net):.3f} PgC")
    excl_f = float((wU * a4 * hi_f).sum() / (wU * a4).sum())
    excl_w = float((wU * a4 * (hi_w & ~hi_f)).sum() / (wU * a4).sum())
    print(f"of the unscreened top {a.budget:g}%: {100 * excl_f:.1f}% above the fire threshold, {100 * excl_w:.1f}% above the water threshold only")
    rk = lambda x: np.argsort(np.argsort(x))
    v = ok & np.isfinite(b_nf) & np.isfinite(b_net)
    wNet, _ = take_mask(b_net, a4, ok, budget)
    print(f"rank correlation of benefit with vs without fire loss: {np.corrcoef(rk(b_nf[v]), rk(b_net[v]))[0, 1]:.3f}; "
          f"overlap of the unscreened top {a.budget:g}% (without fire vs net): {100 * float((np.minimum(wU, wNet) * a4).sum() / (wU * a4).sum()):.0f}%")
    return dict(m=m, ok=ok, a4=a4, E=E, b_nf=b_nf, b_net=b_net, T=T, own=own, above=above, wU=wU, wS=wS, cls=cls,
                share=share, G_unscreened=GU, G_screened=GS, excl_fire=excl_f, excl_water=excl_w,
                benefit_nf_PgC=pg(g_nf), benefit_net_PgC=pg(g_net))


def draw(a, c, vmax=None):
    """The four-panel figure for one SSP; vmax = (benefit, fire, water) colour-scale maxima, default the p98 of each."""
    import cartopy.crs as ccrs
    m, ok, b_nf, T, cls, share = c["m"], c["ok"], c["b_nf"], c["T"], c["cls"], c["share"]
    vmax = vmax or (float(np.nanpercentile(b_nf[ok], 98)), float(np.nanpercentile(m["R4"]["fire"][ok], 98)),
                    float(np.nanpercentile(m["R4"]["water"][ok], 98)))
    tdesc = (f"fixed at the {a.threshold_label} for every SSP" if a.threshold_label else "fixed") if a.thresholds \
        else f"area-weighted p{a.pct:g} of the 4 km component over eligible land"
    lon4, lat4 = m["lon4"], m["lat4"]
    land4 = np.isfinite(m["g4"]) & np.isfinite(m["R4"]["water"])
    inel = np.where(land4 & ~ok, 1.0, np.nan)
    fig = plt.figure(figsize=(15.5, 13.4), facecolor=ps.SURFACE)
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.08, left=0.04, right=0.985, top=0.93, bottom=0.15)

    axa = fig.add_subplot(gs[0, 0], projection=ccrs.PlateCarree())
    base_map(axa, lon4, lat4)
    mesh(axa, lon4, lat4, inel, ListedColormap([INELIGIBLE]), Normalize(0, 1))
    ma = mesh(axa, lon4, lat4, b_nf, BENEFIT_CMAP, Normalize(0, vmax[0]))
    title(axa, "a", "Carbon benefit of RF without fire loss")
    cba = fig.colorbar(ma, ax=axa, orientation="horizontal", fraction=0.045, pad=0.07, shrink=0.8, extend="both")
    cba.set_label("RF − Default, ecosystem carbon per eligible ha, fire loss added back (MgC/ha), 2091–2100", fontsize=9)
    cba.ax.tick_params(labelsize=8.5)

    for axpos, key, vm, cmap, letter, ttl, lab in (
            (gs[0, 1], "fire", vmax[1], FIRE_CMAP, "b", "Fire risk", "Fire carbon loss / ecosystem carbon (%/yr), 2091–2100"),
            (gs[1, 0], "water", vmax[2], WATER_CMAP, "c", "Water stress risk", "1 − BTRAN, April–October, 2091–2100")):
        ax = fig.add_subplot(axpos, projection=ccrs.PlateCarree())
        base_map(ax, lon4, lat4)
        mesh(ax, lon4, lat4, inel, ListedColormap([INELIGIBLE]), Normalize(0, 1))
        mm = mesh(ax, lon4, lat4, np.where(ok, m["R4"][key], np.nan), cmap, Normalize(0, vm))
        title(ax, letter, ttl)
        cb = fig.colorbar(mm, ax=ax, orientation="horizontal", fraction=0.045, pad=0.07, shrink=0.8, extend="max")
        cb.ax.axvline(T[key], color="black", lw=2.4)
        cb.set_label(f"{lab}; black line = threshold {T[key]:.3g} ({c['above'][key]:.0f}% of eligible land above it)", fontsize=9)
        cb.ax.tick_params(labelsize=8.5)

    axd = fig.add_subplot(gs[1, 1], projection=ccrs.PlateCarree())
    base_map(axd, lon4, lat4)
    mesh(axd, lon4, lat4, inel, ListedColormap([INELIGIBLE]), Normalize(0, 1))
    mesh(axd, lon4, lat4, cls, ListedColormap(D_COLS), Normalize(-0.5, 3.5))
    title(axd, "d", f"Where to restore and protect: top {a.budget:g}% benefit, low risk")
    handles = [plt.Rectangle((0, 0), 1, 1, color=D_COLS[k]) for k in (3, 2, 1, 0)]
    axd.legend(handles, [f"{D_NAMES[k]} ({share[k]:.0f}%)" for k in (3, 2, 1, 0)], loc="lower left", fontsize=8.4,
               framealpha=0.93, edgecolor="none", title="share of eligible land", title_fontsize=8)

    fig.suptitle(f"Where to restore and protect forest for carbon (SEUS, {a.ssp}, RF, {a.years}, 4 km)", fontsize=13.5, color=ps.INK,
                 x=0.04, ha="left", y=0.975)
    fig.text(0.04, 0.012,
             "Benefit (a) = TOTECOSYSC stock difference RF − Default plus the cumulative fire carbon loss difference since 2024 (fire = NEP − LAND_USE_FLUX − NBP), "
             "per eligible hectare; adding the fire loss back is an approximation.\n"
             f"Eligible land = RF's 2060 forest fraction (cells ≥ {a.floor:g}; near-white: not eligible). Thresholds (b, c): {tdesc}. "
             "Selected (d) = the highest-benefit land after removing land above either threshold,\n"
             f"{a.budget:g}% of the eligible area; red and blue = land in the top {a.budget:g}% that the screen removes. Fire has ~0.5° effective resolution "
             "at 4 km (population-density input interpolated from 0.5°). RF is restoration plus a region-wide harvest ban.\n"
             f"Colour scales: a 0–{vmax[0]:.3g}, b 0–{vmax[1]:.3g}, c 0–{vmax[2]:.3g}. The 4 km vs 0.5° comparison is in the supplement.",
             fontsize=8.4, color=ps.INK2, va="bottom", ha="left")
    os.makedirs(a.out_dir, exist_ok=True)
    png = os.path.join(a.out_dir, f"fig5_priority_maps_{a.ssp}_{a.years}.png")
    fig.savefig(png, dpi=170, facecolor=ps.SURFACE)
    plt.close(fig)
    print(f"wrote {png}")


def main():
    a = parser().parse_args()
    draw(a, compute(a), a.vmax)


if __name__ == "__main__":
    main()
