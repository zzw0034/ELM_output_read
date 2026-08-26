"""
elmtools.plot — plotting utilities for ELM output data.

All functions use the ``Agg`` backend (no display required) and save figures
to disk.  Safe to call in HPC batch jobs.

Main functions
--------------
plot_regional_mean_timeseries(da, ...)  : regional mean time series (time × value)
plot_2d_map(arr, lat, lon, ...)         : single 2-D pcolormesh map (optional cartopy)
plot_comparison_maps(a1, a2, ...)       : side-by-side comparison of two 2-D maps
build_h0_regular_grid_data(ds, var, ...) : h0 var (time,ncol) -> (time,lat,lon) grid arrays
subset_grid_by_lon(...)                 : keep grid east of a longitude threshold
plot_cartopy_timeslice(...)             : cartopy pcolormesh for one timestep
save_geotiff(lon, lat, data2d, ...)     : write 2-D array as GeoTIFF (EPSG:4326, north-up)
cftime_to_datetime(t)                   : convert cftime/datetime64 → Python datetime
"""

import os

import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed (safe for HPC batch)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from datetime import datetime as dt

import xarray as xr
from .process import build_regular_grid, scatter_to_grid


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def cftime_to_datetime(t) -> dt:
    """
    Convert a cftime object or numpy datetime64 to a Python ``datetime``.

    Needed because Matplotlib's date formatters do not accept cftime objects.

    Example
    -------
    >>> times = np.array([cftime_to_datetime(t) for t in ds["time"].values])
    """
    if hasattr(t, "year"):
        return dt(t.year, t.month, t.day,
                  getattr(t, "hour", 0),
                  getattr(t, "minute", 0),
                  getattr(t, "second", 0))
    # numpy datetime64
    ts = (t - np.datetime64("1970-01-01T00:00:00")) / np.timedelta64(1, "s")
    return dt.utcfromtimestamp(float(ts))


# ---------------------------------------------------------------------------
# Time series
# ---------------------------------------------------------------------------

