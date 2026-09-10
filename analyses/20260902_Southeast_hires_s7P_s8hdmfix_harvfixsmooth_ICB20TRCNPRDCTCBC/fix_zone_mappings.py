"""
Remove ocean-sentinel points from a cpl_bypass zone_mappings.txt.

Why
---
ELM's CPL_BYPASS met reader (`lnd_import_export.F90` ~line 411) loads every row
of `zone_mappings.txt`, then for each land gridcell picks the row minimising
`100*sqrt(dlat^2 + dlon^2)` and reads that record. **It never checks whether the
chosen record contains data.** In the SEUS 4 km forcing, 107661 of the 225625
points are ocean and hold constant sentinels - `FSDS = -1111.027 W/m2`,
`TBOT = 396 K`. The model grid is offset half a cell from the forcing grid, so
every gridcell takes a nearest neighbour, and 194 coastal land cells land on an
ocean point. They produce `GPP = 0` for the entire run, in every SEUS 4 km
simulation we have.

Deleting the sentinel rows is safe and sufficient. `ng` is counted from the file
at read time, and `grid_map` is column 4 - an explicit record index, not the row
position - so removing rows shifts nothing. A gridcell whose nearest point was
already valid keeps that same point, because only farther-or-equal candidates
were removed. **Exactly the 194 broken cells change; the other 75726 are
bit-identical.** Measured displacement for those 194: the nearest valid point is
3.30 km away against 3.27 km for the sentinel it uses today, i.e. the adjacent
land point instead of the adjacent ocean point. As a bonus the O(ng) search per
gridcell halves.

Deploy without touching world-shared data: build a private directory of symlinks
to the original files, then drop the filtered `zone_mappings.txt` in beside them
and point `metdata_bypass` at it. Nothing is copied - the seven forcing files
are 54 GB each.

Five directories need this for the SEUS 4 km chain:

    <root>/cpl_bypass_full                      spin-up and historical
    <root>/cpl_bypass_full/future_clim/ssp119   future scenarios
    <root>/cpl_bypass_full/future_clim/ssp245
    <root>/cpl_bypass_full/future_clim/ssp370
    <root>/cpl_bypass_full/future_clim/ssp585

Sentinels are detected from each directory's own FSDS file, so this works even
if a future_clim directory has a different grid or point count.

Usage (on Pathfinder)
---------------------
    python fix_zone_mappings.py --src <metdata dir> --dst <private dir>
    python fix_zone_mappings.py --src <metdata dir> --dst <private dir> --apply

Without --apply it reports what it would do and writes nothing.
"""

import argparse
import glob
import os

import numpy as np
import netCDF4 as nc

SENTINEL_FSDS = -1000.0     # valid shortwave never goes near this


def find_fsds(src: str) -> str:
    hits = sorted(glob.glob(os.path.join(src, "*_FSDS_*.nc")))
    if not hits:
        raise SystemExit(f"no *_FSDS_*.nc in {src}")
    return hits[0]


def sentinel_mask(fsds_path: str) -> np.ndarray:
    """True where a forcing record holds the ocean sentinel. One timestep is
    enough - the sentinel is constant for the whole record."""
    with nc.Dataset(fsds_path) as d:
        var = [v for v in d.variables if v.upper() == "FSDS"][0]
        first = np.ma.filled(d.variables[var][:, 0], np.nan).astype(np.float32)
    return first < SENTINEL_FSDS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="original metdata_bypass directory")
    ap.add_argument("--dst", required=True, help="private directory to create")
    ap.add_argument("--apply", action="store_true", help="write; otherwise dry run")
    args = ap.parse_args()

    src, dst = os.path.abspath(args.src), os.path.abspath(args.dst)
    zone_src = os.path.join(src, "zone_mappings.txt")
    if not os.path.exists(zone_src):
        raise SystemExit(f"no zone_mappings.txt in {src}")

    fsds = find_fsds(src)
    sent = sentinel_mask(fsds)
    print(f"source        {src}")
    print(f"sentinel scan {os.path.basename(fsds)}: {int(sent.sum())} of {sent.size} "
          f"records are ocean sentinels ({100*sent.mean():.1f}%)")

    rows = np.loadtxt(zone_src)
    idx = rows[:, 3].astype(int) - 1          # column 4 is the 1-based record index
    if idx.max() >= sent.size or idx.min() < 0:
        raise SystemExit("zone_mappings indices fall outside the forcing record range")
    keep = ~sent[idx]
    print(f"zone_mappings {len(rows)} rows -> keeping {int(keep.sum())}, "
          f"dropping {int((~keep).sum())} that point at sentinels")

    if not args.apply:
        print("\ndry run, nothing written. Re-run with --apply to create the directory.")
        return

    os.makedirs(dst, exist_ok=True)
    linked = 0
    for name in sorted(os.listdir(src)):
        if name == "zone_mappings.txt":
            continue
        target, link = os.path.join(src, name), os.path.join(dst, name)
        if os.path.lexists(link):
            os.unlink(link)
        os.symlink(target, link)
        linked += 1

    out = os.path.join(dst, "zone_mappings.txt")
    with open(zone_src) as fin, open(out, "w") as fout:
        for i, line in enumerate(fin):
            if i < len(keep) and keep[i]:
                fout.write(line)

    written = sum(1 for _ in open(out))
    print(f"\nwrote {dst}")
    print(f"  {linked} entries symlinked from the source (no data copied)")
    print(f"  zone_mappings.txt: {written} rows")
    print(f"\nNow set in user_nl_elm:\n  metdata_bypass = '{dst}'")
    print("\nVerify after a short run: count cells with landmask == 1 and "
          "annual-mean FSDS < 1. It should be zero.")


if __name__ == "__main__":
    main()
