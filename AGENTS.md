remote root: /scratch/hpcl-cli185/zw5/ELM_output_read
source of truth: GitHub

# ELM_output_read

Local mirror/workspace for ELM output reading and analysis. See the workspace
root `AGENTS.md` for Pathfinder safety, SSH, and Slurm rules.

## Storage warning

This project's remote root is on **shared Lustre scratch**, which is temporary
and subject to purge. Consequences:

- Do not treat the remote copy as a backup of anything local.
- Do not assume a remote file still exists because it existed earlier; verify
  before relying on it.
- Move results worth keeping to `/projects/hpcl-cli185/proj-shared/zw5/` or
  another approved persistent location.

Keep durable analysis code and Slurm scripts in Git here. Keep NetCDF, figures,
and other generated products remote or in ignored local paths.

## Versioning model

GitHub is the authoritative version history for code, Slurm scripts,
documentation, and small configs. This local directory and the declared
Pathfinder remote root are mirrors/workspaces. Changes may originate locally or
on Pathfinder; after meaningful code/config/job/documentation changes, sync them
into this project Git repository, commit, and push to GitHub.

Use `scp` or `rsync` in either direction only after making the direction explicit:
`remote -> local` to refresh this mirror from Pathfinder, or `local -> remote` to
stage files on Pathfinder for a run. Do not use `rsync --delete` unless the user
explicitly requests that exact deletion behavior.
