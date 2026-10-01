# Figure outputs

Organized by manuscript figure since 2026-10-01, matching [code/](../code/README.md):

| Folder | Contents |
|---|---|
| `figure1/` | Observational evaluation (Results 3.1). Local PNGs from `code/figure1/` |
| `figure2/` – `figure5/` | Main Figures 2–5. Scripts run on Pathfinder write to `figures/figureN/<PAPER_COHORT>/` there, so results from incompatible case versions are not mixed |
| `supplement/` | Supplementary diagnostics |
| [legacy/](legacy/) | Older exploratory PNGs from the former `outputs/` folder |

The legacy PNGs are **not** the five planned manuscript figures, and their
numerical annotations are void for the chosen paper cohort. See
[the legacy status](legacy/README.md).

Generated PNGs are ignored by Git (each folder keeps a `.gitkeep`). A final
figure release should record case, parameter and input versions, source
commit, variables, masks, time window, and cache provenance, then undergo
visual review.
