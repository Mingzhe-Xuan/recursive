# CPU diagnostic job

From the repository root create `outputs/recursive_diagnostics/logs`, then submit `sbatch scripts/slurm/recursive_diagnostics/analyze.sbatch`. The job first runs diagnostic unit/integration tests, then streams the existing paired archives and plots their results. Four CPUs, 12 GiB RAM, and 30 minutes are requested; no GPU or network is needed. The existing task venv is reused without dependency changes.

The default result root is `outputs/recursive_diagnostics/cgcnn-seed123-r012-v1`; `DIAGNOSTIC_ROOT` may select another task-specific root. All diagnostics and test artifacts are Git ignored. Old jobs and held report 893 are untouched.
