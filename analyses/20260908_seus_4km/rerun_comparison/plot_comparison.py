"""Plot paired temporal and spatial comparisons from compact caches."""

from __future__ import annotations

import csv
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from common import CACHE_DIR, CASES, OUTPUT_DIR, VAR_SPECS


OLD = "20260908"
NEW = "20260910_rerun"
FAMILY_LABEL = {OLD: "20260908 (old)", NEW: "20260910 rerun (new)"}


def cache_path(family: str, key: str) -> Path:
    return CACHE_DIR / f"{family}__{key}.nc"


def load_all() -> dict[str, dict[str, xr.Dataset]]:
    data = {family: {} for family in (OLD, NEW)}
    missing = []
    for family in data:
        for key in CASES:
            path = cache_path(family, key)
            if not path.exists():
                missing.append(str(path))
            else:
                data[family][key] = xr.open_dataset(path).load()
    if missing:
        raise FileNotFoundError("Missing extraction caches:\n" + "\n".join(missing))
    return data


def validate_grids(data: dict[str, dict[str, xr.Dataset]]) -> None:
    ref = data[OLD]["transient"]
    for family in data:
        for key, ds in data[family].items():
            if ds.sizes["lat"] != ref.sizes["lat"] or ds.sizes["lon"] != ref.sizes["lon"]:
                raise ValueError(f"Grid shape differs for {family}/{key}")
            if not np.allclose(ds["lat"], ref["lat"]) or not np.allclose(ds["lon"], ref["lon"]):
                raise ValueError(f"Grid coordinates differ for {family}/{key}")


def plot_time_series(data: dict[str, dict[str, xr.Dataset]]) -> None:
    for var, (label, units, _, _) in VAR_SPECS.items():
        fig, axes = plt.subplots(4, 2, figsize=(15, 14), sharex=False)
        for ax, (key, spec) in zip(axes.flat, CASES.items()):
            old = data[OLD][key]
            new = data[NEW][key]
            ax.plot(old["year"], old[var], color="0.35", lw=1.2, label=FAMILY_LABEL[OLD])
            ax.plot(new["year"], new[var], color="tab:red", lw=1.2, label=FAMILY_LABEL[NEW])
            if var == "NBP":
                ax.axhline(0, color="k", lw=0.5)
            ax.set_title(spec["label"], fontsize=10)
            ax.set_ylabel(units, fontsize=8)
            ax.grid(alpha=0.25)
        axes.flat[0].legend(fontsize=8)
        fig.suptitle(f"SEUS 4 km rerun comparison: {label}", fontsize=14)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"timeseries_{var}.png", dpi=170)
        plt.close(fig)


def map_axes(ax) -> None:
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="0.35", linewidth=0.45)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.55)
    ax.set_extent([-92, -75, 24, 37], crs=ccrs.PlateCarree())


def finite_land_values(*fields: np.ndarray) -> np.ndarray:
    values = [f[np.isfinite(f)] for f in fields if np.any(np.isfinite(f))]
    if not values:
        return np.array([0.0])
    return np.concatenate(values)


