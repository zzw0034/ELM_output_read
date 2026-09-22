"""Configuration and numerics for the paired 4 km rerun comparison.

The comparison is deliberately limited to cases that have a like-for-like
member in both families.  The newer family has additional RF/DF/RH cases for
SSP1-1.9, SSP2-4.5, and SSP5-8.5; those have no 20260908 counterpart and are
therefore not used in paired differences.

Rate handling is explicit.  Monthly history records are time means, so a
per-second rate is integrated as ``sum(rate * seconds_in_record)``.  This is
equivalent to multiplying each monthly mean by
``days_in_month * 24 * 3600``.  FAREA_BURNED is treated as s-1 despite its
misleading ``units='proportion'`` history attribute.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import numpy as np


OLD_ROOT = Path(
    "/projects/hpcl-cli185/proj-shared/zw5/e3sm_run/20260901_before_seus_rerun"
)
NEW_ROOT = Path("/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun")

WORK_ROOT = Path(
    "/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/"
    "20260908_seus_4km/rerun_comparison"
)
CACHE_DIR = WORK_ROOT / "_cache"
OUTPUT_DIR = WORK_ROOT / "outputs"
LOG_DIR = WORK_ROOT / "logs"

CASES = OrderedDict(
    [
        (
            "transient",
            {
                "label": "Transient",
                "old": "20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC",
                "new": "20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC",
                "periods": ((2014, 2023),),
            },
        ),
        (
            "ssp119",
            {
                "label": "SSP1-1.9",
                "old": "20260908_seus_4km_fut_ssp119",
                "new": "20260917_seus_4km_fut_ssp119",
                "periods": ((2024, 2033), (2091, 2100)),
            },
        ),
        (
            "ssp245",
            {
                "label": "SSP2-4.5",
                "old": "20260908_seus_4km_fut_ssp245",
                "new": "20260917_seus_4km_fut_ssp245",
                "periods": ((2024, 2033), (2091, 2100)),
            },
        ),
        (
            "ssp370",
            {
                "label": "SSP3-7.0",
                "old": "20260908_seus_4km_fut_ssp370",
                "new": "20260917_seus_4km_fut_ssp370",
                "periods": ((2024, 2033), (2091, 2100)),
            },
        ),
        (
            "ssp370_RF",
            {
                "label": "SSP3-7.0 RF",
                "old": "20260908_seus_4km_fut_ssp370_RF",
                "new": "20260917_seus_4km_fut_ssp370_RF",
                "periods": ((2024, 2033), (2091, 2100)),
            },
        ),
        (
            "ssp370_DF",
            {
                "label": "SSP3-7.0 DF",
                "old": "20260908_seus_4km_fut_ssp370_DF",
                "new": "20260917_seus_4km_fut_ssp370_DF",
                "periods": ((2024, 2033), (2091, 2100)),
            },
        ),
        (
            "ssp370_RH",
            {
                "label": "SSP3-7.0 RH",
                "old": "20260908_seus_4km_fut_ssp370_RH",
                "new": "20260917_seus_4km_fut_ssp370_RH",
                "periods": ((2024, 2033), (2091, 2100)),
            },
        ),
        (
            "ssp585",
            {
                "label": "SSP5-8.5",
                "old": "20260908_seus_4km_fut_ssp585",
                "new": "20260917_seus_4km_fut_ssp585",
                "periods": ((2024, 2033), (2091, 2100)),
            },
        ),
    ]
)

RATE_VARS = ("GPP", "NPP", "NBP", "PFT_FIRE_CLOSS", "FAREA_BURNED")
STATE_VARS = ("TOTSOMC_1m",)
SOC_POOL_VARS = ("SOIL1C_vr", "SOIL2C_vr", "SOIL3C_vr", "SOIL4C_vr")

# Output name -> display label, plotting units, sequential colormap, kind.
VAR_SPECS = OrderedDict(
    [
        ("GPP", ("GPP", "gC m$^{-2}$ yr$^{-1}$", "YlGn", "positive")),
        ("NPP", ("NPP", "gC m$^{-2}$ yr$^{-1}$", "YlGn", "positive")),
        ("NBP", ("NBP (+ = sink)", "gC m$^{-2}$ yr$^{-1}$", "RdBu", "signed")),
        ("SOC_0_30cm", ("Soil C 0-30 cm", "gC m$^{-2}$", "copper_r", "positive")),
        ("TOTSOMC_1m", ("Soil C 0-100 cm", "gC m$^{-2}$", "copper_r", "positive")),
        ("FAREA_BURNED", ("Fractional area burned", "% land area yr$^{-1}$", "YlOrRd", "positive")),
        ("PFT_FIRE_CLOSS", ("PFT fire C loss", "gC m$^{-2}$ yr$^{-1}$", "Reds", "positive")),
    ]
)

SECONDS_PER_DAY = 24.0 * 3600.0


def year_from_path(path: Path) -> int:
    """Read the nominal calendar year from an ELM h0 filename."""
    return int(path.name.split(".elm.h0.", 1)[1].split("-", 1)[0])


def h0_files(root: Path, case: str) -> list[Path]:
    files = sorted((root / case / "run").glob(f"{case}.elm.h0.*.nc"))
    if not files:
        raise FileNotFoundError(f"No h0 files found for {case} under {root}")
    return files


def soil_layer_thickness_to_depth(z: np.ndarray, depth_m: float) -> np.ndarray:
    """Thickness of each ELM decomposition layer above ``depth_m``.

    Interfaces follow the ELM/CLM node-midpoint convention.  A layer that
    crosses the requested cutoff contributes only its portion above it.
    """
    z = np.asarray(z, dtype=float)
    if z.ndim != 1 or len(z) < 2:
        raise ValueError(f"Expected a 1-D soil coordinate, got {z.shape}")
    bottom = np.empty_like(z)
    bottom[:-1] = 0.5 * (z[:-1] + z[1:])
    bottom[-1] = z[-1] + 0.5 * (z[-1] - bottom[-2])
    top = np.concatenate(([0.0], bottom[:-1]))
    return np.clip(np.minimum(bottom, depth_m) - np.minimum(top, depth_m), 0.0, None)


def annual_state_mean(values: np.ndarray, duration_days: np.ndarray) -> np.ndarray:
    """Duration-weighted annual mean, with missing values renormalized."""
    values = np.asarray(values, dtype=np.float64)
    shape = (len(duration_days),) + (1,) * (values.ndim - 1)
    duration = np.asarray(duration_days, dtype=np.float64).reshape(shape)
    finite = np.isfinite(values)
    numerator = np.sum(np.where(finite, values, 0.0) * duration, axis=0)
    denominator = np.sum(np.where(finite, duration, 0.0), axis=0)
    return np.divide(
        numerator,
        denominator,
        out=np.full(values.shape[1:], np.nan, dtype=np.float64),
        where=denominator > 0,
    )


def annual_rate_integral(values: np.ndarray, duration_days: np.ndarray) -> np.ndarray:
    """Integrate monthly mean per-second rates to an annual total."""
    values = np.asarray(values, dtype=np.float64)
    shape = (len(duration_days),) + (1,) * (values.ndim - 1)
    seconds = np.asarray(duration_days, dtype=np.float64).reshape(shape) * SECONDS_PER_DAY
    finite = np.isfinite(values)
    out = np.sum(np.where(finite, values, 0.0) * seconds, axis=0)
    out[~np.any(finite, axis=0)] = np.nan
    return out


def domain_mean(field: np.ndarray, weights_km2: np.ndarray) -> float:
    mask = np.isfinite(field) & np.isfinite(weights_km2) & (weights_km2 > 0)
    if not np.any(mask):
        return np.nan
    return float(np.sum(field[mask] * weights_km2[mask]) / np.sum(weights_km2[mask]))


def domain_total_pgc(field_g_m2: np.ndarray, weights_km2: np.ndarray) -> float:
    mask = np.isfinite(field_g_m2) & np.isfinite(weights_km2) & (weights_km2 > 0)
    if not np.any(mask):
        return np.nan
    return float(np.sum(field_g_m2[mask] * weights_km2[mask]) * 1.0e6 / 1.0e15)