def plot_regional_mean_timeseries(
    da: xr.DataArray,
    var_name: str,
    outfile: str,
    units: str = "",
    title: str | None = None,
    color: str = "steelblue",
    figsize: tuple[float, float] = (10, 4),
) -> None:
    """
    Plot regional mean time series from a gridded DataArray (time, lat, lon).

    Parameters
    ----------
    da : xr.DataArray  dims=(time, lat, lon)
        Gridded data.  Ocean/missing values should be NaN.
    var_name : str
        Variable label used on the y-axis.
    outfile : str
        Path to save the figure (e.g. ``"GPP_timeseries.png"``).
    units : str
        Unit string appended to the y-axis label.
    title : str, optional
        Figure title; defaults to ``"Regional Mean {var_name}"``.
    color : str
        Line color (default ``"steelblue"``).
    figsize : tuple
        Figure size in inches.

    Example
    -------
    >>> plot_regional_mean_timeseries(gpp_da, "GPP", "GPP_ts.png", units="gC/m²/year")
    """
    mean_ts = da.mean(dim=["lat", "lon"], skipna=True)
    time_raw = mean_ts["time"].values
    vals = mean_ts.values
    times = np.array([cftime_to_datetime(t) for t in time_raw])

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(times, vals, color=color, linewidth=1.2)
    ax.set_xlabel("Time")
    ylabel = f"Regional mean {var_name}"
    if units:
        ylabel += f" ({units})"
    ax.set_ylabel(ylabel)
    ax.set_title(title or f"Regional Mean {var_name}")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(
        mdates.MonthLocator(interval=max(1, len(times) // 24))
    )
    plt.xticks(rotation=45)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()
    print(f"Saved: {outfile}")


# ---------------------------------------------------------------------------
# 2-D map
# ---------------------------------------------------------------------------

def plot_2d_map(
    arr: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    var_name: str,
    title: str,
    outfile: str,
    vmin: float | None = None,
    vmax: float | None = None,
    cmap: str = "viridis",
    figsize: tuple[float, float] = (8, 5),
    add_states: bool = False,
    *,
    units: str = "",
    add_coastlines: bool = True,
    add_borders: bool = False,
    add_gridlines: bool = False,
    set_extent: bool = True,
    file_mode: int | None = 0o644,
    norm=None,
    cbar_location: str = "right",
) -> None:
    """
    Plot a single 2-D pcolormesh map on a lat/lon grid.

    With ``add_states=True`` (or any other cartopy-requiring flag) the figure
    uses a cartopy ``PlateCarree`` projection and can show coastlines, state
    borders, country borders, and lat/lon gridlines.  Falls back to a plain
    matplotlib axes when cartopy is unavailable.

    Parameters
    ----------
    arr : np.ndarray  shape (nlat, nlon)
    lat, lon : np.ndarray
        1-D coordinate arrays (or 2-D meshgrid).
    var_name : str
        Variable name shown on the colorbar.
    title : str
        Figure title.
    outfile : str
        Output PNG path.
    vmin, vmax : float, optional
        Color scale limits; auto-computed from data if not given.
    cmap : str
        Matplotlib colormap name.
    figsize : tuple
        Figure size in inches.
    add_states : bool
        Show US state boundaries (requires cartopy).
    units : str, optional
        Appended to the colorbar label as ``"<var_name> (<units>)"``.
    add_coastlines : bool
        Show coastlines (cartopy only).
    add_borders : bool
        Show country borders (cartopy only).
    add_gridlines : bool
        Show lat/lon gridlines with labels (cartopy only).
    set_extent : bool
        Set map extent to the data range (cartopy only).
    file_mode : int, optional
        ``os.chmod`` permission applied to the output file (default ``0o644``).
        Pass ``None`` to skip.
    norm : matplotlib.colors.Normalize, optional
        Custom normalization (e.g. ``BoundaryNorm`` for a quantile color
        scale). When given, it takes precedence over *vmin*/*vmax*.
    cbar_location : {"right", "bottom", "left", "top"}
        Where to place the colorbar (default ``"right"``); ``"bottom"``
        gives a horizontal bar under the map.

    Example
    -------
    >>> plot_2d_map(grid[0], laty, lonx, "GPP", "GPP 1990", "gpp_1990.png",
    ...             units="gC/m²/year", add_states=True)
    """
    cbar_label = f"{var_name} ({units})" if units else var_name
    use_cartopy = add_states or add_coastlines or add_borders or add_gridlines or set_extent
    if norm is not None:
        vmin, vmax = None, None

    cartopy_ok = False
    if use_cartopy:
        try:
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
            cartopy_ok = True
        except ImportError:
            print("cartopy not available; falling back to plain matplotlib axes")

    if cartopy_ok:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        mesh = ax.pcolormesh(lon, lat, arr, vmin=vmin, vmax=vmax, norm=norm,
                             cmap=cmap, shading="auto",
                             transform=ccrs.PlateCarree())
        if add_coastlines:
            ax.coastlines(resolution="10m", linewidth=0.8)
        if add_states:
            ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor="black")
        if add_borders:
            ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        if set_extent:
            lon_arr = np.asarray(lon)
            lat_arr = np.asarray(lat)
            ax.set_extent([lon_arr.min(), lon_arr.max(),
                           lat_arr.min(), lat_arr.max()],
                          crs=ccrs.PlateCarree())
        if add_gridlines:
            gl = ax.gridlines(draw_labels=True, linewidth=0.3,
                              color="gray", alpha=0.5, linestyle="--")
            gl.top_labels = False
            gl.right_labels = False
        cbar_pad = 0.08 if cbar_location in ("bottom", "top") else 0.02
        plt.colorbar(mesh, ax=ax, label=cbar_label, pad=cbar_pad, shrink=0.85,
                     location=cbar_location)
        ax.set_title(title)
    else:
        fig, ax = plt.subplots(figsize=figsize)
        mesh = ax.pcolormesh(lon, lat, arr, vmin=vmin, vmax=vmax, norm=norm,
                             cmap=cmap, shading="auto")
        plt.colorbar(mesh, ax=ax, label=cbar_label, location=cbar_location)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(title)
        ax.set_aspect("equal")

    fig.tight_layout()
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)
    if file_mode is not None:
        try:
            os.chmod(outfile, file_mode)
        except OSError:
            pass
    print(f"Saved: {outfile}")


