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

Replace SETUP_JOB/PREPARE_JOB with returned Slurm job IDs; PILOT_JOB, ACCEPT_JOB and ARRAY_JOB
below likewise denote actual returned IDs. Keep the proxy-owning SSH connection
live during online setup/download; each network job verifies SOCKS access independently.
Offline setup can instead set `CGCNN_WHEELHOUSE` to a task directory containing Linux cp310 wheels
and `SHA256SUMS`; all files are checked before pip uses `--no-index --find-links`.
Production pins the existing NumPy 2.2.6/pymatgen 2025.10.7/matplotlib 3.10.3 combination;
only the small missing pytest dependencies need transfer. A verified source ZIP transferred by scp
to the configured downloads directory also avoids a compute-node download; preparation still checks
official MD5 and size before reading records.
The build backend is explicitly pinned to setuptools 70.2.0 and wheel 0.45.1; setup checks the
installed project name/version, not only whether editable installation exits successfully.
For interrupted large-file transport, SFTP `reput` can resume to
`downloads/jdft_3d-8-18-2021.json.zip.scp.partial`; preparation verifies MD5/size before publishing it.
The runtime uses a dedicated `--system-site-packages` venv to read the already installed
torch 2.8.0+cu128, installs pinned task overrides only inside the venv, and records the full freeze
and effective paths. Never modify the inherited user packages. If PySocks is absent, bootstrap
its wheel into the venv before proxy-based pip; do not fall back to an unverified direct network.

After real pilot acceptance, run all tasks (one array element at a time on the single GPU):

```bash
sbatch --dependency=afterok:PILOT_JOB scripts/slurm/self_evolution/accept.sbatch
sbatch --dependency=afterok:ACCEPT_JOB --array=0-28%1 \
  --export=ALL,CGCNN_TASK=,CGCNN_STOP_ROUND=,CGCNN_NO_CONTROLS=0 \
  scripts/slurm/self_evolution/task.sbatch
sbatch --dependency=afterany:ARRAY_JOB scripts/slurm/self_evolution/summarize.sbatch
```

The same output root resumes the pilot without retraining verified stages. Production jobs run
rounds 0..5, required controls and deferred test evaluation. Do not set pilot-only environment
variables on production submissions. `CGCNN_RUNTIME_ROOT` and `CGCNN_WORK_ROOT` override absolute
runtime/work roots, provided both are visible to the selected compute node and persistent.
The current audited run uses `outputs/self_evolution/jarvis2021-seed123-final` as its work root;
pass that absolute path through `CGCNN_WORK_ROOT` on every submission that continues this run.

`run.py tasks` prints stable task-index mapping. `run.py --help` lists individual CLI actions.
Calling the CLI directly is intended for small tests or inside Slurm, not login-node training.
`accept_real.py` checks actual CUDA native/wrapper parity, batching and the two-stage cache chain
without reading labels. The full task array must depend on this gate as well as successful pilot.
It also runs `pilot_resources.py` on two independent model copies, recording full-library cache
bytes, first verified batch reads and fixed-batch surrogate forward/backward/Adam timings and
PyTorch peak allocation. These are not full-epoch peaks or raw disk bandwidth; no labels are read
and no authoritative checkpoint is updated. CUDA resource diagnostics require a Slurm allocation.
`inspect_environment.py` is metadata-only unless `--gpu` is supplied (GPU mode runs in Slurm).
Reports are under `<work>/run/reports`, including summary.json and the full task coverage table.

`profile_execution.py` is an optional isolated diagnostic. It snapshots a round-zero checkpoint,
does not read labels or alter authoritative weights, and checks a segment-mean pooling candidate
against the original forward and gradients using the already fixed numerical tolerances.
Rejected candidates remain rejected in diagnostic.json; the production model is unchanged.
When sharing an existing task-owned Slurm allocation through `srun --jobid=... --overlap`, record
that condition with `--shared-gpu`; these timings are exploratory, not exclusive-device benchmarks.

`execution_pool.py` is an optional full-matrix scheduler: eight waves (`--array=0-7%1`),
each covering up to four tasks in stable task-index order. It requires the real CUDA acceptance
and matching resource/config/core/geometry hashes. `pilot_resources.py` also probes the 64 structures
with the largest atom counts (or the configured smaller batch); an OOM is recorded explicitly and
forces the scheduler to one worker. Otherwise it caps workers using measured reserved memory,
CPU threads and host memory headroom. The GPU rule budgets twice the measured peak plus 1 GiB
per worker within 75% of device memory; host planning allows 8 GiB per worker. These margins do
not guarantee that every later allocation fits, so normal checkpoint/failure handling still applies.

Use `scripts/slurm/self_evolution/pool.sbatch` with the same `afterok` acceptance dependency as
the task array; select one full-matrix scheduler for a run. It reserves one GPU, 16 CPUs and 64 GiB,
with a 21-day limit to accommodate several complete tasks even if it falls back to one worker.
Per-task model/training budgets are unchanged. Each task keeps its own process/RNG/output namespace.
All training processes in a wave exit before serial evaluation and deployment timing begins.
Shared training wall seconds include contention and are not isolated GPU busy time; execution
contexts and observed wave wall seconds are included in summary.json. Failed task reports are
preserved under the wave directory, and prior attempt ledgers remain available on resume.
`pool_check.sbatch` runs CPU integration/orchestration checks under Slurm before enabling this path.

`cache_provenance.py` publishes the delivery manifest without changing immutable cache identities.
Each `round_NNN/cache_provenance.json` contains the complete configuration, source/geometry and
atom-order binding, checkpoint/parent/core identities, all successful IDs, failed IDs, and each
shard's verified SHA256, byte count and structure/atom counts. It references `cache/manifest.json`
by SHA256, and `chain_manifest.json` references each supplement by SHA256. The original manifest,
checkpoint and feature tensors remain unchanged. All stages are checked before supplements are
published, and rerunning the audit produces identical metadata. Task locks protect publication.

The `run` and pilot-acceptance entry points publish these manifests; `evaluate` first checks the
complete predeclared chain and every raw/cumulative control before any test evaluation. A missing
control, mismatched task/protocol or corrupt checkpoint/shard stops evaluation. Standalone full-cache
audits require Slurm. Audit IO is included in pool wave wall time, outside the original per-stage
cache-generation timer. Each CUDA `run`/`evaluate` also rechecks exact environment versions through
`inspect_environment.py` and records an action/PID-specific environment JSON, including late-starting
workers within an existing allocation.
