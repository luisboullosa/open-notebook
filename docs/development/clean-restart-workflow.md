# Clean Restart Workflow (Keep Local Resources)

Use this workflow to restart from the latest upstream code while preserving local resources, configs, and migration notes.

## What this gives you

- a timestamped backup of local resources/config
- a fresh git worktree on top of `upstream/main`
- your existing workspace remains untouched

## Script

Run:

`./scripts/clean_restart_from_upstream.ps1`

Optional flags:

`./scripts/clean_restart_from_upstream.ps1 -WorktreePath ../open-notebook-clean -NewBranch restart/upstream-main`

## Backed up by default

- `.secrets`
- `docker.env`
- `docker.orangepi.env`
- `duckdns.env`
- `letsencrypt`
- `setup_guide/docker.env`
- `data/uploads`
- `notebook_data`
- `surreal_data`
- `surreal_single_data`
- `anki`
- `rebase_preservation`

Backups are stored under `local_backups/<timestamp>/` with git status/branch metadata.

## After running

1. Open the new folder (`../open-notebook-clean`) in VS Code.
2. Start from upstream defaults and re-apply only what you need.
3. Use your preservation matrix in:
   - `rebase_preservation/2026-02-18/unique_only/KEEP_DECISION_MATRIX.md`
4. Cherry-pick only selected commits/resources into the clean branch.

## Why this is safer than hard reset

- no destruction of your existing fork workspace
- rollback is easy (old workspace + backup folder)
- cleaner PR history from a fresh upstream base