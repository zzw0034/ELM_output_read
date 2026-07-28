"""
elmtools.process — processing utilities for ELM output data.

Main functions
--------------
build_regular_grid(lat, lon, ...)        : build 1/N° regular grid from unstructured lat/lon
scatter_to_grid(vals, lat, lon, ...)     : scatter unstructured columns → regular (lat, lon) grid
elm_to_gridded_da(ds, var, ...)          : end-to-end: open dataset variable → gridded DataArray
flux_to_annual(da)                       : gC/m²/s → gC/m²/year
flux_to_monthly(da)                      : gC/m²/s → gC/m²/month
aggregate_monthly_to_yearly(da, ...)     : monthly → yearly (sum or mean)
time_coord_minus_one_year(tc)            : shift time coordinate back by one year (h0 date fix)
subtract_month_cftime(t)                 : subtract one month from a cftime object
detect_flux_scale_from_bounds(ds, ...)   : auto-detect monthly/yearly averaging → (seconds, units_str)
"""

import numpy as np
import xarray as xr
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SECONDS_PER_YEAR: int = 365 * 24 * 3600   # 31 536 000  s/yr
SECONDS_PER_DAY: int = 24 * 3600          # 86 400  s/day

# Variables treated as fluxes (gC/m²/s) that need unit conversion
DEFAULT_FLUX_VARS: frozenset[str] = frozenset(
    {"GPP", "NPP", "NEE", "ER", "HR", "AR", "FAREA_BURNED", "PFT_FIRE_CLOSS"}
)

# ---------------------------------------------------------------------------
# Regular-grid construction
# ---------------------------------------------------------------------------

def build_regular_grid(
    lat: np.ndarray,
    lon: np.ndarray,
    resolution: int = 24,
) -> tuple[np.ndarray, np.ndarray, int, int]:
    """
    Build a regular lat/lon grid that covers the extent of unstructured ELM output.

    ELM's Southeast US domain uses 1/24° (~4 km) spacing; pass ``resolution=24``
    to match.  For a 1/8° grid pass ``resolution=8``.

    Parameters
    ----------
    lat, lon : np.ndarray
        1-D arrays of unstructured column coordinates (shape ``(ncol,)``).
    resolution : int
        Points per degree (default 24 → 1/24°).

    Returns
    -------
    laty : np.ndarray  shape (nlat,)
    lonx : np.ndarray  shape (nlon,)
    nlat : int
    nlon : int

    Example
    -------
    >>> laty, lonx, nlat, nlon = build_regular_grid(ds["lat"].values, ds["lon"].values)
    """
    lat_min, lat_max = float(np.min(lat)), float(np.max(lat))
    lon_min, lon_max = float(np.min(lon)), float(np.max(lon))
    nlat = int((lat_max - lat_min) * resolution) + 1
    nlon = int((lon_max - lon_min) * resolution) + 1
    laty = np.linspace(lat_min, lat_max, nlat)
    lonx = np.linspace(lon_min, lon_max, nlon)
    return laty, lonx, nlat, nlon


# ---------------------------------------------------------------------------
# Unstructured → regular grid scatter
# ---------------------------------------------------------------------------

def scatter_to_grid(
    vals_all: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    landmask: np.ndarray,
    laty: np.ndarray,
    lonx: np.ndarray,
    lat_min: float | None = None,
    lon_min: float | None = None,
    resolution: int = 24,
) -> np.ndarray:
    """
    Scatter unstructured ELM column data onto a regular (lat, lon) grid.

    Parameters
    ----------
    vals_all : np.ndarray  shape (time, ncol)
        Data values on the unstructured grid.
    lat, lon : np.ndarray  shape (ncol,)
        Column coordinates.
    landmask : np.ndarray  shape (ncol,)
        pftmask: 1 = land, 0 = ocean.  Only land columns are written to the grid.
    laty, lonx : np.ndarray
        1-D coordinate arrays from :func:`build_regular_grid`.
    lat_min, lon_min : float, optional
        Grid origin; defaults to ``min(lat)`` / ``min(lon)``.
    resolution : int
        Points per degree (must match how *laty*/*lonx* were built).

    Returns
    -------
    np.ndarray  shape (time, nlat, nlon)
        Regular grid filled with NaN where no land column maps.

    Example
    -------
    >>> laty, lonx, nlat, nlon = build_regular_grid(lat, lon)
    >>> grid = scatter_to_grid(vals, lat, lon, mask, laty, lonx)
    """
    if lat_min is None:
        lat_min = float(np.min(lat))
    if lon_min is None:
        lon_min = float(np.min(lon))

    nlat, nlon = len(laty), len(lonx)
    ix = np.clip(np.round((lon - lon_min) * resolution).astype(int), 0, nlon - 1)
    iy = np.clip(np.round((lat - lat_min) * resolution).astype(int), 0, nlat - 1)
    iland = np.where(landmask == 1)[0]

    if vals_all.ndim == 1:
        vals_all = vals_all[np.newaxis, :]   # (1, ncol)

    data_grid = np.full((vals_all.shape[0], nlat, nlon), np.nan)
    data_grid[:, iy[iland], ix[iland]] = vals_all[:, iland]
    return data_grid


