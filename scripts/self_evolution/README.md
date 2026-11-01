# Running CGCNN seed 123

Run the following from the repository root after source has been committed/pushed and the server
has pulled it. Record every server connection in docs/agents/gpu.md first. Compute runs via Slurm.
Create the output directory before submission because Slurm opens log paths before executing jobs.

```bash
mkdir -p outputs/self_evolution/logs
sbatch scripts/slurm/self_evolution/setup.sbatch
sbatch --dependency=afterok:SETUP_JOB scripts/slurm/self_evolution/prepare.sbatch
sbatch --dependency=afterok:PREPARE_JOB \
  --export=ALL,CGCNN_TASK=formation_energy_peratom,CGCNN_STOP_ROUND=1,CGCNN_NO_CONTROLS=1 \
  scripts/slurm/self_evolution/task.sbatch
```

Replace SETUP_JOB/PREPARE_JOB with returned Slurm job IDs. Keep the proxy-owning SSH connection
live during setup/download; each network job verifies SOCKS access independently.
The runtime uses a dedicated `--system-site-packages` venv to read the already installed
torch 2.8.0+cu128, installs pinned task overrides only inside the venv, and records the full freeze
and effective paths. Never modify the inherited user packages. If PySocks is absent, bootstrap
its wheel into the venv before proxy-based pip; do not fall back to an unverified direct network.

After real pilot acceptance, run all tasks (one array element at a time on the single GPU):

```bash
sbatch --array=0-28%1 scripts/slurm/self_evolution/task.sbatch
sbatch --dependency=afterany:ARRAY_JOB scripts/slurm/self_evolution/summarize.sbatch
```

The same output root resumes the pilot without retraining verified stages. Production jobs run
rounds 0..5, required controls and deferred test evaluation. Do not set pilot-only environment
variables on production submissions. `CGCNN_RUNTIME_ROOT` and `CGCNN_WORK_ROOT` override absolute
runtime/work roots, provided both are visible to the selected compute node and persistent.

`run.py tasks` prints stable task-index mapping. `run.py --help` lists individual CLI actions.
Calling the CLI directly is intended for small tests or inside Slurm, not login-node training.
`inspect_environment.py` is metadata-only unless `--gpu` is supplied (GPU mode runs in Slurm).
Reports are under `<work>/run/reports`, including summary.json and the full task coverage table.
