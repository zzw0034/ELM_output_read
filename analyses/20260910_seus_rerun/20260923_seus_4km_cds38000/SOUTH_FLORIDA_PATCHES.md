# South-Florida GPP patches in the 4 km future runs — what they are

Diagnosed 2026-09-23 while checking the `crit_dayl_stress = 38000 s` DF runs.
All three patterns below are present in the 36000 s and 38000 s runs, in DF and
Default alike — none of them is related to `crit_dayl_stress`.

Scripts (this folder, run through `submit_py.sbatch`): `diagnose_sfl_blocks.py`,
`diagnose_sfl_blocks2.py`, `diagnose_sfl_edge81w.py`, `diagnose_sfl_jan.py`,
`diagnose_sfl_jan_pft.py`, `diagnose_sfl_spinup.py`, `diagnose_sfl_forcing_hist.py`.
Outputs in `outputs/sfl_*`.

## 1. Dark 4 km squares in annual GPP (Tampa/Lakeland lakes, Miami coast) — land cover

Grid-cell GPP in h0 is per total land area (h1 `Σ GPP·pfts1d_wtgcell` equals the
h0 total, ratio 1.0000), so the lake/urban part of a cell counts as zero.
GPP jumps exactly where the natural-vegetation fraction jumps:

| field | jump ratio | signed corr |
|---|---|---|
| `PCT_NATVEG` (land use) | 8.3 | +0.99 |
| `PCT_LAKE` (surface data) | 5.8 | −0.98 |
| `PCT_URBAN` (surface data) | 5.5 | −0.96 |

Forcing, soil P / texture / organic matter, soil order and colour, FMAX, N/P
deposition and DF grass/C4 fractions all score 0.8–2.1 with correlation ≈ 0.
Real land cover; the "square" look is just the 4 km cell.

## 2. Bright single cells in JANUARY GPP, 27.3–28.6 N (38000 s runs) — evergreen shrub

Cells with up to ~16 % evergreen shrub (PFT 9, `BES_temp`). It is not
stress-deciduous, so it stays green while all grass/crop/BDS are dormant in
January at 38000 s. January is < 2 % of annual GPP, so these cells do not
show in annual maps. Winter rain, temperature and soil water were tested and
do not explain them (jump ratio 1.2–1.5, corr 0.1–0.3).

## 3. Straight N–S boundary at 80.73 W, 25.4–26.9 N — edge of the stranded-pine cluster

- 29 of 36 rows put the LAI step on the two edges at −80.75 / −80.708.
- East of it: TOTSOMC +6.5 kgC/m², more mineral N, weaker N limitation (FPG),
  higher LAI and GPP; in the 38000 s DF runs also a band that greens up
  faster in January.
- **No input steps there**: surface data (incl. FMAX, PCT_NAT_PFT 1850,
  hydrology and fire fields, soil P, texture, organic), historical and future
  forcing (steps 0.2–1.7× the local gradient, inconsistent sign), zone
  mapping (all zone 5), N/P deposition, land use and harvest.
- **It is already there in year 49 of the AD spin-up** (LAI step +1.9 with only
  +222 gC/m² of soil-C difference; fixed 1850 land cover, no harvest). The
  soil-C gap builds during the final spin-up (+6.3 → +6.6 kgC/m²) and then
  persists through the transient and the futures.
- It coincides with the east edge of `stranded_pine_mask_SEUS_1_24deg.nc`
  (in `20260910_seus_rerun_inputs/`): stranded share 61–75 % west of the line,
  39 % / 17 % in the two columns at it, 0 % east of it. The needleleaf
  evergreen patch (~17 % of those cells) sits at near-zero leaf carbon from the
  AD cold start on (the known evergreen-dieback problem; the mask metadata
  attributes it to fire at very low 1850 population density). Less litter →
  less soil C and N → the boundary. DF removes the trees but inherits the soil
  state, so its grass shows the same line.

Implication: the 291 south-Florida cells in the stranded-pine mask (and the
114 on the Big Bend / panhandle coast) should be excluded or flagged in
regional statistics for Default **and DF** — the DF grass there is N-poor
because of the stranded pine history, not because of the DF land use.