# ---------------------------------------------------------------------------
# h0 gridded-map helpers (from analysis scripts)
# ---------------------------------------------------------------------------

def build_h0_regular_grid_data(
    ds: xr.Dataset,
    var_name: str,
    resolution: int = 24,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Build regular-grid map arrays from an ELM h0 variable.

    Parameters
    ----------
    ds : xr.Dataset
        ELM dataset containing ``var_name``, ``pftmask``, ``lat``, and ``lon``.
    var_name : str
        Variable with shape ``(time, ncol)``.
    resolution : int
        Points per degree for regular grid (default 24 -> 1/24 degree).

    Returns
    -------
    lon_grid : np.ndarray  shape (nlat, nlon)
    lat_grid : np.ndarray  shape (nlat, nlon)
    data_grid : np.ndarray shape (time, nlat, nlon)
    time_values : np.ndarray shape (time,)
    """
    vals = ds[var_name].values
    landmask = ds["pftmask"].values
    lat = ds["lat"].values
    lon = ds["lon"].values
    time_values = ds["time"].values

    laty, lonx, _, _ = build_regular_grid(lat, lon, resolution=resolution)
    data_grid = scatter_to_grid(vals, lat, lon, landmask, laty, lonx, resolution=resolution)
    lon_grid, lat_grid = np.meshgrid(lonx, laty)
    return lon_grid, lat_grid, data_grid, time_values


def subset_grid_by_lon(
    lon_grid: np.ndarray,
    lat_grid: np.ndarray,
    data_grid: np.ndarray,
    lon_min: float = -95.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Keep only longitudes >= ``lon_min`` in regular-grid arrays.

    Parameters
    ----------
    lon_grid, lat_grid : np.ndarray  shape (nlat, nlon)
    data_grid : np.ndarray           shape (time, nlat, nlon)
    lon_min : float
        Longitude threshold (default -95.0).

    Returns
    -------
    lon_grid_sub, lat_grid_sub, data_grid_sub : np.ndarray
        Subset arrays with same dimensionality.
    """
    lonx = lon_grid[0, :]
    east_idx = np.where(lonx >= lon_min)[0]
    return lon_grid[:, east_idx], lat_grid[:, east_idx], data_grid[:, :, east_idx]


def plot_cartopy_timeslice(
    lon_grid: np.ndarray,
    lat_grid: np.ndarray,
    data_grid: np.ndarray,
    t_index: int,
    var_name: str,
    outfile: str,
    levels: np.ndarray | None = None,
    cmap: str = "viridis",
    add_borders: bool = True,
    add_states: bool = True,
    title: str | None = None,
    figsize: tuple[float, float] = (10, 6),
) -> None:
    """
    Plot one timestep of a gridded field using Cartopy PlateCarree projection.

    Parameters
    ----------
    lon_grid, lat_grid : np.ndarray  shape (nlat, nlon)
    data_grid : np.ndarray           shape (time, nlat, nlon)
    t_index : int
        Time index to plot.
    var_name : str
        Label for colorbar.
    outfile : str
        Path to save figure.
    levels : np.ndarray, optional
        Boundaries for ``BoundaryNorm``. If ``None``, use plain colormap scaling.
    cmap : str
        Matplotlib colormap.
    add_borders, add_states : bool
        Toggle Cartopy political boundaries.
    title : str, optional
        Figure title.
    figsize : tuple
        Figure size in inches.
    """
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except ImportError as e:
        raise ImportError(
            "cartopy is required for plot_cartopy_timeslice"
        ) from e

    fig = plt.figure(figsize=figsize)
    ax = plt.axes(projection=ccrs.PlateCarree())

    arr = data_grid[t_index, :, :]
    if levels is not None:
        norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=256)
        mesh = ax.pcolormesh(
            lon_grid, lat_grid, arr, norm=norm, cmap=cmap, transform=ccrs.PlateCarree()
        )
    else:
        mesh = ax.pcolormesh(
            lon_grid, lat_grid, arr, cmap=cmap, transform=ccrs.PlateCarree()
        )

    ax.coastlines(resolution="10m")
    if add_borders:
        ax.add_feature(cfeature.BORDERS, linestyle=":")
    if add_states:
        ax.add_feature(cfeature.STATES, linestyle="-", edgecolor="black")

    plt.colorbar(mesh, ax=ax, orientation="vertical", label=var_name)
    ax.set_title(title or f"{var_name} (t={t_index})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.tight_layout()
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {outfile}")


# ---------------------------------------------------------------------------
# Side-by-side comparison
# ---------------------------------------------------------------------------

def plot_comparison_maps(
    arr1: np.ndarray,
    arr2: np.ndarray,
    lat1: np.ndarray,
    lon1: np.ndarray,
    lat2: np.ndarray,
    lon2: np.ndarray,
    var_name: str,
    title: str,
    outfile: str,
    labels: tuple[str, str] = ("Sim 1", "Sim 2"),
    cmap: str = "viridis",
    figsize: tuple[float, float] = (12, 5),
) -> None:
    """
    Plot two 2-D maps side-by-side with a shared color scale.

    Useful for comparing two simulations or two time periods of the same
    variable.

    Parameters
    ----------
    arr1, arr2 : np.ndarray  shape (nlat, nlon)
        Data arrays for each panel.
    lat1, lon1 : np.ndarray
        Coordinates for *arr1*.
    lat2, lon2 : np.ndarray
        Coordinates for *arr2*.
    var_name : str
        Colorbar label.
    title : str
        Figure super-title.
    outfile : str
        Save path.
    labels : tuple[str, str]
        Sub-titles for left and right panels.
    cmap, figsize : as in :func:`plot_2d_map`.

    Example
    -------
    >>> plot_comparison_maps(
    ...     zw5_arr, dan_arr, lat_zw5, lon_zw5, lat_dan, lon_dan,
    ...     "GPP", "GPP 1990", "compare_1990.png",
    ...     labels=("zw5 run", "Dan run"),
    ... )
    """
    all_vals = np.concatenate([arr1.ravel(), arr2.ravel()])
    finite = all_vals[np.isfinite(all_vals)]
    vmin = float(np.nanmin(finite)) if len(finite) else 0.0
    vmax = float(np.nanmax(finite)) if len(finite) else 1.0
    if vmin >= vmax:
        vmin, vmax = 0.0, 1.0

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=figsize)
    for ax, arr, lat, lon, label in zip(
        [ax0, ax1], [arr1, arr2], [lat1, lat2], [lon1, lon2], labels
    ):
        im = ax.pcolormesh(lon, lat, arr, vmin=vmin, vmax=vmax,
                           cmap=cmap, shading="auto")
        ax.set_title(f"{label}\n{var_name}")
        ax.set_xlabel("lon")
        ax.set_ylabel("lat")
        ax.set_aspect("equal")
        plt.colorbar(im, ax=ax, label=var_name)

    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {outfile}")


