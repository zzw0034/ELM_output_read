remote root: /projects/hpcl-cli185/proj-shared/zw5/paper_carbon_offset

# AGENTS.md — paper_carbon_offset

Folder rules for any agent (Codex, Cursor, Claude Code). The full rules are in
[CLAUDE.md](CLAUDE.md) and [README.md](README.md); read both. Keep this file
and CLAUDE.md consistent when either changes. The workspace-root `AGENTS.md`
safety rules apply in full.

Essentials:

- The remote root above (persistent proj-shared, same layout as this folder)
  overrides the scratch root of the parent `ELM_output_read`.
- `/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/paper_carbon_offset/` is
  the original backup: never run, edit or sync into it.
- Read [README.md](README.md), then [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md)
  Part A (current decisions), then [analysis_process_notes.md](analysis_process_notes.md)
  before working on the paper.
- Layout: `code/figure1..5`, `code/supplement`, shared `code/common.py` and
  `code/submit_py.sbatch`; `figures/figure1..5`, `supplement`, `legacy`.
- Record new extracts and decisions in the notes and blueprint in the same
  commit as the work.
