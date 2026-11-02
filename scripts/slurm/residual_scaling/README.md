# Residual validation Slurm entry points

Run from the repository root. Inputs are the audited existing CGCNN prepared library and paused R0–2 checkpoints. Outputs use `outputs/residual_scaling/cgcnn-seed123-r012-v1`; the old experiment is read only. The existing task venv is reused, with no dependency changes.

1. `mkdir -p outputs/residual_scaling/logs`
2. `sbatch scripts/slurm/residual_scaling/check.sbatch`: CPU regression in Slurm.
3. After CPU success, `sbatch scripts/slurm/residual_scaling/accept.sbatch`: full baseline import, four short diagnostic stages, full-library paired archives, direct chain parity and largest-batch backward memory. Diagnostics use separate paths and are excluded from scientific reports.
4. After acceptance success, `sbatch scripts/slurm/residual_scaling/study.sbatch`: at most four independent workers, eight residual branches with exact historical budgets, then validation-only reports. The dispatcher rejects changed acceptance/code/config/graphs.

Override `CGCNN_RUNTIME_ROOT`, `CGCNN_WORK_ROOT`, or `RESIDUAL_WORK_ROOT` only to select task-specific directories. No network access is required by these jobs. Logs and all generated artifacts are Git ignored. Failed stages preserve checkpoints and can resume with the same protocol. These entry points never release the old held report job or submit old 0–5 training.
