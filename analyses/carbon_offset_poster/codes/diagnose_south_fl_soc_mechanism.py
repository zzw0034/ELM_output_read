"""Diagnose the South-Florida SOC deficit in the 4 km and 0.5 degree runs.

The script reads only two small geographic boxes from each yearly h0 file.
It compares 1850 with the 2014--2020 mean and separates the controls on
0--30 cm SOC into plant/litter inputs, heterotrophic respiration,
decomposition scalars, and wetness/anoxia diagnostics.

Run on Pathfinder through ``codes/submit_py.sbatch``; do not run on a login
node.  The script writes no data files.  Its only output is a compact table on
stdout, which is captured by Slurm.
"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass

import numpy as np
import xarray as xr


SECONDS_PER_YEAR = 365.0 * 86400.0
TARGET_DEPTH_M = 0.30

REGIONS = {
    "South_FL": (25.0, 26.5, -81.5, -80.0),
    "North_GA": (33.0, 35.0, -84.5, -82.5),
}

UNION_BOUNDS = (
    min(v[0] for v in REGIONS.values()),
    max(v[1] for v in REGIONS.values()),
    min(v[2] for v in REGIONS.values()),
    max(v[3] for v in REGIONS.values()),
)


@dataclass(frozen=True)
class Case:
    label: str
    name: str
    run_dir: str


CASES = (
    Case(
        label="4km",
        name="20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC",
        run_dir=(
            "/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/"
            "20260901_before_seus_rerun/"
            "20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_"
            "ICB20TRCNPRDCTCBC/run"
        ),
    ),
    Case(
        label="0.5deg",
        name="20260911_seus_halfdeg_transient_dt3600",
        run_dir=(
            "/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/"
            "20260911_seus_halfdeg_transient_dt3600/run"
        ),
    ),
)

SOIL_POOLS = ("SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr")

FLUX_2D = (
    "GPP",
    "NPP",
    "AGNPP",
    "BGNPP",
    "LITFALL",
    "LEAFC_TO_LITTER",
    "FROOTC_LOSS",
    "LITR1C_TO_SOIL1C",
    "LITR2C_TO_SOIL2C",
    "LITR3C_TO_SOIL3C",
    "HR",
    "SOMHR",
    "LITHR",
    "M_SOIL1C_TO_LEACHING",
    "M_SOIL2C_TO_LEACHING",
    "M_SOIL3C_TO_LEACHING",
    "M_SOIL4C_TO_LEACHING",
)

STATE_2D = (
    "ZWT",
    "BTRAN",
    "FSAT",
    "FINUNDATED",
    "FH2OSFC",
    "TG",
    "TBOT",
)

STATE_VERTICAL = (
    "SCALARAVG_vr",
    "T_SCALAR",
    "W_SCALAR",
    "O_SCALAR",
    "H2OSOI",
)

FLUX_VERTICAL = (
    "HR_vr",
    "F_CO2_SOIL_vr",
)


def h0_file(case: Case, year: int) -> str:
    paths = sorted(
        glob.glob(os.path.join(case.run_dir, f"{case.name}.elm.h0.{year:04d}-*.nc"))
    )
    if len(paths) != 1:
        raise RuntimeError(
            f"{case.label}: expected one h0 file for {year}, found {len(paths)}"
        )
    return paths[0]


def day_weighted_mean(da: xr.DataArray, time_bounds: np.ndarray | None) -> np.ndarray:
    """Reduce monthly/annual history records without converting all-NaN to zero."""
    values = np.asarray(da.values, dtype=np.float64)
    if values.shape[0] == 1:
        return values[0]
    if time_bounds is None:
        raise RuntimeError(f"{da.name}: time_bounds is required for multi-record files")
    dt = (time_bounds[:, 1] - time_bounds[:, 0]).astype(float)
    weights = dt / dt.sum()
    shape = (len(weights),) + (1,) * (values.ndim - 1)
    full_weights = np.broadcast_to(weights.reshape(shape), values.shape)
    finite = np.isfinite(values)
    masked_weights = np.where(finite, full_weights, 0.0)
    weight_sum = masked_weights.sum(axis=0)
    out = np.full(values.shape[1:], np.nan, dtype=np.float64)
    valid = weight_sum > 0
    numerator = np.sum(np.where(finite, values, 0.0) * masked_weights, axis=0)
    out[valid] = numerator[valid] / weight_sum[valid]
    return out


def layer_overlap(dzsoi: np.ndarray) -> np.ndarray:
    """Thickness of each soil layer intersecting the top 0.30 m."""
    flat = dzsoi.reshape(dzsoi.shape[0], -1)
    valid = np.isfinite(flat).all(axis=0)
    if not valid.any():
        raise RuntimeError("No complete DZSOI column in diagnostic subset")
    profile = flat[:, np.flatnonzero(valid)[0]]
    bottom = np.cumsum(profile)
    top = bottom - profile
    overlap = np.clip(np.minimum(bottom, TARGET_DEPTH_M) - top, 0.0, None)
    if not np.isclose(overlap.sum(), TARGET_DEPTH_M):
        raise RuntimeError(f"0-30 cm layer overlap sums to {overlap.sum()}, not 0.30")
    return overlap


def region_mask(lat: np.ndarray, lon: np.ndarray, bounds: tuple[float, ...]) -> np.ndarray:
    lat_min, lat_max, lon_min, lon_max = bounds
    lon2d, lat2d = np.meshgrid(lon, lat)
    return (
        (lat2d >= lat_min)
        & (lat2d <= lat_max)
        & (lon2d >= lon_min)
        & (lon2d <= lon_max)
    )


def weighted_mean(values: np.ndarray, mask: np.ndarray, weights: np.ndarray) -> float:
    valid = mask & np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return float("nan")
    return float(np.sum(values[valid] * weights[valid]) / np.sum(weights[valid]))


def read_dzsoi(case: Case) -> np.ndarray:
    path = h0_file(case, 1850)
    lat_min, lat_max, lon_min, lon_max = UNION_BOUNDS
    with xr.open_dataset(path, decode_times=False) as ds:
        return (
            ds["DZSOI"]
            .sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
            .load()
            .values.astype(np.float64)
        )


def one_year(case: Case, year: int, overlap: np.ndarray) -> dict[str, dict[str, float]]:
    path = h0_file(case, year)
    requested = set(SOIL_POOLS + FLUX_2D + STATE_2D + STATE_VERTICAL + FLUX_VERTICAL)
    requested.update(("area", "landfrac"))
    lat_min, lat_max, lon_min, lon_max = UNION_BOUNDS

    with xr.open_dataset(path) as ds:
        missing = sorted(requested - set(ds.variables))
        if missing:
            raise RuntimeError(f"{case.label} {year}: missing variables: {missing}")
        names = sorted(requested)
        subset = (
            ds[names]
            .sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))
            .load()
        )
        time_bounds = ds["time_bounds"].values if "time_bounds" in ds else None

    lat = subset["lat"].values
    lon = subset["lon"].values
    area_weights = np.asarray(subset["area"].values * subset["landfrac"].values)
    masks = {name: region_mask(lat, lon, bounds) for name, bounds in REGIONS.items()}

    annual = {}
    for name in SOIL_POOLS + FLUX_2D + STATE_2D + STATE_VERTICAL + FLUX_VERTICAL:
        annual[name] = day_weighted_mean(subset[name], time_bounds)
    annual["ENV_DECOMP_SCALAR"] = day_weighted_mean(
        subset["T_SCALAR"] * subset["W_SCALAR"] * subset["O_SCALAR"],
        time_bounds,
    )

    out: dict[str, dict[str, float]] = {}
    for region, mask in masks.items():
        metrics: dict[str, float] = {}

        pool_total = np.zeros_like(annual[SOIL_POOLS[0]], dtype=np.float64)
        for pool in SOIL_POOLS:
            pool_total += annual[pool]
            stock = np.sum(annual[pool] * overlap[:, None, None], axis=0) / 1000.0
            metrics[f"SOC30_{pool}"] = weighted_mean(stock, mask, area_weights)
        total_stock = np.sum(pool_total * overlap[:, None, None], axis=0) / 1000.0
        metrics["SOC30_total"] = weighted_mean(total_stock, mask, area_weights)

        for name in FLUX_2D:
            field = annual[name] * SECONDS_PER_YEAR
            metrics[name] = weighted_mean(field, mask, area_weights)

        metrics["soil_input"] = sum(
            metrics[name]
            for name in ("LITR1C_TO_SOIL1C", "LITR2C_TO_SOIL2C", "LITR3C_TO_SOIL3C")
        )
        metrics["soil_leaching"] = sum(
            metrics[name]
            for name in (
                "M_SOIL1C_TO_LEACHING",
                "M_SOIL2C_TO_LEACHING",
                "M_SOIL3C_TO_LEACHING",
                "M_SOIL4C_TO_LEACHING",
            )
        )

        for name in STATE_2D:
            metrics[name] = weighted_mean(annual[name], mask, area_weights)

        for name in STATE_VERTICAL + ("ENV_DECOMP_SCALAR",):
            top30_mean = np.sum(annual[name] * overlap[:, None, None], axis=0) / TARGET_DEPTH_M
            metrics[f"{name}_top30"] = weighted_mean(top30_mean, mask, area_weights)

        for name in FLUX_VERTICAL:
            top30_flux = (
                np.sum(annual[name] * overlap[:, None, None], axis=0)
                * SECONDS_PER_YEAR
            )
            metrics[f"{name}_top30"] = weighted_mean(top30_flux, mask, area_weights)

        out[region] = metrics
    return out


def mean_period(yearly: list[dict[str, dict[str, float]]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for region in REGIONS:
        metrics = yearly[0][region]
        result[region] = {
            name: float(np.nanmean([year[region][name] for year in yearly]))
            for name in metrics
        }
    return result


def print_comparison(
    case: Case,
    initial: dict[str, dict[str, float]],
    modern: dict[str, dict[str, float]],
) -> None:
    order = (
        "SOC30_total",
        "SOC30_SOIL1C_vr",
        "SOC30_SOIL2C_vr",
        "SOC30_SOIL3C_vr",
        "SOC30_SOIL4C_vr",
        "GPP",
        "NPP",
        "AGNPP",
        "BGNPP",
        "LITFALL",
        "LEAFC_TO_LITTER",
        "FROOTC_LOSS",
        "soil_input",
        "HR",
        "SOMHR",
        "LITHR",
        "HR_vr_top30",
        "soil_leaching",
        "SCALARAVG_vr_top30",
        "T_SCALAR_top30",
        "W_SCALAR_top30",
        "O_SCALAR_top30",
        "ENV_DECOMP_SCALAR_top30",
        "H2OSOI_top30",
        "ZWT",
        "FSAT",
        "FINUNDATED",
        "FH2OSFC",
        "BTRAN",
        "TG",
        "TBOT",
    )
    print(f"\n=== {case.label}: 1850 versus 2014-2020 ===")
    print("metric\tSouth_FL_1850\tNorth_GA_1850\tSouth_FL_modern\tNorth_GA_modern\tmodern_SF/GA")
    for name in order:
        sf0 = initial["South_FL"][name]
        ga0 = initial["North_GA"][name]
        sf = modern["South_FL"][name]
        ga = modern["North_GA"][name]
        ratio = sf / ga if np.isfinite(ga) and ga != 0 else np.nan
        print(f"{name}\t{sf0:.6g}\t{ga0:.6g}\t{sf:.6g}\t{ga:.6g}\t{ratio:.6g}")


def main() -> None:
    for case in CASES:
        overlap = layer_overlap(read_dzsoi(case))
        print(f"{case.label} 0-30 cm overlaps (m): {overlap.tolist()}", flush=True)
        initial = one_year(case, 1850, overlap)
        modern_years = []
        for year in range(2014, 2021):
            print(f"{case.label}: reading {year}", flush=True)
            modern_years.append(one_year(case, year, overlap))
        modern = mean_period(modern_years)
        print_comparison(case, initial, modern)


if __name__ == "__main__":
    main()
