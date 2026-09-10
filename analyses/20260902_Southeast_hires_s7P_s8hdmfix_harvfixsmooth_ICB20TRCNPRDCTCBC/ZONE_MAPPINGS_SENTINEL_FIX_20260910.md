# zone_mappings.txt: removal of rows pointing at ocean sentinel records

Date: 2026-09-10   Performed by: zw5   Agreed with f9y, who owns
`cpl_bypass_full/zone_mappings.txt`

## 1. The problem

ELM's CPL_BYPASS meteorology reader
(`components/elm/src/cpl/lnd_import_export.F90`, around lines 411-436) loads
every row of `zone_mappings.txt`, then for each land gridcell picks the row
minimising the distance and reads that record:

```fortran
open(unit=13, file=trim(metdata_bypass) // '/zone_mappings.txt')
ng = 0
do v=1,500000
  read(13,*, end=10), longxy(v), latixy(v), zone_map(v), grid_map(v)
  ng = ng + 1
end do
...
mindist=99999
do g3 = 1,ng
  thisdist = 100*((latixy(g3) - ldomain%latc(g))**2 + (longxy(g3) - ldomain%lonc(g))**2)**0.5
  if (thisdist .lt. mindist) then
    mindist = thisdist;  ztoget = zone_map(g3);  gtoget = grid_map(g3)
  end if
end do
```

It takes whatever is nearest and **never checks whether that record contains
data**.

Of the 225,625 points in this forcing, **107,661 are ocean and hold constant
sentinel values**:

| variable | sentinel |
|---|---|
| `FSDS` | -1111.027 |
| `TBOT` | 396.001 K |
| `PRECTmms` | -0.088 |
| `PSRF` | -9999.086 |
| `FLDS` | 1000.989 |

All five variables flag the same set, and their union is also 107,661, leaving
117,964 valid points. `PSRF`'s -9999 is a conventional missing-value flag, so
these are deliberate no-data markers rather than corrupted data.

## 2. The consequence

The SEUS 4 km model grid is offset **half a cell** from this 4 km forcing grid -
model cell centres fall at forcing index + 0.5 - so every gridcell takes a
nearest neighbour, and a coastal one can land on the ocean point next door.

Measured: **194 land gridcells** (0.256% of land) read sentinels and produce
`GPP = 0`, **the same 194 in every SEUS 4 km run we have** - AD spin-up, final
spin-up, and the 2010 transient are identical. All sit on the immediate
coastline: Miami, Fort Lauderdale, Charlotte Harbor, Galveston Bay, the
Louisiana coast. Their `landfrac` is 1.000, so the model treats them as fully
land.

> Section 10 of `elm_setup_and_run_guide.md` documented a related coastal
> nearest-neighbour trap but stated it can never fire when the run resolution
> matches the forcing file's. That holds only if the two grids' cell centres
> coincide, which they do not here. That claim has been corrected.

## 3. The fix

**Delete only the `zone_mappings.txt` rows that point at sentinel records. No
`.nc` data is modified.**

This is safe because `ng` is counted from the file at read time and `grid_map` is
column 4 - an explicit record index, not a row position - so removing rows
shifts nothing.

More importantly, the rows removed are only ever candidates that were **farther
than or equal to** a valid one. A gridcell whose nearest point was already valid
keeps exactly that point. Therefore:

- **only the 194 broken cells change their mapping**
- the other 75,726 cells are **bit-identical**

Measured displacement for those 194: the nearest valid point is at 3.30 km -
median, mean, p90 and maximum are all 3.30 km - against the 3.27 km sentinel
they use today. Every one is within a single grid cell (4.6 km). They move from
the adjacent ocean point to the adjacent land point.

As a side effect `ng` drops from 225,625 to 117,964, halving the per-gridcell
O(ng) search at initialisation.

## 4. Files changed

| directory | used by | rows before | kept | dropped |
|---|---|---|---|---|
| `cpl_bypass_full/` | spin-up and historical | 225,625 | 117,964 | 107,661 |
| `future_clim/ssp119/` | 4 km future scenarios | 225,625 | 117,964 | 107,661 |
| `future_clim/ssp245/` | | 225,625 | 117,964 | 107,661 |
| `future_clim/ssp370/` | | 225,625 | 117,964 | 107,661 |
| `future_clim/ssp585/` | | 225,625 | 117,964 | 107,661 |

The five originals were byte-identical (md5 `cd20300f893cb80ed563d98aa67b1009`),
so the four `future_clim` copies derive from the historical one. The sentinel
set was nevertheless detected separately in each directory, from that
directory's own `FSDS` file, rather than assuming the future forcing shares the
historical ocean mask.

## 5. Procedure

Script: `fix_zone_mappings.py`, version-controlled at
`ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/`
in GitHub `zzw0034/ELM_output_read`.

Per directory, every step must pass before the next:

1. Detect the sentinel set from that directory's own `FSDS` file, sampling two
   timesteps at 50% and 80% through the record and taking their intersection.
2. Copy `zone_mappings.txt` to
   `zone_mappings.txt.orig_before_sentinel_fix_20260910` with `shutil.copy2`,
   then verify it byte-for-byte with `filecmp.cmp(shallow=False)`. Abort on
   mismatch.
3. Write the filtered table to `zone_mappings.txt.tmp_sentinel_fix` in the same
   directory.
4. Check the temporary file's row count equals the expected number kept.
5. Check that **every** index in the temporary file points at a non-sentinel
   record.
6. `os.replace` the temporary file over the original. The backup is never
   removed.

**Why sample at 50% and 80% rather than the first timestep.** The
`future_clim/*` files `DBCCA_Daymet_TESSFA2_FSDS_2023-2100_z01.nc` open with a
dummy block: for `t = 0..2918` - one year at 3-hourly steps - every one of the
225,625 points holds the sentinel. Reading `t = 0` there classifies the entire
table as sentinel and would delete every row. The first dry run reported exactly
that, which is why detection now samples the middle and later record and
discards any wholly-sentinel timestep as uninformative wherever it occurs. Worth
remembering for anything else that scans these files.

## 6. How to revert

```bash
cd <directory>
cp zone_mappings.txt.orig_before_sentinel_fix_20260910 zone_mappings.txt
```

The script never deletes the backup, and if one already exists it is kept rather
than overwritten, so the pristine original survives repeated invocations.

## 7. How to verify the fix

After a short run, count gridcells with `landmask == 1` and an annual-mean
`FSDS < 1`. It should be **zero**; before the fix it was 194.

```python
land = (landmask == 1)
bad = land & (annual_mean_FSDS < 1.0)
assert bad.sum() == 0
```

This check is worth adding to the setup of any new case, and has been added to
`elm_setup_and_run_guide.md`.

## 8. Who is affected

The change is a strict improvement: coastal cells that produced zero now produce
sensible carbon fluxes. It does change results, so:

- Runs completed before this date still contain zeros at those 194 cells and
  need them masked or flagged in any map or regional total.
- Anyone comparing runs across 2026-09-10 should not compare those 194 cells.
- The other 75,726 cells are unaffected and remain directly comparable.

## 9. Background

This was found while investigating something else: in the SEUS 4 km historical
simulations the evergreen PFTs - needleleaf evergreen temperate and broadleaf
evergreen shrub - sit at near-zero leaf carbon on a fraction of their patches
and never recover. The full record of that investigation is at
`ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/EVERGREEN_DIEBACK.md`.

The sentinel gridcells are a by-product of that investigation and are an
**independent problem** from the evergreen stranding.