def plot_case_maps(key: str, data: dict[str, dict[str, xr.Dataset]]) -> None:
    spec = CASES[key]
    old = data[OLD][key]
    new = data[NEW][key]
    lon, lat = old["lon"].values, old["lat"].values

    for period in old["period"].values.astype(str):
        if period not in set(new["period"].values.astype(str)):
            raise ValueError(f"{key}: period {period} missing from new cache")
        fig, axes = plt.subplots(
            len(VAR_SPECS),
            3,
            figsize=(14, 3.45 * len(VAR_SPECS)),
            subplot_kw={"projection": ccrs.PlateCarree()},
        )
        for row, (var, (label, units, cmap, kind)) in enumerate(VAR_SPECS.items()):
            a = old[f"map_{var}"].sel(period=period).values
            b = new[f"map_{var}"].sel(period=period).values
            delta = b - a
            common = finite_land_values(a, b)
            if kind == "signed":
                vmax = float(np.nanpercentile(np.abs(common), 98.0))
                base_kw = dict(cmap="RdBu", vmin=-vmax, vmax=vmax)
            else:
                vmin, vmax = np.nanpercentile(common, [1.0, 99.0])
                if vmin == vmax:
                    vmax = vmin + 1.0
                base_kw = dict(cmap=cmap, vmin=float(vmin), vmax=float(vmax))
            dvals = finite_land_values(delta)
            dmax = float(np.nanpercentile(np.abs(dvals), 98.0))
            if not np.isfinite(dmax) or dmax == 0:
                dmax = 1.0

            pcs = []
            for col, (field, title) in enumerate(
                ((a, FAMILY_LABEL[OLD]), (b, FAMILY_LABEL[NEW]), (delta, "new - old"))
            ):
                ax = axes[row, col]
                map_axes(ax)
                kw = base_kw if col < 2 else dict(cmap="RdBu", vmin=-dmax, vmax=dmax)
                pc = ax.pcolormesh(
                    lon,
                    lat,
                    field,
                    transform=ccrs.PlateCarree(),
                    shading="auto",
                    **kw,
                )
                pcs.append(pc)
                if row == 0:
                    ax.set_title(title, fontsize=10)
                if col == 0:
                    ax.text(
                        -0.04,
                        0.5,
                        label,
                        transform=ax.transAxes,
                        rotation=90,
                        va="center",
                        ha="right",
                        fontsize=9,
                    )
            fig.colorbar(pcs[1], ax=list(axes[row, :2]), orientation="horizontal", pad=0.035, shrink=0.72, label=units)
            fig.colorbar(pcs[2], ax=axes[row, 2], orientation="horizontal", pad=0.035, shrink=0.82, label=f"delta {units}")

        fig.suptitle(f"{spec['label']}: spatial comparison, {period} mean", fontsize=14, y=0.995)
        fig.savefig(OUTPUT_DIR / f"maps_{key}_{period}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)


def summary_windows(key: str) -> tuple[tuple[int, int], ...]:
    if key == "transient":
        return ((1850, 1859), (2014, 2023))
    return ((2024, 2033), (2091, 2100))


def write_summary(data: dict[str, dict[str, xr.Dataset]]) -> None:
    rows = []
    for key, spec in CASES.items():
        old = data[OLD][key]
        new = data[NEW][key]
        for y0, y1 in summary_windows(key):
            old_mask = (old["year"].values >= y0) & (old["year"].values <= y1)
            new_mask = (new["year"].values >= y0) & (new["year"].values <= y1)
            if old_mask.sum() != y1 - y0 + 1 or new_mask.sum() != y1 - y0 + 1:
                raise ValueError(f"{key}: incomplete summary window {y0}-{y1}")
            for var in VAR_SPECS:
                old_mean = float(np.nanmean(old[var].values[old_mask]))
                new_mean = float(np.nanmean(new[var].values[new_mask]))
                delta = new_mean - old_mean
                pct = 100.0 * delta / abs(old_mean) if old_mean != 0 else np.nan
                rows.append(
                    {
                        "case_key": key,
                        "case_label": spec["label"],
                        "period": f"{y0}-{y1}",
                        "variable": var,
                        "old_mean": old_mean,
                        "new_mean": new_mean,
                        "new_minus_old": delta,
                        "percent_change_vs_abs_old": pct,
                    }
                )

            # Physical burned area is useful alongside the area-normalized fraction.
            for var in ("burned_area_km2", "PFT_FIRE_CLOSS_PgC", "NBP_PgC"):
                old_mean = float(np.nanmean(old[var].values[old_mask]))
                new_mean = float(np.nanmean(new[var].values[new_mask]))
                delta = new_mean - old_mean
                pct = 100.0 * delta / abs(old_mean) if old_mean != 0 else np.nan
                rows.append(
                    {
                        "case_key": key,
                        "case_label": spec["label"],
                        "period": f"{y0}-{y1}",
                        "variable": var,
                        "old_mean": old_mean,
                        "new_mean": new_mean,
                        "new_minus_old": delta,
                        "percent_change_vs_abs_old": pct,
                    }
                )

    csv_path = OUTPUT_DIR / "summary.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    # Compact human-readable table: recent historical and end-of-century
    # paired deltas for the seven primary requested variables.
    selected = [
        row
        for row in rows
        if row["variable"] in VAR_SPECS
        and (
            (row["case_key"] == "transient" and row["period"] == "2014-2023")
            or (row["case_key"] != "transient" and row["period"] == "2091-2100")
        )
    ]
    md_path = OUTPUT_DIR / "RESULTS.md"
    with md_path.open("w") as handle:
        handle.write("# 20260910 rerun minus 20260908 4 km comparison\n\n")
        handle.write(
            "All domain means use `area * landfrac`. Fluxes and fire rates are integrated "
            "month by month using `time_bounds`; `FAREA_BURNED` is treated as s^-1. "
            "Positive deltas mean the newer rerun is larger.\n\n"
        )
        handle.write("| case | period | variable | old | new | new-old | % vs |old| |\n")
        handle.write("|---|---:|---|---:|---:|---:|---:|\n")
        for row in selected:
            handle.write(
                f"| {row['case_label']} | {row['period']} | {row['variable']} | "
                f"{row['old_mean']:.6g} | {row['new_mean']:.6g} | "
                f"{row['new_minus_old']:+.6g} | {row['percent_change_vs_abs_old']:+.2f}% |\n"
            )
        handle.write("\nSee `summary.csv` for early-period values and physical burned area (km2/yr).\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_all()
    validate_grids(data)
    plot_time_series(data)
    for key in CASES:
        plot_case_maps(key, data)
    write_summary(data)
    for family in data:
        for ds in data[family].values():
            ds.close()
    print(f"Figures and summaries written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
