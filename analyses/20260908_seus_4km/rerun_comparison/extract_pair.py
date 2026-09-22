"""Extract one matched old/new case pair into compact comparison caches.

Run only through Slurm; each 4 km h0 file is about 12 GB.  The script reads
one annual file at a time and writes small NetCDF caches containing annual
area-weighted time series plus early/recent and end-of-century map means.

Usage
-----
python extract_pair.py transient
python extract_pair.py ssp370
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import xarray as xr

from common import (
    CACHE_DIR,
    CASES,
    NEW_ROOT,
    OLD_ROOT,
    RATE_VARS,
    SOC_POOL_VARS,
    STATE_VARS,
    VAR_SPECS,
    annual_rate_integral,
    annual_state_mean,
    domain_mean,
    domain_total_pgc,
    h0_files,
    soil_layer_thickness_to_depth,
    year_from_path,
)


def duration_days(ds: xr.Dataset, path: Path) -> np.ndarray:
    if "time_bounds" not in ds:
        raise KeyError(f"{path}: time_bounds is required for rate integration")
    bounds = np.asarray(ds["time_bounds"].values, dtype=np.float64)
    days = bounds[:, 1] - bounds[:, 0]
    if len(days) != ds.sizes["time"] or np.any(~np.isfinite(days)) or np.any(days <= 0):
        raise ValueError(f"{path}: invalid time_bounds durations {days}")
    total = float(days.sum())
    if not 360.0 <= total <= 366.0:
        raise ValueError(f"{path}: annual file covers {total} days, expected 360-366")
    return days


def validate_units(ds: xr.Dataset, path: Path) -> None:
    """Fail loudly if a future file changes the assumptions used here."""
    expected = {
        "GPP": "gC/m^2/s",
        "NPP": "gC/m^2/s",
        "NBP": "gC/m^2/s",
        "PFT_FIRE_CLOSS": "gC/m^2/s",
        "TOTSOMC_1m": "gC/m^2",
        "SOIL1C_vr": "gC/m^3",
        "SOIL2C_vr": "gC/m^3",
        "SOIL3C_vr": "gC/m^3",
        "SOIL4C_vr": "gC/m^3",
        "area": "km^2",
    }
    for name, wanted in expected.items():
        got = ds[name].attrs.get("units", "").strip()
        if got != wanted:
            raise ValueError(f"{path}: {name} units={got!r}, expected {wanted!r}")
    # This attribute is known to be misleading; checking it protects against
    # an unnoticed switch to a genuinely integrated output in a future case.
    burned_units = ds["FAREA_BURNED"].attrs.get("units", "").strip()
    if burned_units != "proportion":
        raise ValueError(
            f"{path}: FAREA_BURNED units changed to {burned_units!r}; re-check rate semantics"
        )


def soil_c_0_30cm(ds: xr.Dataset, days: np.ndarray) -> np.ndarray:
    """Time-weighted annual 0-30 cm soil C, integrating gC m-3 layers."""
    layer_m = soil_layer_thickness_to_depth(ds["levdcmp"].values, 0.30)
    ntime = ds.sizes["time"]
    shape2d = (ds.sizes["lat"], ds.sizes["lon"])
    monthly = np.zeros((ntime,) + shape2d, dtype=np.float64)
    valid_any = np.zeros((ntime,) + shape2d, dtype=bool)
    for name in SOC_POOL_VARS:
        values = np.asarray(ds[name].values, dtype=np.float64)
        finite = np.isfinite(values)
        # Each pool is a density (gC m-3); integrate one pool at a time to
        # keep peak memory bounded instead of materializing all four pools.
        monthly += np.sum(np.where(finite, values, 0.0) * layer_m[None, :, None, None], axis=1)
        valid_any |= np.any(finite & (layer_m[None, :, None, None] > 0), axis=1)
    monthly[~valid_any] = np.nan
    return annual_state_mean(monthly, days)


def extract_family(root: Path, case: str, family: str, key: str, periods: tuple[tuple[int, int], ...]) -> Path:
    files = h0_files(root, case)
    years: list[int] = []
    series = {name: [] for name in VAR_SPECS}
    series.update(
        {
            "burned_area_km2": [],
            "PFT_FIRE_CLOSS_PgC": [],
            "NBP_PgC": [],
        }
    )
    maps = {period: {name: [] for name in VAR_SPECS} for period in periods}
    lat = lon = weights = None

    print(f"[{family}] {case}: {len(files)} h0 files", flush=True)
    for index, path in enumerate(files, start=1):
        year = year_from_path(path)
        print(f"[{family}] {key}: {index:03d}/{len(files):03d} year={year} {path.name}", flush=True)
        with xr.open_dataset(path, decode_times=False, cache=False) as ds:
            missing = [v for v in RATE_VARS + STATE_VARS + SOC_POOL_VARS if v not in ds]
            if missing:
                raise KeyError(f"{path}: missing required variables {missing}")
            validate_units(ds, path)
            days = duration_days(ds, path)

            if lat is None:
                lat = np.asarray(ds["lat"].values, dtype=np.float64)
                lon = np.asarray(ds["lon"].values, dtype=np.float64)
                area = np.asarray(ds["area"].values, dtype=np.float64)
                landfrac = np.asarray(ds["landfrac"].values, dtype=np.float64)
                weights = np.where(
                    np.isfinite(area) & np.isfinite(landfrac) & (landfrac > 0),
                    area * landfrac,
                    0.0,
                )

            annual = {}
            for name in RATE_VARS:
                annual[name] = annual_rate_integral(ds[name].values, days)
            for name in STATE_VARS:
                annual[name] = annual_state_mean(ds[name].values, days)
            annual["SOC_0_30cm"] = soil_c_0_30cm(ds, days)

        years.append(year)
        for name in VAR_SPECS:
            value = domain_mean(annual[name], weights)
            # Present burned fraction as percent of land area per year in all
            # time-series and map products; retain the physical burned area too.
            if name == "FAREA_BURNED":
                value *= 100.0
                map_value = annual[name] * 100.0
            else:
                map_value = annual[name]
            series[name].append(value)
            for period in periods:
                if period[0] <= year <= period[1]:
                    maps[period][name].append(np.asarray(map_value, dtype=np.float32))

        series["burned_area_km2"].append(
            float(np.nansum(annual["FAREA_BURNED"] * weights))
        )
        series["PFT_FIRE_CLOSS_PgC"].append(
            domain_total_pgc(annual["PFT_FIRE_CLOSS"], weights)
        )
        series["NBP_PgC"].append(domain_total_pgc(annual["NBP"], weights))

    if len(set(years)) != len(years):
        raise ValueError(f"{case}: duplicate nominal years in h0 files")
    order = np.argsort(years)
    years_array = np.asarray(years, dtype=np.int32)[order]

    period_names = []
    map_data = {name: [] for name in VAR_SPECS}
    for period in periods:
        expected = period[1] - period[0] + 1
        period_names.append(f"{period[0]}-{period[1]}")
        for name in VAR_SPECS:
            stack = maps[period][name]
            if len(stack) != expected:
                raise ValueError(
                    f"{case} {name} {period}: found {len(stack)} annual maps, expected {expected}"
                )
            map_data[name].append(np.nanmean(np.stack(stack, axis=0), axis=0).astype(np.float32))

    data_vars = {}
    for name in VAR_SPECS:
        data_vars[name] = (("year",), np.asarray(series[name], dtype=np.float64)[order])
        data_vars[f"map_{name}"] = (
            ("period", "lat", "lon"),
            np.stack(map_data[name], axis=0),
        )
    for name in ("burned_area_km2", "PFT_FIRE_CLOSS_PgC", "NBP_PgC"):
        data_vars[name] = (("year",), np.asarray(series[name], dtype=np.float64)[order])

    out = xr.Dataset(
        data_vars,
        coords={
            "year": years_array,
            "period": np.asarray(period_names, dtype=str),
            "lat": lat,
            "lon": lon,
        },
        attrs={
            "family": family,
            "case": case,
            "source_root": str(root),
            "spatial_weighting": "area * landfrac",
            "rate_integration": "sum(monthly_mean_rate * time_bounds_duration_days * 86400)",
            "FAREA_BURNED_interpretation": "per-second rate despite units='proportion'",
            "SOC_0_30cm_method": "sum(SOIL1C_vr..SOIL4C_vr) integrated through 0.30 m",
        },
    )
    for name, (long_name, units, _, _) in VAR_SPECS.items():
        out[name].attrs.update(long_name=f"domain mean {long_name}", units=units.replace("$", ""))
        out[f"map_{name}"].attrs.update(long_name=f"period mean {long_name}", units=units.replace("$", ""))
    out["burned_area_km2"].attrs.update(
        long_name="domain total burned area per year", units="km2 yr-1"
    )
    out["PFT_FIRE_CLOSS_PgC"].attrs.update(
        long_name="domain total PFT fire carbon loss", units="PgC yr-1"
    )
    out["NBP_PgC"].attrs.update(long_name="domain total NBP (+ = sink)", units="PgC yr-1")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CACHE_DIR / f"{family}__{key}.nc"
    encoding = {
        name: {"zlib": True, "complevel": 2}
        for name in out.data_vars
        if name.startswith("map_")
    }
    out.to_netcdf(output_path, encoding=encoding)
    print(f"Wrote {output_path}", flush=True)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("key", choices=CASES.keys())
    args = parser.parse_args()
    spec = CASES[args.key]
    periods = tuple(spec["periods"])
    extract_family(OLD_ROOT, spec["old"], "20260908", args.key, periods)
    extract_family(NEW_ROOT, spec["new"], "20260910_rerun", args.key, periods)


if __name__ == "__main__":
    main()