# ---------------------------------------------------------------------------
# GeoTIFF export
# ---------------------------------------------------------------------------

def save_geotiff(
    lon1d: np.ndarray,
    lat1d: np.ndarray,
    data2d: np.ndarray,
    out_path: str,
    *,
    nodata: float = -9999.0,
    epsg: int = 4326,
    coords_are: str = "center",
    file_mode: int | None = 0o644,
) -> None:
    """
    Write a 2-D array as a GeoTIFF (north-up, EPSG:4326 by default).

    NaN values in ``data2d`` are replaced with ``nodata``.  If ``lat1d`` is
    ascending (south→north), the array is flipped so the resulting raster is
    north-up, which is what GeoTIFF/QGIS expect.

    ELM/CLM h0 ``lat`` and ``lon`` arrays are **cell centers**, which is the
    default here (``coords_are="center"``).  The function adds half a cell on
    each side to derive the true outer bounds expected by GeoTIFF.  Pass
    ``coords_are="edge"`` if your inputs already represent the full bounding
    box (e.g. cell edges from ``lat_bounds``/``lon_bounds``).

    Parameters
    ----------
    lon1d, lat1d : np.ndarray
        1-D coordinate arrays.  See ``coords_are``.
    data2d : np.ndarray  shape (nlat, nlon)
        Data to write.
    out_path : str
        Output ``.tif`` path.
    nodata : float
        NoData value (default -9999.0).
    epsg : int
        EPSG code for the CRS (default 4326 = WGS84 lat/lon).
    coords_are : {"center", "edge"}
        How to interpret ``lon1d``/``lat1d``.  Default ``"center"`` (the
        ELM/CLM convention); ``"edge"`` treats ``min/max`` as the raster
        bounding box directly.
    file_mode : int, optional
        ``os.chmod`` permission applied to the output file (default 0o644).
        Pass ``None`` to skip.

    Raises
    ------
    ImportError
        If ``rasterio`` is not installed.
    ValueError
        If ``coords_are`` is not ``"center"`` or ``"edge"``.

    Example
    -------
    >>> save_geotiff(ds["lon"].values, ds["lat"].values, gpp, "outputs/gpp.tif")
    """
    try:
        import rasterio
        from rasterio.crs import CRS as RioCRS
        from rasterio.transform import from_bounds
    except ImportError as e:
        raise ImportError(
            "rasterio is required for save_geotiff. Install with `pip install rasterio`."
        ) from e

    if coords_are not in ("center", "edge"):
        raise ValueError(f"coords_are must be 'center' or 'edge', got {coords_are!r}")

    nlat, nlon = data2d.shape
    arr = np.where(np.isfinite(data2d), data2d, nodata).astype(np.float32)
    lat1d = np.asarray(lat1d, dtype=float)
    lon1d = np.asarray(lon1d, dtype=float)
    if lat1d[0] < lat1d[-1]:
        arr = arr[::-1, :]

    if coords_are == "center":
        # Use median diff to be robust against tiny float drift at the ends.
        dlon = float(np.median(np.diff(lon1d))) if nlon > 1 else 0.0
        dlat = float(np.median(np.diff(lat1d))) if nlat > 1 else 0.0
        west  = float(lon1d.min()) - 0.5 * abs(dlon)
        east  = float(lon1d.max()) + 0.5 * abs(dlon)
        south = float(lat1d.min()) - 0.5 * abs(dlat)
        north = float(lat1d.max()) + 0.5 * abs(dlat)
    else:
        west, east   = float(lon1d.min()), float(lon1d.max())
        south, north = float(lat1d.min()), float(lat1d.max())

    transform = from_bounds(west, south, east, north, nlon, nlat)
    with rasterio.open(
        out_path, "w",
        driver="GTiff",
        height=nlat, width=nlon,
        count=1,
        dtype=arr.dtype,
        crs=RioCRS.from_epsg(epsg),
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(arr, 1)
    if file_mode is not None:
        try:
            os.chmod(out_path, file_mode)
        except OSError:
            pass
    print(f"Saved: {out_path}")
