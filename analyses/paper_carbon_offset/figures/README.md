# Figure outputs

New runs of the scripts in [code/](../code/) write into a separate directory
for each `PAPER_COHORT`, for example `figures/rerun_20260910/`. This avoids
mixing results from incompatible case versions.

[legacy/](legacy/) holds the older exploratory PNGs transferred from the
former `outputs/` folder. They are **not** the five planned manuscript
figures, and their numerical annotations are void for the chosen paper
cohort. See [the legacy status](legacy/README.md).

Generated PNGs are ignored by Git. A final figure release should record
case, parameter and input versions, source commit, variables, masks, time
window, and cache provenance, then undergo visual review.
