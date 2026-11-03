# iComformer Slurm stages

Create `outputs/icomformer_scaling/logs` before submission. First submit `check.sbatch`, then `prepare.sbatch` with `--dependency=afterok:CHECK_ID`. Both use the already-created CGCNN task venv and leave all dependencies and completed experiments unchanged. Environment manifests record actual package versions and source.

The new root is `outputs/icomformer_scaling/jarvis2021-seed123-r012-v1`. Preparation requires every one of 55,712 structures to succeed; no failed graph is silently discarded. The old task labels/splits are reused by path. GPU/native/cache/resource acceptance and production training follow only after full preparation and training-interface tests. All computation, including preparation, tests and diagnostics, runs in Slurm.
