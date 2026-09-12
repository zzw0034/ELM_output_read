# Have you seen evergreen PFTs die out during ELM spin-up?

In our ELM offline runs over a custom Southeast US grid, the evergreen PFTs go
to **exactly zero leaf carbon on a fraction of their patches during a cold-start
AD spin-up, and never come back**. Deciduous PFTs in the same gridcells are
unaffected.

Two independent chains, both cold-started, AD spin-up then final spin-up then
1850-2023 transient. Needleleaf evergreen temperate patches stranded at zero:
**9% in our 4 km chain, 78% at 0.5 degrees**. Broadleaf evergreen shrub goes the
same way. Of the seven PFTs in our domain, exactly the two with `evergreen = 1`
die and all five with `season_decid` or `stress_decid` survive.

Three things stand out. It is **binary**, not graded - at 4 km, 9.0% of pine
patches sit below LAI 0.01 and 90.9% above 1.0, with 0.5% in between. It is
**one-way** - 26 recoveries across ~800 model years and 63,000 patches. And it
is **set early** - the dead fraction reaches 8.9% by AD year 81 and then does
not move through 440 years of final spin-up and 174 transient years.

Our reading is that `CNEvergreenPhenology` sets `bgtr = 0` and has no onset
event, so an evergreen's leaves come only from current allocation, which
photosynthesis funds, which needs leaves - making zero leafc an absorbing state.
The deciduous subroutines flush `leafc_storage` into `leafc` each season, so
they always recover.

Three questions:

1. Have you seen this, at any resolution or domain?
2. Is that reading of `CNEvergreenPhenology` right - is there really no way back
   for a patch at near-zero `leafc` and `leafc_storage`, short of a `dwt_` seed
   flux from a land-cover transition?
3. If it is known, is there a recommended guard - initializing from a spun-up
   state instead of bare ground, a leaf carbon floor, or something else?

(We have identified what pushed the patches over in each chain, and both were
our own configuration problems. Happy to share the details, but the part we are
asking about is whether the trap itself is expected behaviour.)
