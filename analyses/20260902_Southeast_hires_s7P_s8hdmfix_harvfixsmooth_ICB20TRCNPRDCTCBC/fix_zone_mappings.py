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

Detecting on FSDS alone is exact, not a shortcut. Checked against all seven
variables in the historical file: FSDS, TBOT, PRECTmms, PSRF and FLDS each flag
the same 107661 records, and their union is also 107661, so the ocean set is
identical in every variable. Each carries its own marker - FSDS -1111.027,
TBOT 396.001 K, PRECTmms -0.088, PSRF -9999.086, FLDS 1000.989 - which is what
a deliberate no-data flag looks like rather than corrupted data. (QBOT and WIND
came back empty only because the probe's physical-range thresholds were wrong
for them; it makes no difference, since a record flagged in the other five is
unusable regardless.)

Two deployment modes
--------------------
`--dst <dir>` builds the private symlink directory described above and leaves the
original untouched. `--in-place` edits the directory given by `--src`: it copies
`zone_mappings.txt` to `zone_mappings.txt.orig_before_sentinel_fix_<date>`,
verifies the backup byte-for-byte, writes the filtered table to a temporary file
in the same directory, checks its row count and that every retained index points
at valid data, and only then renames it over the original. The backup is never
removed. If a backup from a previous run already exists it is kept and not
overwritten, so the pristine original survives repeated invocations.

Usage (on Pathfinder)
---------------------
    python fix_zone_mappings.py --src <metdata dir>                    # dry run
    python fix_zone_mappings.py --src <metdata dir> --in-place --apply
    python fix_zone_mappings.py --src <metdata dir> --dst <dir> --apply

Without --apply nothing is written in either mode.
"""

import argparse
import datetime
import filecmp
import glob
import os
import shutil

import numpy as np
import netCDF4 as nc

SENTINEL_FSDS = -1000.0     # valid shortwave never goes near this


def find_fsds(src: str) -> str:
    hits = sorted(glob.glob(os.path.join(src, "*_FSDS_*.nc")))
    if not hits:
        raise SystemExit(f"no *_FSDS_*.nc in {src}")
    return hits[0]


def sentinel_mask(fsds_path: str, fracs=(0.50, 0.80)) -> np.ndarray:
    """True where a forcing record holds the ocean sentinel.

    Do not sample the start of the record. The future DBCCA files open with a
    dummy block - in `DBCCA_Daymet_TESSFA2_FSDS_2023-2100_z01.nc` every point is
    the sentinel for t = 0..2918, one year at 3-hourly steps - so reading t = 0
    there flags all 225625 points and would delete the whole table. Sampling
    from the middle and later part of the record avoids it, and any wholly
    sentinel timestep is discarded as uninformative regardless of where it sits.
    A point counts as ocean only if it is flagged at every usable sample.
    """
    masks = []
    with nc.Dataset(fsds_path) as d:
        var = [v for v in d.variables if v.upper() == "FSDS"][0]
        nt = d.variables[var].shape[1]
        for f in fracs:
            t = min(int(nt * f), nt - 1)
            s = np.ma.filled(d.variables[var][:, t], np.nan).astype(np.float32)
            m = s < SENTINEL_FSDS
            if m.all():
                print(f"  t={t}: every point is sentinel, skipping as a dummy record")
                continue
            masks.append(m)
    if not masks:
        raise SystemExit("every sampled timestep is wholly sentinel; cannot detect "
                         "the ocean set from this file")
    return np.vstack(masks).all(axis=0)


def write_filtered(zone_src: str, out_path: str, keep: np.ndarray) -> int:
    """Write the retained rows, preserving each line verbatim."""
    written = 0
    with open(zone_src) as fin, open(out_path, "w") as fout:
        for i, line in enumerate(fin):
            if i < len(keep) and keep[i]:
                fout.write(line)
                written += 1
    return written


def do_in_place(src: str, zone_src: str, keep: np.ndarray, sent: np.ndarray) -> None:
    stamp = datetime.date.today().strftime("%Y%m%d")
    backup = f"{zone_src}.orig_before_sentinel_fix_{stamp}"

    if os.path.exists(backup):
        print(f"  backup already present, keeping it: {os.path.basename(backup)}")
    else:
        shutil.copy2(zone_src, backup)
        if not filecmp.cmp(zone_src, backup, shallow=False):
            raise SystemExit("backup does not match the original; aborting")
        print(f"  backed up  -> {os.path.basename(backup)} "
              f"({os.path.getsize(backup)} bytes, verified byte-for-byte)")

    tmp = f"{zone_src}.tmp_sentinel_fix"
    written = write_filtered(zone_src, tmp, keep)
    if written != int(keep.sum()):
        os.unlink(tmp)
        raise SystemExit(f"wrote {written} rows, expected {int(keep.sum())}; aborting")

    check = np.loadtxt(tmp)
    if sent[check[:, 3].astype(int) - 1].any():
        os.unlink(tmp)
        raise SystemExit("filtered table still points at sentinels; aborting")

    os.replace(tmp, zone_src)
    print(f"  rewrote    -> zone_mappings.txt ({written} rows, all indices verified valid)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="metdata_bypass directory to read")
    ap.add_argument("--dst", help="build a private symlink directory here")
    ap.add_argument("--in-place", action="store_true", dest="in_place",
                    help="back up and rewrite src/zone_mappings.txt instead")
    ap.add_argument("--apply", action="store_true", help="write; otherwise dry run")
    args = ap.parse_args()
    if bool(args.dst) == bool(args.in_place):
        raise SystemExit("give exactly one of --dst or --in-place")

    src = os.path.abspath(args.src)
    dst = os.path.abspath(args.dst) if args.dst else None
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
        mode = "rewrite it in place (with backup)" if args.in_place else f"build {dst}"
        print(f"\ndry run, nothing written. Re-run with --apply to {mode}.")
        return

    if args.in_place:
        do_in_place(src, zone_src, keep, sent)
        print("\nThe original stays valid at the .orig_before_sentinel_fix_* path.")
        print("Verify after a short run: count cells with landmask == 1 and "
              "annual-mean FSDS < 1. It should be zero.")
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
    written = write_filtered(zone_src, out, keep)
    print(f"\nwrote {dst}")
    print(f"  {linked} entries symlinked from the source (no data copied)")
    print(f"  zone_mappings.txt: {written} rows")
    print(f"\nNow set in user_nl_elm:\n  metdata_bypass = '{dst}'")
    print("\nVerify after a short run: count cells with landmask == 1 and "
          "annual-mean FSDS < 1. It should be zero.")


if __name__ == "__main__":
    main()
