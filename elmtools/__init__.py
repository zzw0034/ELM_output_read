"""
elmtools — reusable utilities for reading, processing, and plotting ELM output.

Modules
-------
io       : file discovery and selective open_mfdataset wrappers
process  : grid scatter, unit conversion, temporal aggregation, time fixups
plot     : time series, 2D map, side-by-side comparison plots
"""

from . import io, process, plot

__all__ = ["io", "process", "plot"]
