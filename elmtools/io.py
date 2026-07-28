"""
elmtools.io — I/O utilities for ELM h0 output NetCDF files.

Main functions
--------------
find_h0_files(run_dir, ...)      : glob + sort ELM h0 files by embedded date
h0_date_key(path)                : sort key (year, month, day) from filename
derive_h0_label(nc_path)         : short label "<case>_<date>" from h0 filename
open_elm_dataset(files, vars, .) : probe-then-open_mfdataset with selective loading
probe_available_vars(file_path)  : list variable names in a single NC file
"""

import os
import re
import glob

import numpy as np
import xarray as xr

xr.set_options(file_cache_maxsize=2000)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def h0_date_key(path: str) -> tuple[int, int, int]:
    """
    Sort key extracted from an ELM h0 filename.

    Expects the pattern ``PREFIX.elm.h0.YYYY-MM-DD-00000.nc`` and returns
    ``(year, month, day)`` as ints so files sort chronologically.
    Returns ``(0, 0, 0)`` if the pattern is not found.

    Example
    -------
    >>> h0_date_key("run/20260206.elm.h0.1973-01-01-00000.nc")
    (1973, 1, 1)
    """
    m = re.search(r"\.elm\.h0\.(\d{4})-(\d{2})-(\d{2})", os.path.basename(path))
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return (0, 0, 0)


def derive_h0_label(nc_path: str) -> str:
    """
    Build a short label from an ELM h0 filename, useful for output subfolder names.

    Pattern recognised: ``PREFIX_<case>.elm.h0.<date>[-00000].nc``  →  ``<case>_<date>``.
    The *case* is taken as the last underscore-token of the prefix immediately
    before ``.elm``; the *date* is whatever follows ``.h0.``, stripped of any
    trailing ``-00000``.

    Falls back to the file stem if the pattern is not recognised.

    Example
    -------
    >>> derive_h0_label(".../20260605_Southeast_hires_ICB20TRCNPRDCTCBC.elm.h0.1898-07.nc")
    'ICB20TRCNPRDCTCBC_1898-07'
    >>> derive_h0_label(".../20260605..._ad_spinup.elm.h0.0021-01-01-00000.nc")
    'spinup_0021-01-01'
    """
    base = os.path.basename(nc_path).replace(".nc", "")
    parts = base.split(".")
    if "elm" in parts and "h0" in parts:
        i_h0 = parts.index("h0")
        casebit = parts[i_h0 - 2] if i_h0 >= 2 else ""
        timebit = parts[i_h0 + 1] if i_h0 + 1 < len(parts) else ""
        casebit = casebit.split("_")[-1]
        timebit = timebit.split("-00000")[0]
        if casebit and timebit:
            return f"{casebit}_{timebit}"
    return base


def find_h0_files(
    run_dir: str,
    pattern: str = "*.elm.h0.*.nc",
    year_min: int | None = None,
    year_max: int | None = None,
) -> list[str]:
    """
    Return a list of ELM h0 output files sorted by the date in their filename.

    Parameters
    ----------
    run_dir : str
        Path to the ELM run directory containing the ``.nc`` files.
    pattern : str
        Glob pattern relative to *run_dir* (default ``"*.elm.h0.*.nc"``).
    year_min, year_max : int, optional
        If given, keep only files whose embedded year is in [year_min, year_max].

    Returns
    -------
    list[str]
        Sorted list of absolute paths.

    Example
    -------
    >>> files = find_h0_files("/gpfs/.../run", year_min=1850, year_max=1973)
    """
    files = sorted(
        glob.glob(os.path.join(run_dir, pattern)),
        key=h0_date_key,
    )
    if year_min is not None:
        files = [f for f in files if h0_date_key(f)[0] >= year_min]
    if year_max is not None:
        files = [f for f in files if h0_date_key(f)[0] <= year_max]
    return files


# ---------------------------------------------------------------------------
# Selective dataset opening
# ---------------------------------------------------------------------------

def open_elm_dataset(
    files: list[str],
    vars_to_read: list[str],
    coord_vars: list[str] | None = None,
    chunks: dict | None = None,
    parallel: bool = True,
    decode_times: bool = True,
) -> xr.Dataset:
    """
    Open a collection of ELM output files, loading only the requested variables.

    Probes the first file to discover all variables, then builds a drop-list so
    that ``open_mfdataset`` reads only *vars_to_read* + *coord_vars*.

    Parameters
    ----------
    files : list[str]
        Paths to NetCDF files (already sorted).
    vars_to_read : list[str]
        Variables of scientific interest (e.g. ``["GPP", "NPP"]``).
    coord_vars : list[str], optional
        Variables always kept regardless of *vars_to_read*.
        Defaults to ``["pftmask", "lat", "lon", "time"]``.
    chunks : dict, optional
        Dask chunk specification (e.g. ``{"time": 12}``).
        If ``None``, defaults to ``{"time": 12}``.
    parallel : bool
        Pass to ``xr.open_mfdataset`` (default ``True``).
    decode_times : bool
        Pass to ``xr.open_mfdataset`` (default ``True``).

    Returns
    -------
    xr.Dataset

    Example
    -------
    >>> ds = open_elm_dataset(files, ["GPP", "TOTVEGC"])
    >>> gpp = ds["GPP"]
    """
    if coord_vars is None:
        coord_vars = ["pftmask", "lat", "lon", "time"]
    if chunks is None:
        chunks = {"time": 12}

    keep = set(vars_to_read) | set(coord_vars)

    # Probe first file to get full variable list
    probe = xr.open_dataset(files[0], decode_times=decode_times)
    all_vars = list(probe.variables.keys())
    all_coords = list(probe.coords.keys())
    probe.close()

    drop = [v for v in all_vars if v not in keep and v not in all_coords]

    ds = xr.open_mfdataset(
        files,
        combine="by_coords",
        drop_variables=drop,
        data_vars="minimal",
        coords="minimal",
        compat="override",
        parallel=parallel,
        chunks=chunks,
        decode_times=decode_times,
    )
    return ds


def probe_available_vars(file_path: str) -> list[str]:
    """
    Return the list of variable names available in a single ELM output file.

    Useful for checking which variables exist before opening a large dataset.

    Example
    -------
    >>> vars = probe_available_vars(files[0])
    >>> "GPP" in vars
    True
    """
    ds = xr.open_dataset(file_path, decode_times=True)
    available = list(ds.variables.keys())
    ds.close()
    return available
