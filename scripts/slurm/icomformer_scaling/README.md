# iComformer Slurm stages

Run the lightweight `scripts/icomformer_scaling/bootstrap.py` first and create `outputs/icomformer_scaling/logs`. Then submit `check.sbatch`, followed by `prepare.sbatch` with `--dependency=afterok:CHECK_ID`. Check installs fixed pure-Python wheels offline in the independent task venv and validates native CPU behavior. Shared dependencies, the CGCNN venv and completed results are unchanged. Environment manifests record actual package versions and source.

The new root is `outputs/icomformer_scaling/jarvis2021-seed123-r012-v1`. Preparation requires every one of 55,712 structures to succeed; no failed graph is silently discarded. The old task labels/splits are reused by path. GPU/native/cache/resource acceptance and production training follow only after full preparation and training-interface tests. All computation, including preparation, tests and diagnostics, runs in Slurm.