# ---------------------------------------------------------------------------
# End-to-end helper: variable in dataset → gridded DataArray
# ---------------------------------------------------------------------------

def elm_to_gridded_da(
    ds: xr.Dataset,
    var: str,
    laty: np.ndarray,
    lonx: np.ndarray,
    landmask: np.ndarray | None = None,
    lat: np.ndarray | None = None,
    lon: np.ndarray | None = None,
    resolution: int = 24,
    lat_min: float | None = None,
    lon_min: float | None = None,
) -> xr.DataArray:
    """
    Compute a variable from *ds* and scatter it to a regular grid DataArray.

    Reads ``pftmask``, ``lat``, ``lon`` from *ds* if not supplied explicitly
    (passing them in avoids recomputing when processing many variables on the
    same dataset).

    Parameters
    ----------
    ds : xr.Dataset
    var : str
        Variable name in *ds*.
    laty, lonx : np.ndarray
        Regular grid coordinates (from :func:`build_regular_grid`).
    landmask, lat, lon : np.ndarray, optional
        Pre-extracted coordinate arrays.  Read from *ds* if ``None``.
    resolution : int
        Points per degree (default 24).
    lat_min, lon_min : float, optional
        Grid origin override.

    Returns
    -------
    xr.DataArray  dims=(time, lat, lon)

    Example
    -------
    >>> laty, lonx, nlat, nlon = build_regular_grid(lat, lon)
    >>> da = elm_to_gridded_da(ds, "GPP", laty, lonx)
    """
    if lat is None:
        lat = ds["lat"].values
    if lon is None:
        lon = ds["lon"].values
    if landmask is None:
        landmask = ds["pftmask"].values

    vals = ds[var].compute().values
    grid = scatter_to_grid(vals, lat, lon, landmask, laty, lonx,
                           lat_min=lat_min, lon_min=lon_min, resolution=resolution)
    da = xr.DataArray(
        grid,
        dims=("time", "lat", "lon"),
        coords={"time": ds["time"], "lat": laty, "lon": lonx},
        name=var,
        attrs={
            "long_name": ds[var].attrs.get("long_name", var),
            "units": ds[var].attrs.get("units", "unknown"),
            "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
    return da


# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------

def flux_to_annual(da: xr.DataArray) -> xr.DataArray:
    """
    Convert a flux variable from **gC/m²/s** to **gC/m²/year**.

    Multiplies by ``365 * 24 * 3600`` seconds.  Suitable for ELM h0 annual
    snapshot files where each file covers one year.

    Parameters
    ----------
    da : xr.DataArray
        DataArray with units gC/m²/s.

    Returns
    -------
    xr.DataArray
        Same shape, units updated in attrs.

    Example
    -------
    >>> gpp_annual = flux_to_annual(ds["GPP"])
    """
    out = da * SECONDS_PER_YEAR
    out.attrs = {**da.attrs, "units": "gC/m^2/year"}
    return out


def flux_to_monthly(da: xr.DataArray) -> xr.DataArray:
    """
    Convert a flux variable from **gC/m²/s** to **gC/m²/month**.

    Multiplies by ``days_in_month * 24 * 3600`` where ``days_in_month`` is
    read from the time coordinate.

    Parameters
    ----------
    da : xr.DataArray
        DataArray with a ``time`` dimension and units gC/m²/s.

    Returns
    -------
    xr.DataArray  same shape, units gC/m²/month.
    """
    days = da["time"].dt.days_in_month
    out = da * days * SECONDS_PER_DAY
    out.attrs = {**da.attrs, "units": "gC/m^2/month"}
    return out


# ---------------------------------------------------------------------------
# Auto-detect flux scaling from time_bounds
# ---------------------------------------------------------------------------

def detect_flux_scale_from_bounds(
    ds: xr.Dataset,
    time_index: int = 0,
) -> tuple[float, str]:
    """
    Auto-detect the averaging period of an h0 dataset and return a flux scale factor.

    Looks at ``time_bounds[time_index]`` to compute the duration of one time
    record; falls back to ``cftime.daysinmonth`` or 365 days if absent.

    Returns
    -------
    (seconds, units_str) where ``units_str`` is one of:
        - ``"gC/m²/year"``    for ~365 days (350–380 d window)
        - ``"gC/m²/month"``   for ~30 days (27–32 d window)
        - ``"gC/m²/day"``     for ~1 day (0.9–1.1 d window)
        - ``"gC/m² ({d}-day avg)"`` otherwise

    Multiply a gC/m²/s flux by ``seconds`` to get total carbon over the period.

    Example
    -------
    >>> import xarray as xr
    >>> ds = xr.open_dataset("monthly_file.nc")
    >>> scale, units = detect_flux_scale_from_bounds(ds)
    >>> gpp_monthly_total = ds["GPP"].isel(time=0).values * scale   # gC/m²/month
    """
    # Try time_bounds (exact)
    try:
        tb = ds["time_bounds"].isel(time=time_index).values
        t0, t1 = tb[0], tb[1]
        delta = t1 - t0
        if hasattr(delta, "total_seconds"):
            secs = float(delta.total_seconds())
        else:
            secs = float(delta / np.timedelta64(1, "s"))
        days = secs / SECONDS_PER_DAY
        if 350 <= days <= 380:
            return secs, "gC/m²/year"
        if 27 <= days <= 32:
            return secs, "gC/m²/month"
        if 0.9 <= days <= 1.1:
            return secs, "gC/m²/day"
        return secs, f"gC/m² ({days:.1f}-day avg)"
    except Exception:
        pass

    # Fallback: cftime daysinmonth
    try:
        t0 = ds["time"].values[time_index]
        days = t0.daysinmonth if hasattr(t0, "daysinmonth") else 365
    except Exception:
        days = 365

    if days >= 350:
        return float(SECONDS_PER_YEAR), "gC/m²/year"
    return float(days * SECONDS_PER_DAY), "gC/m²/month"


# ---------------------------------------------------------------------------
# Temporal aggregation
# ---------------------------------------------------------------------------

def aggregate_monthly_to_yearly(
    da: xr.DataArray,
    method: str = "mean",
    time_offset: bool = True,
) -> xr.DataArray:
    """
    Aggregate monthly ELM output to yearly values.

    Parameters
    ----------
    da : xr.DataArray
        Monthly data with a ``time`` dimension using cftime coordinates.
    method : {"mean", "sum"}
        Use ``"mean"`` for pool variables (carbon stocks), ``"sum"`` for
        flux variables already converted to monthly totals.
    time_offset : bool
        If ``True`` (default), subtract one month from each time stamp before
        grouping.  ELM h0 monthly files are stamped on the *first of the next
        month* (e.g. Jan output → Feb 1 stamp), so this correction restores
        the true month.

    Returns
    -------
    xr.DataArray  with a ``year`` dimension (integer).

    Example
    -------
    >>> gpp_annual = aggregate_monthly_to_yearly(gpp_monthly, method="sum")
    """
    if method not in ("mean", "sum"):
        raise ValueError(f"method must be 'mean' or 'sum', got {method!r}")

    time_vals = da["time"].values
    if time_offset:
        time_vals = np.array([subtract_month_cftime(t) for t in time_vals])

    years = np.array([t.year for t in time_vals])
    unique_years = np.unique(years)

    yearly_slices = []
    for yr in unique_years:
        mask = years == yr
        subset = da.isel(time=mask)
        valid_mask = ~np.isnan(subset).all(dim="time")
        if method == "sum":
            agg = subset.sum(dim="time", skipna=True)
        else:
            agg = subset.mean(dim="time", skipna=True)
        agg = agg.where(valid_mask)
        agg = agg.assign_coords(year=int(yr))
        yearly_slices.append(agg)

    out = xr.concat(yearly_slices, dim="year")
    out.attrs = {
        **da.attrs,
        "aggregation_method": method,
        "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return out


# ---------------------------------------------------------------------------
# Time coordinate utilities
# ---------------------------------------------------------------------------

def time_coord_minus_one_year(time_coord: xr.DataArray) -> np.ndarray:
    """
    Return time values shifted back by one year.

    ELM h0 annual files are written with a timestamp of ``YYYY-01-01`` but
    record the *state at the end of the previous year* (i.e. year YYYY-1).
    This function corrects that offset.

    Works with both cftime objects (e.g. ``DatetimeNoLeap``) and
    ``numpy.datetime64``.

    Parameters
    ----------
    time_coord : xr.DataArray  (the ``time`` coordinate of a dataset)

    Returns
    -------
    np.ndarray  same dtype/class as input values, year decremented by 1.

    Example
    -------
    >>> ds = ds.assign_coords(time=time_coord_minus_one_year(ds["time"]))
    """
    tvals = time_coord.values
    if len(tvals) == 0:
        return tvals
    t0 = tvals.flat[0]
    if hasattr(t0, "year"):
        # cftime (e.g. DatetimeNoLeap, DatetimeGregorian)
        return np.array(
            [
                type(t)(
                    t.year - 1,
                    t.month,
                    t.day,
                    getattr(t, "hour", 0),
                    getattr(t, "minute", 0),
                    getattr(t, "second", 0),
                )
                for t in tvals
            ]
        )
    # numpy datetime64: subtract 365 days as approximation
    return tvals - np.timedelta64(365, "D")


def subtract_month_cftime(t) -> object:
    """
    Subtract one month from a cftime object, wrapping December → previous year.

    Parameters
    ----------
    t : cftime date object  (e.g. ``cftime.DatetimeNoLeap``)

    Returns
    -------
    Same cftime type with month decremented.

    Example
    -------
    >>> corrected = [subtract_month_cftime(t) for t in ds["time"].values]
    """
    year = t.year
    month = t.month - 1
    if month == 0:
        year -= 1
        month = 12
    return type(t)(year, month, t.day,
                   getattr(t, "hour", 0),
                   getattr(t, "minute", 0),
                   getattr(t, "second", 0))
