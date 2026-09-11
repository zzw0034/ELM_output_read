# Smoke test acceptance: 4 km AD rerun, both fixes active

Case `20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup`,
job 522838, 2 model years, 30 nodes, 3840 ranks, COMPLETED in 00:11:28 with
exit code 0 on 2026-09-11. Checks by job 522842, script `verify_smoketest.py`.

**All five checks pass.** What that licenses and what it does not is in the last
section.

## 1. Both fixes act in this one run

This is the first run with the corrected HDM reader **and** the repaired
`zone_mappings.txt` together. Until now each had only single-factor support.

| check | measured | verdict |
|---|---|---|
| `HDM` domain mean | **5.128131**, against 5.128 measured in job 522373 | PASS |
| `HDM` range | min 0.0047, max 39.53, not identically zero | PASS |
| land cells on sentinel forcing | **0 of 75,920** | PASS |
| minimum `FSDS` over land | 160.40 W/m2, against -1111.03 before the fix | PASS |
| `TBOT` range over land | 4.02 to 24.84 C, against a constant 122.85 before | PASS |

The executable carries the HDM fix by construction: `PROVENANCE.txt` records
`SRCROOT` at `17efedae5f` with no tracked modifications and no untracked files,
the build log that produced `e3sm.exe` has 573 `CPL_BYPASS` hits, and the
executable md5 is `b882ff67cf805c0ab95495890ffea1ec`.

**One thing to look at, not a failure.** Four land cells still report `GPP` at
or below zero in model year 2, down from 194. Their forcing is physical, so this
is not the sentinel problem. They are most likely genuinely unvegetated cells.
Identify them before the production run rather than after.

## 2. Annual fluxes complete, and h2 is the state the restart holds

All 14 requested flux fields are present on `h1`, including the five that are
`default='inactive'` in the source and whose absence is why job 522626 could not
split fire from background mortality: `M_LEAFC_TO_FIRE`,
`M_LEAFC_TO_LITTER_FIRE`, `M_LEAFC_TO_LITTER`, `M_LEAFC_STORAGE_TO_FIRE`,
`M_LEAFC_XFER_TO_FIRE`.

`h1` carries `cell_methods = "time: mean"`. `h2` carries
`cell_methods = "time: point"`.

**The h2 check was not decided on h2 differing from h1.** It required four
things at once:

| requirement | result |
|---|---|
| snapshot date equals restart date | both `30101`, model date 0003-01-01 |
| `cell_methods` says point sampling | `"time: point"` on LEAFC, TLAI, CPOOL |
| patch vectors align elementwise by `ixy`, `jxy`, veg type | 2,441,624 patches, identical |
| leaf carbon matches patch by patch | **max relative difference 6.0e-8** |

629,207 patches are reported by both files; the other 1,812,417 hold the
`1e36` fill value in `h2` because the tape does not carry inactive patches, and
they are excluded rather than compared. A first version of this check compared
fill against data and reported a spurious failure. The surviving 6.0e-8 is
single-precision rounding, `h2` being float32 and the restart float64. `TLAI`
agrees to 1.5e-8.

So the instantaneous tape does what the leaf budget needs: a year-boundary state
that pairs with the annual mean fluxes of the year that just ended.

## 3. The new build at 30 nodes

| item | measured |
|---|---|
| allocation | 30 nodes, 3840 single-threaded ranks |
| PIO tasks | **3840 compute, 30 I/O**, read from the Scorpio component names in `spio_stats` |
| write throughput | 128.1 MB/s, 19.5 GB written in 145 s |
| read throughput | 2401 MB/s |
| record structure | calendar `noleap`, expected interval 365 days, 3 records, 2 full years accepted, 1 rejected at 0.0417 days |

The 30 I/O tasks are one per node and follow from `PIO_STRIDE = 128` with 3840
ranks, confirmed from the run rather than inferred from the setting.

### Storage, corrected

Measured per record, which supersedes the estimate in
[AD_RERUN_CASE_CONFIG.md](AD_RERUN_CASE_CONFIG.md). That estimate assumed 34
fields on `h1`; the tape actually carries the reference 57 plus 20 additions.

| tape | measured per record | 200 model years |
|---|---|---|
| `h1` patch vector, annual mean | 926.5 MB | 185 GB |
| `h0` gridded, annual mean | 99.5 MB | 20 GB |
| `h2` patch vector, instantaneous | 159.5 MB | 32 GB |
| `elm.r` restart | 14.85 GB each | 119 GB at `REST_N = 25` |
| **total** | | **about 356 GB** |

Not 225 GB. Still about 2% of the 16.79 T already on scratch, so it does not
change the plan.

## 4. What this licenses, and what it does not

**Licensed:** starting the formal AD verification. The configuration, the
executable, the inputs, the output specification and the 30-node layout all
behave as designed, and both fixes act together in one run for the first time.

**Not licensed:** any statement about evergreen dieback. Two model years is
before establishment even completes. In job 522626 the median establishment year
is 6, the first fire events appear around year 7, and the declines cluster at
year 17. Nothing about the residual 405 patches, or about whether the combined
fix removes the stranding, can be read from a two-year run.

That question needs the trajectory across the two regime boundaries: nitrogen
limitation resuming at year 26, and the AD fuel formula switching at year 40.
Both lie inside the first 50-year segment.

**Not yet done:** `check_node_freq.sh` was not run, because the job finished in
11 minutes and node frequency has to be sampled under load. It runs five minutes
into the production run instead.
